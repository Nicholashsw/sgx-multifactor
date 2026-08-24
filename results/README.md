# Results

## results/verified/ (current)

Aggregated result files backing VERIFICATION_LEDGER.md, all from executed runs on real vendor data. Highlights: `canonical_table1/2/3.csv` (broad-universe ICs, survivorship reversal, size tiers), `waterfall_definitive.csv` (gross 1.661 t=5.13 to 0.282 t=0.85), `survivorship_summary_final.csv` (the canonical quarterly-PIT blue-chip run: Sharpe 1.002 naive to 0.447 corrected), `ic_results_71_final.csv` (71-name PIT ICs, composite 0.0697 t=5.90), `spec_results_N65.csv` (the 65-test grid; zero survive BHY), `deciles_corrected.csv` (monotone payoff after the forward-return bug fix), `compustat_backtest_quarterly.csv` (independent reproduction +0.36 t=2.26), Markit borrow scenarios, jump/GARCH/Markov overlay tests, and the re-executed sensitivity outputs (`rescue_*`).

`verified/attribution/` holds the STI-core attribution and leakage tables behind REPORT_FINAL §7/§10 and ledger rows E4/E8/E9/E11, with its own README. Note that `verified/attribution_loo.csv` (broad Compustat, N=366, full composite +0.526 t=1.93) and `verified/attribution/attrib_factor_loo.csv` (top-100 10-name book, full composite +0.468 t=1.67) are **different runs on different universes** and are not expected to agree.

No raw vendor panels ship; these are strategy-level series and test statistics.

## Top-level CSVs (superseded diagnostics, kept for the record)

`ic_results.csv`, `ic_results_real.csv`, `backtest_results.csv`, `backtest_real.csv` are the 30-name survivor-universe diagnostic re-runs on the real Bloomberg workbook: real data, executed, but a survivorship-biased universe that carries no inferential weight (ledger C12). `survivorship_summary.csv` and `survivorship_comparison.csv` are the FIRST 71-name survivorship pass (Sharpe 0.975 to 0.607), superseded by `verified/survivorship_summary_final.csv` (1.002 to 0.447) because its book-to-market factor was backfilled from a contaminated file and its membership was yearly rather than quarterly. See EXCLUSIONS.md. Do not quote the superseded pair.
