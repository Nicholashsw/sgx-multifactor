# Strategy freeze

Frozen on 17 October 2026. From this date the main strategy below does not change. Anything tested afterwards is a robustness check: it goes in the log at the bottom with its result, whatever the result is, and counts toward the number of specifications tried.

## Main strategy

- **Universe.** WRDS World Indices Singapore constituents, point in time (the latest June snapshot at each month end), 1991 to 2026. Prices and fundamentals from Compustat Global. Delisted firms stay in until their last trading month.
- **Factors.** Eight, winsorised at 1% and 99% and z-scored each month: 12-1 and 6-1 momentum, book-to-market, dividend yield, earnings yield, ROE, small size (minus log market cap) and Amihud liquidity (signed so liquid scores high). Fundamentals are lagged four months.
- **Composite.** Fixed weights from the project's first factor model on the Bloomberg STI panel, never fitted to this universe: 12-1 momentum, book-to-market and ROE 0.20 each; dividend yield, earnings yield and Amihud 0.10 each; 6-1 momentum and small size 0.05 each. Weights are rescaled over the factors present, and a stock needs at least four.
- **Portfolio.** Monthly rebalance, equal-weighted deciles, long the top decile and short the bottom.
- **Evaluation.** IC is the Spearman correlation with next month's return, joined on the calendar. Alpha is the intercept on the WRDS Singapore market return. Both use Newey-West standard errors with 6 lags.
- **Costs.** Corwin-Schultz half-spreads (traded-days recipe) charged on the names bought and sold each month; shorts only where Markit showed lendable inventory the month before; Markit indicative fee on the shorts. 2003 to 2026, the Markit window.
- **Code.** `code/canonical_rerun.py` (Tables 1 to 4), `code/cs_spreads.py` and `code/waterfall.py` (costs).

## Numbers at the freeze

- Composite IC 0.049 (t = 5.15). Point-in-time long-short alpha 1.32%/mo (t = 3.82) at a flat 20 bp cost (Table 2).
- Cost waterfall: gross 1.661%/mo (t = 5.13), 0.920 after spreads, 0.611 after the borrow screen, 0.366 (t = 1.08) after fees.

## Robustness only

These are reported next to the main strategy and never replace it:

- Ex-quality, equal-weight and walk-forward IC weights (Table 4 and the waterfall files).
- The long-only top decile.
- The other cost conventions: spreads charged on every held name, and the uncorrected spread recipe (fully costed alpha 0.06 to 0.54%/mo).
- Size tiers, sector-neutral ranking and volatility targeting.
- The 65-test specification grid on 1995 to 2019.

## Rules after the freeze

- No change to the universe, factors, weights, portfolio rule, cost model or sample.
- Every new test is added to the log below with its date and result.
- Bug fixes are allowed. Each goes in the corrections log in REPORT_FINAL.md with the numbers before and after.

## Tests at the freeze

The 65-test grid, the four weightings in Table 4, four cost conventions, and the long-only book.

## Log of tests after the freeze

- 19 October 2026. Kalman dynamic hedge ratios on daily data, a labelled extension outside the strategy (results/kalman/PREREG.md, 295 daily tests, Bonferroni |t| > 3.76). H1 (Kalman beats a 252-day rolling beta) not supported; H2 (daily Kalman pairs net OOS t > 2) not supported.
