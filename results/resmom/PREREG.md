# Pre-registration: PCA residual momentum against plain momentum

Written 19 Nov 2026, before the first run. This is an extension and does not change the frozen strategy (`STRATEGY_FREEZE.md`). Every cell below is reported whatever the result. Changes after the first run go in the amendment log at the bottom, with date and reason.

Development window: holding months 2003-01 to 2019-12. Hold-out: holding months 2020-01 to 2026-06 (`HOLDOUT_START = "2020-01-01"` in `code/holdout.py`). A development run drops all daily returns and monthly panel rows dated on or after `HOLDOUT_START` as it loads them, and its cost inputs come from months before formation, so it uses nothing from the hold-out. The hold-out is run once, with `--final`, after the development table is written up. Nothing is changed in response to it.

## Question

Does momentum measured on PCA residual returns earn more, net of costs, than plain 12-1 momentum on the same SGX universe and the same books?

## Signals (2)

- Plain momentum: `MOM_12_1` from the broad monthly panel, total return index at t-1 over t-12, minus 1.
- Residual momentum: at each month-end formation date, a PCA is fitted on the last 252 trading days of daily returns of the eligible names, using only data up to that date. Residuals are the daily returns minus their projection on the first 3 components. The signal is the sum of daily residuals from the start of month t-11 to the end of month t-1, divided by their standard deviation over the same days.

The window (252) and number of components (3) are fixed here and in `code/resmom_compare.py` (`PCA_WINDOW = 252`, `PCA_K = 3`). Neither is tuned.

## Universe (identical for both signals)

At each formation date, a name is eligible if all of these hold:
- it is in the point-in-time WRDS index list (`in_index`) on its last trading day in the formation month;
- it has a return on at least 80% of the 252 days in the window, with non-zero variance;
- both signals are defined for it.

A month is skipped if fewer than 40 names are eligible.

## Books

- Decile long-short, k = max(5, n // 10) names per leg, formed monthly, held one month.
- The short leg keeps only names Markit showed as lendable in the month before formation; a month with fewer than 3 such names is skipped.
- Weights within each leg, three schemes: equal; inverse volatility (1 / daily std over the window); hierarchical risk parity (single-linkage clustering on correlation distance, recursive bisection with inverse-variance cluster weights, from the window's covariance).
- Holding returns are the panel's next-month total return. A held name with no return is dropped from its leg for that month and the leg is reweighted over the others, as in `code/cen/costs.py`.

## Costs (the repository's engine, `code/cen/costs.py`, charged on weights)

- Corwin-Schultz traded-days half-spread from the month before formation, charged on |change in weight| on each leg. A missing spread takes the leg median.
- Markit indicative fee from the month before formation, weighted over the short leg, divided by 12.
- Gross is the same borrow-screened book before spreads and fees.

## Reported (6 cells: 2 signals x 3 schemes)

Gross and net annualised return, net Sharpe (monthly, times sqrt 12, no risk-free), net maximum drawdown, annual one-way turnover (average of the two legs), average number of holdings (both legs), average holding half-spread (weight-averaged, both legs), number of months. For each scheme, on the months both signals have: the mean monthly net return of residual momentum minus plain momentum, and its Newey-West t (6 lags).

## What counts as a result

- Residual momentum is better if its net Sharpe beats plain momentum's under the same scheme in at least 2 of 3 schemes, in development and then in the hold-out.
- Six cells are compared. Over 17 years the standard error of one annual Sharpe is about 0.24 (roughly 1 / sqrt(years)), so small differences are noise; this is stated, not tested.
- Any net Sharpe above 1.5 is treated as a likely error and checked before it is reported.

## Amendment log

- 19 Nov 2026, after the first development run. Bug fix, not a change of specification. The first run took residuals of demeaned returns. Over a 252-day window, which the 12-1 period almost fills, demeaned residuals sum to about zero, so the signal was close to minus the last month's residual return: a reversal signal with the sign flipped. That run showed one-way turnover of about 1,070% a year and negative gross returns in all three schemes (equal -4.86%, inverse vol -4.51%, HRP -4.94% a year). The components are still estimated from demeaned returns, but residuals now come from the raw returns, so each name keeps its drift, as the definition above intends. The plain momentum rows are unaffected. The first run's table is not kept as a result.
- 19 Nov 2026, after the development run and before the hold-out. Settings moved out of `config.py`, which `.git/info/exclude` keeps untracked, into tracked files: `HOLDOUT_START = "2020-01-01"` in `code/holdout.py`, `PCA_WINDOW = 252` and `PCA_K = 3` in `code/resmom_compare.py`. Values unchanged. The table gains the common-month comparison above, because the borrow screen skips different months for the two signals (192 and 196 development months). This is reporting only; the pass rule is unchanged.
