"""
The long-short cost engine of code/waterfall.py, ported so it runs on any score and on
weekly as well as monthly periods (results/cen_replication/PREREG.md, A2 tradability).

The rules are waterfall.py's, line for line: decile book (k = max(5, n // 10), at least
40 names), Corwin-Schultz half-spread known at formation charged on both legs every
period or only on the names bought and sold ("traded"), shorts limited to names Markit
showed as lendable, and the Markit indicative fee on the shorts. The only change is
that the fee is divided by the number of periods a year (12 in waterfall.py).
check_waterfall.py confirms the port reproduces waterfall.py's saved table.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm


def markit_by_secid(markit_csv, xw):
    """Last lendable value and fee per security and month, on ISIN then SEDOL (as waterfall.py)."""
    mk = pd.read_csv(markit_csv, usecols=["isin", "sedol", "datadate", "activeavailablevalue", "indicativefee", "dcbs"],
                     low_memory=False)
    mk["datadate"] = pd.to_datetime(mk["datadate"])
    mk["Date"] = mk["datadate"] + pd.offsets.MonthEnd(0)
    for c in ["activeavailablevalue", "indicativefee", "dcbs"]:
        mk[c] = pd.to_numeric(mk[c], errors="coerce")
    mk["fee"] = (mk["indicativefee"].fillna(mk["dcbs"].map(mk.groupby("dcbs")["indicativefee"].median()))
                 .fillna(mk["indicativefee"].median()))
    mkm = (mk.sort_values("datadate").groupby(["isin", "sedol", "Date"])
           .agg(avail=("activeavailablevalue", "last"), fee=("fee", "last")).reset_index())
    by_isin = xw.dropna(subset=["isin"]).merge(mkm, on="isin")[["SecID", "Date", "avail", "fee"]]
    rest = xw[~xw["SecID"].isin(set(by_isin["SecID"]))].dropna(subset=["sedol"])
    by_sedol = rest.merge(mkm, on="sedol")[["SecID", "Date", "avail", "fee"]]
    return (pd.concat([by_isin, by_sedol], ignore_index=True).groupby(["SecID", "Date"])
            .agg(avail=("avail", "max"), fee=("fee", "median")).reset_index())


def traded_cost(new, old, hs, fill):
    """Half-spread on the names bought and sold this period, as a fraction of the leg."""
    def spread(s):
        v = hs.get(s, np.nan)
        return fill if pd.isna(v) else v
    c = sum(spread(s) for s in new - old) / len(new)
    if old:
        c += sum(spread(s) for s in old - new) / len(old)
    return c / 1e4


def long_short(q, score, members, start, periods_per_year=12, use_cs=False, screen=False, fee=False, traded=False):
    """Decile long-short. q: SecID, Date, score, Ret (return over the period ending at Date),
    cs_half_bp_l, avail_l, fee_l (known at formation). Returns net returns and turnover."""
    dts = sorted(q["Date"].unique())
    by_date = {d: g for d, g in q.groupby("Date")}
    rows, turn, prev, book = [], [], None, None
    for i, d in enumerate(dts[:-1]):
        if d < start:
            continue
        am = members(d)
        if am is None:
            continue
        now = by_date[d]
        c = now[now["SecID"].isin(am)].dropna(subset=[score])
        if len(c) < 40:
            continue
        k = max(5, len(c) // 10)
        c = c.sort_values(score, ascending=False)
        lo, sh = c.head(k), c.tail(k)
        held = (set(lo["SecID"]), set(sh["SecID"]))
        if prev is not None:
            turn.append(np.mean([len(held[j] - prev[j]) / k for j in (0, 1)]))
        prev = held
        fee_cost = 0.0
        if screen:
            sh = sh[sh["avail_l"].fillna(0) > 0]
            if len(sh) < 3:
                continue
            if fee:
                fee_cost = float(sh["fee_l"].fillna(0).mean()) / periods_per_year
        if use_cs:
            cl = lo["cs_half_bp_l"].fillna(lo["cs_half_bp_l"].median())
            cx = sh["cs_half_bp_l"].fillna(sh["cs_half_bp_l"].median())
            cost = (cl.mean() + cx.mean()) / 1e4
        else:
            cost = 0.0
        if use_cs and traded:
            hs = now.drop_duplicates("SecID").set_index("SecID")["cs_half_bp_l"]
            new = (set(lo["SecID"]), set(sh["SecID"]))
            old = book or (set(), set())
            cost = (traded_cost(new[0], old[0], hs, lo["cs_half_bp_l"].median())
                    + traded_cost(new[1], old[1], hs, sh["cs_half_bp_l"].median()))
            book = new
        nr = by_date[dts[i + 1]].drop_duplicates("SecID").set_index("SecID")["Ret"]
        rl, rs = nr.reindex(lo["SecID"]).mean(), nr.reindex(sh["SecID"]).mean()
        if np.isnan(rl) or np.isnan(rs):
            continue
        rows.append({"Date": dts[i + 1], "R": rl - rs - cost - fee_cost})
    return pd.DataFrame(rows).set_index("Date")["R"], np.mean(turn)


def summary(r, bench, label, periods_per_year=12, lags=6):
    """waterfall.py's nwa(): annual return, Sharpe, drawdown, alpha on the market and its NW t."""
    r = r.dropna()
    df = pd.concat([r, bench], axis=1, keys=["s", "b"], sort=True).dropna()
    m = sm.OLS(df["s"], sm.add_constant(df["b"])).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    c = (1 + r).cumprod()
    return {"Stage": label, "Ann%": round(((1 + r).prod() ** (periods_per_year / len(r)) - 1) * 100, 2),
            "Sharpe": round(r.mean() / r.std() * np.sqrt(periods_per_year), 2),
            "MaxDD%": round(((c - c.cummax()) / c.cummax()).min() * 100, 1),
            "Alpha%mo": round(m.params["const"] * 100, 3), "t": round(m.tvalues["const"], 2), "N": len(r)}
