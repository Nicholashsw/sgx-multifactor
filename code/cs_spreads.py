"""
Monthly Corwin-Schultz spreads and the SecID to ISIN/SEDOL crosswalk, built from the
Compustat Global Security Daily extract (ledger D1, D4, D14r).

Needs pyvzpcslf5l2s1kh.csv (Compustat Global Security Daily, Singapore, with isin,
sedol, prchd and prcld) in the working folder. Licensed, not shipped.

Two recipes:
  naive   the published estimator on every day with a valid high and low. This is
          what the cost waterfall used, and it rebuilds cs_spreads_monthly.csv.
  traded  drops zero-volume and zero-range days first, and day pairs more than five
          calendar days apart. On SGX many illiquid names have days with no trade or
          one price; the naive recipe reads those as a zero spread, so illiquid names
          come out cheaper than liquid ones (ledger D4).

Run: python cs_spreads.py naive    writes crosswalk_secid_isin_sedol.csv, cs_spreads_monthly.csv
     python cs_spreads.py traded   writes cs_spreads_traded.csv
Both print median half-spreads by liquidity tercile.
"""

import sys

import numpy as np
import pandas as pd

DAILY = "pyvzpcslf5l2s1kh.csv"
USE = ["gvkey", "iid", "datadate", "isin", "sedol", "curcdd", "exchg", "tpci",
       "prccd", "prchd", "prcld", "cshtrd"]
K = 3 - 2 * np.sqrt(2)


def load():
    """SGD common stock on the SGX main board and Catalist."""
    keep = []
    for ch in pd.read_csv(DAILY, usecols=USE, chunksize=500_000, low_memory=False):
        keep.append(ch[(ch["curcdd"] == "SGD") & (ch["tpci"].astype(str) == "0") & (ch["exchg"].isin([251, 252]))])
    d = pd.concat(keep, ignore_index=True)
    d["datadate"] = pd.to_datetime(d["datadate"])
    d["SecID"] = d["gvkey"].astype(str) + "_" + d["iid"].astype(str)
    for c in ["prccd", "prchd", "prcld", "cshtrd"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d


def spread(h, l, h1, l1):
    """Corwin-Schultz spread from two consecutive days' highs and lows, negatives set to zero."""
    beta = np.log(h / l) ** 2 + np.log(h1 / l1) ** 2
    gamma = np.log(np.maximum(h, h1) / np.minimum(l, l1)) ** 2
    a = (np.sqrt(2 * beta) - np.sqrt(beta)) / K - np.sqrt(gamma / K)
    s = 2 * (np.exp(a) - 1) / (1 + np.exp(a))
    return np.where(s > 0, s, 0.0)


def naive(d):
    d = d.sort_values(["SecID", "datadate"])
    d = d[(d["prchd"] > 0) & (d["prcld"] > 0) & (d["prchd"] >= d["prcld"])]
    g = d.groupby("SecID")
    d = d.assign(H1=g["prchd"].shift(-1), L1=g["prcld"].shift(-1))
    d = d[d["H1"].notna() & d["L1"].notna()].copy()
    d["cs"] = spread(d["prchd"], d["prcld"], d["H1"], d["L1"])
    d["Date"] = d["datadate"] + pd.offsets.MonthEnd(0)
    m = d.groupby(["SecID", "Date"]).agg(cs=("cs", "mean"), advol=("cshtrd", "mean"),
                                         px=("prccd", "last")).reset_index()
    m["adv_sgd"] = m["advol"] * m["px"]
    m["cs_half_bp"] = m["cs"] / 2 * 1e4
    return m[["SecID", "Date", "cs_half_bp", "adv_sgd"]]


def traded(d):
    d = d.sort_values(["SecID", "datadate"])
    d = d[(d["prchd"] > 0) & (d["prcld"] > 0) & (d["prchd"] >= d["prcld"])]
    d = d.assign(Date=d["datadate"] + pd.offsets.MonthEnd(0))
    adv = d.groupby(["SecID", "Date"]).agg(advol=("cshtrd", "mean"), px=("prccd", "last"))

    t = d[(d["prchd"] > d["prcld"] * (1 + 1e-12)) & (d["cshtrd"].fillna(0) > 0)].copy()
    g = t.groupby("SecID")
    s = spread(t["prchd"], t["prcld"], g["prchd"].shift(1), g["prcld"].shift(1))
    s = pd.Series(s, index=t.index).where(g["datadate"].diff().dt.days <= 5)
    t["cs"] = s.where(s <= 0.5)  # above 50% is not a believable spread
    m = t.groupby(["SecID", "Date"])["cs"].agg(cs="mean", nd="size")
    m = m[m["nd"] >= 5].join(adv).reset_index()
    m["adv_sgd"] = m["advol"] * m["px"]
    m["cs_half_bp"] = m["cs"] / 2 * 1e4
    return m[["SecID", "Date", "cs_half_bp", "adv_sgd"]]


def by_tercile(m):
    """Median half-spread (bp) by monthly liquidity tercile."""
    x = m.dropna(subset=["adv_sgd", "cs_half_bp"]).copy()
    x["r"] = x.groupby("Date")["adv_sgd"].rank(pct=True)
    x["tercile"] = pd.cut(x["r"], [0, 1 / 3, 2 / 3, 1], labels=["illiquid", "middle", "liquid"],
                          include_lowest=True)
    return x.groupby("tercile", observed=True)["cs_half_bp"].median().round(1)


if __name__ == "__main__":
    recipe = sys.argv[1] if len(sys.argv) > 1 else ""
    if recipe not in ("naive", "traded"):
        raise SystemExit("usage: python cs_spreads.py naive|traded")
    d = load()
    print(f"daily rows: {len(d):,}, securities: {d['SecID'].nunique()}")
    if recipe == "naive":
        xw = d.groupby("SecID").agg(isin=("isin", "last"), sedol=("sedol", "last")).reset_index()
        xw.to_csv("crosswalk_secid_isin_sedol.csv", index=False)
        m = naive(d)
        out = "cs_spreads_monthly.csv"
    else:
        m = traded(d)
        out = "cs_spreads_traded.csv"
    m.to_csv(out, index=False)
    print(f"{out}: {len(m):,} name-months, median half-spread {m['cs_half_bp'].median():.1f} bp")
    print(by_tercile(m).to_string())
