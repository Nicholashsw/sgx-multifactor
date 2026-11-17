"""
Part A2 of results/cen_replication/PREREG.md: Cen's signals on the project's data,
development window only (formations 2003-01 to 2019-12; no data after 2019-12-31 is read).

Signals (9), from Compustat daily split-adjusted high, low, close and cshtrd:
  wr, rsi, bbp, kcp, stoch_signal   Cen's five, ta defaults (14; 14; 20, 2; 20 with ATR 10; 14, 3)
  trend                             close / 200-day average - 1
  atr                               ATR(14) / close
  mfi                               MFI(14)
  reversal                          minus the past 5-day return (weekly), minus the
                                    formation month's return (monthly)
Universes: broad = the point-in-time WRDS index list (latest June list), delisted firms
included; sti = top 30 of the broad list by lagged market cap at each June rebalance.
Robustness only, outside the bars: fssti = Bloomberg FSSTI year-end rosters, 2009-2019.
Horizons: weekly (last trading day of the week) and monthly (last trading day of the
month). A stock enters a cross-section only if it traded on that period's last market
day; the return is the next period's compounded total return.

Each signal is winsorised at 1/99 and z-scored across the universe on each date.
  primary      Fama-MacBeth slope on one signal, NW t (4 lags weekly, 6 monthly), bar 3.20
  mechanism    oscillator slope with the reversal control added, bar 3.02
  tradability  broad universe, decile long-short in the registered direction, after
               traded-days spreads, Markit screen and fee (costs.py, the waterfall port);
               NW t of the mean net return, bar 2.99
Benjamini-Yekutieli q across all 74. Also written: the FSSTI robustness cells, the yearly
overlap of the two STI lists, and gross weekly long-short by size third (H4).

Writes results/cen_replication/a2_dev.csv, a2_dev_fssti.csv, a2_sti_overlap.csv,
a2_size_terciles.csv (statistics only).

Run: python code/cen/extend.py                      development, 2003-01 to 2019-12
     python code/cen/extend.py --sample holdout     once, 2020-01 to 2026-06: a2_holdout.csv,
                                                    a2_holdout_size_terciles.csv, development directions
"""

import argparse
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.multitest import multipletests
from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator
from ta.volatility import AverageTrueRange, BollingerBands, KeltnerChannel
from ta.volume import MFIIndicator

from _paths import FSSTI_MAP, INDEX, MARKIT, RESULTS, RETS, SECD, SPREADS_TRADED, XW
from costs import long_short, markit_by_secid

SAMPLES = {"dev": ("2001-06-01", "2003-01-01", "2019-12-31"), "holdout": ("2018-06-01", "2020-01-01", "2026-06-30")}
_ap = argparse.ArgumentParser()
_ap.add_argument("--sample", choices=list(SAMPLES), default="dev")
SAMPLE = _ap.parse_known_args()[0].sample
LOAD_FROM, START, END = SAMPLES[SAMPLE][0], pd.Timestamp(SAMPLES[SAMPLE][1]), pd.Timestamp(SAMPLES[SAMPLE][2])
OSC = ["wr", "rsi", "bbp", "kcp", "stoch_signal"]
SIGNALS = OSC + ["trend", "atr", "mfi", "reversal"]
WARMUP = {"wr": 14, "rsi": 14, "bbp": 20, "kcp": 20, "stoch_signal": 16, "trend": 200, "atr": 14, "mfi": 14}
DIRECTION = {**{s: -1 for s in OSC}, "trend": 1, "atr": -1, "reversal": 1}  # H1, H3; mfi set from data
HORIZONS = {"weekly": ("W-FRI", 4, 52), "monthly": ("M", 6, 12)}
BAR = {"primary": 3.20, "mechanism": 3.02, "tradability": 2.99}
MIN_NAMES = 10


# ---- daily data, signals at each date ----
def load_daily():
    cols = ["gvkey", "iid", "prirow", "exchg", "datadate", "prccd", "prchd", "prcld", "ajexdi", "cshtrd"]
    parts = []
    for ch in pd.read_csv(SECD, usecols=cols, dtype={"gvkey": str, "iid": str, "prirow": str, "exchg": str},
                          chunksize=1_000_000):
        parts.append(ch[(ch.exchg == "251") & (ch.iid == ch.prirow) & ch.prccd.notna()
                        & ch.datadate.between(LOAD_FROM, END.strftime("%Y-%m-%d"))])
    d = pd.concat(parts, ignore_index=True).drop(columns=["exchg", "prirow"])
    d["datadate"] = pd.to_datetime(d.datadate)
    r = pd.read_parquet(RETS, columns=["gvkey", "datadate", "ret", "in_index", "mcap_lag"])
    d = d.merge(r[r.datadate <= END], on=["gvkey", "datadate"], how="inner")
    assert d.datadate.max() <= END
    d["SecID"] = d.gvkey.astype(int).astype(str) + "_" + d.iid
    return d.sort_values(["gvkey", "datadate"]).reset_index(drop=True)


def stock_signals(x):
    a = x.ajexdi.fillna(1.0)
    c = x.prccd / a
    h, lo, v = (x.prchd / a).fillna(c), (x.prcld / a).fillna(c), x.cshtrd.fillna(0.0)
    s = pd.DataFrame(np.nan, index=x.index, columns=list(WARMUP))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if len(x) >= 20:  # ta fails below its window; shorter stocks get no indicator values
            s["wr"] = WilliamsRIndicator(h, lo, c, lbp=14).williams_r()
            s["rsi"] = RSIIndicator(c, window=14).rsi()
            s["bbp"] = BollingerBands(c, window=20, window_dev=2).bollinger_pband()
            s["kcp"] = KeltnerChannel(h, lo, c, window=20, window_atr=10, original_version=True).keltner_channel_pband()
            s["stoch_signal"] = StochasticOscillator(h, lo, c, window=14, smooth_window=3).stoch_signal()
            s["trend"] = c / c.rolling(200).mean() - 1
            s["atr"] = AverageTrueRange(h, lo, c, window=14).average_true_range() / c
            s["mfi"] = MFIIndicator(h, lo, c, v, window=14).money_flow_index()
    age = np.arange(len(x))
    for k, w in WARMUP.items():
        s.loc[age < w, k] = np.nan
    s["logr"] = np.log1p(x.ret.fillna(0.0)).cumsum()
    s["rev5"] = -np.expm1(s.logr - s.logr.shift(5))
    return s.replace([np.inf, -np.inf], np.nan)


# ---- one row per stock and formation period ----
def period_table(d, freq):
    x = d.assign(period=d.datadate.dt.to_period(freq)).groupby(["gvkey", "period"]).tail(1).copy()
    x = x.sort_values(["gvkey", "period"])
    g = x.groupby("gvkey")
    consecutive = (x.period - g.period.shift()).map(lambda p: getattr(p, "n", np.nan)) == 1
    x["Ret"] = np.where(consecutive, np.expm1(x.logr - g.logr.shift()), np.nan)  # return over this period
    nxt = g.Ret.shift(-1)
    x["next_ret"] = np.where((g.period.shift(-1) - x.period).map(lambda p: getattr(p, "n", np.nan)) == 1, nxt, np.nan)
    x["reversal"] = x.rev5 if freq == "W-FRI" else -x.Ret
    x["fresh"] = x.datadate == x.groupby("period").datadate.transform("max")  # traded on the last market day
    x["Date"] = x.period.dt.end_time.dt.normalize()
    return x[x.Date.between(START, END)]


def sti_top30(d):
    """gvkeys in the top 30 of the June list by lagged market cap, keyed by list date."""
    idx = pd.read_csv(INDEX, dtype={"gvkey": str}, usecols=["gvkey", "JuneDate"], parse_dates=["JuneDate"])
    out = {}
    for jd, g in idx.groupby("JuneDate"):
        day = d.loc[d.datadate >= jd, "datadate"].min()
        snap = d[(d.datadate == day) & d.gvkey.isin(g.gvkey)].dropna(subset=["mcap_lag"])
        out[jd] = set(snap.nlargest(30, "mcap_lag").gvkey)
    return out


def add_universes(x, top30, fssti):
    lists = np.array(sorted(top30), dtype="datetime64[ns]")
    pos = np.searchsorted(lists, x.datadate.values, side="right") - 1
    x["list_date"] = np.where(pos >= 0, lists[np.maximum(pos, 0)], np.datetime64("NaT"))
    x["u_broad"] = x.in_index & x.fresh
    x["u_sti"] = x.fresh & pd.Series([ld in top30 and g in top30[ld] for ld, g in zip(x.list_date, x.gvkey)], index=x.index)
    x["u_fssti"] = x.fresh & pd.Series([(y, g) in fssti for y, g in zip(x.Date.dt.year, x.gvkey)], index=x.index)
    return x


def zscore(x, universe):
    u = x[x[universe]].copy()
    for s in SIGNALS:
        g = u.groupby("Date")[s]
        lo, hi = g.transform(lambda v: v.quantile(0.01)), g.transform(lambda v: v.quantile(0.99))
        w = u[s].clip(lo, hi)
        u[s + "_z"] = (w - w.groupby(u.Date).transform("mean")) / w.groupby(u.Date).transform("std")
    return u


# ---- tests ----
def nw_t(series, lags):
    y = np.asarray(series)
    return sm.OLS(y, np.ones(len(y))).fit(cov_type="HAC", cov_kwds={"maxlags": lags}).tvalues[0]


def fama_macbeth(u, cols, lags):
    slopes = []
    for _, g in u.groupby("Date"):
        g = g.dropna(subset=["next_ret", *cols])
        if len(g) < MIN_NAMES:
            continue
        slopes.append(np.linalg.lstsq(np.c_[np.ones(len(g)), g[cols]], g.next_ret, rcond=None)[0][1])
    return np.mean(slopes), nw_t(slopes, lags), len(slopes)


def costs_table(x, d):
    """Spread, Markit lendable value and fee from the month before the formation month."""
    cs = pd.read_csv(SPREADS_TRADED, parse_dates=["Date"])[["SecID", "Date", "cs_half_bp"]]
    mm = markit_by_secid(MARKIT, pd.read_csv(XW))
    c = cs.merge(mm, on=["SecID", "Date"], how="outer").rename(columns={"Date": "cost_month"})
    c = c.rename(columns={"cs_half_bp": "cs_half_bp_l", "avail": "avail_l", "fee": "fee_l"})
    x["cost_month"] = (x.Date.dt.to_period("M") - 1).dt.end_time.dt.normalize()
    return x.merge(c, on=["SecID", "cost_month"], how="left")


def broad_frame(x, d):
    """All period rows with broad z-scores (blank outside the universe) and known-at-formation costs."""
    z = zscore(x, "u_broad")[[s + "_z" for s in SIGNALS]]
    return costs_table(x.join(z), d)


def members_of(frame, mask):
    return {dt: set(g.SecID) for dt, g in frame[mask].groupby("Date")}


def tradability(frame, signal, sign, ppy, lags, members):
    """Decile long-short; names are picked from members at formation, and each held name's
    next-period return comes from all rows, as in waterfall.py."""
    q = frame[["SecID", "Date", "Ret", "cs_half_bp_l", "avail_l", "fee_l"]].copy()
    q["score"] = sign * frame[signal + "_z"]
    gross, _ = long_short(q, "score", members.get, START, ppy)
    net, turnover = long_short(q, "score", members.get, START, ppy, use_cs=True, screen=True, fee=True, traded=True)
    return gross, net, turnover


def frozen_directions():
    """Tradability directions recorded in the development results (used for the hold-out)."""
    r = pd.read_csv(RESULTS / "a2_dev.csv").query("family == 'tradability'")
    return r.set_index(["signal", "horizon"]).direction.astype(int).to_dict()



def main():
    d = load_daily()
    sig = pd.concat([stock_signals(x) for _, x in d.groupby("gvkey")])
    d = d.join(sig)
    top30 = sti_top30(d)
    fm = pd.read_csv(FSSTI_MAP, dtype=str).dropna(subset=["SecID"])
    fssti = {(int(y), s.split("_")[0].zfill(6)) for y, s in zip(fm.applies_year, fm.SecID)}

    universes = ["broad", "sti", "fssti"] if SAMPLE == "dev" else ["broad", "sti"]
    frozen = frozen_directions() if SAMPLE == "holdout" else None
    rows, robust, terciles, overlap = [], [], [], []
    for horizon, (freq, lags, ppy) in HORIZONS.items():
        x = add_universes(period_table(d, freq), top30, fssti)
        assert x.Date.between(START, END).all() and x.datadate.max() <= END
        z = {u: zscore(x, "u_" + u) for u in universes}
        for universe in universes:
            out = rows if universe != "fssti" else robust
            prim = {}
            for s in SIGNALS:
                coef, t, n = fama_macbeth(z[universe], [s + "_z"], lags)
                prim[s] = t
                out.append({"family": "primary", "signal": s, "universe": universe, "horizon": horizon,
                            "coef": coef, "t": t, "n_periods": n, "bar": BAR["primary"]})
            for s in OSC:
                coef, t, n = fama_macbeth(z[universe], [s + "_z", "reversal_z"], lags)
                out.append({"family": "mechanism", "signal": s, "universe": universe, "horizon": horizon,
                            "coef": coef, "t": t, "n_periods": n, "bar": BAR["mechanism"],
                            "primary_t": prim[s], "t_ratio": abs(t) / abs(prim[s])})
            if universe == "broad":
                if frozen:
                    DIRECTION.update({s: frozen[s, horizon] for s in SIGNALS})
                else:
                    DIRECTION["mfi"] = int(np.sign(prim["mfi"]))
                ub = broad_frame(x, d)
                broad = members_of(ub, ub.u_broad)
                for s in SIGNALS:
                    gross, net, turnover = tradability(ub, s, DIRECTION[s], ppy, lags, broad)
                    rows.append({"family": "tradability", "signal": s, "universe": "broad", "horizon": horizon,
                                 "direction": DIRECTION[s], "coef": net.mean(), "t": nw_t(net, lags),
                                 "n_periods": len(net), "bar": BAR["tradability"], "gross_mean": gross.mean(),
                                 "gross_t": nw_t(gross, lags), "turnover": turnover})
                if horizon == "weekly":  # H4: gross by size third
                    ub["size_third"] = ub[ub.u_broad].groupby("Date").mcap_lag.transform(
                        lambda v: pd.qcut(v.rank(method="first"), 3, labels=["small", "mid", "large"]))
                    for third in ["small", "mid", "large"]:
                        sets = members_of(ub, ub.size_third == third)
                        for s in SIGNALS:
                            gross, _, _ = tradability(ub, s, DIRECTION[s], ppy, lags, sets)
                            terciles.append({"signal": s, "size_third": third, "direction": DIRECTION[s],
                                             "gross_mean": gross.mean(), "gross_t": nw_t(gross, lags), "n_periods": len(gross)})

        if horizon == "weekly" and SAMPLE == "dev":  # yearly overlap of the two STI lists, Jan of each year
            for y in range(2009, 2020):
                ld = max(k for k in top30 if k < pd.Timestamp(f"{y}-01-01"))
                f = {g for yy, g in fssti if yy == y}
                overlap.append({"year": y, "fssti_mapped": len(f), "top30": len(top30[ld]), "both": len(f & top30[ld])})

    res = pd.DataFrame(rows)
    res["p"] = 2 * stats.norm.sf(res.t.abs())
    res["by_q"] = multipletests(res.p, method="fdr_by")[1]
    res["pass"] = np.where(res.family == "tradability", res.t >= res.bar, res.t.abs() >= res.bar)
    assert len(res) == 74, len(res)
    outputs = {"dev": [("a2_dev.csv", res), ("a2_size_terciles.csv", pd.DataFrame(terciles))],
               "holdout": [("a2_holdout.csv", res), ("a2_holdout_size_terciles.csv", pd.DataFrame(terciles))]}[SAMPLE]
    if SAMPLE == "dev":
        rob = pd.DataFrame(robust)
        rob["pass"] = rob.t.abs() >= rob.bar
        outputs += [("a2_dev_fssti.csv", rob), ("a2_sti_overlap.csv", pd.DataFrame(overlap))]
    for name, df in outputs:
        df.round(6).to_csv(RESULTS / name, index=False)
    pd.set_option("display.width", 250)
    print(res.round(4).to_string(index=False))
    print(pd.DataFrame(terciles).round(5).to_string(index=False))


if __name__ == "__main__":
    main()
