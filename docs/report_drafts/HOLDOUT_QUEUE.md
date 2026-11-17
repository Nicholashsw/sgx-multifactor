# Hold-out queue

Written 19 Nov 2026 overnight. Nothing listed here was run, and no 2020+ data was read tonight.

## Ready to run

**None.** Every registered hold-out that can be run has been run once. The only remaining one, A3, is not ready.

## Status of each registered hold-out

| Study | Hold-out | Status | Command | Commit |
|---|---|---|---|---|
| News layer (`results/news_text/PREREG.md`) | 2020-01 to 2026-06 | Done once, 17 Nov 2026. Do not rerun. | `python code/news/drift_test.py --sample holdout` | ran on f58a98c; results in c556ee8 |
| Cen A1 (`results/cen_replication/PREREG.md`) | none: a fixed replication of Cen's 2012 to 2022 window | Not applicable | `python code/cen/replicate.py` | b3c1123 |
| Cen A2 | 2020-01 to 2026-06 | Done once, 18 Nov 2026. Do not rerun. | `python code/cen/extend.py --sample holdout` and `python code/cen/robust_costs.py --sample holdout` | ran on 30cfe3c (code at 364b857); results in 49b6542 |
| Cen A3 | 2020-01 onward | **Not ready.** The development run was skipped: the rule definitions are missing from the registration and there is no daily STI series (`PREREG.md`, row "A3 skipped"). No code exists. | none | none |
| Kalman (`results/kalman/PREREG.md`) | 2019-12-01 onward | Done once (logged 19 Oct 2026 in `STRATEGY_FREEZE.md`: H1 and H2 not supported). Do not rerun. | see `results/kalman/PREREG.md` | earlier history |

## What would make A3 ready

1. **Rule definitions:** the four timing rules defined in an amendment row before any run. For each: entry trigger, thresholds, and which markout horizon (1, 5 or 20 days) is its single test, or a revised test count and bar.
2. **Daily STI:** a daily STI level, for example a Bloomberg FSSTI Index PX_LAST pull, saved to `~/datasets/bloomberg/index/` and logged in `data.lock`. Alternatively, drop the STI 200-day rule by amendment.
3. **Order of work:** a development run and write-up. Only after that would an A3 hold-out command go in this table.
