# Hold-out queue

Written 19 Nov 2026; updated the same day for A3-cost. Nothing listed here was run, and no 2020+ data was read for it.

## Ready to run

**One: A3-cost** (see below). Every other registered hold-out has been run once, and the original A3 was withdrawn before any run.

## Status of each registered hold-out

| Study | Hold-out | Status | Command | Commit |
|---|---|---|---|---|
| News layer (`results/news_text/PREREG.md`) | 2020-01 to 2026-06 | Done once, 17 Nov 2026. Do not rerun. | `python code/news/drift_test.py --sample holdout` | ran on f58a98c; results in c556ee8 |
| Cen A1 (`results/cen_replication/PREREG.md`) | none: a fixed replication of Cen's 2012 to 2022 window | Not applicable | `python code/cen/replicate.py` | b3c1123 |
| Cen A2 | 2020-01 to 2026-06 | Done once, 18 Nov 2026. Do not rerun. | `python code/cen/extend.py --sample holdout` and `python code/cen/robust_costs.py --sample holdout` | ran on 30cfe3c (code at 364b857); results in 49b6542 |
| Cen A3 | none | **Withdrawn** before any run (`PREREG.md`, row "A3 withdrawn"). No code exists. | none | none |
| Cen A3-cost | 2020-01 to 2026-06 | **Ready, not run.** Development written up in `A3_RESULTS.md`. Not a clean test: 2020+ was already seen for these signals in A2. | `python code/cen/timing.py --sample holdout` | code at ada4023 (`timing.py`, with `extend.py` and `costs.py` unchanged since 364b857) |
| Kalman (`results/kalman/PREREG.md`) | 2019-12-01 onward | Done once (logged 19 Oct 2026 in `STRATEGY_FREEZE.md`: H1 and H2 not supported). Do not rerun. | see `results/kalman/PREREG.md` | earlier history |

## A3

A3 was withdrawn before any run on 19 Nov 2026 (`results/cen_replication/PREREG.md`, row "A3 withdrawn"). Its rules were never specified beyond "the work plan", no daily STI series is available, and defining the rules after the A2 results would be post hoc. It has no hold-out.

## A3-cost

Registered 19 Nov 2026, after the A2 results were seen (`PREREG.md`, row "A3-cost registered").

- **Command:** run once from the repo root: `python code/cen/timing.py --sample holdout`. It writes `results/cen_replication/a3_holdout.csv` and reads no data after 2026-06-30. Prices from 2018-06 are loaded only to warm up the signals and the 200-day regime average.
- **Directions:** taken from `a2_dev.csv`.
- **Caveat:** the 2020 to 2026 returns of the A2 weekly Williams %R, Keltner %B and reversal books were already seen in the A2 hold-out (`a2_holdout.csv`, commit 49b6542). That includes their net t of 2.71 and 2.37 for Williams %R and Keltner %B. An A3-cost hold-out on the same period re-uses data that informed the registration, so its result is descriptive, not out-of-sample evidence.
