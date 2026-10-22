# Exclusions

What was cut from the final body of work, and why. Ledger IDs refer to VERIFICATION_LEDGER.md. Three cut classes: CONTAMINATED (traces to fabricated data), UNSUPPORTED (prose with no executed evidence in the folders), SUPERSEDED (executed, but a later corrected run replaces it). Contaminated-lineage results are excluded outright, not caveated.

## 1. Contaminated (fabricated-data lineage)

| Item | Lineage | Ledger |
|---|---|---|
| Every number descending from project-blob `panel_stock.csv`, `panel_with_factors.csv`, `ic_results.csv`, `backtest_results.csv`, `backtest_oos.csv` (composite IC 0.010 t 0.84; long-only 17.56%/yr Sharpe 1.43; "benchmark" Sharpe 3.14 at 5% vol; OOS Sharpe 1.364/1.432) | build_synthetic_panel (np.random.seed(42), 28 hardcoded tickers) and fill_missing_stock_columns (zlib.adler32 ticker-hash constants) in the original pipeline.ipynb; generator reproduced exactly (5/5 tickers) by the detector runs | M2 |
| All columns of `panel_stock_generated.csv` except PX_LAST and TOT_RETURN, and any result touching them; TOT_RETURN in that file is itself a price rescale for 23/30 tickers (zero dividend content) so it is unusable for total-return claims | fill_missing_stock_columns fallback | A9, M2 |
| Earlier report draft (.docx) §VII.C walk-forward OOS Sharpe 1.364 / full-sample 1.432 | irreconcilable with the fixed pipeline (Sharpe ~0.52); synthetic-era remnant left in a real-data paper | M3 |
| The first 71-name survivorship run's B/M factor (survivor PX_TO_BOOK backfilled from a resident panel_stock.csv that is demonstrably fabricated in the project blobs) and therefore the run's headline pair Sharpe 0.975→0.607, L/S 0.635→0.249 | backtest_survivorship.ipynb CELL 6; superseded by the BVPS + quarterly-PIT canonical run | O1 |

Note: the fabricated CSVs were never committed to this repository. The clean pipelines write files with the same names, so any copy found elsewhere should be checked by content, not by filename.

## 2. Unsupported (prose only, no executed evidence in the folders)

| Item | Where it appears | Why cut | Ledger |
|---|---|---|---|
| Blue-chip survivorship alpha pair: naive +0.71%/mo t=4.60 → corrected +0.25%/mo t=1.19; post-crisis +0.55%/mo t=2.60; benchmark inflation 9.8 vs 5.5%/yr | SGX2_Paper Table 3/abstract, REPORT.md §4 | The canonical notebook has no regression cell; no monthly series for the final spec survives. Replaced by the verified Sharpe/return/DD pair (1.002→0.447 etc.) | B10 |
| Survivorship bias bounds [−1.12, −0.07] pp/yr over "97 unresolved exits" | REPORT.md §4 | Not produced anywhere; unresolved worksheets cover 79 gvkeys, not 97 | B6 |
| Sensitivity "−0.89 → −0.60 pp/yr forcing −100% on 37 wipeouts" | SOURCE_GUIDE.md | Stated, never executed at the time. Later re-run on the Compustat panel; see section 7 | B7 |
| Binding-name capacity "SGD 4,000/month, 100% of months < SGD 1m" | DEFINITIVE waterfall memo, REPORT.md §6 | No artifact, no code. The verified capacity statements are: STI-core ~S$50M feasibility-bound (D12), and degenerate binding-name capacity on the liquid100 L/S book (D13) | D3 |
| "22.6% of short-leg names zero lendable inventory; short-leg mean fee 0.024%/yr; availability screen eliminates 57% via 0.636→0.299 (53% of alpha lost)" | SGX_Remaining_Items markdown recollection, REPORT.md §6 | The referenced run exists nowhere. Replaced by executed borrow numbers: 60.7% active-available / 37.9% GC / median fee 0.048%/yr; 1.661→0.712 (57%) borrow-feasible waterfall; Markit fee-vs-availability scenarios | D10 |
| "liquid100 validated at 0.974 cap-weighted correlation against the WRDS SGP country index" | REPORT.md §2 | The executed 0.974 is a TSMOM Sharpe, not a correlation. Replaced by executed validations: 0.967 Bloomberg-vs-Compustat top-30, 0.947 EW-panel-vs-STI, per-name median r 0.9998 (238 matches) | A2 |
| Cross-vendor "r = 0.979 across 8,035 name-months" | Risk_Module_Memo, PROVENANCE memo, REPORT.md §2 lineage argument | Input panels not in the archive; not reproducible | A6, E19 |
| Compustat independent reproduction variant "+0.42%/mo t=2.68" | Risk_Module_Memo (one of two conflicting quarterly entries) | Contradicted by the staged artifact: compustat_backtest_quarterly.csv recomputes to +0.360 t=2.26. The +0.42 run was overwritten and survives nowhere | E3 |
| "Merton and Markov-switching forecast skew worse than the naive sample moment" | REPORT.md §9.4 | No code or output anywhere; the jump/regime appendix is self-declared prose-only and concerns variance/ES, not skew forecasting | K5 |
| STI-core capacity "~S$100M at 20% participation" | Risk_Module_Memo | Memo-only; only the 10%-participation S$50M line has an artifact | D12 |
| CAPM decomposition style loading "MOM +0.43 (t 7.3)"; GARCH persistence 0.98; benchmark entrant decomposition +25.11% vs +0.72% | Risk_Module_Memo | Memo-only; the surrounding results (CAPM alpha, GJR selection, +0.395 measured benchmark gap) are executed and kept | E15, L2, E4 |
| Broad-track finish.py results: sector-neutral kill (+0.526→+0.169), Brinson-Fachler (+1.28 selection), 12% vol-target (+0.663 t 3.08), cost break-even 86bp | FINAL_STATUS_pending_closed.md | Code present, stdout never captured at the time. Later re-run on sg_broad_quarterly.csv; see section 7. Note the memo's Brinson refutes the older "+8.4%/yr selection" on that track; the verified Brinson (with interaction) on the STI track is kept (E12) | C7 |
| Broad-panel IC alignment diagnostics (contemporaneous ~0, U-shaped deciles, tercile t 2.94/8.74/5.90) | ic_alignment_diagnostic.md | Run on the unfiltered panel with the constituents file lost; author-flagged "re-run on PIT before use". The PIT-based alignment results are kept instead (F3, F8, I6) | C8 |
| IBES layer lift on the broad composite (1.321→1.523, t 4.73) | layer2_layer4_results.md | Unexecuted, blend not pre-specified, and contradicted by the executed pre-registered IBES orthogonality null which is kept (E10) | C9 |
| REALIS property-beta layer on the broad universe (IC −2.36, composite survives neutralisation) | layer2_layer4_results.md | Unexecuted; author holds "loosely"; sector sanity check fails. The executed REALIS results kept are the aggregate lead-lag null and the suggestive volume differential (t=−2.61, fails Bonferroni, so reported as suggestive only) | C10 |
| WRDS-track (S&P BMI) result family: SF ICs (EY t=10.98), survivorship gap +1.56pp t=0.74, walk-forward Sharpe 0.23, EW→VW 0.39→0.15, JKP spanning 13.8%/yr t=2.56, optimizer table, 16-factor HLZ survivors (B/M, Amihud) | The nine result .txt files and Strategy/Survivorship papers | Executed in an external WRDS session; no notebook, panel or output CSV in the folders. Internally consistent and directionally aligned with kept results, but fails the evidence bar. Re-enters only if that session's artifacts are recovered | B15 |
| Cross-track reconciliation imports (SGX2 t=4.60→1.19, composite IC 0.054 t=7.6, +9.5 pp/yr membership bias hardcoded into fig surv3) | Cross_Track_Reconciliation.docx, decomposition figure | Imports of numbers whose executed backing is absent (or, for +9.5, approximated by the verified 9.46pp Sharpe-level gap B9) | B10, B15 |
| Legacy Table II module numbers (Barra bias-stat 0.29, GBM OOS Sharpe 0.24, MVO 0.75, HMM 0.36 vs 0.70) | papers, Specification_Tracker | From uninspectable early sessions; PROVENANCE memo itself marks them unverified. The "eight overlays, eight fails" conclusion stands on the five executed overlay tests | E20, E21 |
| Jump-momentum K-sensitivity values at K=30/120 | SGX_Remaining_Items fallback print | Printed from a FileNotFound fallback; jumps_K.py absent. The conservative downgrade (do not claim the signal) is kept | I7 |
| Corwin-Schultz Bloomberg comparator (44/14/81/267) and the "143,978 name-months, median 23.5bp" cs_spreads figures | Eff_Spreads hard-coded dict; DEFINITIVE memo | Comparator typed in, not loaded. The 143,978 / 23.5bp figures were later verified; see section 7 | D14 |
| "51 additions and 51 deletions across 75 quarterly reviews" | two markdown cells | Executed count is 30/30 | A8 |
| Specification_Tracker's lagged Paper-A restatement "+0.40%/mo NW-t 2.82 under the lag: survives comfortably" and its module table "3 value factors survive Bonferroni" | Specification_Tracker.md | Hotter parallel rebuild superseded by the canonical conservative pipeline (t 2.26) and by the corrected Table I (0 survive Bonferroni) | E1, E2 |
| SGX2 quarterly membership "92 snapshots" verification | SGX2_Paper §3.1 | VBA builder present, MembershipQ sheet not in archive; the yearly 23-snapshot file is verified. Kept as described tooling, not as a verified count | S14 (branch audit) |

## 3. Superseded (executed, replaced by corrected or more authoritative runs)

| Item | Superseded by | Ledger |
|---|---|---|
| 30-name survivor diagnostics as headline results: composite IC 0.0752 t=5.05; long-only 18.84%/yr Sharpe 1.007; Bloomberg-track paper families (IC 0.068/0.058) | 71-name PIT IC table (0.0697 t=5.90); PIT/broad-universe results; the corrected price-only diagnostic (M1). The 30-name numbers remain in the ledger as diagnostics; the Bloomberg-track scripts additionally embed full-sample IC weights and ex-dividend returns (M3), so their families are also methodologically compromised | C12, M3 |
| First and second 71-name survivorship runs (PTB-backfill; yearly-PIT BVPS) | backtest_survivorship_final.ipynb (quarterly PIT + BVPS): survivor 17.37/1.002/−44.2 → PIT-quarterly 7.91/0.447/−62.7; L/S 10.35/0.586 → 5.03/0.313 | B9, O1 |
| Stale size-tier Sharpes (0.15/0.54/0.78) and the risk_and_overlays memo line splicing them with canonical t-stats | canonical_table3.csv (−0.01/0.32/0.68; alpha t 0.81/2.99/4.13) | C3 |
| Flat-cost waterfall (endpoint t=1.57) | Definitive CS + identifier-Markit waterfall (endpoint 0.282%/mo t=0.85), itself superseded by the corrected waterfall (0.366%/mo t=1.08) | D1, D1c, D2 |
| TSMOM 30-name Bloomberg Sharpe 0.876 as the module headline | liquid100 k=3 Sharpe 0.974 t=4.65 (survivorship-clean) and PIT top-30 0.565; plus the lag disclosure (0.727→0.510 wide-universe) | H1, H2, H5 |
| TSMOM NB1 "second-half Sharpe 0.50 t=1.47" prose | NB2 executed 0.53 / t=1.84 | H2 |
| Mechanism framings for the 52WH conditioning: breadth, then liquidity | Share turnover (third, final framing); ADV was a correlated proxy | I2 |
| Mid-cap 52WH subsumption claim | Withdrawn net of spreads (t=1.85) by the branch itself | I5 |
| Momentum-vol-management notebook's "selective dominates universal" interpretation | Its own executed output (cond 0.0522 < always 0.0560, p=0.47) and the later ex-ante gate null | K4 |
| In-notebook PIT weighting grid (absolute cap, never binds; score-cap t 1.88) | R_H_grid_fixed.csv from the fixed engine (cap=max_wt/n; score-cap t 2.12) | F6 |
| Bench-A (t+1 membership) benchmark and every Paper B breadth-null number resting on it | Bench-B investable-cohort benchmark; broad null reverses at top-150/200 (t 3.30/3.61) | E4 |
| Paper variants not matching the corrections: Paper_A_STI_Core_final (t=2.82 ×5, "three value factors", "top-decile"), SGX_MultiFactor_Paper (stale Table I), Paper_B_Expansion_v1–v3 (Bench-A numbers; v3 also t=2.82 twice), IEEE variants' "long-short spread t=+0.04 (flat)" and Brinson-without-interaction | The corrected memos, rederived tables, corrected deciles (+0.995 t 2.74), Markit L/S (+0.764 t 2.23), Brinson with interaction. REPORT_FINAL is the corrected version | SGX3 audit §C |
| "Nothing on SGX cleared the seasonality multiple-testing bar" | Executed: August clears Bonferroni (t=−3.80); correct claim is "no tradable seasonality" | J1 |
| REPORT.md §11 external-track numbers (0.98→0.61, 0.64→0.25, IC 0.075 t=5.05) | Traced to the superseded/suspect first survivorship run and the survivor-30 IC re-run; replaced by B9 and C11. These also appeared on the project site | O1, O2 |

## 4. Figures

No figure in REPORT_FINAL derives from fabricated data. Figures whose only source would be fabricated data (the original synthetic-era pipeline plots) are listed as missing and not substituted. Two figures are excluded on evidence grounds even though their PNGs exist: the survivorship decomposition bar chart surv3 (hardcodes the +9.5pp import) and any figure of the WRDS S&P-BMI track (no notebooks or outputs archived). fig1_synthetic_data_audit.png (the detector) is kept in the corrections section.

## 5. Still open (would re-enter the verified set if recovered)

1. The external WRDS S&P-BMI session artifacts (B15 family).
2. The SGX2_v4.xlsm workbook or the final-spec monthly series (B10 alpha regressions).
3. The mc_*.npy bootstrap inputs (E18a).

## 6. Added in the final check

| Item | Why cut | Ledger |
|---|---|---|
| STI-core-labelled book-size sweep (t 1.06 at 3 names to 4.80 at 25) and weighting row (cap-weight +0.068 t=0.22 vs equal +0.468) | Memo prose only, no artifact; and the memo's own baseline shows it is the top-100 10-name book, not the STI core. Breadth is carried by the executed Bench-B table (E4), weighting by C4/F6 | E22 |
| Bootstrap alpha 95% CI [+0.05, +0.73] and the 0.3% data-snooping probability | Figure-legend evidence only; the mc_*.npy inputs are absent from the archive. P(alpha>0)=98.7% and the drawdown-typicality result are stream-verified and kept | E18a |
| SPH in the padding-truncation recovery list | Markdown-only; the executed table lists CMA, KPLD, NOL, MRT, GLP, NOBL, CCT, JS. CCT substituted | B14 |

## 7. Re-run later (no longer excluded)

| Item | Now | Ledger |
|---|---|---|
| Sensitivity −0.89 → −0.60 pp/yr (37 forced wipeouts) | Re-executed on the real Compustat panel; baseline replicated exactly first | B7r |
| Bias magnitude bracket | Replaced the unverifiable [−1.12, −0.07]/97 with an executed bracket: −0.89 to −0.40 pp/yr (harshest −100% assumptions), sign robust | B6a |
| finish.py family (sector-neutral kill, Brinson-Fachler, 12% vol target, 86bp break-even) | Re-executed on sg_broad_quarterly.csv; memo reproduced exactly | C7r |
| cs_spreads "143,978 name-months, median 23.5bp" | Verified by direct recomputation from the staged file | D14r |
