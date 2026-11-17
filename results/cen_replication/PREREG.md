# Pre-registration: replication and extension of Cen (2023), timing layer

Written 13 Nov 2026 and committed 16 Nov 2026. The commit that adds this file is its timestamp.

This is an extension after the 17 Oct 2026 strategy freeze and does not change the frozen strategy. Every test below is reported whatever the result. Any change after this commit goes in the amendment log at the bottom, with its date and reason.

Development window: 2003-01 to 2019-12. Hold-out: 2020-01 to 2026-06, run once, after the development results are written up.

## Part A. Replication and extension of Cen (2023)

### A1. Replicate his setup

- Universe: his 25 names, A17U, BN4, BS6, C07, C09, C38U, C6L, D01, D05, F34, G13, H78, J36, M44U, ME8U, N2IU, O39, S58, S63, S68, U11, U14, U96, V03, Z74.
- Period: 2012-01-03 to 2022-12-30, the window his t-tests cover.
- Data: Compustat Security Daily OHLCV. D01, H78 and J36 are not in the SGP extract, so they come from Bloomberg daily OHLCV. If that pull is not possible, the run uses 22 names and says so.
- Signals: all 86 from `ta` (`add_all_ta_features`, default windows), with the package version pinned.
- Method: each day, regress the next day's return on one signal across the names, average the daily slopes, and compute t = mean / (sd / sqrt(T)) as he did. The Newey-West t (5 lags) is reported next to it.
- Same-day returns are run as a diagnostic only. His report does not say which he used; if same-day matches his t-statistics better, his results contained look-ahead.
- Pass: his five Bonferroni survivors (momentum_wr, momentum_rsi, volatility_bbp, volatility_kcp, momentum_stoch_signal) keep their sign and land within 1.0 of his appendix t. Anything else is reported as a failure to replicate, with the likely cause (price source, dividend adjustment, return timing).
- This is its own family of 86 tests. Bonferroni bar: 3.44.

### A2. Extend to the project's data

Signals (9):

- His five survivors, same windows: Williams %R (14), RSI (14), Bollinger %B (20, 2), Keltner %B (20), stochastic signal (14, 3).
- One for each family he did not keep: trend, close / 200-day average minus 1; volatility, ATR(14) / close; volume, MFI(14).
- Control: plain reversal, minus the past 5-day return (weekly) or the past 1-month return (monthly).

Raw price and volume levels (SMA, EMA, OBV, ADI and similar) are left out because they cannot be compared across stocks.

Universes (2): the broad point-in-time Compustat universe including delisted firms, as in the main strategy, and the point-in-time STI roster.

Horizons (2): weekly (signal at Friday close, held the next week) and monthly (signal at month-end, held the next month).

Each signal uses data up to the formation close only, is trimmed at the 1st and 99th percentiles, and is z-scored across stocks on each date.

Tests:

| Family | Count | What | Bonferroni bar |
|---|---|---|---|
| Primary | 36 (9 x 2 x 2) | Fama-MacBeth slope, Newey-West t (4 lags weekly, 6 monthly) | 3.20 |
| Mechanism | 20 (5 x 2 x 2) | Oscillator slope with the reversal control added | 3.02 |
| Tradability | 18 (9 x 2, broad universe) | Equal-weight decile long-short after traded-days Corwin-Schultz spreads, Markit availability and fees, using `code/waterfall.py` unchanged | 2.99 |

Benjamini-Yekutieli is also reported across all 74.

Expected signs, stated now:

- H1: all five oscillators have negative slopes (overbought names do worse next period).
- H2: adding the reversal control cuts each oscillator's |t| by at least half, meaning they are mostly reversal.
- H3: trend positive, volatility negative, volume two-sided.
- H4: nothing survives net of costs at the weekly horizon, and the gross effect is strongest in the smallest, least liquid third.

A signal counts as a finding only if it clears its Bonferroni bar in development, keeps its sign in the hold-out, and has a net long-short t above 1.96.

### A3. Entry and exit rules on the frozen book

The four timing rules in the work plan (3-month trend filter, price above its 10-month average, nearness to the 52-week high, STI 200-day filter) are applied to the frozen top-decile book. Each is judged by markouts: the average return 1, 5 and 20 trading days after entry, after spreads, against entering on a random day in the same month. 4 tests, Bonferroni bar 2.50.

## Outputs

- `results/cen_replication/`: A1 table against his appendix, A2 test table, A3 markouts, test count.

## Amendment log

| Date | Change | Reason |
|---|---|---|
| 17 Nov 2026 | A1 universe: 21 names, not 22. D01, H78 and J36 are not in the Compustat SGP extract (Bermuda-incorporated Jardine group). Yangzijiang Shipbuilding (BS6) is not in it either; the only Yangzijiang gvkeys are the 2022 and 2025 spin-offs, and the Capital IQ map had matched BS6 to one of them (status weak). C07 is Jardine Cycle & Carriage, gvkey 100296, checked by name; the map had rejected it and matched it to another firm. The other 20 come from the map at status dividends and were checked by name. No Bloomberg pull was made. | Universe |
| 17 Nov 2026 | A1 data: Compustat Security Daily, primary SGX issue, 2012-01-03 to 2022-12-30 only (indicators warm up inside the window). High, low and close are divided by ajexdi, and volume is cshtrd. Compustat has no open, so the open is the previous day's adjusted close. In ta 0.11.0 none of the 86 add_all_ta_features outputs reads the open (checked by scaling it), so the proxy changes nothing. Return: total return from prccd / ajexdi x trfd. Daily slopes need at least 5 names on the day. | Data and open proxy |
