"""
IBES earnings surprise for each labelled earnings firm-day (results/news_text/PREREG.md,
Part B control).

IBES Summary Statistics, FPI 1 (current fiscal year EPS), ESTFLAG P, with an actual and
an announcement date. The announcement time is US Eastern; it is converted to
Asia/Singapore and the Singapore date is used. Consensus is MEDEST at the last STATPERS
before that date. SUE = (ACTUAL - MEDEST) / price, where price is the Compustat close on
the last trading day before that date divided by ajexdi, so it is on the same current
share basis as IBES EPS. SUE is stored raw; drift_test.py winsorises it. Kept only when CURCODE, CURR_ACT and the price currency are SGD.

IBES ticker to gvkey: the ibtic column of the WRDS index-constituent lists. Each IBES
announcement is matched to the labelled earnings firm-day of the same gvkey whose day 0
is nearest the Singapore date, within 5 calendar days.

Writes derived_sgx_ibes_sue_evt_2002_2026.parquet (licensed-derived, does not ship).

Run: python code/news/build_surprise.py
"""

from zoneinfo import ZoneInfo

import pandas as pd

from _paths import IBES, INDEX, LABELLED, SECD, SUE

MAX_DAYS = 5

# IBES rows
ib = pd.read_csv(IBES, dtype=str)
ib.columns = ib.columns.str.lower()
ib = ib[(ib.fpi == "1") & (ib.estflag == "P") & ib.actual.notna() & ib.anndats_act.notna()].copy()
for c in ["actual", "medest"]:
    ib[c] = pd.to_numeric(ib[c])
ib["statpers"] = pd.to_datetime(ib.statpers)

# Announcement time: US Eastern -> Singapore date
eastern, singapore = ZoneInfo("America/New_York"), ZoneInfo("Asia/Singapore")
stamp = pd.to_datetime(ib.anndats_act + " " + ib.anntims_act.fillna("00:00:00"))
ib["sg_date"] = stamp.dt.tz_localize(eastern, ambiguous="NaT", nonexistent="NaT").dt.tz_convert(singapore) \
    .dt.tz_localize(None).dt.normalize()
print(f"announcement time missing for {ib.anntims_act.isna().sum():,} rows (midnight Eastern assumed)")

# Consensus: last STATPERS before the Singapore date, one row per announcement
ann_keys = ["ticker", "fpedats", "anndats_act"]
ib = ib[ib.statpers < ib.sg_date].sort_values("statpers")
ann = ib.groupby(ann_keys).tail(1).copy()
print(f"IBES announcements with a prior consensus: {len(ann):,}")

# Link to gvkey
link = pd.read_csv(INDEX, dtype=str, usecols=["gvkey", "ibtic"]).dropna().drop_duplicates()
assert not link.ibtic.duplicated().any()
ann = ann.merge(link.rename(columns={"ibtic": "ticker"}), on="ticker", how="inner")
print(f"linked to a gvkey: {len(ann):,}")

# Price on the last trading day before the Singapore date
cols = ["gvkey", "iid", "prirow", "exchg", "datadate", "prccd", "curcdd", "ajexdi"]
parts = []
for ch in pd.read_csv(SECD, usecols=cols, dtype={"gvkey": str, "iid": str, "prirow": str, "exchg": str},
                      chunksize=500_000):
    ch = ch[(ch.exchg == "251") & (ch.iid == ch.prirow) & ch.prccd.notna() & ch.gvkey.isin(link.gvkey)]
    parts.append(ch[["gvkey", "datadate", "prccd", "curcdd", "ajexdi"]])
px = pd.concat(parts, ignore_index=True)
px["datadate"] = pd.to_datetime(px.datadate)
ann = pd.merge_asof(ann.sort_values("sg_date"), px.sort_values("datadate"), left_on="sg_date",
                    right_on="datadate", by="gvkey", allow_exact_matches=False)

sgd = ann.curcode.eq("SGD") & ann.curr_act.eq("SGD") & ann.curcdd.eq("SGD")
print(f"dropped for currency (estimate, actual or price not SGD, or price missing): {(~sgd).sum():,} of {len(ann):,}")
ann = ann[sgd & (ann.prccd > 0)].copy()
ann["sue"] = (ann.actual - ann.medest) / (ann.prccd / ann.ajexdi)

# Match to labelled earnings firm-days
lab = pd.read_parquet(LABELLED, columns=["gvkey", "day0", "type"])
fd = lab[lab.type.eq("Announcement of Earnings") & lab.day0.notna()][["gvkey", "day0"]].drop_duplicates()
m = ann.merge(fd, on="gvkey", how="inner")
m["gap"] = (m.day0 - m.sg_date).dt.days
m = m[m.gap.abs() <= MAX_DAYS].assign(dist=lambda x: x.gap.abs())
m = m.sort_values(["dist", "gap"]).drop_duplicates(ann_keys).drop_duplicates(["gvkey", "day0"])
print(f"matched to a labelled firm-day: {len(m):,} of {len(ann):,} ({len(m) / len(ann):.1%}); "
      f"day 0 minus IBES date: {m.gap.value_counts().sort_index().to_dict()}")

out = m[["gvkey", "day0", "ticker", "sg_date", "fpedats", "actual", "medest", "numest", "prccd", "ajexdi", "sue"]]
out.sort_values(["day0", "gvkey"]).to_parquet(SUE, index=False)
print(f"saved {len(out):,} rows, {out.gvkey.nunique()} firms, {out.day0.min().date()} to {out.day0.max().date()}")
