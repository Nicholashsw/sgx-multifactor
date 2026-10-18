# Kalman dynamic hedge ratios on daily data: pre-registration

Written on 19 October 2026, before any daily test was run. This is a labelled extension
under STRATEGY_FREEZE.md. It does not change the frozen strategy, its code or its results.

## Why

The monthly study on the Bloomberg STI panel was null: out-of-sample hedge effectiveness
30.7% for the Kalman beta against 31.5% for a 36-month rolling beta, Kalman beat rolling on
the Diebold-Mariano test for 0 of 27 names, and the best pairs portfolio had an
out-of-sample t of 1.74. With 74 holdout months and about 2.6 trades per pair that test had
little power. Daily data gives it more.

## Hypotheses

- **H1.** On the daily holdout, Kalman hedge effectiveness exceeds that of the 252-day
  rolling beta. Expected: no.
- **H2.** Daily Kalman pairs earn a net out-of-sample t above 2 at 30 bp one-way per leg.
  Expected: no.

## Rules

- Holdout: 2019-12-01 onward. It is touched once, for the final run.
- Every test is counted and listed in `test_count.txt`.
- Significance uses a Bonferroni correction across all daily tests.
