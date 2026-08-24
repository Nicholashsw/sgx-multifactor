# Module 1. Survivorship methodology study

Finding: delisting survivorship bias on SGX runs backwards. Dropping dead names LOWERS measured universe returns by 0.89 pp/yr (8.85% point-in-time vs 7.96% survivors-only), because 59% of the 338 exits are acquisitions that pay a premium. The pre-registered alternative (index membership flips the sign) was tested and rejected: within point-in-time index members the bias is -1.01 pp/yr, same sign.

Magnitude is an upper bound: Compustat freezes suspension prints. An executed terminal-return sensitivity brackets it at -0.89 to -0.40 pp/yr under progressively harsher -100% assumptions (37 triaged wipeouts: -0.60; plus 25 ambiguous: -0.40; all 53 no-deal code-10 exits: -0.44). Sign robust throughout.

Strategy level: the naive blue-chip survivor backtest (Sharpe 1.002) corrects to 0.447 under quarterly point-in-time membership with real book values; the broad-universe long-short REVERSES (survivor t=1.01 vs point-in-time t=3.82); on the 54-name PIT roster the correction is near-symmetric across legs (long -5.43, short +5.26 pp/yr), so long-only investors are hurt and long-short investors roughly insulated.

Evidence: REPORT_FINAL.md section 4; ledger rows B1-B14, B6a, B7r. Figures: surv_exit_mix, surv_bias_both_universes, surv_leg_symmetry_pit, surv_total_return_correction. Results: results/verified/survivorship_summary_final.csv, canonical_table2.csv, spec grid files, rescue_survivorship_output.txt.
