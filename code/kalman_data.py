"""
Compustat loader and market proxy for the Kalman hedge ratio study (labelled
extension, see results/kalman/PREREG.md). The tests live in kalman_hedge.py.

TR index is prccd / ajexdi * trfd (trfd missing -> 1), on the primary SGD issue of
each gvkey. Each name is matched to Bloomberg by company name and checked: month-end
TR returns must correlate above 0.99 with Bloomberg's, or the run stops. On stale
days (no shares traded, or an unchanged price on zero volume) the TR level is set
to missing, so neither that day nor the next earns a return.

The market series is a cap-weighted proxy built from the same names, weights
prccd x cshoc lagged one period, leave-one-out: hedging name i uses the proxy
without i. It is not the STI. Nothing here writes vendor data to the repo.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from kalman_hedge import load_bloomberg_monthly

DATA = Path("/Users/nick/Documents/datasets/SGX/STI SGX2")
DAILY_CSV = DATA / "pyvzpcslf5l2s1kh.csv"
BBG_XLSM = Path("/Users/nick/Downloads/bloombergapi4_fixed.xlsm")
MATCH_MIN_CORR = 0.99
PROXY_LABEL = "25-name cap-weighted LOO proxy, not the STI"

# Bloomberg ticker -> exact Compustat company name (conm)
CONM = {
    "CICT": "CAPITALAND INTEGRATED COMMER", "CIT": "CITY DEVELOPMENTS LTD",
    "CLAR": "CAPITALAND ASCENDAS REIT", "CLI": "CAPITALAND INVESTMENT LTD",
    "DBS": "DBS GROUP HOLDINGS LTD", "FCT": "FRASERS CENTREPOINT TRUST",
    "FLT": "FRASERS LOGISTICS & INDUST", "GENS": "GENTING SINGAPORE LTD",
    "KDCREIT": "KEPPEL DC REIT", "KEP": "KEPPEL LTD",
    "MINT": "MAPLETREE INDUSTRIAL TRUST", "MLT": "MAPLETREE LOGISTICS TRUST",
    "MPACT": "MAPLETREE PAN ASIA", "OCBC": "OVERSEA CHINESE BANKING",
    "SATS": "SATS LTD", "SCI": "SEMBCORP INDUSTRIES LTD",
    "SGX": "SINGAPORE EXCHANGE LIMITED", "SIA": "SINGAPORE AIRLINES LTD",
    "ST": "SINGAPORE TELECOMMUNICATIONS", "STE": "SINGAPORE TECHNOLOGIES ENGR",
    "STM": "SEATRIUM LIMITED", "UOB": "UNITED OVERSEAS BANK LTD",
    "UOL": "UOL GROUP LTD", "VMS": "VENTURE CORP LTD", "WIL": "WILMAR INTERNATIONAL LTD",
}
# Not in the extract, which holds Singapore-incorporated issuers only (fic = SGP)
EXCLUDED = {"DFI", "HKL", "JM", "THBEV", "YZJSGD"}

USE = ["gvkey", "iid", "datadate", "conm", "curcdd", "prirow", "prccd", "ajexdi", "trfd",
       "cshtrd", "cshoc"]


def _read_daily(path: Path = DAILY_CSV) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Compustat daily file not found: {path}")
    d = pd.read_csv(path, usecols=USE, dtype={"gvkey": str, "iid": str, "prirow": str})
    d = d[(d["curcdd"] == "SGD") & (d["iid"] == d["prirow"])]      # primary SGD issue
    d["datadate"] = pd.to_datetime(d["datadate"])
    return d


def match_names(d: pd.DataFrame) -> pd.DataFrame:
    """Ticker -> gvkey by exact conm; exactly one gvkey per name or the run stops."""
    rows = []
    for tick, name in CONM.items():
        g = sorted(d.loc[d["conm"] == name, "gvkey"].unique())
        if len(g) != 1:
            raise RuntimeError(f"{tick}: {len(g)} gvkeys for conm {name!r}")
        rows.append({"ticker": tick, "conm": name, "gvkey": g[0]})
    return pd.DataFrame(rows)


def compustat_panel(d: pd.DataFrame, names: pd.DataFrame):
    """Daily TR index (missing on stale days) and market cap, date x ticker."""
    d = d[d["gvkey"].isin(names["gvkey"])].copy()
    d["tick"] = d["gvkey"].map(dict(zip(names["gvkey"], names["ticker"])))
    d["tr"] = d["prccd"] / d["ajexdi"] * d["trfd"].fillna(1.0)
    d["cap"] = d["prccd"] * d["cshoc"]
    wide = lambda col: d.pivot_table(index="datadate", columns="tick", values=col, aggfunc="last")
    tr = wide("tr").sort_index()
    px, vol, cap = (wide(c).reindex(tr.index) for c in ("prccd", "cshtrd", "cap"))
    stale = (vol == 0) | ((px.diff() == 0) & (vol.fillna(0) == 0))
    return tr.mask(stale)[list(CONM)], cap[list(CONM)], stale[list(CONM)]


def month_end(frame: pd.DataFrame) -> pd.DataFrame:
    """Last available value in each calendar month, indexed by month-end date."""
    m = frame.groupby(frame.index.to_period("M")).last()
    m.index = m.index.to_timestamp("M")
    return m


def verify_matches(tr_daily: pd.DataFrame, bbg_tr: pd.DataFrame, names: pd.DataFrame) -> pd.DataFrame:
    """Correlation of month-end Compustat TR returns with Bloomberg's, per name."""
    me = month_end(tr_daily)
    out = names.copy()
    for i, r in out.iterrows():
        j = pd.concat([me[r["ticker"]].pct_change(fill_method=None),
                       bbg_tr[r["ticker"]].pct_change(fill_method=None)], axis=1).dropna()
        out.loc[i, "months"] = len(j)
        out.loc[i, "corr"] = j.iloc[:, 0].corr(j.iloc[:, 1])
    out["status"] = np.where(out["corr"] > MATCH_MIN_CORR, "ok", f"corr below {MATCH_MIN_CORR}")
    return out


def loo_proxy(ret: pd.DataFrame, cap: pd.DataFrame) -> pd.DataFrame:
    """Cap-weighted market return with weights lagged one period: a column per name
    leaving that name out, plus 'EW book' with every name in."""
    w = cap.shift(1).where(ret.notna())          # a name counts only when it has a return
    num = (w * ret).sum(axis=1, min_count=1)
    den = w.sum(axis=1, min_count=1)
    out = {n: (num - (w[n] * ret[n]).fillna(0)) / (den - w[n].fillna(0)) for n in ret.columns}
    out["EW book"] = num / den
    return pd.DataFrame(out)


def load_compustat(freq: str = "daily"):
    """TR index and LOO proxy for the 25 matched names at 'daily' or 'monthly' frequency.
    Stops if any matched name fails the Bloomberg check."""
    d = _read_daily()
    names = match_names(d)
    tr, cap, stale = compustat_panel(d, names)
    bbg_tr, _ = load_bloomberg_monthly(BBG_XLSM)
    table = verify_matches(tr, bbg_tr, names)
    failed = table[table["status"] != "ok"]
    if len(failed):
        raise RuntimeError("names failed the match check:\n" + failed.to_string(index=False))
    if freq == "monthly":
        tr, cap = month_end(tr), month_end(cap)
    elif freq != "daily":
        raise ValueError(f"freq must be daily or monthly, not {freq!r}")
    proxy = loo_proxy(tr.pct_change(fill_method=None), cap)
    return tr, proxy, table, stale


if __name__ == "__main__":
    tr, proxy, table, stale = load_compustat("daily")
    print(table.to_string(index=False))
    print(f"excluded (not in the extract): {sorted(EXCLUDED)}")
    print(f"daily TR {tr.index.min().date()} to {tr.index.max().date()}, {tr.shape[1]} names; "
          f"stale days set to missing: {int(stale.sum().sum())}")
    print(f"market: {PROXY_LABEL}")
