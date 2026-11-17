# Draft: Replicating and extending Cen (2023) on Singapore stocks

*Draft section for the FYP report, 19 Nov 2026. It does not replace anything in `REPORT_FINAL.md`. Every number comes from a file in `results/cen_replication/`; the file and the commit that last wrote it are given under each table. The plan was pre-registered in `results/cen_replication/PREREG.md`, and every change is in its amendment log.*

## Background

Cen (2023) tested 86 technical-analysis signals from the Python `ta` package on 25 large Singapore stocks over 2012 to 2022. After a Bonferroni correction, five survived: Williams %R, RSI, Bollinger %B, Keltner %B and the stochastic signal. We did three things:

1. Rebuilt his setup as closely as the data allow (Part A1).
2. Tested his five signals, plus three others and a reversal control, on a much larger point-in-time universe with trading costs (Part A2).
3. Planned to test four entry and exit timing rules on the main strategy's book (Part A3). This part was not run; see below.

## A1: replicating his setup

- **Universe:** 21 of his 25 stocks. DFI Retail (D01), Hongkong Land (H78) and Jardine Matheson (J36) are incorporated in Bermuda and are not in our Compustat Singapore extract. Yangzijiang Shipbuilding (BS6) is missing too; only its later spin-offs are there.
- **Data:** Compustat daily prices, 2012-01-03 to 2022-12-30.
- **Method:** each day, the next day's return is regressed across stocks on one signal at a time. The t is the mean slope over its standard error, as Cen computed it, with a Newey-West t (5 lags) beside it.
- **Pass rule:** one of his five survivors passes if it keeps his sign and lands within 1.0 of his t.

| Signal | Cen's t | Our t | Newey-West t | Same-day t (diagnostic) | Replicates? |
|---|---|---|---|---|---|
| Williams %R | -5.84 | -6.30 | -6.32 | 53.10 | yes |
| RSI | -4.62 | -4.92 | -4.76 | 52.97 | yes |
| Bollinger %B | -4.23 | -4.82 | -4.52 | 52.10 | yes |
| Keltner %B | -4.09 | -6.95 | -6.46 | 72.47 | no (same sign, 2.9 stronger) |
| Stochastic signal | 3.51 | -3.00 | -2.92 | 20.34 | no (opposite sign) |

*Source: `results/cen_replication/a1_replication.csv` (commit b3c1123).*

Three of the five replicate. Eleven of the 86 signals clear Cen's bar of 3.44, under both the plain and the Newey-West t. All eleven are negative, and the strongest is the day's own return (t = -10.0), which is plain one-day reversal.

The same-day t-statistics are very large and positive. That is mechanical, since each signal uses the same day's close. Cen's survivors have the next-day signs, so his results do not look like they contained look-ahead.

The two failures are discussed in the "A1 notes" in `PREREG.md`:

- **Keltner %B:** `ta`'s default Keltner channel uses a 10-day window.
- **Stochastic signal:** Cen's own appendix is not internally consistent for the stochastic columns. Williams %R and the stochastic %K have the same slopes by construction, yet he reports different t-statistics for them.

## A2: the extension

- **Signals:**
  - Cen's five, with the same windows.
  - Trend: close over its 200-day average, minus 1.
  - Volatility: ATR(14) over close.
  - Volume: MFI(14).
  - A reversal control: minus the past week's or month's return.
- **Universes:**
  - The broad point-in-time WRDS index list, about 230 stocks a date, with delisted firms included.
  - An STI-like list: the 30 largest names by market cap at each June rebalance.
- **Horizons:** weekly and monthly. A stock only enters a cross-section if it traded on that period's last market day.
- **Test families:**

| Family | What it measures | Bar |
|---|---|---|
| Primary (36 tests) | Fama-MacBeth slope on one signal, Newey-West t | 3.20 |
| Mechanism (20 tests) | Oscillator slope with the reversal control added | 3.02 |
| Tradability (18 tests) | Decile long-short on the broad universe, after Corwin-Schultz spreads, the Markit borrow screen and Markit fees | 2.99 |

The cost code is a port of the main study's `waterfall.py`. It reproduces that script's saved results exactly (`PREREG.md`, row "Waterfall port").

### Primary results (Newey-West t, bar 3.20)

| Signal | Broad weekly, dev | Broad weekly, hold-out | Broad monthly, dev | Broad monthly, hold-out | STI weekly, dev | STI weekly, hold-out |
|---|---|---|---|---|---|---|
| Williams %R | -12.90 | -14.54 | -1.40 | -6.61 | -4.75 | -0.19 |
| RSI | -6.87 | -9.62 | 1.61 | -3.51 | -2.91 | 0.37 |
| Bollinger %B | -9.97 | -11.35 | 0.16 | -6.09 | -3.44 | 0.08 |
| Keltner %B | -9.70 | -11.34 | -0.27 | -6.67 | -3.33 | 0.08 |
| Stochastic signal | -6.52 | -8.63 | 0.74 | -3.65 | -3.49 | 0.59 |
| Trend | -0.52 | -2.18 | 3.17 | 1.81 | 0.56 | 0.55 |
| ATR / close | -0.29 | 2.04 | -2.37 | 0.55 | -0.32 | -1.33 |
| MFI | -2.40 | 0.63 | 5.04 | 1.55 | -1.31 | 1.39 |
| Reversal | 11.02 | 9.44 | -1.24 | 1.77 | 4.77 | 1.24 |

*Sources: `results/cen_replication/a2_dev.csv` (development, 2003 to 2019, commit 028cb2b) and `results/cen_replication/a2_holdout.csv` (hold-out, 2020 to 2026, commit 49b6542), rows `family = primary`. STI monthly cells are in the same files.*

In the broad universe, stocks that look overbought on any of Cen's five oscillators do worse the next week, in both periods. In the hold-out this also shows up monthly. Among STI-sized stocks the effect is there in development, but it disappears in the hold-out.

### Is it just reversal? (mechanism, bar 3.02)

Adding last week's return as a control takes most of the weekly effect away in development. Only Williams %R in the broad universe survives, with t = -7.48. In the hold-out more of it survives: Williams %R -11.84 and Keltner %B -6.18 weekly (`a2_dev.csv` and `a2_holdout.csv`, rows `family = mechanism`).

### Tradability (bar 2.99)

| Signal | Weekly net, dev | Weekly net, hold-out | Monthly net, dev | Monthly net, hold-out |
|---|---|---|---|---|
| Williams %R | -0.10% (t -1.15) | +0.37% (t 2.71) | -1.08% (t -2.91) | -0.13% (t -0.26) |
| Keltner %B | -0.03% (t -0.33) | +0.37% (t 2.37) | -1.57% (t -4.60) | -0.63% (t -1.10) |
| Reversal | -0.83% (t -7.42) | -0.82% (t -4.86) | -3.22% (t -9.08) | -1.33% (t -1.52) |

*Sources: `a2_dev.csv` and `a2_holdout.csv`, rows `family = tradability`. The other signals are in the same files.*

None of the 18 long-short books clears 2.99 in either period. The weekly books turn over 52% to 86% a week, and the gross effect sits in the smallest third of stocks. In the smallest third, the weekly gross t for the oscillators is 8.6 to 14.9 in development; in the largest third it is 0.4 to 4.4 (`a2_size_terciles.csv`, commit 028cb2b).

### Cost sensitivity

The rule is untradable at estimated Corwin-Schultz spreads. Williams %R weekly is positive at half cost: +0.64% a week (t 7.28) in development and +1.19% a week (t 8.61) in the hold-out. Restricted to the larger two thirds of stocks, every weekly book loses money at full cost in both periods.

*Sources: `a2_dev_cost_robustness.csv` (commit 028cb2b) and `a2_holdout_cost_robustness.csv` (commit 49b6542).*

### Hypotheses

| Hypothesis | Development | Hold-out |
|---|---|---|
| H1: all five oscillators negative | holds weekly, fails monthly | holds in the broad universe, fails in the STI-like universe |
| H2: the reversal control at least halves each oscillator's \|t\| | holds weekly in 9 of 10 cells | mostly fails |
| H3: trend positive, volatility negative, volume two-sided | signs as expected; only MFI is significant | fails |
| H4: nothing survives costs weekly; gross effect strongest in the smallest third | holds | holds on the bar (no book clears 2.99), but two weekly books are positive net |

### Findings

The registered rule needs three things: the signal clears its bar in development, keeps its sign in the hold-out, and has a net long-short t above 1.96 in development. The rule did not say which period's net t counts. That gap came up after the hold-out had run, so the stricter reading, development, was taken (`PREREG.md`, row "Finding rule").

Under that rule **nothing qualifies as a finding**. Williams %R and Keltner %B weekly are positive net of costs in the hold-out (t 2.71 and 2.37). They are reported as exploratory, not as findings.

### Checks

- **Real STI members.** On the Bloomberg year-end STI rosters for 2009 to 2019, mapped to Compustat, the weekly oscillators stay negative: Williams %R t = -3.84. Each year 22 to 25 of the mapped STI names are also in our top-30 list (`a2_dev_fssti.csv`, commit 028cb2b; `a2_sti_overlap.csv`, commit 8ff0d18).
- **Independent rebuild.** An independent rebuild of the broad-universe cells was compared cell by cell. With both using the same formation rule, nine of the ten differing weekly cells matched within 0.3. Weekly reversal (1.2 apart) and three small monthly cells still differed. The formation rule was then changed before the hold-out, and the reason is logged (`PREREG.md`, rows "Independent cross-check" and "Formation rule").

## A3: timing rules (not run)

A3 would have tested four entry and exit rules on the main strategy's top-decile book. It was not run, for three reasons:

- `PREREG.md` names the rules but defines them only "in the work plan", which is not in the repository or the backups.
- The registration does not say which markout horizon is each rule's test.
- There is no daily STI index series for the STI 200-day filter.

Defining the rules now, after seeing A2, would have meant making design choices after the results (`PREREG.md`, row "A3 skipped").

## Conclusion

Cen's oscillators do predict short-term returns in Singapore, and the effect replicates for three of his five signals. It is mostly short-term reversal in small, illiquid stocks, and it does not survive realistic trading costs. Among the large stocks Cen studied, the effect was present in 2003 to 2019 and gone in 2020 to 2026.
