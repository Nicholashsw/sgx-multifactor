# Module 4. Jump-diffusion and regime risk measurement

A null for alpha, real for risk. Merton fits the STI-core daily series decisively (57.9% of variance is jump risk; Gaussian understates 99% ES by 1.60pp, a 34% relative error), licensing sizing and risk-limit claims only. As a conditional forecaster Merton is superseded by GJR-GARCH skew-t (713 BIC; the only model passing conditional VaR backtests at both levels). Eight overlays tested, eight failed to add risk-adjusted return; mean-variance optimisation alone halves drawdown at equal Sharpe. Two traps caught and quantified: a GARCH same-month look-ahead (Sharpe 0.73 to a fake 1.05) and the Markov smoothed-probability illusion (+0.525 Sharpe vs filtered). Open benchmark: naive inverse-realised-vol scaling.

Evidence: REPORT_FINAL.md section 9.5; ledger rows L1-L6, E21. Figures: risk_*. Results: results/verified/jumpmodel_test_*.json, garch_*.csv, ms_sizing_results.csv, jump_sizing_results.csv.
