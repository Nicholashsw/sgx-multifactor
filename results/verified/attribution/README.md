# Attribution artefacts (SGX3 / STI-core track)

The aggregated result files behind the attribution and leakage claims in
[`REPORT_FINAL.md`](../../../REPORT_FINAL.md) §7 and §10, and behind ledger rows **E4, E8, E9, E11**
in [`VERIFICATION_LEDGER.md`](../../../VERIFICATION_LEDGER.md). Produced by the
`SGX_Alpha_Attribution_Leakage` and `SGX_Attribution_Holdings_Brinson` notebooks.

## Two different leave-one-out tables — do not confuse them

| File | Universe / book | Full-composite alpha |
|---|---|---|
| [`../attribution_loo.csv`](../attribution_loo.csv) | **Broad Compustat**, N = 366 months | +0.526%/mo, t = 1.93 |
| [`attrib_factor_loo.csv`](attrib_factor_loo.csv) | **Top-100 universe, 10-name book**, Bench B | +0.468%/mo, t = 1.67 |

They are different runs on different universes and they do not agree, which is expected. The
−50.2 bp quality drag and the ROE-drop result quoted in REPORT_FINAL §7 are the **top-100** figures
in `attrib_factor_loo.csv`, not the broad-universe file one directory up. The broad-universe LOO's
largest single contributor is 12-month momentum (ΔAlpha −0.369), not quality.

## Contents

| File | Backs | Key numbers |
|---|---|---|
| `attrib_factor_loo.csv` | E8 | Leave-one-group-out on the top-100 book. QUALITY marginal −50.19 bp (alpha without ROE +0.970, t = 4.710); MOMENTUM +12.35 bp, the only positive group |
| `attrib_holdings.csv` | E11 | Holdings-based attribution: MOMENTUM +0.427 (t = 2.61), VALUE +0.257 (t = 3.86), QUALITY +0.023 (t = 0.26) on 0.985 z exposure, RESIDUAL −0.150 |
| `attrib_sector.csv` | E8 | Active bp/mo and NW-t by sector bucket |
| `attrib_size_t.csv` | E8 | Small +31.3 bp (t = 2.15), Mid +12.7, Large +4.5 — monotone down-cap |
| `attrib_liq_t.csv` | E8 | Illiquid +24.3 bp, Medium +15.5, Liquid +8.4 |
| `repeatability.csv` | E8, E9 | Full sample +0.492 (t = 1.75); leave-out-top-5 +0.210 (t = 0.94); leave out Fin_RE +0.689 (t = 2.99) |
| `concentration.csv` | E8 | Share of cumulative active return: top-1 27.9%, top-5 69.9%, top-10 96.7% |
| `subperiods.csv` | E9 | 2008–13 t = 0.13; 2014–19 t = 0.43; 2020–26 t = 3.52 |
| `regime_attribution.csv` | E9 | Calm +1.205 (t = 3.91) vs turbulent −0.123 (t = −0.34) |
| `benchmark_sensitivity.csv` | E4 | Bench A vs Bench B by book breadth: top-150 t = 3.30, top-200 t = 3.61 under the investable-cohort benchmark |
| `leakage_funnel.csv` | §10 | Contaminated benchmark 0.097 (t = 0.31) → corrected 0.492 → costs/screens → 0.186 (t = 1.12) |

## What is deliberately not published

Per the data policy in [`DATA.md`](../../../DATA.md), only strategy-level series and test statistics
ship; no vendor rows and no name-level holdings. The following inputs to the tables above therefore
stay unpublished:

- `attrib_by_name.csv` — per-ticker active contribution for 129 SGX names. `concentration.csv` is
  the aggregate derived from it.
- `attrib_con.csv` — 2,154 name-month contribution rows carrying per-name Corwin-Schultz spread
  estimates derived from licensed daily high/low data.
- `attrib_holdings_monthly.csv`, `sti_benchmark.csv` — monthly factor-exposure detail and the STI
  index level series.

`concentration.csv` was recomputed from `attrib_by_name.csv` during the 2026-08-24 traceability pass
and reproduces the ledger's 27.9 / 69.9 / 96.7 exactly.
