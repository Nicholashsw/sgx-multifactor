"""
Attach returns to Capital IQ Key Developments for the announcement-drift test
(results/news_text/PREREG.md).

Reads the Key Developments extract, the gvkey map and the daily returns (paths in
_paths.py). Writes derived_sgx_keydev_labelled_evt_2002_2026.parquet (licensed-derived,
does not ship) and results/news_text/coverage.csv (counts only).

Timing follows the pre-registration. Day 0 is the first trading day on or after the
announced date (Singapore time when Capital IQ gives a time, the calendar date when it
does not). The first trade is at the close of day +1, so the drift windows start on
day +2. Day 0 to +1 and days -5 to -1 are kept as controls, not as targets.

Abnormal return = stock return minus the equal-weight return of the point-in-time
index universe. A window is left empty if any day in it is missing or day 0 is more
than 7 calendar days after the announcement.

in_index marks events whose firm was in the point-in-time index list on day 0. The main
test uses those events only; small names outside the list carry extreme 60-day returns.

Dropped before labelling: forecast dates ("Earnings Release Date, Estimated"),
anything dated after the last price, and firms whose match is not "dividends" or "name".

Run: python code/news/label_events.py
"""

import numpy as np
import pandas as pd

from _paths import KEYDEV, LABELLED, MAP, RESULTS, RETS

WINDOWS = {"car_m5m1": (-5, -1), "car_0p1": (0, 1), "car_p2p6": (2, 6), "car_p2p21": (2, 21), "car_p2p61": (2, 61)}

kd = pd.read_parquet(KEYDEV)
mp = pd.read_csv(MAP, dtype={"gvkey": str})
mp = mp[mp.status.isin(["dividends", "name"])]
kd = kd.merge(mp[["sgx_ticker", "sgx_company", "gvkey", "status"]], on=["sgx_ticker", "sgx_company"], how="inner")
kd = kd[~kd.type.str.contains("Estimated")]

d = pd.read_parquet(RETS, columns=["gvkey", "datadate", "ret", "mkt_ew", "mcap_lag", "in_index"])
d = d[d.ret.notna() & d.mkt_ew.notna()].sort_values(["gvkey", "datadate"])
d["ar"] = d.ret - d.mkt_ew

t = kd.date
placeholder = t.dt.hour.isin([0, 4, 5]) & (t.dt.minute == 0) & (t.dt.second == 0)
kd["has_time"] = ~placeholder
kd["announced"] = (t + pd.Timedelta(hours=8)).where(kd.has_time, t).dt.normalize()
kd = kd[kd.announced <= d.datadate.max()]

out = []
for gvkey, ev in kd.groupby("gvkey"):
    x = d[d.gvkey == gvkey]
    if x.empty:
        continue
    dates, ar, mcap, member = x.datadate.values, x.ar.values, x.mcap_lag.values, x.in_index.values
    n = len(dates)
    i0 = np.searchsorted(dates, ev.announced.values, side="left")
    ok = (i0 < n) & ((dates[np.minimum(i0, n - 1)] - ev.announced.values) <= np.timedelta64(7, "D"))
    ev = ev.assign(day0=np.where(ok, dates[np.minimum(i0, n - 1)], np.datetime64("NaT")),
                   mcap_lag=np.where(ok, mcap[np.minimum(i0, n - 1)], np.nan),
                   in_index=ok & member[np.minimum(i0, n - 1)])
    csum = np.concatenate([[0.0], np.cumsum(ar)])
    for name, (a, b) in WINDOWS.items():
        lo, hi = i0 + a, i0 + b
        valid = ok & (lo >= 0) & (hi < n)
        ev[name] = np.where(valid, csum[np.clip(hi + 1, 0, n)] - csum[np.clip(lo, 0, n)], np.nan)
    out.append(ev)

lab = pd.concat(out, ignore_index=True)
assert (lab.day0.dropna().values >= lab.loc[lab.day0.notna(), "announced"].values).all(), "day 0 before announcement"
lab.to_parquet(LABELLED, index=False)

earn = lab.type.eq("Announcement of Earnings")
cov = (lab.assign(year=lab.announced.dt.year, earnings=earn, labelled=lab.car_p2p21.notna())
       .groupby(["year", "earnings"]).agg(events=("oid", "size"), labelled=("labelled", "sum"),
                                          firms=("gvkey", "nunique"), with_time=("has_time", "mean"))
       .reset_index())
cov["with_time"] = cov.with_time.round(3)
cov.to_csv(RESULTS / "coverage.csv", index=False)

e = lab[earn & lab.car_p2p21.notna()]
print(f"events {len(lab):,}, firms {lab.gvkey.nunique()}, earnings labelled {len(e):,} "
      f"({e.day0.min():%Y-%m} to {e.day0.max():%Y-%m}), with real time {e.has_time.mean():.0%}")
print(e.groupby(e.day0.dt.year).size().to_string())
