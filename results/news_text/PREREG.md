# Pre-registration: announcement text, news layer

Written 13 Nov 2026 and committed 16 Nov 2026. The commit that adds this file is its timestamp.

This is an extension after the 17 Oct 2026 strategy freeze and does not change the frozen strategy. Every test below is reported whatever the result. Any change after this commit goes in the amendment log at the bottom, with its date and reason.

Development window: 2003-01 to 2019-12. Hold-out: 2020-01 to 2026-06, run once, after the development results are written up.

## Part B. Announcement text (news layer)

Question: does the tone of a company's own announcement predict its return afterwards, beyond the earnings surprise?

Data:

- Text and dates: Capital IQ Key Developments on WRDS (headline, situation text, announced date, event type) for Singapore companies. First check the day pass covers it; Factiva is the fallback.
- Earnings surprise: IBES actual against the median consensus, scaled by price.
- Prices: Compustat Security Daily.

Events: results announcements are the main test. Placements and rights issues, buybacks, substantial shareholder changes and profit warnings are exploratory and labelled as such.

Text scores (2):

- Loughran-McDonald net tone, (positive minus negative words) / total words, with the dictionary version pinned.
- FinBERT (ProsusAI/finbert, model commit pinned): average positive minus negative probability across sentences.

No large language model is used in the main test. They are trained on text written after many of these events and can already know how a company turned out. A large-model score may be added later only for events after its training cutoff, as a labelled side check.

Timing: the time of day is often missing, so the first trade is at the close of the next trading day after the announced date, and returns are measured from the day after that. The announcement-day move is not used.

Tests (6 = 2 scores x 3 windows): return minus the equal-weight point-in-time universe over days +2 to +6, +2 to +21 and +2 to +61, regressed on tone with controls for earnings surprise, announcement-window return, size, book-to-market and 12-month momentum. Standard errors clustered by announcement date. Bonferroni bar 2.64.

- H5: the tone coefficient is positive after controlling for the earnings surprise.

Tradability: long the top third and short the bottom third by tone, held 20 days, after spreads and borrow, using the same waterfall code.

Leakage checks: (1) a placebo with each firm's tone moved to a random non-announcement date, which should show nothing; (2) an assertion that every score uses only text dated before the formation date.

## Outputs

- `results/news_text/`: event file counts, B test table, placebo, test count.

## Amendment log

| Date | Change | Reason |
|---|---|---|
| 15 Nov 2026 | Capital IQ Key Developments confirmed and already pulled: 254,214 events, 1,171 SGX firms, 1990 to 2026 (thin before 2005), 584 matched to Compustat gvkeys, 34,784 earnings announcements. | Data check |
| 15 Nov 2026 | Disclosure: on 14 and 15 Nov, before this plan was committed, a TF-IDF baseline (train to 2016, validate 2017 to 2019, test 2020 on) and Qwen scores on 2020+ earnings events were run against the day 0 to +1 reaction. As far as the saved scripts show, the Part B target (drift from day +2) has not been looked at. | Honest record of what was seen |
| 15 Nov 2026 | Qwen scores are excluded from the main test: the model's training data covers the 2020 to 2024 test years. | Look-ahead in the model |
| 16 Nov 2026 | The extract carries SGX tickers but no Capital IQ company id, so the WRDS gvkey link cannot be joined directly. Name matches are checked against dividends instead (`code/news/match_firms.py`): a match is kept if at least 60% of the firm's Capital IQ ex-dividend dates inside the Compustat window fall within 3 days of a Compustat ex-dividend day (at least 5 dates), or if the cleaned names are identical and the dividends do not clearly disagree (under 30% hit). 609 Capital IQ firms kept, 93 rejected (for example CapitaLand India Trust had been matched to CapitaLand China Trust). | Cleaner identifiers |
| 16 Nov 2026 | Main test sample: earnings announcements of firms in the point-in-time index list on day 0, one observation per firm and day 0 (several Capital IQ records can share a day; their text is joined). 14,469 firm-days, 553 firms: 11,019 in 2004 to 2019, 3,426 from 2020. Returns are winsorised at the 1st and 99th percentiles. Decided after seeing only the unconditional return spread (names outside the list average +15% over days +2 to +61, driven by outliers), before any tone score exists. | Data quality |
| 17 Nov 2026 | Tone scored for 14,481 index firm-days with Loughran-McDonald (pysentiment2 0.1.1 word lists) and FinBERT (ProsusAI/finbert, revision 0bc2ac10), all chunks on CPU with torch 2.14.1 (chunks 1 to 6 in a Linux sandbox, the rest on this Mac). A batched re-score of chunk 1 matched the original to within 0.000001. The scorer reads no returns. | Scoring record |
| 17 Nov 2026 | Count note: 14,481 index earnings firm-days were scored; 14,469 have a complete day +2 to +21 window. Of the 12 without, 2 are June 2026 announcements cut off by the last price date (10 Jul 2026) and 9 are firms whose prices end within 21 trading days of day 0; the remaining 1 is likely a gap in that firm's returns. | Count reconciliation |
| 17 Nov 2026 | Diagnostic, run before any return test (`code/news/check_tone.py`, `results/news_text/tone_validity.csv`): each tone score is compared with the earnings change parsed from the same text. corr(lm_tone, finbert_tone) is 0.002 overall, +0.30 to +0.55 by year in 2002 to 2010 and -0.26 to +0.07 in 2011 to 2019. | Measurement check |
| 17 Nov 2026 | Earnings surprise source: IBES Summary Statistics, international file, EPS consensus for fiscal year 1, quarter 1 and half-year 1, 2002-01 to 2026-08 (WRDS query 11922228, saved as wrds_ibes_sg_statsum_m_2002_2026.zip). 469 firms. Consensus exists almost only for full years (39 half-year rows), giving 3,676 full-year announcements with both consensus and actual. The registered test therefore runs on full-year results of IBES-covered index firms (main test). A second test, labelled as such, runs the same six regressions on all index firm-days with the earnings change parsed from the text (code/news/check_tone.py) in place of the IBES surprise, against its own Bonferroni bar of 2.64. IBES announcement times are US Eastern and are converted to Singapore time before matching to day 0. Checked before use: DBS actual EPS for FY2022 to 2025 matches its reported EPS after the April 2024 bonus issue, and its February 2026 IBES timestamp equals the Capital IQ timestamp. Decided before any return test. | Surprise data |
| 17 Nov 2026 | SUE scaling (`code/news/build_surprise.py`): price is the Compustat close on the last trading day before the Singapore announcement date divided by ajexdi, the current share basis IBES EPS uses (see the DBS check above). Raw prccd put 548 of 1,412 matched rows on a different basis and gave SUE as low as -256. SUE is winsorised at the 1st and 99th percentiles of each regression sample, like the returns. 395 of 3,399 IBES announcements dropped because estimate, actual or price is not in SGD. 1,416 of 3,004 SGD announcements (47.1%) match a Capital IQ earnings firm-day within 5 days; most of the rest have no Capital IQ earnings record within 30 days. Decided before any event return was read. | SUE scaling |
| 17 Nov 2026 | Second test scope: exploratory. H5 rests on the IBES main test only. It runs only on firm-days with a parsed earnings change (about 20% of firm-days before 2019, nearly all from 2020); missing values are not filled. | Second test scope |
| 17 Nov 2026 | Controls and placebo, fixed before any event return was read (`code/news/drift_test.py`). Book-to-market is BM_Ratio from the main-study panel at the last month-end before day 0 (the panel carries the 4-month lag). Momentum is the compounded return over trading days -252 to -21. Size is log mcap_lag. Placebo: each firm-day's tone and SUE go to a random trading day of the same firm in the same calendar year that is not within 5 trading days of any of its Capital IQ earnings day 0s (seed 20261117). The windows, car_0p1, size, book-to-market and momentum are rebuilt at that day from daily returns. Window returns and tone are winsorised and z-scored within each sample as in the main test. | Design detail |
| 17 Nov 2026 | Development results written (`results/news_text/drift_dev.csv`, `drift_placebo.csv`), window 2003-01 to 2019-12 as registered; the hold-out is not run. Routine choices made in the code: SUE, the parsed earnings change, car_0p1, book-to-market and momentum are winsorised at 1/99 within each regression sample like the window returns (tone is z-scored within year, not winsorised). Regressions are complete-case; book-to-market is missing in the main-study panel for 339 of 846 firm-days with SUE, mostly firms with no book equity there. A year with a single firm-day in a sample cannot be z-scored and is dropped (one 2003 firm-day in the main test); this was fixed after the first run stopped on it, before any estimate was produced. Rebuilt windows are checked equal to the labelled ones. OLS from statsmodels 0.15.0. | Run record |
| 17 Nov 2026 | Tradability (`code/news/tradability.py`): each development firm-day is entered at the close of day +1 and held 20 trading days (the +2 to +21 window). It is long the top third and short the bottom third of tone, with breakpoints from the previous calendar year so none uses later text. Costs follow the waterfall convention: the Corwin-Schultz half-spread at the last month-end before day 0, charged on entry and exit. Borrow is not charged. The book-to-market gap was diagnosed before the hold-out: not a join error; book equity is empty in the main-study panel for financials and real estate (18% and 21% coverage, 2004 to 2019). Left as is. `drift_test.py` gained `--sample holdout` (day 0 from 2020-01-01 to 2026-06-30); the development outputs were re-run and are byte-identical. Development results written in `DEV_RESULTS.md` before the hold-out. | Tradability and hold-out setup |
| 17 Nov 2026 | Aborted hold-out attempt. The first `--sample holdout` run (code at d2bba35) stopped on the assertion that every placebo day lies inside the sample window: the same-year placebo pool for 2026 firm-days included 1 to 10 July 2026, after the 30 June 2026 end. The main and second hold-out regressions had been computed in memory, but no estimate was printed or saved and no hold-out file was written. Fix: the placebo pool is limited to trading days inside the sample window. The development window ends at a year-end, so the development outputs are unchanged; `drift_dev.csv` and `drift_placebo.csv` were re-run and are byte-identical. The hold-out is then run once on that commit. | Hold-out attempt and fix |
| 17 Nov 2026 | Hold-out run once on f58a98c (`drift_test.py --sample holdout`, day 0 from 2020-01 to 2026-06): `drift_holdout.csv`, `drift_holdout_placebo.csv`. No test clears 2.64 in either direction, main or second; the placebo is clean. N: 209 main (206 for +2 to +61), about 2,200 to 2,260 second, 211 to 222 placebo. | Hold-out record |
