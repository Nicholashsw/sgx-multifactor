"""
A2 cost robustness, outside every bar, development window only
(results/cen_replication/PREREG.md, row "Cost robustness").

The 18 tradability cells of extend.py are rerun two ways:
  half_spread   traded-days Corwin-Schultz half-spread x 0.5, screen and fee unchanged
  top_two_size  full costs, universe limited to the top two thirds of the broad universe
                by lagged market cap at each formation date
Directions are those recorded in a2_dev.csv.

Writes results/cen_replication/a2_dev_cost_robustness.csv (statistics only).

Run: python code/cen/robust_costs.py
"""

import pandas as pd

from _paths import RESULTS
from extend import (END, HORIZONS, SIGNALS, costs_table, load_daily, nw_t, period_table,
                    stock_signals, tradability, zscore)

direction = (pd.read_csv(RESULTS / "a2_dev.csv").query("family == 'tradability'")
             .set_index(["signal", "horizon"]).direction)

d = load_daily()
d = d.join(pd.concat([stock_signals(x) for _, x in d.groupby("gvkey")]))
rows = []
for horizon, (freq, lags, ppy) in HORIZONS.items():
    x = period_table(d, freq).assign(u_broad=lambda t: t.in_index)
    assert x.Date.max() <= END and x.datadate.max() <= END
    ub = costs_table(zscore(x, "u_broad"), d)
    half = ub.assign(cs_half_bp_l=ub.cs_half_bp_l * 0.5)
    third = ub.groupby("Date").mcap_lag.transform(lambda v: pd.qcut(v.rank(method="first"), 3, labels=False))
    top_two = {dt: set(g.SecID) for dt, g in ub[third >= 1].groupby("Date")}
    for s in SIGNALS:
        sign = int(direction[s, horizon])
        for check, frame, members in [("half_spread", half, None), ("top_two_size", ub, top_two)]:
            gross, net, turnover = tradability(frame, s, sign, ppy, lags, members=members)
            rows.append({"check": check, "signal": s, "horizon": horizon, "direction": sign,
                         "gross_mean": gross.mean(), "gross_t": nw_t(gross, lags), "net_mean": net.mean(),
                         "net_t": nw_t(net, lags), "n_periods": len(net), "turnover": turnover})

out = pd.DataFrame(rows)
out.round(6).to_csv(RESULTS / "a2_dev_cost_robustness.csv", index=False)
print(out.round(4).to_string(index=False))
