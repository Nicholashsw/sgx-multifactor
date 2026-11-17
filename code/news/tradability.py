"""
Tradability of announcement tone, development window (results/news_text/PREREG.md, Part B).

Each index earnings firm-day with day 0 from 2003-01-01 to 2019-12-31 is bought or sold
at the close of day +1 and held 20 trading days (days +2 to +21, the car_p2p21 window,
return in excess of the equal-weight index universe). Long when the tone is in the top
third, short when in the bottom third. The thirds use the previous calendar year's tone
distribution, so no breakpoint uses later text; the first year is therefore not traded.

Costs follow the waterfall convention (code/waterfall.py): the Corwin-Schultz half-spread
of the name at the last month-end before day 0, charged on entry and on exit. Borrow
is not charged.

Reported per score: mean 20-day return of the long leg, the short leg and long minus
short (mean long + mean short), gross and net, with a Welch t for long against short and
the number of trades in each leg. Writes results/news_text/tradability_dev.csv.

Run: python code/news/tradability.py
"""

import numpy as np
import pandas as pd
from scipy import stats

from _paths import LABELLED, RESULTS, SPREADS, TONE

START, END = pd.Timestamp("2003-01-01"), pd.Timestamp("2019-12-31")
SCORES = ["lm_tone", "finbert_tone"]

lab = pd.read_parquet(LABELLED, columns=["gvkey", "day0", "type", "in_index", "car_p2p21"])
lab = lab[lab.type.eq("Announcement of Earnings") & lab.in_index & lab.day0.between(START, END)]
fd = lab.drop_duplicates(["gvkey", "day0"]).merge(pd.read_parquet(TONE, columns=["gvkey", "day0", *SCORES]),
                                                  on=["gvkey", "day0"], how="inner")
fd = fd[fd.car_p2p21.notna()].copy()
assert fd.day0.between(START, END).all()
fd["year"] = fd.day0.dt.year

# Half-spread at the last month-end before day 0; the most-traded issue when a firm has several
cs = pd.read_csv(SPREADS, parse_dates=["Date"])
cs["gvkey"] = cs.SecID.str.split("_").str[0].str.zfill(6)
cs = (cs.sort_values("adv_sgd").drop_duplicates(["gvkey", "Date"], keep="last")
      .astype({"Date": "datetime64[ns]"}).sort_values("Date")[["gvkey", "Date", "cs_half_bp"]])
fd = pd.merge_asof(fd.astype({"day0": "datetime64[ns]", "gvkey": str}).sort_values("day0"),
                   cs.astype({"gvkey": str}), left_on="day0", right_on="Date", by="gvkey",
                   allow_exact_matches=False, tolerance=pd.Timedelta(days=31))
fd["round_trip"] = 2 * fd.cs_half_bp / 1e4


def tstat(a, b):
    return stats.ttest_ind(a, b, equal_var=False).statistic


rows = []
for score in SCORES:
    cuts = fd.groupby("year")[score].quantile([1 / 3, 2 / 3]).unstack()
    cuts.index = cuts.index + 1  # last year's breakpoints apply this year
    x = fd.join(cuts, on="year")
    x = x[x[1 / 3].notna() & x.round_trip.notna()]
    long, short = x[x[score] > x[2 / 3]], x[x[score] < x[1 / 3]]
    for basis, cost in [("gross", 0.0), ("net of spreads", 1.0)]:
        lr = long.car_p2p21 - cost * long.round_trip
        sr = -short.car_p2p21 - cost * short.round_trip
        rows.append({"score": score, "basis": basis, "long": lr.mean(), "short": sr.mean(),
                     "long_short": lr.mean() + sr.mean(), "t": tstat(lr, -sr),
                     "n_long": len(lr), "n_short": len(sr)})

out = pd.DataFrame(rows).round({"long": 5, "short": 5, "long_short": 5, "t": 2})
out.to_csv(RESULTS / "tradability_dev.csv", index=False)
print(out.to_string(index=False))
print(f"firm-days with a 20-day return {len(fd):,}; with a spread {fd.round_trip.notna().sum():,}; "
      f"median round trip {fd.round_trip.median() * 1e4:.0f} bp")
