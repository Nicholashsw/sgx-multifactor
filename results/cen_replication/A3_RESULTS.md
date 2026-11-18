# Trading rules on the A2 weekly books: results (A3-cost)

The original A3 was withdrawn before any run: its rules were never specified, and there is no daily STI series. A3-cost replaces it. It was registered on 19 Nov 2026, **after the A2 development and hold-out results were seen** (`PREREG.md`, row "A3-cost registered"), so it is not a blind test. Code: `code/cen/timing.py`. Table: `a3_dev.csv`.

## Development window, 2003-01 to 2019-12

Written 19 Nov 2026. The hold-out has not been run.

### In plain English

- **No rule makes the books profitable after costs.** None of the 12 tests clears the bar of 2.87. The best is banding on Williams %R, at +0.03% a week (t = 0.40).
- **Banding is the only rule that helps consistently.** Requiring a name to leave the top (or bottom) 30% before it is sold cuts turnover:

  | Signal | A2 turnover | Banded turnover |
  |---|---|---|
  | Williams %R | 76% | 50% |
  | Keltner %B | 59% | 37% |
  | Reversal | 86% | 71% |

  This improves the net return over the A2 book for all three signals (t 3.70, 1.22 and 8.47). It takes Williams %R and Keltner %B from small losses to roughly zero, and reversal from -0.83% to -0.58% a week.
- **Holding four weeks cuts turnover to about 22% but makes things worse.** Most of the edge is gone after the first week: the 20-day markout is no larger than the 5-day one.
- **Trading only names with below-median spreads removes most of the gross edge.** The 1-day markout falls by more than half, so the signal lives in the expensive names.
- **The market-regime filter hurts.** The filter sits out the 28% of weeks when the equal-weight index is below its 200-day average. It does worse than the A2 book for Williams %R and Keltner %B (t -2.29 and -2.51 for the difference) and makes no difference for reversal. The weeks in the market look no better than average, so paying to exit and re-enter is a net loss.

### Method

- **Baseline:** the A2 weekly decile long-short in the broad universe, with A2's directions and costs. The costs are the traded-days Corwin-Schultz half-spread on names bought and sold, the Markit lendable screen on shorts and the Markit fee. The engine reproduces A2's weekly net series exactly before any rule is run.
- **Rules:**
  1. Banding: enter the top (bottom) decile; exit only when the name leaves the top (bottom) 30%.
  2. Spread filter: trade only names whose prior-month half-spread is below that date's median.
  3. 4-week hold: four staggered sub-books, a quarter rebalanced each week.
  4. Regime: hold positions only when the equal-weight index is above its 200-day average; otherwise cash, with exit and re-entry costs charged.
- **Test:** the Newey-West t (4 lags) of the mean weekly net return. There are 12 tests (3 signals x 4 rules) and the bar is 2.87.
- **Descriptive only:** turnover, the rule minus the A2 book, and gross markouts after each entry, signed by leg.

### Tests: weekly net return, bar 2.87 (0 of 12 pass)

| Signal | Rule | Net per week | t | Weeks | Turnover | Rule minus A2 (t) |
|---|---|---|---|---|---|---|
| Williams %R | *A2 book* | -0.10% | -1.15 | 860 | 76% | |
| Williams %R | banding | +0.03% | 0.40 | 867 | 50% | +0.13% (3.70) |
| Williams %R | spread filter | -0.05% | -0.67 | 848 | 79% | +0.04% (0.57) |
| Williams %R | 4-week hold | -0.26% | -5.14 | 871 | 22% | -0.17% (-2.85) |
| Williams %R | regime | -0.20% | -3.06 | 868 | 55% | -0.11% (-2.29) |
| Keltner %B | *A2 book* | -0.03% | -0.33 | 861 | 59% | |
| Keltner %B | banding | +0.02% | 0.20 | 867 | 37% | +0.04% (1.22) |
| Keltner %B | spread filter | -0.09% | -0.87 | 849 | 62% | -0.08% (-0.97) |
| Keltner %B | 4-week hold | -0.36% | -6.05 | 870 | 22% | -0.34% (-4.90) |
| Keltner %B | regime | -0.18% | -2.30 | 868 | 43% | -0.14% (-2.51) |
| Reversal | *A2 book* | -0.83% | -7.42 | 858 | 86% | |
| Reversal | banding | -0.58% | -5.46 | 864 | 71% | +0.25% (8.47) |
| Reversal | spread filter | -0.23% | -2.09 | 851 | 88% | +0.60% (6.34) |
| Reversal | 4-week hold | -0.38% | -5.59 | 872 | 22% | +0.43% (5.47) |
| Reversal | regime | -0.80% | -9.37 | 864 | 62% | +0.03% (0.36) |

The regime rule was in the market in 71.5% of weeks for each signal.

### Gross markouts after entry (descriptive)

Mean signed return from the formation close, before costs:

| Signal | Rule | 1 day | 5 days | 20 days |
|---|---|---|---|---|
| Williams %R | A2 book | 0.50% | 0.76% | 0.55% |
| Williams %R | banding | 0.50% | 0.78% | 0.58% |
| Williams %R | spread filter | 0.19% | 0.31% | 0.15% |
| Keltner %B | A2 book | 0.28% | 0.62% | 0.35% |
| Keltner %B | spread filter | 0.11% | 0.33% | 0.00% |
| Reversal | A2 book | 0.31% | 0.69% | 0.49% |
| Reversal | spread filter | 0.11% | 0.33% | 0.13% |

The other rows are in `a3_dev.csv`. The gross edge peaks around five days and fades by twenty. Among names with below-median spreads, it is less than half as large.

### Reading

The A2 weekly oscillator books fail because turnover is high and the edge sits in expensive, illiquid names. Of the four rules, only banding attacks the first problem without giving up the edge, and it gets the books to about break-even at best. None of the rules makes the signals tradable at estimated Corwin-Schultz spreads.

## Hold-out

Not run. The command and its caveats are in `docs/report_drafts/HOLDOUT_QUEUE.md`. These signals' 2020+ returns were already seen in A2, so an A3-cost hold-out would not be a clean out-of-sample test.
