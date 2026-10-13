"""PIT-correct portfolio runner.

The bug this fixes: if the point-in-time membership filter is applied to the whole panel,
a name ejected from the index at t+1 has no row at t+1, so its holding-month return is
silently dropped. In reality you form the portfolio from members at t and then hold
through the month, taking whatever the stock does, including the month it leaves the
index or delists. Filtering both eligibility and returns reintroduces exactly the
survivorship the PIT universe was built to remove.

Fix: eligibility at formation uses the PIT-filtered panel; returns come from the
unfiltered (padding-truncated, delisting-adjusted) panel.
"""
import numpy as np
import pandas as pd

from attribution import score, WEIGHTS, RF_M

MIN_NAMES = 12


def run_pit(elig, ret_src, weights=WEIGHTS, sector_neutral=False, cost_bps=0.0,
            n_long=6, n_short=6, start="2008-03-31", universe_filter=None,
            weighting="equal", max_wt=None, scored=None):
    """elig: PIT-filtered panel (who may be selected at t)
       ret_src: unfiltered panel (what a held name actually returned t -> t+1)"""
    p = score(elig, weights, sector_neutral) if scored is None else scored
    p = p[p.Date >= start]
    if universe_filter is not None:
        p = p[universe_filter(p)]
    groups = {d: g for d, g in p.groupby("Date")}
    dates = sorted(groups)

    rmap = {d: g.set_index("Ticker")["Ret"] for d, g in ret_src.groupby("Date")}
    mcap = {d: g.set_index("Ticker")["MKT_CAP_USDmn"] for d, g in ret_src.groupby("Date")}

    def wts(sub, col, side):
        n = len(sub)
        if weighting == "equal":
            w = pd.Series(1.0 / n, index=sub["Ticker"])
        elif weighting == "value":
            mc = mcap.get(sub["Date"].iloc[0], pd.Series(dtype=float)).reindex(sub["Ticker"])
            mc = mc.fillna(mc.median())
            w = mc / mc.sum()
        elif weighting == "score":
            s = sub[col].to_numpy(float)
            s = s - s.min() + 1e-6
            w = pd.Series(s / s.sum(), index=sub["Ticker"])
        else:
            raise ValueError(weighting)
        if max_wt is not None:
            # cap expressed as a MULTIPLE of equal weight, which is always feasible.
            # An absolute cap below 1/n is infeasible (n*cap < 1) and makes the
            # redistribution loop diverge toward equal weight - a silent bug.
            cap = max_wt / n
            v = np.array(w.to_numpy(float), copy=True)
            for _ in range(200):
                over = v > cap + 1e-12
                if not over.any():
                    break
                excess = (v[over] - cap).sum()
                v[over] = cap
                free = ~over
                if not free.any() or v[free].sum() <= 0:
                    break
                v[free] += excess * v[free] / v[free].sum()
            w = pd.Series(v, index=w.index)
        return w * side

    rows, contrib, prev = [], [], {"L": {}, "S": {}}
    for i, d in enumerate(dates[:-1]):
        cur = groups[d].dropna(subset=["Composite"])
        if len(cur) < MIN_NAMES:
            rows.append({"Date": dates[i + 1], "Long": RF_M, "Short": np.nan,
                         "LS": np.nan, "Bench": np.nan, "TO_L": 0.0, "Cash": 1,
                         "NL": 0, "NS": 0})
            prev = {"L": {}, "S": {}}
            continue
        cur = cur.sort_values("Composite", ascending=False)
        Lsub, Ssub = cur.head(n_long), cur.tail(n_short)
        wL = wts(Lsub, "Composite", +1.0)
        wS = wts(Ssub, "Composite", -1.0)

        nxt = rmap.get(dates[i + 1], pd.Series(dtype=float))
        rL = nxt.reindex(wL.index)
        rS = nxt.reindex(wS.index)

        # turnover on weights, not just names
        aw = pd.Series(prev["L"]).reindex(wL.index.union(pd.Index(prev["L"].keys()))).fillna(0)
        bw = wL.reindex(aw.index).fillna(0)
        to_l = (bw - aw).abs().sum() / 2 if len(prev["L"]) else 1.0
        aws = pd.Series(prev["S"]).reindex(wS.index.union(pd.Index(prev["S"].keys()))).fillna(0)
        bws = wS.reindex(aws.index).fillna(0)
        to_s = (bws - aws).abs().sum() / 2 if len(prev["S"]) else 1.0

        # a held name with no return in the holding month: only legitimate if the
        # panel genuinely ends (dead and cash-settled). count it for diagnostics.
        missL = int(rL.isna().sum())
        gL = float((wL * rL.fillna(0.0)).sum())
        gS = float((wS * rS.fillna(0.0)).sum())
        bench = float(nxt.reindex(cur["Ticker"]).mean())

        for t_, w_ in wL.items():
            contrib.append({"Date": dates[i + 1], "Ticker": t_, "Leg": "Long",
                            "w": w_, "r": rL.get(t_, np.nan), "c": w_ * (rL.get(t_) or 0.0)})
        for t_, w_ in wS.items():
            contrib.append({"Date": dates[i + 1], "Ticker": t_, "Leg": "Short",
                            "w": w_, "r": rS.get(t_, np.nan), "c": w_ * (rS.get(t_) or 0.0)})

        rows.append({"Date": dates[i + 1],
                     "Long": gL - to_l * cost_bps / 1e4,
                     "Short": gS - to_s * cost_bps / 1e4,
                     "LS": gL + gS - (to_l + to_s) * cost_bps / 1e4,
                     "Bench": bench, "TO_L": to_l, "Cash": 0,
                     "NL": len(wL), "NS": len(wS), "MissL": missL})
        prev = {"L": wL.to_dict(), "S": wS.to_dict()}

    return pd.DataFrame(rows), pd.DataFrame(contrib)
