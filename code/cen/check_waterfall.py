"""
Check that costs.py reproduces code/waterfall.py: the main panel's Composite, monthly
decile long-short with traded-days Corwin-Schultz spreads, against the saved table
results/verified/waterfall_schemes_traded_days.csv (Composite, long-short rows).

Run: python code/cen/check_waterfall.py
"""

import sys
from pathlib import Path

import pandas as pd

from costs import long_short, markit_by_secid, summary

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from config import DERIVED_SGX_EQUITIES, WRDS_SGX_EQUITIES, WRDS_WORLD_INDICES  # noqa: E402

PANEL = DERIVED_SGX_EQUITIES / "derived_sgx_broad_panel_m_1991_2026.csv"
SPREADS = DERIVED_SGX_EQUITIES / "derived_sgx_cs_spreads_traded_m_1993_2026.csv"
XW = DERIVED_SGX_EQUITIES / "derived_sgx_crosswalk_secid_isin_sedol_static.csv"
MARKIT = WRDS_SGX_EQUITIES / "wrds_markit_sg_secfinance_d_2002_2026.csv"
INDEX = WRDS_WORLD_INDICES / "wrds_compustat_world_index_constituents_a_1990_2026.csv"
BENCH = WRDS_WORLD_INDICES / "wrds_compustat_world_indices_m_1986_2026.csv"
SAVED = REPO / "results" / "verified" / "waterfall_schemes_traded_days.csv"
START = pd.Timestamp("2003-01-01")

q = pd.read_csv(PANEL, parse_dates=["Date"]).sort_values(["SecID", "Date"])
q["Ret"] = q["Return_1M"]
cs = pd.read_csv(SPREADS, parse_dates=["Date"])
mm = markit_by_secid(MARKIT, pd.read_csv(XW))
q = q.merge(mm, on=["SecID", "Date"], how="left").merge(cs, on=["SecID", "Date"], how="left")
q = q.sort_values(["SecID", "Date"])
for c in ["avail", "fee", "cs_half_bp", "adv_sgd"]:
    q[c + "_l"] = q.groupby("SecID")[c].shift(1)

wc = pd.read_csv(INDEX, parse_dates=["JuneDate"])
wc["SecID"] = wc["gvkey"].astype(str) + "_" + wc["iid"].astype(str)
snaps = sorted(wc["JuneDate"].unique())
lists = {s: set(wc.loc[wc.JuneDate == s, "SecID"]) for s in snaps}


def members(d):
    v = [s for s in snaps if s <= d]
    return lists[v[-1]] if v else None


mw = pd.read_csv(BENCH)
mw["date"] = pd.to_datetime(mw["date"]) + pd.offsets.MonthEnd(0)
bench = mw[mw["fic"] == "SGP"].set_index("date")["mportret"]

STAGES = [("Every month", "1. Gross signal", {}),
          ("Traded", "2. + spreads on traded names", {"use_cs": True, "traded": True}),
          ("Traded", "3. + Markit borrow availability screen", {"use_cs": True, "traded": True, "screen": True}),
          ("Traded", "4. + Markit borrow fee", {"use_cs": True, "traded": True, "screen": True, "fee": True})]
saved = pd.read_csv(SAVED)
saved = saved[(saved.Score == "Composite") & (saved.Book == "Long-short")]
rows = []
for costing, label, kw in STAGES:
    r, turnover = long_short(q, "Composite", members, START, **kw)
    got = {**summary(r, bench, label), "Turnover": round(turnover, 3)}
    want = saved[(saved.Costing == costing) & (saved.Stage == label)].iloc[0]
    for k in ["Ann%", "Alpha%mo", "t", "N", "Turnover"]:
        rows.append({"stage": label, "stat": k, "port": got[k], "waterfall": want[k], "gap": got[k] - want[k]})
out = pd.DataFrame(rows)
print(out.to_string(index=False))
print("max |gap|:", out.gap.abs().max())
