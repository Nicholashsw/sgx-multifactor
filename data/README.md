# Data. Licensed, not shipped

The factor panels are built from licensed vendor data (Bloomberg, Compustat/WRDS, IBES, Markit, SDC, CapIQ, CEIC, JKP) and are not committed. See DATA.md at the repo root for the full source list, fields, windows and reproduction routes.

To run without entitlements: `python code/make_synthetic.py` writes labelled synthetic replicas (`data/synthetic/synthetic_panel_stock.csv`, `synthetic_macro_monthly.csv`; tickers SYN01 to SYN30, seeded generator). No number computed from them is a research result. Note: `src/simulate.py` is a GBM teaching simulation, not the synthetic-panel generator.
