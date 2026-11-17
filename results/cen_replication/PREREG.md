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

### A1 notes

Written 18 Nov 2026 after the A1 run (`code/cen/replicate.py`, `a1_replication.csv`). The method is unchanged. These notes explain two of the failures.

- Keltner %B (`volatility_kcp`): t = -6.95 (Newey-West -6.46) against his -4.09. The sign matches but the gap is 2.86, so it fails the 1.0 rule. `add_all_ta_features` in ta 0.11.0 builds the Keltner channel with window 10 (middle line the 10-day average of the typical price, bands at plus and minus the 10-day average of high minus low), not 20.
- Stochastic signal (`momentum_stoch_signal`): t = -3.00 (Newey-West -2.92) against his +3.51. The sign is opposite, so it fails. Our definition is ta 0.11.0 `StochasticOscillator(window=14, smooth_window=3)`: `momentum_stoch` is %K = 100 x (close - 14-day low) / (14-day high - 14-day low), and `momentum_stoch_signal` is %D, the 3-day simple average of %K. Neither is inverted, so both rise with the close. His report (section 4.1 and the appendix) says only that the 86 signals come from the ta package with its defaults. It does not define %K or %D, give a window or name a ta version. We use %D (14, 3) as ta computes it and do not change it.
- His appendix does not agree with itself here. In ta, Williams %R is %K minus 100, so `momentum_wr` and `momentum_stoch` have the same daily slopes by construction (both -6.30 in our run). He reports -5.84 for `momentum_wr` but -0.35 for `momentum_stoch`, and +3.51 for `momentum_stoch_signal`, which is a 3-day average of that same %K. One computation on one panel cannot give those three numbers, so his stochastic columns were built or aligned differently from his Williams %R. The report does not say how. Our same-day diagnostic for `momentum_stoch_signal` is +20.34, the same sign as his, but far larger in size.

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
| 18 Nov 2026 | A2 STI universe. The registered "point-in-time STI roster" has no source back to 2003: the only roster is Bloomberg FSSTI year-end snapshots from 2008 (`bloomberg_sgx_index_membership_a_2003_2025.csv`, was membership_pit.csv). Main STI test: top 30 of the broad point-in-time list by lagged market cap at each June rebalance, 2003 to 2019; test counts and bars unchanged (36 primary, 20 mechanism). Robustness only, not counted in any bar: the STI cells rerun on the FSSTI rosters, each year-end snapshot applied to the next calendar year, 2009 to 2019. Mapping (`code/cen/map_fssti.py`): Bloomberg ticker to ISIN via Markit bb_ticker, then the crosswalk (34 tickers), and by Compustat name for Olam (OLAM, OLAMR) and Hutchison Port (HPHT). All names were checked by eye; 270 of 331 ticker-years mapped. Unmapped (not in the Compustat SGP extract): DFI, GGR, HKL, IHH, JM, JS, NOBL, THBEV, YZJSGD. The yearly overlap of the two lists is reported. | STI roster |
| 18 Nov 2026 | A2 tradability. `code/waterfall.py` cannot run unchanged: it is monthly only, tied to the main panel's composite scores, and reads deleted file names. Its long-short engine is ported line for line to `code/cen/costs.py`, with the fee divided by periods a year (12 or 52). Check before A2 (`code/cen/check_waterfall.py`): on the main panel's Composite, monthly, with traded-days spreads, the port reproduces `results/verified/waterfall_schemes_traded_days.csv` exactly (Ann%, alpha, t, N, turnover; gap 0 for all four stages). Test: decile long-short on the broad universe, after traded-days spreads, the Markit availability screen and the fee. Spread, lendable value and fee are from the month before the formation month, at both horizons. The statistic is the NW t of the mean net return (4 lags weekly, 6 monthly), since there is no weekly vendor benchmark for waterfall's alpha. Pass at t >= 2.99 in the registered direction: oscillators and ATR short the top decile, trend and reversal long; MFI, registered as two-sided, takes the sign of its primary broad slope at that horizon. The traded-days spread file is copied from the iCloud backup to `derived_sgx_cs_spreads_traded_m_1993_2026.csv`. | Waterfall port |
| 18 Nov 2026 | A2 construction (`code/cen/extend.py`). Compustat daily, primary SGX issue, split-adjusted high, low and close with cshtrd, loaded from 2001-06 for warm-up and never after 2019-12-31. Each signal is blank until its window has filled. Broad universe: in the latest June WRDS index list. Formation is each stock's last trading day in the week or month. The return is the next period's compounded daily total return (`derived_sgx_daily_rets_d_2000_2026.parquet`), blank if the stock misses a period. Fama-MacBeth needs at least 10 names on a date. Weekly reversal is minus the past 5 trading days' return; monthly is minus the formation month's return. H4's size test: gross weekly decile long-short within thirds of lagged market cap in the broad universe, descriptive, not counted. Benjamini-Yekutieli p uses the normal two-sided p of each t. | Construction |
| 18 Nov 2026 | A2 run record. The first run (code at f94e567) stopped inside ta before producing any statistic: ATR fails for a stock with fewer than 14 trading days. Fix: stocks with fewer than 20 days in the load window get no indicator values (the warm-up rule already blanks most such rows). Development results: `a2_dev.csv` (74 tests with Benjamini-Yekutieli q), plus outside the bars `a2_dev_fssti.csv` (FSSTI roster), `a2_sti_overlap.csv` (22 to 25 of the 23 to 25 mapped FSSTI names are in the top-30 list each year) and `a2_size_terciles.csv` (H4). | Run record |
| 18 Nov 2026 | A2 cross-check against an independent build of the broad cells (`~/scratch/a2_independent/a2_dev_broad.csv`, kept outside the repo). Settings actually used, already logged above: broad universe is the latest June WRDS index list; Fama-MacBeth needs at least 10 names a date; stocks with fewer than 20 days get no indicator values. The independent build used at least 5 names and a 30-day minimum history. Both were rerun on this code and give the same broad weekly t to two decimals, so they are not adopted. 13 of 28 broad cells differ by more than 0.3 in abs(t). (1) Ten weekly cells: primary wr, rsi, bbp, kcp, stoch_signal and reversal, and mechanism wr, bbp, kcp and stoch_signal. This code forms each stock on its own last trading day of the week, so a name that did not trade on the week's last market day enters with a stale signal and price. Forming only on names that traded that day brings nine of the ten within 0.3 of the independent values: wr -12.81 vs -12.67, bbp -10.02 vs -9.72, kcp -9.62 vs -9.56, mechanism kcp -2.64 vs -2.78. Primary rsi narrows to 0.47 (-6.98 vs -6.51). Primary reversal stays 1.2 apart (11.12 vs 9.90), cause not found; defining reversal as minus the week's own return widens it (11.98). (2) Three monthly cells: reversal, mechanism wr and mechanism stoch_signal, all with abs(t) at most 2.35. The independent build has 202 months for these against 203 here: its reversal lacks January 2003, so it was likely built without pre-2003 history. The stale-formation rule does not reconcile them (it moves monthly reversal to -1.85). Verdicts: only mechanism kcp weekly would change, from pass (-3.93) to fail (-2.64), under the stricter formation rule. The recorded results keep the formation rule as run. | Independent cross-check |
