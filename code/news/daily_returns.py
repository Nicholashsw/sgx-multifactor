"""
Daily total returns and ex-dividend dates for SGX primary issues, from Compustat
Security Daily. Feeds match_firms.py and label_events.py.

Needs in the working folder (licensed, does not ship):
  pyvzpcslf5l2s1kh.csv          Compustat Global Security Daily, fic SGP
  World_Index_Constituents.csv  WRDS Singapore index members, one list each June

Writes:
  sgx_daily_rets.parquet  gvkey, datadate, conm, ret, mcap_lag, in_index, mkt_ew
  sgx_div_dates.parquet   gvkey, datadate for every day with a cash dividend going ex

Total return index is prccd / ajexdi * trfd. No return is taken across a gap of more
than 10 calendar days. The market is the equal-weight return of names in the latest
June index list on or before each day, the point-in-time universe of the main study.

Run: python daily_returns.py
"""

import argparse

import numpy as np
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--secd", default="pyvzpcslf5l2s1kh.csv")
ap.add_argument("--index", default="World_Index_Constituents.csv")
ap.add_argument("--start", default="2000-01-01")
args = ap.parse_args()

cols = ["gvkey", "iid", "datadate", "conm", "exchg", "prirow", "prccd", "ajexdi", "trfd", "cshoc", "div"]
dtypes = {"gvkey": str, "iid": str, "prirow": str, "exchg": str, "conm": str}
parts = []
for ch in pd.read_csv(args.secd, usecols=cols, dtype=dtypes, chunksize=500_000):
    ch = ch[(ch.exchg == "251") & (ch.iid == ch.prirow) & ch.prccd.notna() & (ch.datadate >= args.start)]
    parts.append(ch.drop(columns=["exchg", "prirow"]))
d = pd.concat(parts, ignore_index=True)
d["datadate"] = pd.to_datetime(d.datadate)
d = d.sort_values(["gvkey", "datadate"]).reset_index(drop=True)

d.loc[d["div"] > 0, ["gvkey", "datadate"]].to_parquet("sgx_div_dates.parquet", index=False)

g = d.groupby("gvkey")
d["tri"] = d.prccd / d.ajexdi.fillna(1.0) * g.trfd.ffill().fillna(1.0)
d["ret"] = g.tri.pct_change()
d.loc[g.datadate.diff().dt.days > 10, "ret"] = np.nan
d.loc[~d.ret.between(-0.9, 3), "ret"] = np.nan
d["mcap_lag"] = g.prccd.shift() * g.cshoc.shift()

idx = pd.read_csv(args.index, dtype={"gvkey": str}, usecols=["gvkey", "JuneDate"])
idx["JuneDate"] = pd.to_datetime(idx.JuneDate)
lists = np.sort(idx.JuneDate.drop_duplicates().to_numpy())
d["list_date"] = pd.Series(lists).iloc[np.searchsorted(lists, d.datadate.values, side="right") - 1].values
d.loc[d.datadate < lists[0], "list_date"] = pd.NaT
members = idx.rename(columns={"JuneDate": "list_date"}).drop_duplicates().assign(in_index=True)
d = d.merge(members, on=["gvkey", "list_date"], how="left")
d["in_index"] = d.in_index.eq(True)

mkt = d[d.in_index & d.ret.notna()].groupby("datadate").ret.mean().rename("mkt_ew")
d = d.merge(mkt, on="datadate", how="left")

out = d[["gvkey", "datadate", "conm", "ret", "mcap_lag", "in_index", "mkt_ew"]]
out.to_parquet("sgx_daily_rets.parquet", index=False)
print(f"{len(out):,} rows, {out.gvkey.nunique()} firms, {out.datadate.min().date()} to {out.datadate.max().date()}")
print(f"index names a day: {d[d.in_index].groupby('datadate').size().median():.0f} median")
print(f"ex-dividend days: {(d['div'] > 0).sum():,}")
