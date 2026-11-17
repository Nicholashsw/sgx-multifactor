# Cen's technical signals on Singapore stocks: results (Part A2)

Registered in `PREREG.md`, Part A2, with the amendments in its log. Code: `code/cen/extend.py`, `code/cen/costs.py` (the waterfall port), `code/cen/robust_costs.py`. Tables: `a2_dev.csv`, `a2_size_terciles.csv`, `a2_dev_cost_robustness.csv`, plus `a2_dev_fssti.csv` and `a2_sti_overlap.csv` for the roster check.

## Development window, 2003-01 to 2019-12

Written 18 Nov 2026, before the hold-out is run.

### In plain English

- **Weekly, overbought stocks do worse the next week.** All five of Cen's oscillators have negative weekly slopes in both universes. Nine of the ten weekly cells clear the bar of 3.20; RSI in the STI universe falls just short at -2.91.
- **This is mostly one-week reversal.** With last week's return added as a control, the oscillators lose most of their t. Only Williams %R in the broad universe keeps a significant slope (t = -7.48), and even it keeps 58% of its t.
- **Monthly, almost nothing.** No oscillator has a significant monthly slope, and three have the wrong sign. MFI is the one monthly signal that clears its bar (t = 5.04). Trend just misses (3.17).
- **Untradable at estimated Corwin-Schultz spreads.** None of the 18 long-short tests passes after spreads, the borrow screen and fees. Most are significantly negative: the oscillator and reversal books turn over 52% to 86% a week, and the effect sits in the smallest, least liquid names.
- **Williams %R weekly is positive at half cost.** At half the estimated spread it earns +0.64% a week (t = 7.28), and Keltner %B +0.40% (t = 3.97). Among the larger two thirds of stocks, every weekly cell loses money at full cost.

### Sample and method

- **Universes:**
  - Broad: the point-in-time WRDS index list, about 230 names a date, with delisted firms included.
  - STI: the top 30 of that list by lagged market cap at each June rebalance.
- **Signals and dates:**
  - Signals are formed at the last market day of each week or month. The tests use 874 to 883 weeks and 201 to 203 months; fewer dates where a cross-section has under 10 names that traded on the day.
  - A stock enters a cross-section only if it traded on that day.
  - Each signal is winsorised at 1/99 and z-scored across the universe on each date.
- **Tests:**
  - Primary and mechanism are Fama-MacBeth slopes with a Newey-West t (4 lags weekly, 6 monthly).
  - Tradability is an equal-weight decile long-short in the registered direction, net of traded-days Corwin-Schultz spreads, the Markit availability screen and the Markit fee. The cost engine reproduces `code/waterfall.py`'s saved results exactly. Its t is the Newey-West t of the mean net return.

### Primary: Fama-MacBeth t, bar 3.20 (12 of 36 pass, in bold)

| Signal | Broad weekly | Broad monthly | STI weekly | STI monthly |
|---|---|---|---|---|
| Williams %R | **-12.90** | -1.40 | **-4.75** | -1.55 |
| RSI | **-6.87** | 1.61 | -2.91 | -0.21 |
| Bollinger %B | **-9.97** | 0.16 | **-3.44** | -0.48 |
| Keltner %B | **-9.70** | -0.27 | **-3.33** | -0.11 |
| Stochastic signal | **-6.52** | 0.74 | **-3.49** | -0.13 |
| Trend (close / 200-day average - 1) | -0.52 | 3.17 | 0.56 | 0.70 |
| ATR / close | -0.29 | -2.37 | -0.32 | -0.39 |
| MFI | -2.40 | **5.04** | -1.31 | 2.01 |
| Reversal | **11.02** | -1.24 | **4.77** | -0.92 |

### Mechanism: oscillator t with the reversal control, bar 3.02 (1 of 20 passes)

| Signal | Broad weekly | Broad monthly | STI weekly | STI monthly |
|---|---|---|---|---|
| Williams %R | **-7.48** | -2.38 | -1.52 | -1.91 |
| RSI | 2.01 | 1.49 | 0.22 | -0.30 |
| Bollinger %B | -1.00 | -0.57 | 0.09 | -0.68 |
| Keltner %B | -2.90 | -1.35 | -0.10 | -0.65 |
| Stochastic signal | 2.66 | 0.08 | -0.28 | -0.42 |

### Tradability: broad universe decile long-short, bar 2.99 (0 of 18 pass)

The direction is short the top decile for the oscillators and ATR, and long for trend and reversal. MFI is short weekly and long monthly, following the sign of its primary slope. Returns are per holding period: one week or one month.

| Signal | Weekly gross (t) | Weekly net (t) | Weekly turnover | Monthly gross (t) | Monthly net (t) |
|---|---|---|---|---|---|
| Williams %R | +1.54% (15.57) | -0.10% (-1.15) | 76% | +1.02% (2.33) | -1.08% (-2.91) |
| RSI | +0.55% (5.07) | -0.41% (-3.89) | 52% | -0.43% (-1.15) | -1.94% (-5.65) |
| Bollinger %B | +0.87% (8.47) | -0.55% (-5.91) | 78% | -0.05% (-0.14) | -1.87% (-5.96) |
| Keltner %B | +0.97% (9.20) | -0.03% (-0.33) | 58% | +0.09% (0.25) | -1.57% (-4.60) |
| Stochastic signal | +0.74% (8.60) | -0.55% (-6.60) | 70% | +0.13% (0.31) | -1.47% (-3.84) |
| Trend | -0.08% (-0.62) | -0.64% (-4.74) | 17% | +1.74% (3.41) | -0.09% (-0.14) |
| ATR / close | +0.17% (1.21) | -0.43% (-2.79) | 20% | +1.19% (2.10) | -0.78% (-0.87) |
| MFI | +0.26% (3.79) | -0.99% (-14.85) | 57% | +0.72% (2.96) | -1.55% (-5.67) |
| Reversal | +1.35% (12.02) | -0.83% (-7.42) | 86% | -0.54% (-1.60) | -3.22% (-9.08) |

Benjamini-Yekutieli puts 29 of the 74 tests at q < 0.05: 14 primary, 2 mechanism and 13 tradability. All 13 tradability ones are significantly negative.

### Hypotheses

- **H1 (all five oscillators negative): holds weekly, fails monthly.** All ten weekly cells are negative, nine of them significant. Monthly, RSI, Bollinger %B and the stochastic signal have positive slopes in the broad universe, none significant.
- **H2 (the reversal control at least halves each oscillator's |t|): holds weekly in 9 of 10 cells.** The exception is Williams %R in the broad universe, which keeps 58%. Monthly, the oscillators have no effect to explain, so H2 does not apply there.
- **H3 (trend positive, volatility negative, volume two-sided): signs as expected monthly, not significant except volume.**
  - Trend is positive monthly (broad 3.17, STI 0.70) but slightly negative weekly in the broad universe.
  - ATR is negative in three of four cells, all with |t| below 2.4.
  - MFI is two-sided: +5.04 monthly (passes) and -2.40 weekly.
- **H4 (nothing survives net of costs weekly; the gross effect is strongest in the smallest, least liquid third): holds.** No weekly cell is positive net of costs. The weekly gross t in the smallest third is 8.6 to 14.9 for every oscillator and for reversal, against 0.4 to 4.4 in the largest third.

Gross weekly long-short t by size third (`a2_size_terciles.csv`):

| Signal | Small | Mid | Large |
|---|---|---|---|
| Williams %R | 14.92 | 7.96 | 4.43 |
| RSI | 8.60 | 0.53 | 0.40 |
| Bollinger %B | 11.17 | 2.49 | 2.51 |
| Keltner %B | 11.88 | 3.75 | 1.29 |
| Stochastic signal | 10.69 | 2.67 | 3.22 |
| Trend | -3.89 | 2.32 | 1.48 |
| ATR / close | -0.74 | 1.62 | 0.55 |
| MFI | 5.59 | 0.55 | 0.59 |
| Reversal | 14.57 | 4.28 | 3.15 |

### Cost sensitivity (outside the bars)

Untradable at estimated Corwin-Schultz spreads; Williams %R weekly is positive at half cost. This check was registered before running: the same 18 long-short books, once with the half-spread halved and once on the top two thirds by size at full cost. Net return per period, with t:

| Signal | Half spread, weekly | Half spread, monthly | Top two thirds, weekly | Top two thirds, monthly |
|---|---|---|---|---|
| Williams %R | **+0.64% (7.28)** | -0.22% (-0.57) | -0.46% (-6.78) | -0.97% (-4.14) |
| RSI | +0.01% (0.07) | -1.32% (-3.74) | -0.63% (-6.78) | -1.82% (-6.30) |
| Bollinger %B | +0.09% (0.94) | -1.15% (-3.53) | -0.72% (-8.84) | -1.80% (-7.11) |
| Keltner %B | **+0.40% (3.97)** | -0.97% (-2.75) | -0.42% (-5.13) | -1.63% (-6.62) |
| Stochastic signal | +0.06% (0.77) | -0.72% (-1.86) | -0.69% (-9.55) | -1.47% (-5.26) |
| Trend | -0.41% (-3.14) | +0.35% (0.56) | -0.16% (-1.34) | +0.24% (0.49) |
| ATR / close | -0.22% (-1.43) | -0.32% (-0.36) | -0.27% (-1.65) | -0.68% (-0.92) |
| MFI | -0.46% (-6.80) | -0.76% (-2.98) | -0.84% (-11.91) | -0.56% (-2.25) |
| Reversal | +0.16% (1.37) | -2.26% (-6.40) | -0.88% (-8.85) | -2.75% (-7.87) |

Whether the weekly oscillator edge is real money depends on trading the smallest names at well under the estimated spread.

### Robustness: Bloomberg FSSTI roster, 2009 to 2019 (outside the bars)

On the actual STI members, as far as they map to Compustat (22 to 25 of 30 a year), the weekly oscillators stay negative:

- Williams %R -3.84, Bollinger %B -3.37, Keltner %B -3.22, stochastic -2.58, RSI -2.38. Reversal is +4.58.
- With the reversal control, every oscillator's |t| falls below 1.1.

Each year, 22 to 25 of the mapped FSSTI names are also in the top-30 list (`a2_sti_overlap.csv`).

### Notes

- **Formation rule:** changed before the hold-out (see the amendment log). The cross-check row keeps the as-run numbers. The change weakened results, and mechanism Keltner %B weekly went from pass (-3.93) to fail (-2.90).
- **Return windows:** they never extend past 2019-12-31, because no data after that date is read in the development run.

## Hold-out, 2020-01 to 2026-06

Run once on 18 Nov 2026 on the frozen code (A2 frozen at 30cfe3c, code unchanged since 364b857). It used the same rules, with tradability directions taken from development. The sample is 339 weeks and 77 months. Tables: `a2_holdout.csv`, `a2_holdout_size_terciles.csv`, `a2_holdout_cost_robustness.csv`. The FSSTI roster check covers 2009 to 2019 only and is not part of the hold-out.

### In plain English

- **In the broad universe the oscillator effect is stronger than in development, and now shows monthly too.** All five oscillators are significantly negative weekly (t -8.6 to -14.5) and monthly (t -3.5 to -6.7).
- **In the STI universe it disappears.** No STI oscillator cell is significant at either horizon, and three weekly development passes flip to small positive t.
- **Reversal explains less of it than before.** Williams %R keeps 81% of its weekly t with the reversal control, and Keltner %B keeps 54%.
- **Still untradable at estimated Corwin-Schultz spreads.** No long-short cell clears 2.99. Williams %R weekly (+0.37% a week, t = 2.71) and Keltner %B weekly (+0.37%, t = 2.37) are positive net of costs. Williams %R weekly is positive at half cost in both periods (+1.19% a week, t = 8.61, here). Among the larger two thirds of stocks every weekly cell loses money at full cost again.

### Primary: Fama-MacBeth t, bar 3.20 (11 of 36 pass, in bold)

| Signal | Broad weekly | Broad monthly | STI weekly | STI monthly |
|---|---|---|---|---|
| Williams %R | **-14.54** | **-6.61** | -0.19 | 0.27 |
| RSI | **-9.62** | **-3.51** | 0.37 | 1.29 |
| Bollinger %B | **-11.35** | **-6.09** | 0.08 | 1.47 |
| Keltner %B | **-11.34** | **-6.67** | 0.08 | 1.14 |
| Stochastic signal | **-8.63** | **-3.65** | 0.59 | 0.87 |
| Trend | -2.18 | 1.81 | 0.55 | 0.99 |
| ATR / close | 2.04 | 0.55 | -1.33 | -0.90 |
| MFI | 0.63 | 1.55 | 1.39 | 1.81 |
| Reversal | **9.44** | 1.77 | 1.24 | -0.78 |

### Mechanism: oscillator t with the reversal control, bar 3.02 (7 of 20 pass)

| Signal | Broad weekly | Broad monthly | STI weekly | STI monthly |
|---|---|---|---|---|
| Williams %R | **-11.84** | **-6.68** | 0.66 | -0.61 |
| RSI | **-3.19** | -1.96 | 1.41 | -0.05 |
| Bollinger %B | **-3.97** | **-3.24** | 1.09 | 0.28 |
| Keltner %B | **-6.18** | **-3.54** | 0.80 | -0.14 |
| Stochastic signal | -2.91 | -2.92 | 1.83 | -0.21 |

### Tradability: broad universe decile long-short, bar 2.99 (0 of 18 pass)

| Signal | Weekly gross (t) | Weekly net (t) | Monthly gross (t) | Monthly net (t) |
|---|---|---|---|---|
| Williams %R | +2.29% (16.62) | +0.37% (2.71) | +2.28% (7.60) | -0.13% (-0.26) |
| RSI | +1.02% (6.84) | -0.06% (-0.44) | +1.07% (2.91) | -0.99% (-2.03) |
| Bollinger %B | +1.33% (9.90) | -0.41% (-3.07) | +1.49% (3.76) | -0.76% (-1.46) |
| Keltner %B | +1.61% (10.40) | +0.37% (2.37) | +1.44% (4.01) | -0.63% (-1.10) |
| Stochastic signal | +1.32% (9.62) | -0.29% (-2.07) | +1.54% (3.96) | -0.98% (-1.47) |
| Trend | -0.56% (-2.62) | -0.76% (-3.05) | +1.63% (2.93) | +0.92% (1.33) |
| ATR / close | -0.34% (-1.88) | -0.68% (-3.02) | -0.04% (-0.07) | -1.47% (-1.61) |
| MFI | +0.05% (0.44) | -1.30% (-10.73) | +0.18% (0.64) | -1.99% (-4.76) |
| Reversal | +1.63% (9.61) | -0.82% (-4.86) | +1.52% (2.30) | -1.33% (-1.52) |

Benjamini-Yekutieli puts 24 of the 74 at q < 0.05: 11 primary, 7 mechanism and 6 tradability.

### Development against hold-out, for the 13 development passes

| Test | Development t | Hold-out t | Same sign |
|---|---|---|---|
| Primary Williams %R, broad weekly | -12.90 | -14.54 | yes |
| Primary RSI, broad weekly | -6.87 | -9.62 | yes |
| Primary Bollinger %B, broad weekly | -9.97 | -11.35 | yes |
| Primary Keltner %B, broad weekly | -9.70 | -11.34 | yes |
| Primary stochastic, broad weekly | -6.52 | -8.63 | yes |
| Primary reversal, broad weekly | 11.02 | 9.44 | yes |
| Mechanism Williams %R, broad weekly | -7.48 | -11.84 | yes |
| Primary Williams %R, STI weekly | -4.75 | -0.19 | yes |
| Primary Bollinger %B, STI weekly | -3.44 | 0.08 | no |
| Primary Keltner %B, STI weekly | -3.33 | 0.08 | no |
| Primary stochastic, STI weekly | -3.49 | 0.59 | no |
| Primary reversal, STI weekly | 4.77 | 1.24 | yes |
| Primary MFI, broad monthly | 5.04 | 1.55 | yes |

**Findings under the registered rule.** The rule: clears its bar in development, keeps its sign in the hold-out, and has a net long-short t above 1.96. PREREG does not say which period's net t is meant.

- **Development net t:** no signal qualifies. The best weekly development net t is Keltner %B at -0.33.
- **Hold-out net t:** two signals qualify. Williams %R weekly has a hold-out net t of 2.71 and Keltner %B weekly 2.37. Both passed their broad weekly primary test in development and kept the sign.

Neither reading lets any net long-short book clear its own Bonferroni bar of 2.99 in either period.

### Hypotheses in the hold-out

- **H1 (all five oscillators negative): holds in the broad universe, fails in the STI universe.** All ten broad cells are negative and significant. Nine of the ten STI cells are positive, none significant.
- **H2 (the reversal control at least halves |t|): mostly fails.** In the broad universe, weekly RSI, Bollinger %B and the stochastic are halved (34% to 35% of t kept). Williams %R (81%) and Keltner %B (54%) are not, and no monthly cell is halved (53% to 101% kept). In the STI universe there is no effect to explain.
- **H3: fails.**
  - Trend is negative weekly (-2.18) and positive but not significant monthly (1.81).
  - ATR is positive in the broad universe (2.04 weekly), against the expected sign.
  - MFI is not significant anywhere.
- **H4 (nothing survives net of costs weekly; gross strongest in the smallest third): holds on the bar, not on the sign.**
  - No weekly long-short clears 2.99, but Williams %R and Keltner %B are positive net (t 2.71 and 2.37).
  - The gross effect is again strongest in the smallest third: t 9.0 to 13.0 for the oscillators, against -2.0 to 2.7 in the largest third.

Gross weekly long-short t by size third:

| Signal | Small | Mid | Large |
|---|---|---|---|
| Williams %R | 13.02 | 9.54 | 2.73 |
| RSI | 8.96 | 0.87 | -1.97 |
| Bollinger %B | 11.70 | 3.10 | -0.35 |
| Keltner %B | 10.17 | 5.55 | -1.31 |
| Stochastic signal | 10.67 | 5.10 | -0.85 |
| Trend | -5.53 | 1.66 | 1.46 |
| ATR / close | -2.92 | -0.83 | -0.78 |
| MFI | 2.91 | -2.71 | -1.62 |
| Reversal | 9.64 | 3.25 | 0.14 |

### Cost sensitivity in the hold-out (outside the bars)

Net return per period, with t:

| Signal | Half spread, weekly | Half spread, monthly | Top two thirds, weekly | Top two thirds, monthly |
|---|---|---|---|---|
| Williams %R | **+1.19% (8.61)** | +0.82% (1.61) | -0.38% (-3.75) | -0.61% (-1.76) |
| RSI | +0.39% (2.73) | -0.28% (-0.56) | -0.85% (-7.31) | -2.20% (-4.54) |
| Bollinger %B | +0.32% (2.35) | +0.08% (0.15) | -1.00% (-8.45) | -1.56% (-3.64) |
| Keltner %B | **+0.84% (5.31)** | +0.07% (0.12) | -0.60% (-4.94) | -1.87% (-3.26) |
| Stochastic signal | +0.40% (2.83) | -0.12% (-0.18) | -0.97% (-9.36) | -1.63% (-4.26) |
| Trend | -0.51% (-2.11) | +1.41% (2.08) | -0.13% (-0.72) | +1.24% (2.11) |
| ATR / close | -0.46% (-2.03) | -0.90% (-0.98) | -0.65% (-3.44) | -1.68% (-2.30) |
| MFI | -0.71% (-5.90) | -1.05% (-2.53) | -1.38% (-14.63) | -1.30% (-2.89) |
| Reversal | +0.28% (1.67) | -0.29% (-0.32) | -1.33% (-9.50) | -2.54% (-3.61) |

### Overall

Cen's oscillators predict next-week returns of Singapore stocks in both periods, but only across the broad universe. The effect is concentrated in the smallest names and is absent among STI-sized stocks in the hold-out.

It is untradable at estimated Corwin-Schultz spreads. Williams %R weekly is positive at half cost in both periods, and in the hold-out it is also positive at full cost (t = 2.71), though below its bar of 2.99. Whether that counts as a registered finding depends on which period the rule's net t refers to; see above.
