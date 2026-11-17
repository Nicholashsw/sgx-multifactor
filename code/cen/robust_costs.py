"""
A2 cost robustness, outside every bar (results/cen_replication/PREREG.md, row "Cost
robustness").

The 18 tradability cells of extend.py are rerun two ways:
  half_spread   traded-days Corwin-Schultz half-spread x 0.5, screen and fee unchanged
  top_two_size  full costs, universe limited to the top two thirds of the broad universe
                by lagged market cap at each formation date
Directions are those recorded in a2_dev.csv.

Writes results/cen_replication/a2_dev_cost_robustness.csv, or with --sample holdout
a2_holdout_cost_robustness.csv (statistics only).

Run: python code/cen/robust_costs.py [--sample holdout]
"""

import pandas as pd

from _paths import RESULTS
from extend import (END, HORIZONS, SAMPLE, SIGNALS, START, broad_frame, frozen_directions, load_daily,
                    members_of, nw_t, period_table, stock_signals, tradability)

direction = frozen_directions()
d = load_daily()
d = d.join(pd.concat([stock_signals(x) for _, x in d.groupby("gvkey")]))
rows = []
for horizon, (freq, lags, ppy) in HORIZONS.items():
    x = period_table(d, freq).assign(u_broad=lambda t: t.in_index & t.fresh)
    assert x.Date.between(START, END).all() and x.datadate.max() <= END
    ub = broad_frame(x, d)
    half = ub.assign(cs_half_bp_l=ub.cs_half_bp_l * 0.5)
    third = ub[ub.u_broad].groupby("Date").mcap_lag.transform(lambda v: pd.qcut(v.rank(method="first"), 3, labels=False))
    broad = members_of(ub, ub.u_broad)
    top_two = members_of(ub, third.reindex(ub.index) >= 1)
    for s in SIGNALS:
        sign = direction[s, horizon]
        for check, frame, members in [("half_spread", half, broad), ("top_two_size", ub, top_two)]:
            gross, net, turnover = tradability(frame, s, sign, ppy, lags, members)
            rows.append({"check": check, "signal": s, "horizon": horizon, "direction": sign,
                         "gross_mean": gross.mean(), "gross_t": nw_t(gross, lags), "net_mean": net.mean(),
                         "net_t": nw_t(net, lags), "n_periods": len(net), "turnover": turnover})

out = pd.DataFrame(rows)
out.round(6).to_csv(RESULTS / f"a2_{SAMPLE}_cost_robustness.csv", index=False)
print(out.round(4).to_string(index=False))
