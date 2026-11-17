# Morning note, 19 Nov 2026

The overnight queue ran unattended. Nothing read or ran on 2020+ data, and no hold-out was run. Every step was committed and pushed to `main` as Nicholashsw, with no trailer.

## Finished

| Step | What | Commit |
|---|---|---|
| 3a | `docs/report_drafts/news_layer_null_result.md`: news-layer null result, development and hold-out, every table cited to its CSV and commit | 8c40f87 |
| 3b | `docs/report_drafts/cen_replication_and_extension.md`: A1, A2 (development and hold-out), and a note that A3 was not run | 9d9f5bc |
| 4 | `docs/report_drafts/HOLDOUT_QUEUE.md`: no hold-out is ready to run; the status of each, and what A3 needs | b40239e |
| 5 | this note | see `git log` |

`REPORT_FINAL.md` and `paper/` were not touched.

## Skipped, and why

Both skips are logged in `results/cen_replication/PREREG.md`, commit 58eedb4.

- **Step 1, A3 timing rules: skipped.**
  - PREREG names the four rules but defines them only "in the work plan", which is not in the repo, `~/Documents`, `~/Downloads` or the iCloud backups.
  - Their thresholds, entry trigger and which markout horizon (1, 5 or 20 days) is each rule's single test are unregistered.
  - No daily STI series exists in `~/datasets` for the STI 200-day filter. The Bloomberg SGX workbook is month-end only.
  - Writing the definitions tonight, after seeing A2, would have been an unattended post-hoc design choice.
- **Step 2, "Part B of results/cen_replication/PREREG.md": skipped.** That file has no Part B; it registers A1 to A3 only. The Part B registered in this project is the announcement-text study in `results/news_text/PREREG.md`, which is already complete with its hold-out.

## Needs your decision

1. **A3 definitions.** Supply the work-plan rules, or write them as an amendment: for each rule the entry trigger, thresholds and its test horizon, or a new test count and bar. Then either pull a daily FSSTI series from Bloomberg or drop the STI 200-day rule by amendment. Until then A3 cannot run as registered.
2. **Queue step 2.** If you meant something other than the news study, say which part. Nothing called Part B exists for the Cen study.
3. **Commit attribution.** The "A1 notes" section of `results/cen_replication/PREREG.md` was written by another session. It went into my commit f94e567 on 18 Nov because I staged the whole file. The text is unchanged, but the commit history credits it to that A2 commit. No action is needed unless you want it recorded separately.
4. **Drafts to review.** Both drafts use plain wording and cite every table. Check the framing in particular:
   - The news-layer limitations paragraph, including the C07 map error.
   - The A2 "Findings" paragraph, which uses your 18 Nov ruling on development net t.

## Still running

- `caffeinate -dims` is in the background from last night. Stop it with `pkill caffeinate`, or it ends with this session.
