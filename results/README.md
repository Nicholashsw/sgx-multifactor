# Results

## results/verified/

Aggregated result files backing VERIFICATION_LEDGER.md, all from executed runs on real vendor data. Highlights: `canonical_table1/2/3.csv` (broad-universe ICs, survivorship reversal, size tiers), `waterfall_schemes_traded_days.csv` (corrected waterfall, gross 1.661 t=5.13 to 0.366 t=1.08, plus every weighting and the long-only book), `waterfall_definitive.csv` (the published 0.282 t=0.85 version), `survivorship_summary_final.csv` (the canonical quarterly-PIT blue-chip run: Sharpe 1.002 naive to 0.447 corrected), `ic_results_71_final.csv` (71-name PIT ICs, composite 0.0697 t=5.90), `spec_results_N65.csv` (the 65-test grid; zero survive BHY), `sgx3_deciles_corrected.csv` (monotone payoff after the forward-return bug fix), `compustat_backtest_quarterly.csv` (independent reproduction +0.36 t=2.26), Markit borrow scenarios, jump/GARCH/Markov overlay tests, and the re-executed sensitivity outputs (`survivorship_sensitivity_output.txt`, `finish_output.txt`, `cs_spreads_check.txt`).

`verified/code10/` holds the aggregate outcome of the code-10 exit adjudication (category counts, category by triage prior, and the terminal-return sensitivity before and after), from `code/code10_adjudication.py`; the firm-level worksheet carries SDC and Compustat fields and stays local.

`verified/overlay_ivol/` holds the inverse-realised-vol benchmark for the sizing overlays (ledger L6), from `code/inverse_vol_benchmark.py`. Sharpe is the test statistic and reproduces the published overlay table exactly; MaxDD there is on compounded w x net returns and differs slightly from the published leveraged rows, so it is indicative only.

`verified/attribution/` holds the STI-core attribution and leakage tables behind REPORT_FINAL §7/§10 and ledger rows E4/E8/E9/E11, with its own README. Note that `verified/attribution_loo.csv` (broad Compustat, N=366, full composite +0.526 t=1.93) and `verified/attribution/attrib_factor_loo.csv` (top-100 10-name book, full composite +0.468 t=1.67) are **different runs on different universes** and are not expected to agree.

No raw vendor panels ship; these are strategy-level series and test statistics.
