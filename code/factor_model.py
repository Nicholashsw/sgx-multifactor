"""
SGX Multi-Factor FYP A1083. factor_model.py
Run after pipeline.py: python factor_model.py

Cross-sectional factor construction, IC analysis, quintile diagnostics.

Conventions used throughout the project:
  Spearman rank IC at h=1 (next month), never contemporaneous. Contemporaneous
  IC is structurally wrong-signed for any price-denominated ratio because
  price sits in the denominator of the signal and the numerator of the return.

  Fundamentals carry a fixed 4-month reporting embargo (RDQ is unavailable
  for SGP, so the embargo is fixed rather than announcement-dated).

  Forward returns are joined by explicit point-in-time lookup on the next
  panel date, not groupby shift(-1). The shift variant produced a false
  U-shaped decile payoff in an earlier version of this project when the panel
  had gaps; it is banned here.

  Newey-West t-statistics at 6 lags on the IC series.
"""

import warnings

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

DATA_DIR = "."
EMBARGO_MONTHS = 4
NW_LAGS = 6

FUNDAMENTAL_COLS = ["PE_RATIO", "ROE", "PX_TO_BOOK", "DIV_YIELD", "BM_Ratio"]

FACTOR_SPECS = {
    # name         : (raw_col,     direction, description)
    "MOM_12_1":     ("MOM_12_1",   +1, "12-1 month total-return momentum"),
    "MOM_6_1":      ("MOM_6_1",    +1, "6-1 month total-return momentum"),
    "MOM_3_1":      ("MOM_3_1",    +1, "3-1 month total-return momentum"),
    "VALUE_BM":     ("BM_Ratio",   +1, "Book-to-market"),
    "VALUE_DY":     ("DIV_YIELD",  +1, "Dividend yield"),
    "VALUE_PE_INV": ("PE_RATIO",   -1, "Inverse PE"),
    "QUALITY_ROE":  ("ROE",        +1, "Return on equity"),
    "SIZE_SMALL":   ("LogMktCap",  -1, "Size, small tilt"),
    "LIQ_AMIHUD":   ("Amihud",     -1, "Illiquidity, liquid tilt"),
}

# Equal weights across available factors. Hand-tuned weights are a searched
# space; equal weighting is the pre-registered null. QUALITY_ROE is left out:
# it subtracted about 50 bps/month on the top-100 10-name book
# (REPORT_FINAL.md section 7). Add it back only when testing that result.
COMPOSITE_FACTORS = ["MOM_12_1", "VALUE_BM", "VALUE_DY", "SIZE_SMALL",
                     "LIQ_AMIHUD"]


def cs_zscore(s: pd.Series) -> pd.Series:
    mu, sig = s.mean(), s.std()
    return (s - mu) / sig if sig > 1e-9 else s * 0.0


def winsorise(s: pd.Series, lo=0.01, hi=0.99) -> pd.Series:
    return s.clip(s.quantile(lo), s.quantile(hi))


def nw_tstat(x: np.ndarray, lags: int = NW_LAGS) -> float:
    """Newey-West t-stat of the mean with Bartlett kernel."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < lags + 2:
        return np.nan
    e = x - x.mean()
    s = np.dot(e, e) / n
    for l in range(1, lags + 1):
        w = 1 - l / (lags + 1)
        s += 2 * w * np.dot(e[l:], e[:-l]) / n
    se = np.sqrt(s / n)
    return x.mean() / se if se > 0 else np.nan


def apply_embargo(panel: pd.DataFrame) -> pd.DataFrame:
    """Lag fundamental-derived columns by the fixed reporting embargo."""
    p = panel.sort_values(["Ticker", "Date"]).copy()
    for col in FUNDAMENTAL_COLS:
        if col in p.columns:
            p[col] = p.groupby("Ticker")[col].shift(EMBARGO_MONTHS)
    return p


def compute_factors(panel: pd.DataFrame) -> pd.DataFrame:
    p = panel.copy()
    for fname, (col, direction, _) in FACTOR_SPECS.items():
        if col not in p.columns or p[col].notna().sum() == 0:
            print(f"  Warning: {col} unusable, skipping {fname}")
            continue
        raw = p.groupby("Date")[col].transform(winsorise)
        p[f"Z_{fname}"] = direction * raw.groupby(p["Date"]).transform(cs_zscore)

    z_cols = [f"Z_{f}" for f in COMPOSITE_FACTORS if f"Z_{f}" in p.columns]
    if not z_cols:
        raise SystemExit("FACTOR ERROR: no usable factors, composite undefined")
    p["Composite"] = p[z_cols].mean(axis=1)
    return p


def add_forward_returns(panel: pd.DataFrame) -> pd.DataFrame:
    """Explicit PIT lookup of next calendar panel date. Not shift(-1)."""
    p = panel.copy()
    dates = np.sort(p["Date"].unique())
    nxt = {d: dates[i + 1] for i, d in enumerate(dates[:-1])}
    p["NextDate"] = p["Date"].map(nxt)
    ret = p[["Date", "Ticker", "Return_1M"]].rename(
        columns={"Date": "NextDate", "Return_1M": "Fwd_Return_1M"})
    p = pd.merge(p, ret, on=["NextDate", "Ticker"], how="left")
    return p.drop(columns=["NextDate"])


def compute_ic(panel: pd.DataFrame, factor_cols: list) -> pd.DataFrame:
    results = {}
    for fc in factor_cols:
        if fc not in panel.columns:
            continue
        ics = []
        for _, grp in panel.groupby("Date"):
            sub = grp[[fc, "Fwd_Return_1M"]].dropna()
            if len(sub) < 5:
                continue
            ic, _ = stats.spearmanr(sub[fc], sub["Fwd_Return_1M"])
            ics.append(ic)
        ic_arr = np.array(ics)
        if len(ic_arr) == 0:
            continue
        results[fc] = {
            "Mean_IC": round(ic_arr.mean(), 4),
            "IC_Std": round(ic_arr.std(), 4),
            "NW_t": round(nw_tstat(ic_arr), 3),
            "IR": round(ic_arr.mean() / ic_arr.std(), 3) if ic_arr.std() > 0 else 0,
            "n_periods": len(ic_arr),
            "Pct_Positive": round((ic_arr > 0).mean(), 3),
        }
    return pd.DataFrame(results).T.sort_values("NW_t", ascending=False)


def quintile_returns(panel: pd.DataFrame, score_col="Composite") -> pd.DataFrame:
    rows = []
    for date, grp in panel.groupby("Date"):
        sub = grp[[score_col, "Fwd_Return_1M"]].dropna()
        if len(sub) < 10:
            continue
        sub["Quintile"] = pd.qcut(sub[score_col], q=5,
                                  labels=["Q1_Low", "Q2", "Q3", "Q4", "Q5_High"])
        for q, qg in sub.groupby("Quintile"):
            rows.append({"Date": date, "Quintile": str(q),
                         "AvgReturn": qg["Fwd_Return_1M"].mean()})
    return pd.DataFrame(rows)


def main():
    print("=== Factor Model ===")
    panel = pd.read_csv(f"{DATA_DIR}/panel_stock.csv", parse_dates=["Date"])
    panel["Date"] = panel["Date"] + pd.offsets.MonthEnd(0)
    panel = panel[panel["Date"] >= "2005-01-01"].copy()
    print(f"  Panel: {len(panel):,} rows | {panel['Ticker'].nunique()} tickers")

    panel = apply_embargo(panel)
    print(f"  Applied {EMBARGO_MONTHS}-month fundamental embargo")

    panel = compute_factors(panel)
    panel = add_forward_returns(panel)

    print("\n=== Information Coefficients (h=1, NW 6 lags) ===")
    z_cols = [f"Z_{f}" for f in FACTOR_SPECS if f"Z_{f}" in panel.columns]
    z_cols.append("Composite")
    ic_df = compute_ic(panel, z_cols)
    print(ic_df.to_string())

    print("\n=== Quintile Returns (Composite) ===")
    qr = quintile_returns(panel)
    qs = qr.groupby("Quintile")["AvgReturn"].agg(["mean", "std", "count"])
    qs["Ann_Return"] = qs["mean"] * 12
    qs["Ann_Sharpe"] = qs["mean"] / qs["std"] * np.sqrt(12)
    print(qs.to_string())
    print("\nCheck the payoff shape before trusting the IC. Momentum's payoff "
          "on this market is U-shaped: IC does not convert to a monotone "
          "long-short spread.")

    panel.to_csv(f"{DATA_DIR}/panel_with_factors.csv", index=False)
    ic_df.to_csv(f"{DATA_DIR}/ic_results.csv")
    print("\nSaved panel_with_factors.csv and ic_results.csv")
    print("Next: python backtest.py")


if __name__ == "__main__":
    main()
