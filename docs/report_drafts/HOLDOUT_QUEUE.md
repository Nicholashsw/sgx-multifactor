# Hold-out queue

Written 19 Nov 2026 overnight. Nothing listed here was run, and no 2020+ data was read tonight.

## Ready to run

**None.** Every registered hold-out has been run once. A3 was withdrawn before any run, so it has none.

## Status of each registered hold-out

| Study | Hold-out | Status | Command | Commit |
|---|---|---|---|---|
| News layer (`results/news_text/PREREG.md`) | 2020-01 to 2026-06 | Done once, 17 Nov 2026. Do not rerun. | `python code/news/drift_test.py --sample holdout` | ran on f58a98c; results in c556ee8 |
| Cen A1 (`results/cen_replication/PREREG.md`) | none: a fixed replication of Cen's 2012 to 2022 window | Not applicable | `python code/cen/replicate.py` | b3c1123 |
| Cen A2 | 2020-01 to 2026-06 | Done once, 18 Nov 2026. Do not rerun. | `python code/cen/extend.py --sample holdout` and `python code/cen/robust_costs.py --sample holdout` | ran on 30cfe3c (code at 364b857); results in 49b6542 |
| Cen A3 | none | **Withdrawn** before any run (`PREREG.md`, row "A3 withdrawn"). No code exists. | none | none |
| Kalman (`results/kalman/PREREG.md`) | 2019-12-01 onward | Done once (logged 19 Oct 2026 in `STRATEGY_FREEZE.md`: H1 and H2 not supported). Do not rerun. | see `results/kalman/PREREG.md` | earlier history |

## A3

A3 was withdrawn before any run on 19 Nov 2026 (`results/cen_replication/PREREG.md`, row "A3 withdrawn"). Its rules were never specified beyond "the work plan", no daily STI series is available, and defining the rules after the A2 results would be post hoc. It has no hold-out.
