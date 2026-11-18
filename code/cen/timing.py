"""
A3-cost (results/cen_replication/PREREG.md, row "A3-cost registered"): four trading rules
on the A2 weekly long-short books of Williams %R, Keltner %B and reversal, broad universe.

  banding     enter the top (bottom) decile, exit only on leaving the top (bottom) 30%
  spread      trade only names with prior-month half-spread below the date's median
  hold4       4-week holding period, four staggered sub-books, a quarter rebalanced weekly
  regime      hold only in weeks when the equal-weight index is above its 200-day average

Costs are A2's (costs.py rules): traded-days Corwin-Schultz half-spread on names bought
and sold, Markit lendable screen on shorts, Markit fee. The engine reproduces A2's weekly
tradability series for the plain decile book before any rule runs. Test: Newey-West t (4
lags) of the mean weekly net return, 12 tests, bar 2.87. Also: turnover, the rule minus
the A2 book, and 1-, 5- and 20-day gross markouts after entry (descriptive).

Writes results/cen_replication/a3_dev.csv, or a3_holdout.csv with --sample holdout.

Run: python code/cen/timing.py [--sample holdout]
"""

import numpy as np
import pandas as pd

from _paths import RESULTS, RETS
from extend import (END, LOAD_FROM, SAMPLE, START, broad_frame, frozen_directions, load_daily, members_of, nw_t,
                    period_table, stock_signals, tradability)

SIGNALS = ["wr", "kcp", "reversal"]
RULES = ["banding", "spread", "hold4", "regime"]
BAR, LAGS, PPY = 2.87, 4, 52
MARKOUTS = (1, 5, 20)


# ---- the book engine: costs.long_short's rules, with the books chosen by a rule ----
def leg_cost(new, old, hs, fill):
    """Half-spread on names bought and sold, as a fraction of the leg (traded_cost in costs.py)."""
    def spread(s):
        v = hs.get(s, np.nan)
        return fill if pd.isna(v) else v
    c = sum(spread(s) for s in new - old) / len(new) if new else 0.0
    if old:
        c += sum(spread(s) for s in old - new) / len(old)
    return c / 1e4


def run_book(q, members, choose):
    """Weekly net returns, turnover and entries. choose(c, book, i) returns (long, short) sets."""
    dts = sorted(q.Date.unique())
    by_date = {d: g for d, g in q.groupby("Date")}
    rows, turns, entries, book = [], [], [], (set(), set())
    for i, d in enumerate(dts[:-1]):
        if d < START or members.get(d) is None:
            continue
        now = by_date[d]
        c = now[now.SecID.isin(members[d])].dropna(subset=["score"])
        if len(c) < 40:
            continue
        lo, sh = choose(c, book, i)
        info = now.drop_duplicates("SecID").set_index("SecID")
        if lo or sh:
            sh = {s for s in sh if info.avail_l.fillna(0).get(s, 0) > 0}
            if len(sh) < 3:
                continue
        hs = info.cs_half_bp_l
        fill = lambda new, old: np.nanmedian([hs.get(s, np.nan) for s in (new or old)]) if (new or old) else 0.0
        cost = sum(leg_cost(n, o, hs, fill(n, o)) for n, o in [(lo, book[0]), (sh, book[1])])
        fee = info.fee_l.fillna(0).reindex(list(sh)).mean() / PPY if sh else 0.0
        nr = by_date[dts[i + 1]].drop_duplicates("SecID").set_index("SecID").Ret
        turns.append(np.mean([len(n - o) / len(n) for n, o in [(lo, book[0]), (sh, book[1])] if n]) if lo or sh else 0.0)
        entries += [(d, s, 1) for s in lo - book[0]] + [(d, s, -1) for s in sh - book[1]]
        book = (lo, sh)  # as in costs.long_short, the book moves even if the week's return is missing
        rl = nr.reindex(list(lo)).mean() if lo else 0.0
        rs = nr.reindex(list(sh)).mean() if sh else 0.0
        if np.isnan(rl) or np.isnan(rs):
            continue
        rows.append({"Date": dts[i + 1], "R": rl - rs - cost - fee})
    return pd.DataFrame(rows).set_index("Date").R, float(np.mean(turns)), entries


def deciles(c):
    k = max(5, len(c) // 10)
    c = c.sort_values("score", ascending=False)
    return set(c.SecID.head(k)), set(c.SecID.tail(k))


def plain(c, book, i):
    return deciles(c)


def banding(c, book, i):
    top, bottom = deciles(c)
    k30 = max(5, int(round(0.3 * len(c))))
    c = c.sort_values("score", ascending=False)
    keep_long, keep_short = set(c.SecID.head(k30)), set(c.SecID.tail(k30))
    return (book[0] & keep_long) | top, (book[1] & keep_short) | bottom


def spread_filter(c, book, i):
    s = c.dropna(subset=["cs_half_bp_l"])
    return deciles(s[s.cs_half_bp_l < s.cs_half_bp_l.median()])


def staggered(j):
    def choose(c, book, i):
        if i % 4 == j or not (book[0] or book[1]):
            return deciles(c)
        alive = set(c.SecID)
        return book[0] & alive, book[1] & alive
    return choose


def regime_rule(above):
    def choose(c, book, i):
        return deciles(c) if above.get(c.Date.iloc[0], False) else (set(), set())
    return choose


def markouts(entries, daily):
    """Mean gross signed return 1, 5 and 20 trading days after each entry."""
    out = {h: [] for h in MARKOUTS}
    for d, sec, sign in entries:
        dates, logr = daily[sec]
        i = np.searchsorted(dates, np.datetime64(d, "ns"), side="right") - 1  # last trading day on or before
        if i < 0:
            continue
        for h in MARKOUTS:
            if i + h < len(dates):
                out[h].append(sign * np.expm1(logr[i + h] - logr[i]))
    return {f"markout_{h}d": np.mean(v) if v else np.nan for h, v in out.items()}


def regime_weeks(x):
    m = pd.read_parquet(RETS, columns=["datadate", "mkt_ew"]).drop_duplicates("datadate").sort_values("datadate")
    m = m[m.datadate.between(LOAD_FROM, END.strftime("%Y-%m-%d"))].dropna()
    level = (1 + m.mkt_ew).cumprod()
    above = pd.Series((level > level.rolling(200).mean()).values, index=m.datadate.values)
    form = x.groupby("Date").datadate.max()  # the week's last market day
    return {dt: bool(above.get(day, False)) for dt, day in form.items()}


def main():
    direction = frozen_directions()
    d = load_daily()
    d = d.join(pd.concat([stock_signals(x) for _, x in d.groupby("gvkey")]))
    assert d.datadate.max() <= END
    daily = {s: (g.datadate.values.astype("datetime64[ns]"), g.logr.values) for s, g in d.groupby("SecID")}
    x = period_table(d, "W-FRI").assign(u_broad=lambda t: t.in_index & t.fresh)  # as in robust_costs.py
    assert x.Date.between(START, END).all()
    ub = broad_frame(x, d)
    broad = members_of(ub, ub.u_broad)
    above = regime_weeks(x)

    rows = []
    for s in SIGNALS:
        sign = direction[s, "weekly"]
        q = ub[["SecID", "Date", "Ret", "cs_half_bp_l", "avail_l", "fee_l"]].assign(score=sign * ub[s + "_z"])
        base, base_turn, base_entries = run_book(q, broad, plain)
        _, a2_net, _ = tradability(ub, s, sign, PPY, LAGS, broad)
        assert base.index.equals(a2_net.index) and np.allclose(base.values, a2_net.values), f"engine differs for {s}"
        rows.append({"signal": s, "rule": "A2 decile book", "test": False, "mean_net": base.mean(),
                     "t": nw_t(base, LAGS), "n_weeks": len(base), "turnover": base_turn,
                     **markouts(base_entries, daily)})
        books = {"banding": [banding], "spread": [spread_filter], "hold4": [staggered(j) for j in range(4)],
                 "regime": [regime_rule(above)]}
        for rule in RULES:
            runs = [run_book(q, broad, ch) for ch in books[rule]]
            net = pd.concat([r[0] for r in runs], axis=1).mean(axis=1)
            diff = (net - base).dropna()
            rows.append({"signal": s, "rule": rule, "test": True, "mean_net": net.mean(), "t": nw_t(net, LAGS),
                         "n_weeks": len(net), "turnover": np.mean([r[1] for r in runs]),
                         "minus_a2_mean": diff.mean(), "minus_a2_t": nw_t(diff, LAGS),
                         **markouts([e for r in runs for e in r[2]], daily)})
            if rule == "regime":
                rows[-1]["weeks_in_market"] = float(np.mean([above.get(dt, False) for dt in net.index]))

    out = pd.DataFrame(rows)
    out["bar"] = np.where(out.test, BAR, np.nan)
    out["pass"] = np.where(out.test, out.t >= BAR, np.nan)
    assert out.test.sum() == 12
    out.round(6).to_csv(RESULTS / f"a3_{SAMPLE}.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
