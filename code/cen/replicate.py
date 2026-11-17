"""
Part A1 of results/cen_replication/PREREG.md: the exact replication of Cen (2023).

Universe: 21 of his 25 names (D01, H78, J36 and BS6 are not in the Compustat SGP extract).
Data: Compustat Security Daily, primary SGX issue, 2012-01-03 to 2022-12-30. High, low
and close divided by ajexdi; volume cshtrd; open = previous adjusted close (ta 0.11.0
reads no open, so this changes nothing). Signals: the 86 columns of ta's
add_all_ta_features with default windows, computed per stock inside the window.

Each day t, the return of each name from t to t+1 (total return, prccd / ajexdi x trfd)
is regressed on one signal at day t across names (OLS with intercept, at least 5 names).
The daily slopes are averaged; t = mean / (sd / sqrt(T)) as Cen did, and a Newey-West t
with 5 lags. The same-day return (t-1 to t) is run as a diagnostic only.

Writes results/cen_replication/a1_replication.csv (statistics only).

Run: python code/cen/replicate.py
"""

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from ta import add_all_ta_features

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from config import WRDS_SGX_EQUITIES  # noqa: E402

SECD = WRDS_SGX_EQUITIES / "wrds_compustat_sg_secdaily_d_1984_2026.csv"
OUT = REPO / "results" / "cen_replication" / "a1_replication.csv"
START, END = "2012-01-03", "2022-12-30"
MIN_NAMES = 5
BAR = 3.44
NW_LAGS = 5

# SGX code -> gvkey: Capital IQ map at status dividends, plus C07 checked by name
UNIVERSE = {
    "A17U": ("256078", "CAPITALAND ASCENDAS REIT"), "BN4": ("100076", "KEPPEL LTD"),
    "C07": ("100296", "JARDINE CYCLE & CARRIAGE LTD"), "C09": ("100922", "CITY DEVELOPMENTS LTD"),
    "C38U": ("255118", "CAPITALAND INTEGRATED COMMER"), "C6L": ("100713", "SINGAPORE AIRLINES LTD"),
    "D05": ("015743", "DBS GROUP HOLDINGS LTD"), "F34": ("246116", "WILMAR INTERNATIONAL LTD"),
    "G13": ("210177", "GENTING SINGAPORE LTD"), "M44U": ("273612", "MAPLETREE LOGISTICS TRUST"),
    "ME8U": ("295651", "MAPLETREE INDUSTRIAL TRUST"), "N2IU": ("297302", "MAPLETREE PAN ASIA"),
    "O39": ("015753", "OVERSEA CHINESE BANKING"), "S58": ("242894", "SATS LTD"),
    "S63": ("214882", "SINGAPORE TECHNOLOGIES ENGR"), "S68": ("241904", "SINGAPORE EXCHANGE LIMITED"),
    "U11": ("015679", "UNITED OVERSEAS BANK LTD"), "U14": ("019799", "UOL GROUP LTD"),
    "U96": ("019774", "SEMBCORP INDUSTRIES LTD"), "V03": ("209401", "VENTURE CORP LTD"),
    "Z74": ("208095", "SINGAPORE TELECOMMUNICATIONS"),
}
CEN = {"momentum_wr": -5.84, "momentum_rsi": -4.62, "volatility_bbp": -4.23,
       "volatility_kcp": -4.09, "momentum_stoch_signal": 3.51}


def load_prices():
    gvkeys = {g for g, _ in UNIVERSE.values()}
    cols = ["gvkey", "iid", "prirow", "exchg", "datadate", "conm", "prccd", "prchd", "prcld", "ajexdi", "trfd",
            "cshtrd"]
    parts = []
    for ch in pd.read_csv(SECD, usecols=cols, dtype={"gvkey": str, "iid": str, "prirow": str, "exchg": str},
                          chunksize=1_000_000):
        ch = ch[ch.gvkey.isin(gvkeys) & (ch.exchg == "251") & (ch.iid == ch.prirow) & ch.prccd.notna()
                & ch.datadate.between(START, END)]
        parts.append(ch)
    d = pd.concat(parts, ignore_index=True)
    d["datadate"] = pd.to_datetime(d.datadate)
    names = d.groupby("gvkey").conm.last()
    for code, (g, name) in UNIVERSE.items():
        assert names.get(g) == name, f"{code}: gvkey {g} is {names.get(g)}"
    return d.sort_values(["gvkey", "datadate"]).reset_index(drop=True)


def signals(x):
    """ta features and returns for one stock."""
    adj = x.ajexdi.fillna(1.0)
    p = pd.DataFrame({"high": x.prchd / adj, "low": x.prcld / adj, "close": x.prccd / adj,
                      "volume": x.cshtrd.fillna(0.0)}, index=x.index)
    p["high"] = p.high.fillna(p.close)
    p["low"] = p.low.fillna(p.close)
    p["open"] = p.close.shift().fillna(p.close)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        f = add_all_ta_features(p.copy(), "open", "high", "low", "close", "volume")
    f = f.drop(columns=p.columns)
    tri = p.close * x.trfd.ffill().fillna(1.0)
    f["ret_same"] = tri.pct_change()
    f["ret_next"] = f.ret_same.shift(-1)
    f["datadate"] = x.datadate.values
    return f


def daily_slopes(panel, feature, ret):
    def slope(g):
        g = g[[feature, ret]].replace([np.inf, -np.inf], np.nan).dropna()
        if len(g) < MIN_NAMES or g[feature].std() == 0:
            return np.nan
        return np.polyfit(g[feature], g[ret], 1)[0]
    return panel.groupby("datadate")[[feature, ret]].apply(slope).dropna()


def t_stats(s):
    plain = s.mean() / (s.std(ddof=1) / np.sqrt(len(s)))
    nw = sm.OLS(s.values, np.ones(len(s))).fit(cov_type="HAC", cov_kwds={"maxlags": NW_LAGS}).tvalues[0]
    return plain, nw


d = load_prices()
panel = pd.concat([signals(x) for _, x in d.groupby("gvkey")], ignore_index=True)
features = [c for c in panel.columns if c not in ("ret_same", "ret_next", "datadate")]
assert len(features) == 86, len(features)
print(f"{d.gvkey.nunique()} names, {d.datadate.min().date()} to {d.datadate.max().date()}, {len(features)} signals")

rows = []
for f in features:
    nxt, same = daily_slopes(panel, f, "ret_next"), daily_slopes(panel, f, "ret_same")
    t, t_nw = t_stats(nxt) if len(nxt) > NW_LAGS else (np.nan, np.nan)
    t_same, t_same_nw = t_stats(same) if len(same) > NW_LAGS else (np.nan, np.nan)
    row = {"signal": f, "days": len(nxt), "mean_slope": nxt.mean(), "t": t, "t_nw": t_nw,
           "t_same_day": t_same, "t_same_day_nw": t_same_nw, "bar": BAR,
           "clears_bar": abs(t) >= BAR, "clears_bar_nw": abs(t_nw) >= BAR}
    if f in CEN:
        row["cen_t"] = CEN[f]
        row["replicates"] = bool(np.sign(t) == np.sign(CEN[f]) and abs(t - CEN[f]) <= 1.0)
    rows.append(row)

out = pd.DataFrame(rows)
out.round({"mean_slope": 8, "t": 2, "t_nw": 2, "t_same_day": 2, "t_same_day_nw": 2}).to_csv(OUT, index=False)
show = ["signal", "cen_t", "t", "t_nw", "t_same_day", "replicates"]
print(out[out.signal.isin(CEN)][show].round(2).to_string(index=False))
print(f"clear {BAR}: plain t {out.clears_bar.sum()}, Newey-West t {out.clears_bar_nw.sum()} of {len(out)}")
