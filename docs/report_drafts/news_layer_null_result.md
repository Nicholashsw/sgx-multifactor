# Draft: Does announcement tone predict returns? (news layer)

*Draft section for the FYP report, 19 Nov 2026. It does not replace anything in `REPORT_FINAL.md`. Every number comes from a file in `results/news_text/`; the file and the commit that last wrote it are given under each table.*

## What we tested

We asked whether the tone of a Singapore company's own results announcement predicts its share price drift after the announcement, once the earnings surprise is known. The test was pre-registered before any return was looked at (`results/news_text/PREREG.md`, committed in c6464f0). The data were checked and every change was logged in that file's amendment log before the results were produced.

The announcement texts are Capital IQ Key Developments for the stocks in the point-in-time WRDS Singapore index list. We scored each firm-day's text two ways:

- **Loughran-McDonald word counts:** positive minus negative words over all words, using the pysentiment2 0.1.1 word lists.
- **FinBERT:** the average of P(positive) minus P(negative) across sentences (ProsusAI/finbert, revision 0bc2ac10).

Neither score was fitted to returns.

The return windows start on day +2 after the announcement, so the announcement-day jump is not counted. The windows are +2 to +6, +2 to +21 and +2 to +61 trading days, in excess of the equal-weight index universe. Each window return was regressed on tone, controlling for:

- the IBES earnings surprise (actual minus median forecast, scaled by price);
- the day 0 to +1 return;
- size, book-to-market and 12-month momentum.

Standard errors are clustered by announcement date. With 2 scores and 3 windows there are 6 tests, so the Bonferroni bar is |t| = 2.64.

## The two scores barely agree

Before any return test, we checked each score against the change in net income that could be parsed from the same text. The correlation between the two scores over all 14,481 firm-days is only 0.002. By year it is about +0.30 to +0.55 in 2002 to 2010 and about -0.26 to +0.07 in 2011 to 2019.

Against the parsed earnings change, the LM score tracks the change better than FinBERT. The Spearman correlation with the size of the change is 0.395 for LM and 0.177 for FinBERT.

*Source: `results/news_text/tone_validity.csv` (commit 0faf3ec).*

## Main result: no tone effect (development window, 2003 to 2019)

| Score | Window | Coefficient | t | N | Passes 2.64? |
|---|---|---|---|---|---|
| LM | +2 to +6 | 0.00021 | 0.10 | 501 | no |
| LM | +2 to +21 | -0.00016 | -0.04 | 501 | no |
| LM | +2 to +61 | 0.00154 | 0.23 | 500 | no |
| FinBERT | +2 to +6 | 0.00268 | 1.17 | 501 | no |
| FinBERT | +2 to +21 | 0.00658 | 1.77 | 501 | no |
| FinBERT | +2 to +61 | 0.01054 | 1.57 | 500 | no |

*Source: `results/news_text/drift_dev.csv`, rows `test = main` (commit 17c5e99).*

None of the six tests passes, so the hypothesis that tone predicts drift after controlling for the surprise (H5) is not supported. The sample is small: 501 firm-days have both an IBES surprise and every control. Most of the loss comes from book-to-market, which is missing for 339 of the 846 firm-days with a surprise. The main-study panel has almost no book equity for banks and real-estate firms: coverage is 18% and 21% in those sectors over 2004 to 2019 (`PREREG.md`, row "Tradability and hold-out setup").

## Exploratory test with the parsed earnings change

The same regressions were run with the earnings change parsed from the text in place of the IBES surprise. This was labelled exploratory before it was run.

| Score | Window | Coefficient | t | N |
|---|---|---|---|---|
| LM | +2 to +6 | -0.00085 | -0.79 | 1,660 |
| LM | +2 to +21 | -0.00020 | -0.09 | 1,659 |
| LM | +2 to +61 | -0.00223 | -0.63 | 1,646 |
| FinBERT | +2 to +6 | 0.00302 | 2.96 | 1,660 |
| FinBERT | +2 to +21 | 0.00451 | 2.16 | 1,659 |
| FinBERT | +2 to +61 | 0.00579 | 1.59 | 1,646 |

*Source: `results/news_text/drift_dev.csv`, rows `test = second` (commit 17c5e99).*

Only FinBERT over days +2 to +6 is above 2.64. The parsed change covers only about 20% of firm-days before 2019, and this test is exploratory, so it is not counted as support for H5.

## Placebo

Each firm-day's tone was moved to a random non-announcement trading day of the same firm in the same year, and the main regressions were rerun. Nothing should show up, and nothing did: every |t| is below 1.4.

| Score | Window | t | N |
|---|---|---|---|
| LM | +2 to +6 | -0.26 | 512 |
| LM | +2 to +21 | 1.34 | 512 |
| LM | +2 to +61 | -0.11 | 507 |
| FinBERT | +2 to +6 | -0.08 | 512 |
| FinBERT | +2 to +21 | 0.97 | 512 |
| FinBERT | +2 to +61 | 1.08 | 507 |

*Source: `results/news_text/drift_placebo.csv` (commit 17c5e99).*

## Can it be traded?

Each trade is held 20 trading days. It is long the top third and short the bottom third of tone, with breakpoints from the previous year.

| Score | Basis | Long minus short per trade | t |
|---|---|---|---|
| LM | gross | +0.21% | 1.07 |
| LM | after spreads | -1.02% | -5.15 |
| FinBERT | gross | +0.49% | 2.28 |
| FinBERT | after spreads | -0.79% | -3.58 |

*Source: `results/news_text/tradability_dev.csv` (commit d2bba35).*

After Corwin-Schultz spreads (median round trip 47 bp), both books lose money. Borrow costs were not charged, so the true net figures would be lower still.

## Hold-out, 2020 to 2026 (run once)

The hold-out was run once, on the committed code (commit f58a98c), after the development write-up.

| Test | Score | Window | t | N |
|---|---|---|---|---|
| main | LM | +2 to +6 | -1.59 | 209 |
| main | LM | +2 to +21 | -1.21 | 209 |
| main | LM | +2 to +61 | -0.98 | 206 |
| main | FinBERT | +2 to +6 | -1.25 | 209 |
| main | FinBERT | +2 to +21 | -0.02 | 209 |
| main | FinBERT | +2 to +61 | 0.05 | 206 |
| exploratory | LM | +2 to +6 | 1.49 | 2,260 |
| exploratory | LM | +2 to +21 | 0.93 | 2,258 |
| exploratory | LM | +2 to +61 | -1.76 | 2,204 |
| exploratory | FinBERT | +2 to +6 | -1.47 | 2,260 |
| exploratory | FinBERT | +2 to +21 | -1.05 | 2,258 |
| exploratory | FinBERT | +2 to +61 | 1.10 | 2,204 |

*Source: `results/news_text/drift_holdout.csv` (commit c556ee8).*

Nothing passes. The one exploratory pass in development, FinBERT +2 to +6, changes sign in the hold-out (t = -1.47). The hold-out placebo is also clean, with t between 0.31 and 1.49 (`results/news_text/drift_holdout_placebo.csv`, commit c556ee8).

## Limitations

- **Small main sample, mostly non-financial firms.** This follows from the book-to-market gap above.
- **The IBES surprise covers only full-year results.** About half of the IBES announcements match a Capital IQ earnings record: 1,416 of 3,004, or 47.1% (`PREREG.md`, row "SUE scaling").
- **One firm mapping error was found after the hold-out.** Jardine Cycle & Carriage (C07) was left out by mistake. It was not corrected in the recorded results, because the hold-out had already run on the old mapping; correcting only the development sample would put the two samples on different maps. The effect is bounded: at most 6 extra firm-days in the main test, where no t is above 1.77 (`PREREG.md`, row "Firm map error", commit 9870688).
- **The two scores measure different things.** Their near-zero correlation means a null result for one says little about the other.

## Conclusion

In Singapore, the tone of a company's results announcement does not predict its returns after day +1 once the earnings surprise is controlled for. This holds in the 2003 to 2019 development window and in the 2020 to 2026 hold-out. The only result that cleared a bar in development was exploratory, and it reversed in the hold-out.
