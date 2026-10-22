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

## Amendment, 19 October 2026 (before any daily run)

- **Universe: 25 names.** DFI, HKL, JM, THBEV and YZJSGD are excluded. The Compustat Global
  Security Daily extract covers Singapore-incorporated issuers only (every row has
  fic = SGP), and these five are incorporated elsewhere. The other 25 match Bloomberg's
  month-end total returns with r > 0.99. THBEV and YZJSGD were two of the three
  drifting-beta names in the monthly study, so the daily universe has fewer of the names
  where a dynamic beta should help most.
- **Pairs: 10, not 12.** Losing HKL drops CIT/HKL and HKL/UOL.
- **Market series: a 25-name cap-weighted leave-one-out proxy, not the STI.** Weights are
  prccd x cshoc lagged one day. When hedging name i, i is left out of the proxy; the
  equal-weight book is hedged against the full proxy.
- **Stale prints.** The TR level is set to missing on days with zero volume, or an
  unchanged price on zero volume, so neither that day nor the next earns a return.
- **Runs.** monthly_30_sti (the original reference), monthly_25_sti, monthly_25_proxy,
  daily_25_proxy (daily rebalancing) and daily_25_proxy_weekly (beta hedge only,
  rebalanced every 5 days). The two middle monthly runs separate the universe and proxy
  effects from the frequency effect.
- **Test count.** Every hedge Diebold-Mariano test and every pair x method x entry
  out-of-sample test in the two daily runs is counted; the Bonferroni threshold is
  0.05 divided by that count.
