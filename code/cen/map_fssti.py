"""
Map the Bloomberg FSSTI year-end rosters (2008 to 2018 snapshots, used for 2009 to 2019)
to Compustat SecIDs, for the A2 STI robustness check.

Route: Bloomberg ticker -> ISIN through the Markit bb_ticker field (the Markit row
nearest the snapshot date) -> SecID through the crosswalk. Tickers Markit cannot place
are mapped by Compustat company name where the firm is in the SGP extract (BY_NAME);
the rest are listed as unmapped. Every mapped name is printed for an eye check.

Writes derived_sgx_fssti_gvkey_map_a_2008_2018.csv (licensed-derived, does not ship).

Run: python code/cen/map_fssti.py
"""

import pandas as pd

from _paths import FSSTI_MAP, MARKIT, MEMBERSHIP, SECD, XW

BY_NAME = {"OLAM SP": "272365_01W", "OLAMR SP": "272365_01W", "HPHT SP": "297101_01W"}

m = pd.read_csv(MEMBERSHIP, parse_dates=["AsOfDate"])
m = m[(m.Index == "FSSTI Index") & (m.AsOfDate <= "2018-12-31")].copy()
m["bb"] = m.Ticker.str.replace(" Equity", "", regex=False)

mk = pd.read_csv(MARKIT, usecols=["isin", "bb_ticker", "datadate"], dtype=str).dropna()
mk["datadate"] = pd.to_datetime(mk.datadate)
mk = mk[mk.bb_ticker.isin(m.bb)].drop_duplicates()
xw = pd.read_csv(XW)

names = []
for ch in pd.read_csv(SECD, usecols=["gvkey", "iid", "exchg", "conm"], dtype=str, chunksize=1_000_000):
    names.append(ch[ch.exchg == "251"].drop_duplicates(["gvkey", "iid"]))
names = pd.concat(names).drop_duplicates(["gvkey", "iid"])
names["SecID"] = names.gvkey.astype(int).astype(str) + "_" + names.iid
conm = names.set_index("SecID").conm


def secid(bb, date):
    if bb in BY_NAME:
        return BY_NAME[bb], "name"
    c = mk[mk.bb_ticker == bb]
    if c.empty:
        return None, "unmapped"
    isin = c.loc[(c.datadate - date).abs().idxmin(), "isin"]
    hit = [s for s in xw.loc[xw["isin"] == isin, "SecID"] if s in conm.index]
    return (hit[0], "markit isin") if hit else (None, "unmapped")


m[["SecID", "route"]] = [secid(b, d) for b, d in zip(m.bb, m.AsOfDate)]
m["conm"] = m.SecID.map(conm)
m["applies_year"] = m.AsOfDate.dt.year + 1
out = m[["AsOfDate", "applies_year", "Ticker", "SecID", "conm", "route"]]
out.to_csv(FSSTI_MAP, index=False)

check = out.drop_duplicates(["Ticker", "SecID"]).sort_values("Ticker")
print(check[["Ticker", "SecID", "conm", "route"]].to_string(index=False))
print(f"mapped {out.SecID.notna().sum()} of {len(out)} ticker-years; unmapped: "
      f"{sorted(out.loc[out.SecID.isna(), 'Ticker'].str.replace(' SP Equity', '').unique())}")
