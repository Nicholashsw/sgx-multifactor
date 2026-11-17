# Announcement tone and post-announcement drift: development results

Development window: day 0 from 2003-01 to 2019-12, as registered in `PREREG.md`. Written 17 Nov 2026, before the 2020+ hold-out is run. Code: `code/news/drift_test.py`, `code/news/tradability.py`. Tables: `drift_dev.csv`, `drift_placebo.csv`, `tradability_dev.csv`.

## Summary

- **Main test (H5): not supported.** Neither tone score predicts the return over days +2 to +6, +2 to +21 or +2 to +61 once the IBES surprise and the other controls are in. The largest t is 1.77 (FinBERT, +2 to +21), below the Bonferroni bar of 2.64.
- **Exploratory test:** FinBERT over days +2 to +6 clears its own bar (t = 2.96). Nothing else does, and LM tone is never positive. The test is exploratory, so this does not support H5.
- **Placebo:** clean. With tone moved to random non-announcement days, all six |t| are below 1.4.
- **Tradability:** before costs, the FinBERT long-short earns +0.49% per 20-day trade (t = 2.28) and LM +0.21% (t = 1.07). Spreads turn both negative: -0.79% and -1.02%.

## Sample

11,041 index earnings firm-days have both tone scores. 846 have an IBES surprise, and 2,545 have a net-income change parsed from the text.

Regressions use complete cases. The main test loses most of its rows to book-to-market: the main-study panel has no book equity (`ceqq`) for 339 of the 846 SUE firm-days. The join is not the cause. Every one of these firm-days has a panel row for the month, but `ceqq` is empty. The gap is almost all financials and real estate:

- 93% of GICS 40 firm-days and 92% of GICS 60 firm-days are missing.
- Across the whole panel in 2004 to 2019, `ceqq` coverage is 18% in financials and 21% in real estate, against 90% or more in every other sector.

The main test therefore covers mostly non-financial firms. N is 501 (500 for +2 to +61).

## Main test: IBES surprise control (registered, H5)

Window return on tone (z-scored within year), SUE, car_0p1, log size, book-to-market and 12-month momentum. Standard errors are clustered by day 0. H5 passes at t >= 2.64.

| Score | Window | Coef | t | N | Result |
|---|---|---|---|---|---|
| LM | +2 to +6 | 0.00021 | 0.10 | 501 | fail |
| LM | +2 to +21 | -0.00016 | -0.04 | 501 | fail |
| LM | +2 to +61 | 0.00154 | 0.23 | 500 | fail |
| FinBERT | +2 to +6 | 0.00268 | 1.17 | 501 | fail |
| FinBERT | +2 to +21 | 0.00658 | 1.77 | 501 | fail |
| FinBERT | +2 to +61 | 0.01054 | 1.57 | 500 | fail |

## Exploratory test: parsed earnings change in place of SUE

Same regressions on firm-days with a parsed net-income change. Missing values are not filled. Parse coverage is about 20% of firm-days before 2019. The bar is again 2.64.

| Score | Window | Coef | t | N | Result |
|---|---|---|---|---|---|
| LM | +2 to +6 | -0.00085 | -0.79 | 1,660 | fail |
| LM | +2 to +21 | -0.00020 | -0.09 | 1,659 | fail |
| LM | +2 to +61 | -0.00223 | -0.63 | 1,646 | fail |
| FinBERT | +2 to +6 | 0.00302 | 2.96 | 1,660 | pass |
| FinBERT | +2 to +21 | 0.00451 | 2.16 | 1,659 | fail |
| FinBERT | +2 to +61 | 0.00579 | 1.59 | 1,646 | fail |

## Placebo

Each main-test firm-day's tone and SUE are moved to a random trading day of the same firm in the same year, at least 5 trading days from any earnings day 0 (seed 20261117). Windows and controls are rebuilt at that day. The placebo passes at |t| < 2.64.

| Score | Window | Coef | t | N | Result |
|---|---|---|---|---|---|
| LM | +2 to +6 | -0.00045 | -0.26 | 512 | pass |
| LM | +2 to +21 | 0.00505 | 1.34 | 512 | pass |
| LM | +2 to +61 | -0.00071 | -0.11 | 507 | pass |
| FinBERT | +2 to +6 | -0.00016 | -0.08 | 512 | pass |
| FinBERT | +2 to +21 | 0.00404 | 0.97 | 512 | pass |
| FinBERT | +2 to +61 | 0.00726 | 1.08 | 507 | pass |

## Tradability

Each trade enters at the close of day +1 and is held 20 trading days. It is long when tone is in the top third and short when in the bottom third, using the previous year's breakpoints, so 2003 is not traded. Returns are in excess of the equal-weight universe.

The net figures charge the Corwin-Schultz half-spread on entry and exit, following the waterfall's convention. The median round trip is 47 bp. Borrow is not charged, though PREREG mentions it. The t compares the long leg with the short leg (Welch). The legs are uneven because tone drifts down over time against the previous year's breakpoints.

| Score | Basis | Long | Short | Long-short | t | Trades long | Trades short |
|---|---|---|---|---|---|---|---|
| LM | gross | -0.06% | +0.27% | +0.21% | 1.07 | 3,048 | 3,789 |
| LM | net of spreads | -0.61% | -0.41% | -1.02% | -5.15 | 3,048 | 3,789 |
| FinBERT | gross | +0.12% | +0.37% | +0.49% | 2.28 | 3,179 | 4,088 |
| FinBERT | net of spreads | -0.48% | -0.31% | -0.79% | -3.58 | 3,179 | 4,088 |

## Caveats

- The main test rests on 501 firm-days of mostly non-financial firms, because of the book-to-market gap.
- The two tone scores barely agree from 2011 to 2019 (see `tone_validity.csv`), so a null on one says little about the other.
- Return windows of late-2019 events run into early 2020. The rows are development events, but those returns fall in the hold-out calendar period.
