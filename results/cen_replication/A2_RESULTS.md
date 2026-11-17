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
