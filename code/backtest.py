"""
SGX Multi-Factor FYP A1083. backtest.py
Run after factor_model.py: python backtest.py

Monthly rebalanced long-only and long-short backtest with transaction costs,
regime breakdown, and walk-forward validation with actual per-window training.

Honesty notes baked into the design:
  1. The earlier walk-forward in this project was degenerate: it re-ran the
     same fixed-weight strategy on date slices, so OOS equalled IS by
     construction. Here the composite weights are re-estimated on each
     training window from trailing ICs, so the walk-forward tests something.
  2. Flat 10 bp costs understate SGX reality. The locked project finding is
     that per-name Corwin-Schultz spreads average 0.906%/mo of drag on the
     broad-universe composite. TC_BPS here is a floor; report both.
  3. No borrow modelling on the short leg in this file. The locked finding
     is that availability, not fee, is binding (22.6% of short-leg names
     with zero lendable inventory). Long-short numbers from this file are
     upper bounds and are labelled as such.
  4. On a 6-name book, absolute position caps are infeasible (a 15% cap
     silently reverts to equal weighting). Equal weighting is used and
     stated, not disguised as an optimised book.
"""

import warnings

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

DATA_DIR = "."

BACKTEST_START = "2006-01-01"
BACKTEST_END = "2026-01-31"
N_LONG = 6
N_SHORT = 6
TC_BPS = 10                # one-way, a floor; see header note 2
RISK_FREE_ANN = 0.01412    # MASB3M
RF_M = RISK_FREE_ANN / 12
NW_LAGS = 6

Z_FACTORS = ["Z_MOM_12_1", "Z_VALUE_BM", "Z_VALUE_DY", "Z_SIZE_SMALL",
             "Z_LIQ_AMIHUD"]


def sharpe(r: pd.Series) -> float:
    e = r - RF_M
    return e.mean() / e.std() * np.sqrt(12) if e.std() > 0 else 0


def sortino(r: pd.Series) -> float:
    e = r - RF_M
    d = e[e < 0].std()
    return e.mean() / d * np.sqrt(12) if d and d > 0 else 0


def max_drawdown(cum: pd.Series) -> float:
    return ((cum - cum.cummax()) / cum.cummax()).min()


def nw_tstat(x: pd.Series, lags: int = NW_LAGS) -> float:
    x = np.asarray(x.dropna(), dtype=float)
    n = len(x)
    if n < lags + 2:
        return np.nan
    e = x - x.mean()
    s = np.dot(e, e) / n
    for l in range(1, lags + 1):
        s += 2 * (1 - l / (lags + 1)) * np.dot(e[l:], e[:-l]) / n
    se = np.sqrt(s / n)
    return x.mean() / se if se > 0 else np.nan


def perf_summary(r: pd.Series, label: str) -> dict:
    cum = (1 + r).cumprod()
    ann = (1 + r).prod() ** (12 / len(r)) - 1
    return {
        "Strategy": label,
        "Ann_Return_%": round(ann * 100, 2),
        "Ann_Vol_%": round(r.std() * np.sqrt(12) * 100, 2),
        "Sharpe": round(sharpe(r), 3),
        "Sortino": round(sortino(r), 3),
        "Max_DD_%": round(max_drawdown(cum) * 100, 2),
        "Hit_Rate_%": round((r > 0).mean() * 100, 1),
        "NW_t_mean": round(nw_tstat(r), 2),
        "N_Months": len(r),
    }


def estimate_weights(train: pd.DataFrame) -> dict:
    """Trailing-IC weights on the training window only, floored at zero.
    Falls back to equal weights when the window is too short. Equal weights
    are the pre-registered null; learned weights must beat them to matter."""
    ics = {}
    for f in Z_FACTORS:
        if f not in train.columns:
            continue
        per = []
        for _, g in train.groupby("Date"):
            sub = g[[f, "Fwd_Return_1M"]].dropna()
            if len(sub) >= 5:
                per.append(stats.spearmanr(sub[f], sub["Fwd_Return_1M"])[0])
        if per:
            ics[f] = max(np.mean(per), 0.0)
    tot = sum(ics.values())
    if tot <= 0 or len(ics) == 0:
        avail = [f for f in Z_FACTORS if f in train.columns]
        return {f: 1 / len(avail) for f in avail}
    return {f: v / tot for f, v in ics.items()}


def score_panel(panel: pd.DataFrame, weights: dict) -> pd.Series:
    s = pd.Series(0.0, index=panel.index)
    for f, w in weights.items():
        if f in panel.columns:
            s = s + w * panel[f].fillna(0)
    return s


def run_backtest(panel: pd.DataFrame, weights: dict, start: str, end: str,
                 label: str) -> pd.DataFrame:
    sub = panel[(panel["Date"] >= start) & (panel["Date"] <= end)].copy()
    sub["Score"] = score_panel(sub, weights)
    dates = sorted(sub["Date"].unique())
    results, prev_long, prev_short = [], [], []

    for i, d in enumerate(dates[:-1]):
        curr = sub[sub["Date"] == d].dropna(subset=["Score"])
        curr = curr.sort_values("Score", ascending=False)
        if len(curr) < N_LONG + N_SHORT:
            continue
        long_t = curr.head(N_LONG)["Ticker"].tolist()
        short_t = curr.tail(N_SHORT)["Ticker"].tolist()

        nd = dates[i + 1]
        nxt = sub[sub["Date"] == nd].set_index("Ticker")["Return_1M"]
        lg = nxt.reindex(long_t).mean()
        sg = nxt.reindex(short_t).mean()
        bm = sub[sub["Date"] == nd]["Return_1M"].mean()

        lto = len(set(long_t) - set(prev_long)) / N_LONG if prev_long else 1.0
        sto = len(set(short_t) - set(prev_short)) / N_SHORT if prev_short else 1.0

        ln = lg - lto * TC_BPS / 1e4
        sn = -sg - sto * TC_BPS / 1e4 if not np.isnan(sg) else np.nan
        row = curr.iloc[0]
        results.append({
            "Date": nd, "LongReturn_Net": ln, "LongReturn_Gross": lg,
            "ShortReturn_Net": sn,
            "LSReturn_Net": ln + sn if not np.isnan(sn) else np.nan,
            "BenchmarkReturn": bm, "LongTurnover": lto,
            "LongTickers": "|".join(long_t), "ShortTickers": "|".join(short_t),
            "Regime_RiskOn": row.get("Regime_RiskOn", np.nan),
            "Regime_SGGrowth": row.get("Regime_SGGrowth", np.nan),
            "VIX": row.get("VIX", np.nan), "SG_PMI": row.get("SG_PMI", np.nan),
            "Label": label,
        })
        prev_long, prev_short = long_t, short_t
    return pd.DataFrame(results)


def walk_forward(panel: pd.DataFrame, train_months=60, test_months=12):
    """Estimate weights on each training window, apply to the next test
    window. Weights change per window: this is a real walk-forward."""
    dates = sorted(panel["Date"].unique())
    out = []
    i = train_months
    while i + test_months <= len(dates):
        tr = panel[(panel["Date"] >= dates[i - train_months])
                   & (panel["Date"] <= dates[i - 1])]
        w = estimate_weights(tr)
        te_start = str(pd.Timestamp(dates[i]).date())
        te_end = str(pd.Timestamp(dates[min(i + test_months - 1,
                                            len(dates) - 1)]).date())
        out.append(run_backtest(panel, w, te_start, te_end,
                                f"OOS_{te_start[:7]}"))
        i += test_months
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def regime_breakdown(res: pd.DataFrame, ret_col="LongReturn_Net"):
    rows = []
    for rc in ["Regime_RiskOn", "Regime_SGGrowth"]:
        if rc not in res.columns:
            continue
        for val in [0, 1]:
            s = res.loc[res[rc] == val, ret_col].dropna()
            if len(s) < 6:
                continue
            rows.append({"Regime": f"{rc}={val}",
                         "Ann_Return_%": round(s.mean() * 12 * 100, 2),
                         "Ann_Vol_%": round(s.std() * np.sqrt(12) * 100, 2),
                         "Sharpe": round(sharpe(s), 3), "N_Months": len(s)})
    return pd.DataFrame(rows)


def main():
    print("=== Backtest Engine ===")
    panel = pd.read_csv(f"{DATA_DIR}/panel_with_factors.csv",
                        parse_dates=["Date"])
    panel["Date"] = panel["Date"] + pd.offsets.MonthEnd(0)
    panel = panel[panel["Date"] >= BACKTEST_START].copy()
    print(f"  Panel: {len(panel):,} rows | {panel['Ticker'].nunique()} tickers")

    is_train = panel[panel["Date"] < "2011-01-01"]
    weights = estimate_weights(is_train)
    print("  Full-period weights (estimated on pre-2011 only):")
    for f, w in weights.items():
        print(f"    {f:16s}: {w:.1%}")

    res = run_backtest(panel, weights, BACKTEST_START, BACKTEST_END, "Full")
    res.to_csv(f"{DATA_DIR}/backtest_results.csv", index=False)

    print("\n=== Performance Summary ===")
    perf = pd.DataFrame([
        perf_summary(res["LongReturn_Net"].dropna(),
                     f"Long-Only Top {N_LONG}, net {TC_BPS}bp"),
        perf_summary(res["LSReturn_Net"].dropna(),
                     "Long-Short, net, NO BORROW MODELLED (upper bound)"),
        perf_summary(res["BenchmarkReturn"].dropna(),
                     "Equal-Weight Universe"),
    ])
    print(perf.to_string(index=False))

    print("\n=== Regime Breakdown (Long-Only) ===")
    print(regime_breakdown(res).to_string(index=False))

    print(f"\n  Avg monthly long turnover: {res['LongTurnover'].mean():.1%}")

    print("\n  Walk-forward (60M train, 12M test, weights re-estimated "
          "per window)...")
    oos = walk_forward(panel)
    if not oos.empty:
        print("\n=== Walk-Forward OOS ===")
        print(pd.DataFrame([
            perf_summary(oos["LongReturn_Net"].dropna(), "OOS Long-Only"),
            perf_summary(oos["LSReturn_Net"].dropna(),
                         "OOS Long-Short (upper bound)"),
        ]).to_string(index=False))
        oos.to_csv(f"{DATA_DIR}/backtest_oos.csv", index=False)

    print("\nSaved backtest_results.csv and backtest_oos.csv")
    print("Costs here are a floor. See REPORT.md section 6 for the full "
          "Corwin-Schultz plus Markit waterfall on the broad universe.")


if __name__ == "__main__":
    main()
