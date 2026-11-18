# Hold-out diagnostic: plain 12-1 momentum, 2020-01 to 2026-06

Diagnostic only, written after the hold-out was scored (PREREG.md). Nothing here changes a scored number. Code: `code/resmom_diagnostic.py`.

## Net Sharpe with 2020-03 to 2020-12 left out

| weights | months | net Sharpe, all | months left | net Sharpe, ex 2020-03 to 2020-12 | net ann %, ex |
|---|---|---|---|---|---|
| equal | 78 | 0.85 | 68 | 0.72 | 13.07 |
| inverse_vol | 78 | 0.77 | 68 | 0.76 | 13.78 |
| hrp | 78 | 0.80 | 68 | 0.78 | 14.70 |

## Five best months, equal weight

| month | net % | gross % | long leg % | short leg % |
|---|---|---|---|---|
| 2020-07 | +18.08 | +20.51 | +15.32 | -5.19 |
| 2026-01 | +16.72 | +17.91 | +13.69 | -4.22 |
| 2025-08 | +16.55 | +17.65 | +17.08 | -0.56 |
| 2026-04 | +16.20 | +16.90 | +20.53 | +3.63 |
| 2021-01 | +11.21 | +12.86 | +16.03 | +3.17 |

## Five worst months, equal weight

| month | net % | gross % | long leg % | short leg % |
|---|---|---|---|---|
| 2021-03 | -12.17 | -11.02 | -1.31 | +9.71 |
| 2026-06 | -8.72 | -7.34 | -10.77 | -3.43 |
| 2021-06 | -8.44 | -7.28 | +1.19 | +8.47 |
| 2025-10 | -7.66 | -6.67 | -1.67 | +4.99 |
| 2024-09 | -7.01 | -6.16 | +2.69 | +8.85 |

Leg returns are gross and reweighted over names with a return, as in `resmom_compare.py`.

What drove them: in the five best months the long leg made 16.5% on average against -0.6% for the short leg; in 4 of the five worst months the short leg rose (5.0% to 9.7%). In these ten months the largest single name moved the long-short by 2.0 to 8.2 points.

Leg sizes in the hold-out: long median 23 names; short median 10, minimum 5, at most 6 names in 10 of 78 months. The borrow screen keeps the short leg small, so one short can move a month by several points.
