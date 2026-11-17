"""
Announcement-drift test, development window only (results/news_text/PREREG.md, Part B).

Sample: index earnings firm-days, one per gvkey and day 0, day 0 from 2003-01-01 to
2019-12-31, with both tone scores. The 2020+ hold-out is never read into a regression.

Each regression: window return (car_p2p6, car_p2p21, car_p2p61) on tone (z-scored
within year) plus the surprise, car_0p1, log mcap_lag, book-to-market and 12-month
momentum, with standard errors clustered by day 0. Return windows, the surprise and the
continuous controls are winsorised at 1/99 within each regression sample.

  main    firm-days with an IBES SUE (H5). 2 scores x 3 windows, Bonferroni bar 2.64
  second  firm-days with a parsed earnings change in place of SUE (exploratory), own bar
  placebo each main firm-day's tone and SUE moved to a random non-announcement trading
          day of the same firm and year; windows and controls rebuilt there

result: main and second pass when t >= 2.64 (H5 is a positive coefficient); the placebo
passes when |t| < 2.64.

Writes results/news_text/drift_dev.csv and drift_placebo.csv (estimates only).

Run: python code/news/drift_test.py
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm

from _paths import LABELLED, PANEL, RESULTS, RETS, SUE, TONE
from earnings_text import documents, ni_change

DEV_START, DEV_END = pd.Timestamp("2003-01-01"), pd.Timestamp("2019-12-31")
HOLDOUT = pd.Timestamp("2020-01-01")
WINDOWS = {"car_p2p6": (2, 6), "car_p2p21": (2, 21), "car_p2p61": (2, 61)}
SCORES = ["lm_tone", "finbert_tone"]
CONTROLS = ["car_0p1", "log_mcap", "bm", "mom"]
BAR = 2.64
SEED = 20261117
PLACEBO_GAP = 5  # trading days kept clear of any earnings day 0


def winsor(s):
    lo, hi = s.quantile([0.01, 0.99])
    return s.clip(lo, hi)


# Daily abnormal returns per firm, as in label_events.py
d = pd.read_parquet(RETS, columns=["gvkey", "datadate", "ret", "mkt_ew", "mcap_lag"])
d = d[d.ret.notna() & d.mkt_ew.notna()].sort_values(["gvkey", "datadate"])
d["ar"] = d.ret - d.mkt_ew
series = {g: (x.datadate.values, x.ar.values, x.ret.values, x.mcap_lag.values) for g, x in d.groupby("gvkey")}


def at_days(gvkey, days):
    """Return windows, car_0p1, momentum and mcap_lag for one firm at given trading days."""
    dates, ar, ret, mcap = series[gvkey]
    n, i0 = len(dates), np.searchsorted(dates, days)
    assert (dates[i0] == days).all()
    car = np.concatenate([[0.0], np.cumsum(ar)])
    logret = np.concatenate([[0.0], np.cumsum(np.log1p(ret))])
    out = {}
    for name, (a, b) in {**WINDOWS, "car_0p1": (0, 1)}.items():
        hi = i0 + b
        out[name] = np.where(hi < n, car[np.minimum(hi + 1, n)] - car[np.minimum(i0 + a, n)], np.nan)
    lo, hi = i0 - 252, i0 - 21
    out["mom"] = np.where(lo >= 0, np.expm1(logret[np.maximum(hi + 1, 0)] - logret[np.maximum(lo, 0)]), np.nan)
    out["log_mcap"] = np.log(mcap[i0])
    return pd.DataFrame(out)


def momentum(df):
    parts = [at_days(g, x.day0.values)[["mom"]].set_index(x.index) for g, x in df.groupby("gvkey")]
    return pd.concat(parts).mom


# Book-to-market: main-study panel at the last month-end before the day (4-month lag inside)
panel = pd.read_csv(PANEL, usecols=["Date", "gvkey", "BM_Ratio", "MKT_CAP"], parse_dates=["Date"])
panel["gvkey"] = panel.gvkey.astype(str).str.zfill(6)
panel = (panel.sort_values("MKT_CAP").drop_duplicates(["gvkey", "Date"], keep="last")
         .rename(columns={"BM_Ratio": "bm"})[["gvkey", "Date", "bm"]].sort_values("Date"))
panel["Date"] = panel.Date.astype("datetime64[ns]")


def book_to_market(df):
    left = df[["gvkey", "day0"]].astype({"day0": "datetime64[ns]"}).reset_index().sort_values("day0")
    m = pd.merge_asof(left, panel, left_on="day0",
                      right_on="Date", by="gvkey", allow_exact_matches=False, tolerance=pd.Timedelta(days=31))
    return m.set_index("index").bm.reindex(df.index)


# Sample
lab = pd.read_parquet(LABELLED, columns=["gvkey", "day0", "announced", "type", "in_index", "mcap_lag",
                                         "car_0p1", *WINDOWS])
lab = lab[lab.type.eq("Announcement of Earnings") & lab.day0.notna()]
earnings_days = lab.groupby("gvkey").day0.apply(lambda s: np.unique(s.values))  # dates only, for the placebo
lab = lab[lab.in_index & lab.day0.between(DEV_START, DEV_END)]
assert (lab.announced <= lab.day0).all(), "text dated after day 0"  # PREREG leakage check (2)
fd = lab.drop_duplicates(["gvkey", "day0"]).drop(columns=["announced", "type", "in_index"])

fd = fd.merge(pd.read_parquet(TONE, columns=["gvkey", "day0", *SCORES]), on=["gvkey", "day0"], how="inner")
fd = fd.merge(pd.read_parquet(SUE, columns=["gvkey", "day0", "sue"]), on=["gvkey", "day0"], how="left")
docs = documents()
docs["ni_chg"] = docs.text.map(ni_change)
fd = fd.merge(docs[["gvkey", "day0", "ni_chg"]], on=["gvkey", "day0"], how="left")
fd = fd[fd.gvkey.isin(series.keys())].reset_index(drop=True)
fd["log_mcap"] = np.log(fd.mcap_lag)
fd["mom"] = momentum(fd)
fd["bm"] = book_to_market(fd)
assert fd.day0.max() < HOLDOUT

check = pd.concat([at_days(g, x.day0.values).set_index(x.index) for g, x in fd.groupby("gvkey")])
assert np.allclose(check.car_p2p21, fd.car_p2p21, equal_nan=True), "rebuilt windows differ from labelled"


def regress(df, score, window, surprise):
    x = df.dropna(subset=[window, score, surprise, *CONTROLS]).copy()
    assert x.day0.max() < HOLDOUT, "hold-out row in a regression"
    for c in [window, surprise, *CONTROLS]:
        x[c] = winsor(x[c])
    year = x.groupby(x.day0.dt.year)[score]
    x["tone_z"] = (x[score] - year.transform("mean")) / year.transform("std")
    x = x[x.tone_z.notna()]  # a year with one firm-day cannot be z-scored
    fit = sm.OLS(x[window], sm.add_constant(x[["tone_z", surprise, *CONTROLS]])).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(x.day0)[0]})
    return {"coef": fit.params.tone_z, "t": fit.tvalues.tone_z, "n": len(x)}


def run(df, test, surprise, passes):
    rows = []
    for score in SCORES:
        for window in WINDOWS:
            r = regress(df, score, window, surprise)
            rows.append({"test": test, "score": score, "window": window, "coef": r["coef"], "t": r["t"],
                         "n": r["n"], "bar": BAR, "result": "pass" if passes(r["t"]) else "fail"})
    return rows


main = fd[fd.sue.notna()]
second = fd[fd.ni_chg.notna()]
dev = pd.DataFrame(run(main, "main", "sue", lambda t: t >= BAR) + run(second, "second", "ni_chg", lambda t: t >= BAR))

# Placebo: same firm, same year, at least PLACEBO_GAP trading days from any earnings day 0
rng = np.random.default_rng(SEED)
picks = []
for r in main.sort_values(["gvkey", "day0"]).itertuples():
    dates = series[r.gvkey][0]
    eidx = np.searchsorted(dates, earnings_days[r.gvkey])
    idx = np.arange(len(dates))
    clear = np.abs(idx[:, None] - eidx[None, :]).min(axis=1) > PLACEBO_GAP
    pool = idx[clear & (dates.astype("datetime64[Y]").astype(int) + 1970 == r.day0.year)]
    if len(pool):
        picks.append({"gvkey": r.gvkey, "day0": dates[rng.choice(pool)], "sue": r.sue,
                      "lm_tone": r.lm_tone, "finbert_tone": r.finbert_tone})
pl = pd.DataFrame(picks)
pl = pd.concat([pd.concat([x, at_days(g, x.day0.values).set_index(x.index)], axis=1) for g, x in pl.groupby("gvkey")])
pl["bm"] = book_to_market(pl)
assert pl.day0.max() < HOLDOUT
placebo = pd.DataFrame(run(pl, "placebo", "sue", lambda t: abs(t) < BAR))

for name, df in [("drift_dev.csv", dev), ("drift_placebo.csv", placebo)]:
    df.round({"coef": 5, "t": 2}).to_csv(RESULTS / name, index=False)
    print(df.round({"coef": 5, "t": 2}).to_string(index=False), "\n")
print(f"firm-days: sample {len(fd):,}, with SUE {len(main):,}, with parsed change {len(second):,}, "
      f"placebo days {len(pl):,} of {len(main):,}")
