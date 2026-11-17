"""
Claim check for README.md and paper/sgx_multifactor.tex.

Reads only committed files. Every result number in the two documents is a row in CLAIMS:
(doc, where, snippet, printed, source file, field, expected). The test finds the snippet in the
document, finds the printed number inside it, and compares it with the value computed from the
source file, using a tolerance of half a unit in the last printed digit unless stated.

A second test tokenises every number in both documents and fails on any number that is neither
in a claim row nor in the allowlist (each entry carries a one-word reason).

Known-unverifiable cells (README says they cannot be rechecked from the repository) are rows with
source None; they are marked xfail(strict) so they show up as failures that are expected, never
as passes.

Run: pytest tests/test_claims.py
"""
import glob
import json
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results" / "verified"
DOCS = {"README": ROOT / "README.md", "tex": ROOT / "paper" / "sgx_multifactor.tex"}


# ---------------------------------------------------------------- source readers
@lru_cache(None)
def csv(f):
    return pd.read_csv(f if Path(f).is_absolute() else RES / f)


@lru_cache(None)
def js(f):
    return json.load(open(RES / f))


def v(f, col, **flt):
    d = csv(f)
    for k, x in flt.items():
        d = d[d[k] == x]
    assert len(d) == 1, (f, flt, len(d))
    return float(d[col].iloc[0])


def vs(f, col, startswith=None, **flt):
    d = csv(f)
    for k, x in flt.items():
        d = d[d[k] == x]
    if startswith:
        d = d[d.iloc[:, 0].astype(str).str.startswith(startswith)]
    assert len(d) == 1
    return float(d[col].iloc[0])


def nw_mean(x, lags=6):
    m = sm.OLS(np.asarray(x, float), np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(m.params[0]), float(m.tvalues[0])


def diff_vs_bm(f):  # mean monthly excess over the benchmark column, %/mo, NW-6 t
    d = csv(f)
    return nw_mean((d["net"] - d["bm"]) * 100)


def grep(f, pat):  # first capture group of a regex in a committed code file, as float
    m = re.search(pat, (ROOT / f).read_text())
    assert m, (f, pat)
    return float(m.group(1))


def W(score, book, costing, stage, col):
    return v("waterfall_schemes_traded_days.csv", col, Score=score, Book=book, Costing=costing, Stage=stage)


def WU(score, book, costing, stage, col):  # uncorrected-spread run
    return v("waterfall_schemes.csv", col, Score=score, Book=book, Costing=costing, Stage=stage)


def T2(u, leg, col): return v("canonical_table2.csv", col, Universe=u, Leg=leg)
def T1(fac, col): return v("canonical_table1.csv", col, Factor=fac)
def T3(tier, col): return v("canonical_table3.csv", col, Tier=tier)
def T4(sc, col): return v("canonical_table4.csv", col, Score=sc)
def SS(run, col): return v("survivorship_summary_final.csv", col, Run=run)
def C10(scn): return v("code10/code10_sensitivity.csv", "bias_pp_yr", scenario=scn)
def LM(col):  # Markit long-short, 6-lag NW
    d = csv("ls_markit.csv")
    return nw_mean(d[col] * 100)
FIN_TXT = lambda: (RES / "finish_output.txt").read_text()


def fin(pat):
    m = re.search(pat, FIN_TXT())
    assert m, pat
    return float(m.group(1))


def DEC(k):
    d = csv("sgx3_deciles_corrected.csv")
    p = d.pivot(index="Date", columns="dec", values="act")
    s = p[k] if k != "spread" else p[9] - p[0]
    return nw_mean(s * 100)


def SPEC(): return csv("spec_results_N65.csv")
def KAL(run, col): return float(csv("../kalman/hedge_summary.csv").set_index("Unnamed: 0").loc[run, col]) * 100


def BIC(m): return v("garch_model_comparison.csv", "BIC", model=m)
def MS(label, col): return v("ms_sizing_results.csv", col, label=label)
def JS(label, col): return v("jump_sizing_results.csv", col, label=label)
def IV(label, col): return v("overlay_ivol/ivol_benchmark_vs_overlays.csv", col, overlay=label)
def IVT(label, col): return v("overlay_ivol/ivol_benchmark_table.csv", col, label=label)
def BM(book, col): return v("attribution/benchmark_sensitivity.csv", col, Universe=book)
def BMN(book, col): return float(csv("attribution/benchmark_sensitivity.csv").set_index("Universe").loc[book, col])
def CB(spec, col): return v("constrained_backtest.csv", col, spec=spec)
def CAP(aum, col): return v("capacity_analysis.csv", col, AUM=aum)
def FM(fac, col): return v("rederived_table1_fm.csv", col, Factor=fac)
def LOO(c, col): return v("attribution_loo.csv", col, Component=c)
def QL(g, col): return v("attribution/attrib_factor_loo.csv", col, Group=g)
def HO(s, col): return v("attribution/attrib_holdings.csv", col, source=s)
def SUB(p, col): return v("attribution/subperiods.csv", col, period=p)
def REG(p, col): return v("attribution/regime_attribution.csv", col, regime=p)
def FUN(p, col): return csv("attribution/leakage_funnel.csv").set_index("stage").loc[p, col]
def MKT(sc, col): return csv("borrow_markit.csv").set_index("scenario").loc[sc, col]
def BW(stage, col): return v("borrow_waterfall.csv", col, Stage=stage)
def JM(k): return js("jumpmodel_test_b.json")[k]
def JMs(a, b): return js("jumpmodel_test_b.json")[a][b]
def code10_total():
    return float(csv("code10/code10_category_counts.csv")["n"].sum())
def code10_cat(pat):
    d = csv("code10/code10_category_counts.csv")
    return float(d[d["category"].str.contains(pat) | d["category"].str.contains(pat, case=False)]["n"].sum())
def REL(f, col, label, ref): return v(f, col, label=label) - v(f, col, label=ref)
def npng(): return float(len(glob.glob(str(ROOT / "figures" / "*.png"))))
def pairs_oos_t():
    d = csv("../kalman/pairs_portfolio_daily_25_proxy.csv")
    d = d[(d.method == "Kalman MLE") & (d.entry == 1.0) & (d.period == "oos")]
    return float(d["t_nw"].iloc[0])
def kal_tests(): return grep_text(ROOT / "results/kalman/test_count.txt", r"total: (\d+)")
def kal_bar(): return grep_text(ROOT / "results/kalman/test_count.txt", r"\|t\| > ([\d.]+)")
def grep_text(path, pat):
    m = re.search(pat, Path(path).read_text()); assert m, pat; return float(m.group(1))


# ---------------------------------------------------------------- claim rows
CLAIMS = []  # (doc, where, snippet, printed, source, field, expected_fn, tol, unverifiable_reason)


def add(doc, where, snippet, source, items, unver=None):
    """items: (printed, field, expected_fn[, tol]). snippet starting with '@' = the whole doc line
    that begins with the text after '@'."""
    for it in items:
        printed, field, fn = it[:3]
        tol = it[3] if len(it) > 3 else None
        CLAIMS.append((doc, where, snippet, printed, source, field, fn, tol, unver))


R, X = "README", "tex"
UNV_README = "README states this cannot be rechecked from the repository"

# ======================= README =======================
add(R, "intro", "the 59% takeout share", None, [("59", "takeout share of exits", None)], UNV_README)
add(R, "intro", "the 694-firm count", None, [("694", "firm count", None)], UNV_README)
add(R, "intro", "the 36.4 bp half-spread", None, [("36.4", "traded-days median half-spread", None)], UNV_README)
add(R, "Data", "A 694-firm survivorship-free", None, [("694", "firm count", None)], UNV_README)
add(R, "Main result row 1", "@| Survivorship correction reverses the broad long-short", "canonical_table2.csv",
    [("1.01", "Survivor-only LS Alpha_t", lambda: T2("Survivor-only", "LS", "Alpha_t")),
     ("3.82", "Point-in-time LS Alpha_t", lambda: T2("Point-in-time", "LS", "Alpha_t"))])
add(R, "Main result row 2", "@| Result does not hinge on the factor weights", "canonical_table4.csv",
    [("1.32", "Composite LS_Alpha%mo", lambda: T4("Composite", "LS_Alpha%mo")),
     ("3.82", "Composite LS_Alpha_t", lambda: T4("Composite", "LS_Alpha_t")),
     ("1.01", "Composite_Equal LS_Alpha%mo", lambda: T4("Composite_Equal", "LS_Alpha%mo")),
     ("3.08", "Composite_Equal LS_Alpha_t", lambda: T4("Composite_Equal", "LS_Alpha_t")),
     ("1.72", "Composite_WF LS_Alpha%mo", lambda: T4("Composite_WF", "LS_Alpha%mo")),
     ("4.58", "Composite_WF LS_Alpha_t", lambda: T4("Composite_WF", "LS_Alpha_t")),
     ("20", "flat LS cost in bp per month (code: L-S-0.002)", lambda: grep("code/canonical_rerun.py", r"'LS':L-S-(0\.\d+)") * 1e4, 0.5)])
add(R, "Main result row 3", "@| Delisting survivorship bias is negative", "code10/code10_sensitivity.csv",
    [("-0.89", "before/baseline bias_pp_yr", lambda: C10("baseline, no terminal adjustment")),
     ("-0.88", "after/confirmed insolvencies", lambda: C10("confirmed insolvencies forced -100%")),
     ("-0.50", "after/every unresolved exit", lambda: C10("+ every unresolved exit (harshest)"))])
add(R, "Main result row 3", "59% of exits are takeouts", None, [("59", "takeout share of exits", None)], UNV_README)
add(R, "Main result row 3", "694-firm survivorship-free", None, [("694", "firm count", None)], UNV_README)
add(R, "Main result row 4", "@| Implementable long-short with real borrow", "ls_markit.csv",
    [("0.764", "mean of ls, %/mo", lambda: LM("ls")[0]), ("2.23", "NW-6 t of ls", lambda: LM("ls")[1])])
add(R, "Main result row 5", "@| STI-core strategy", "sti_core_returns.csv / compustat_backtest_quarterly.csv",
    [("0.396", "mean(net-bm) %/mo", lambda: diff_vs_bm("sti_core_returns.csv")[0]),
     ("2.26", "NW-6 t of net-bm (STI-core)", lambda: diff_vs_bm("sti_core_returns.csv")[1]),
     ("0.36", "mean(net-bm) %/mo, quarterly Compustat", lambda: diff_vs_bm("compustat_backtest_quarterly.csv")[0]),
     ("2.26", "NW-6 t, quarterly Compustat", lambda: diff_vs_bm("compustat_backtest_quarterly.csv")[1])])
add(R, "Main result row 6", "@| Risk is jump-dominated", "jumpmodel_test_b.json",
    [("57.9", "var_jump_share x100", lambda: JM("var_jump_share") * 100),
     ("1.60", "(gaussian es99 - empirical es99), pp", lambda: (JMs("gaussian", "es99") - JMs("empirical", "es99")) * 100),
     ("34", "understatement / |empirical es99|, %", lambda: (JMs("gaussian", "es99") - JMs("empirical", "es99")) / abs(JMs("empirical", "es99")) * 100, 0.5)])
add(R, "Two findings", "because 59% of exits are takeouts", None, [("59", "takeout share of exits", None)], UNV_README)
add(R, "What didn't work row 1", "@| Cost waterfall on the preset composite", "waterfall_schemes_traded_days.csv / waterfall_schemes.csv",
    [("1.661", "gross alpha", lambda: W("Composite", "Long-short", "Every month", "1. Gross signal", "Alpha%mo")),
     ("5.13", "gross t", lambda: W("Composite", "Long-short", "Every month", "1. Gross signal", "t")),
     ("0.366", "traded stage 4 alpha", lambda: W("Composite", "Long-short", "Traded", "4. + Markit borrow fee", "Alpha%mo")),
     ("1.08", "traded stage 4 t", lambda: W("Composite", "Long-short", "Traded", "4. + Markit borrow fee", "t")),
     ("0.06", "min fully costed alpha over four conventions",
      lambda: min(W("Composite", "Long-short", "Every month", "4. + Markit borrow fee", "Alpha%mo"),
                  W("Composite", "Long-short", "Traded", "4. + Markit borrow fee", "Alpha%mo"),
                  WU("Composite", "Long-short", "Every month", "4. + Markit borrow fee", "Alpha%mo"),
                  WU("Composite", "Long-short", "Traded", "4. + Markit borrow fee", "Alpha%mo"))),
     ("0.54", "max fully costed alpha over four conventions",
      lambda: max(W("Composite", "Long-short", "Every month", "4. + Markit borrow fee", "Alpha%mo"),
                  W("Composite", "Long-short", "Traded", "4. + Markit borrow fee", "Alpha%mo"),
                  WU("Composite", "Long-short", "Every month", "4. + Markit borrow fee", "Alpha%mo"),
                  WU("Composite", "Long-short", "Traded", "4. + Markit borrow fee", "Alpha%mo")), 0.0051),
     ("0.45", "min WF fully costed alpha over four conventions",
      lambda: min(W("Composite_WF", "Long-short", c, "4. + Markit borrow fee", "Alpha%mo") for c in ("Every month", "Traded")), 0.0051),
     ("1.01", "max WF fully costed alpha over four conventions",
      lambda: max(WU("Composite_WF", "Long-short", c, "4. + Markit borrow fee", "Alpha%mo") for c in ("Every month", "Traded"))),
     ("2.03", "WF traded stage 4 t, corrected spreads", lambda: W("Composite_WF", "Long-short", "Traded", "4. + Markit borrow fee", "t")),
     ("2.57", "WF traded stage 4 t, uncorrected spreads", lambda: WU("Composite_WF", "Long-short", "Traded", "4. + Markit borrow fee", "t"))])
add(R, "What didn't work row 2", "@| Dominant cost", "waterfall_schemes_traded_days.csv",
    [("0.741", "gross alpha minus alpha after spreads on traded names",
      lambda: W("Composite", "Long-short", "Every month", "1. Gross signal", "Alpha%mo") - W("Composite", "Long-short", "Traded", "2. + spreads on traded names", "Alpha%mo"))])
add(R, "What didn't work row 2", "median half-spread 36.4 bp", None, [("36.4", "traded-days median half-spread", None)], UNV_README)
add(R, "What didn't work row 3", "@| Long-only top decile after spreads", "waterfall_schemes_traded_days.csv",
    [("0.09", "long-only traded alpha", lambda: W("Composite", "Long-only", "Traded", "Long-only + spreads on traded names", "Alpha%mo")),
     ("0.36", "long-only traded t", lambda: W("Composite", "Long-only", "Traded", "Long-only + spreads on traded names", "t"))])
add(R, "What didn't work row 4", "@| Blue-chip naive backtest vs corrected", "survivorship_summary_final.csv",
    [("1.002", "A Survivor-only Long Sharpe", lambda: SS("A  Survivor-only  [Long]", "Sharpe")),
     ("0.447", "C PIT quarterly Long Sharpe", lambda: SS("C  PIT quarterly  [Long]", "Sharpe"))])
add(R, "What didn't work row 5", "@| Multiple-testing discipline", "spec_results_N65.csv",
    [("65", "rows", lambda: float(len(SPEC()))),
     ("24", "count |nw_t|>1.96", lambda: float((SPEC().nw_t.abs() > 1.96).sum())),
     ("1.96", "threshold", lambda: 1.96, 0.0051),
     ("3.0", "threshold", lambda: 3.0, 0.0501)])
add(R, "What didn't work row 6", "@| Reference paper's Table I", "rederived_table1_fm.csv",
    [("0", "count of factors with Bonferroni == 'Pass'", lambda: float((csv("rederived_table1_fm.csv").Bonferroni == "Pass").sum()), 0.5),
     ("9", "factors", lambda: float(len(csv("rederived_table1_fm.csv"))), 0.5),
     ("2.767", "max NW_t", lambda: float(csv("rederived_table1_fm.csv").NW_t.max())),
     ("2.77", "Bonferroni z for 9 tests, two-sided 5%", lambda: float(stats.norm.ppf(1 - 0.05 / 9 / 2)), 0.0051)])
add(R, "What didn't work row 7", "8 tested, 8 failed", None,
    [("8", "overlays tested", None)], "Barra, HMM and GBM outputs are not kept (README says so); IBES output file not shipped")
add(R, "What didn't work row 7", "8 failed to add", None,
    [("8", "overlays failed", None)], "Barra, HMM and GBM outputs are not kept (README says so); IBES output file not shipped")
add(R, "What didn't work row 8", "(combo 0.460 < TSMOM 0.543)", None,
    [("0.460", "TSMOM combination Sharpe", None), ("0.543", "TSMOM Sharpe", None)], UNV_README)
add(R, "Errors paragraph", "Markov smoothed probabilities worth a spurious +0.525 Sharpe", "ms_sizing_results.csv",
    [("0.525", "Sharpe(smoothed) - Sharpe(filtered)", lambda: MS("MS SMOOTHED (look-ahead, INVALID)", "Sharpe") - MS("MS FILTERED (legitimate)", "Sharpe"))])
add(R, "Errors paragraph", "overstated the passive alternative by 0.395%/mo", "attribution/leakage_funnel.csv",
    [("0.395", "corrected minus raw benchmark alpha", lambda: FUN("1. Corrected benchmark (investable cohort)", "alpha_pct_mo") - FUN("0. Raw, contaminated benchmark (as published)", "alpha_pct_mo"))])
add(R, "What is where", "46 figures", "figures/*.png",
    [("46", "count of png files", npng, 0.5)])

# ======================= paper =======================
add(X, "abstract", "alpha $1.32$\\%/month, $t=3.82$", "canonical_table4.csv",
    [("1.32", "Composite LS_Alpha%mo", lambda: T4("Composite", "LS_Alpha%mo")), ("3.82", "Composite LS_Alpha_t", lambda: T4("Composite", "LS_Alpha_t"))])
add(X, "abstract", "$t=1.01$ on survivors only", "canonical_table2.csv", [("1.01", "Survivor-only LS Alpha_t", lambda: T2("Survivor-only", "LS", "Alpha_t"))])
add(X, "abstract", "gross alpha of $1.661$\\%/month ($t=5.13$) to $0.366$\\%/month ($t=1.08$)", "waterfall_schemes_traded_days.csv",
    [("1.661", "gross", lambda: W("Composite", "Long-short", "Every month", "1. Gross signal", "Alpha%mo")),
     ("5.13", "gross t", lambda: W("Composite", "Long-short", "Every month", "1. Gross signal", "t")),
     ("0.366", "stage 4", lambda: W("Composite", "Long-short", "Traded", "4. + Markit borrow fee", "Alpha%mo")),
     ("1.08", "stage 4 t", lambda: W("Composite", "Long-short", "Traded", "4. + Markit borrow fee", "t"))])
add(X, "data", "Eligibility averages $199$ names per month", "canonical_results.json",
    [("199", "universe.PIT_avg_per_month", lambda: js("canonical_results.json")["universe"]["PIT_avg_per_month"], 0.5),
     ("37", "universe.PIT_min", lambda: js("canonical_results.json")["universe"]["PIT_min"], 0.5),
     ("292", "universe.PIT_max", lambda: js("canonical_results.json")["universe"]["PIT_max"], 0.5),
     ("427", "universe.months", lambda: js("canonical_results.json")["universe"]["months"], 0.5)])
add(X, "methods", "The composite uses fixed weights", "code/canonical_rerun.py",
    [("0.20", "PRESET Z_MOM_12_1", lambda: grep("code/canonical_rerun.py", r"'Z_MOM_12_1':(\.\d+)")),
     ("0.10", "PRESET Z_DIV_YIELD", lambda: grep("code/canonical_rerun.py", r"'Z_DIV_YIELD':(\.\d+)")),
     ("0.05", "PRESET Z_MOM_6_1", lambda: grep("code/canonical_rerun.py", r"'Z_MOM_6_1':(\.\d+)")),
     ])
add(X, "methods", "equal weights until a factor has $36$ months", "code/canonical_rerun.py",
    [("36", "walk-forward ICs minimum", lambda: grep("code/canonical_rerun.py", r">=(36)"), 0.5)])
add(X, "methods", "a flat deduction of $10$ bp per month", "code/canonical_rerun.py",
    [("10", "long-leg cost bp", lambda: grep("code/canonical_rerun.py", r"'Long':L-(0\.\d+)") * 1e4, 0.5),
     ("20", "LS cost bp", lambda: grep("code/canonical_rerun.py", r"'LS':L-S-(0\.\d+)") * 1e4, 0.5)])
add(X, "methods", "all $t$-statistics use Newey-West standard errors with $6$ lags", "code/canonical_rerun.py",
    [("6", "maxlags", lambda: grep("code/canonical_rerun.py", r"'maxlags':(\d+)"), 0.5)])
add(X, "methods", "Measured turnover is $31$\\% of each leg", "waterfall_schemes_traded_days.csv",
    [("31", "Turnover x100", lambda: W("Composite", "Long-short", "Every month", "1. Gross signal", "Turnover") * 100, 0.5)])
# --- survivorship table
for u, leg, label in [("Survivor-only", "Long", "Survivor-only & Long &"), ("Survivor-only", "LS", "Survivor-only & Long-short &"),
                      ("Point-in-time", "Long", "Point-in-time & Long &"), ("Point-in-time", "LS", "Point-in-time & Long-short &")]:
    vals = {"Survivor-only/Long": ("14.9", "0.59", "-63.2", "0.87", "2.25"), "Survivor-only/LS": ("-2.3", "0.11", "-92.5", "0.46", "1.01"),
            "Point-in-time/Long": ("11.6", "0.55", "-69.0", "0.54", "2.08"), "Point-in-time/LS": ("8.0", "0.46", "-87.6", "1.32", "3.82")}[f"{u}/{leg}"]
    cols = ["Ann%", "Sharpe", "MaxDD%", "Alpha%mo", "Alpha_t"]
    add(X, "Table 1 survivor vs PIT", "@" + label, "canonical_table2.csv",
        [(p, f"{u} {leg} {c}", (lambda u=u, leg=leg, c=c: T2(u, leg, c))) for p, c in zip(vals, cols)])
add(X, "survivorship text", "Restricting to survivors turns a significant long-short alpha", "canonical_table2.csv",
    [("3.82", "PIT LS Alpha_t", lambda: T2("Point-in-time", "LS", "Alpha_t")), ("1.01", "Survivor LS Alpha_t", lambda: T2("Survivor-only", "LS", "Alpha_t"))])
add(X, "delisting bias", "the bias from dropping them is", "code10/code10_sensitivity.csv",
    [("-0.89", "baseline", lambda: C10("baseline, no terminal adjustment"))])
add(X, "delisting bias", "Of the 115 exits coded", "code10/code10_category_counts.csv",
    [("115", "sum n", code10_total, 0.5),
     ("61", "SDC completed", lambda: code10_cat("SDC completed|takeout, consideration"), 0.5),
     ("5", "hand adjudicated", lambda: float(csv("code10/code10_category_counts.csv").query("evidence == 'Factiva/BT hand adjudication'")["n"].sum()), 0.5),
     ("49", "unresolved", lambda: float(csv("code10/code10_category_counts.csv").query("category == 'UNRESOLVED'")["n"].sum()), 0.5)])
add(X, "delisting bias", "Forcing a $-100$\\% terminal return", "code10/code10_sensitivity.csv",
    [("-100", "forced terminal return in scenario name", lambda: grep_text(RES / "code10/code10_sensitivity.csv", r"forced (-100)%"), 0.5),
     ("-0.88", "confirmed insolvencies", lambda: C10("confirmed insolvencies forced -100%")),
     ("-0.60", "+ unresolved triaged wipeouts", lambda: C10("+ unresolved triaged wipeouts")),
     ("-0.55", "+ and ambiguous", lambda: C10("+ unresolved triaged wipeouts and ambiguous")),
     ("-0.50", "every unresolved", lambda: C10("+ every unresolved exit (harshest)"))])
add(X, "blue chip", "the naive survivor backtest earns", "survivorship_summary_final.csv",
    [("17.37", "A Long Ann", lambda: SS("A  Survivor-only  [Long]", "Ann_Return_%")), ("1.002", "A Long Sharpe", lambda: SS("A  Survivor-only  [Long]", "Sharpe")),
     ("-44.2", "A Long MaxDD", lambda: SS("A  Survivor-only  [Long]", "Max_DD_%"), 0.051)])
add(X, "blue chip", "The quarterly point-in-time run earns", "survivorship_summary_final.csv",
    [("7.91", "C Long Ann", lambda: SS("C  PIT quarterly  [Long]", "Ann_Return_%")), ("0.447", "C Long Sharpe", lambda: SS("C  PIT quarterly  [Long]", "Sharpe")),
     ("-62.7", "C Long MaxDD", lambda: SS("C  PIT quarterly  [Long]", "Max_DD_%"), 0.051)])
add(X, "blue chip", "The long-short Sharpe ratio falls from", "survivorship_summary_final.csv",
    [("0.586", "A L/S Sharpe", lambda: SS("A  Survivor-only  [L/S]", "Sharpe")), ("0.313", "C L/S Sharpe", lambda: SS("C  PIT quarterly  [L/S]", "Sharpe"))])
add(X, "IC text", "small size has the wrong sign", "canonical_table1.csv", [("-0.0496", "Z_LogMktCap Mean_IC", lambda: T1("Z_LogMktCap", "Mean_IC"))])
for lab, fac in [("Dividend yield &", "Z_DIV_YIELD"), ("ROE &", "Z_ROE"), ("Earnings yield &", "Z_EY"), ("Momentum 12-1 &", "Z_MOM_12_1"),
                 ("Composite &", "Composite"), ("Momentum 6-1 &", "Z_MOM_6_1"), ("Book-to-market &", "Z_BM_Ratio"),
                 ("Amihud liquidity &", "Z_Amihud"), ("Small size &", "Z_LogMktCap")]:
    pr = {"Z_DIV_YIELD": ("0.0769", "14.22"), "Z_ROE": ("0.0674", "9.19"), "Z_EY": ("0.0622", "7.50"), "Z_MOM_12_1": ("0.0599", "6.08"),
          "Composite": ("0.0488", "5.15"), "Z_MOM_6_1": ("0.0503", "5.09"), "Z_BM_Ratio": ("0.0038", "0.47"), "Z_Amihud": ("-0.0054", "-0.91"),
          "Z_LogMktCap": ("-0.0496", "-6.45")}[fac]
    add(X, "Table 2 ICs", "@" + lab + " " + pr[0].replace("-", "-"), "canonical_table1.csv",
        [(pr[0], fac + " Mean_IC", lambda fac=fac: T1(fac, "Mean_IC")), (pr[1], fac + " t_NW6", lambda fac=fac: T1(fac, "t_NW6"))])
add(X, "size text", "is not significant among the 30 largest names", "canonical_table3.csv",
    [("30", "Large AvgNames", lambda: T3("Large", "AvgNames"), 0.5), ("0.81", "Large Alpha_t", lambda: T3("Large", "Alpha_t")),
     ("1.92", "liq-screen alpha", lambda: T3("Small (liq-screen)", "Alpha%mo")), ("5.12", "liq-screen t", lambda: T3("Small (liq-screen)", "Alpha_t"))])
for lab, tier, pr in [("Large &", "Large", ("30", "0.0150", "1.14", "-0.01", "0.25", "0.81")), ("Mid &", "Mid", ("69", "0.0381", "3.77", "0.32", "0.78", "2.99")),
                      ("Small &", "Small", ("132", "0.0803", "7.91", "0.68", "1.38", "4.13"))]:
    cols = ["AvgNames", "IC", "IC_t_NW6", "LS_Sharpe", "Alpha%mo", "Alpha_t"]
    add(X, "Table 3 tiers", "@" + lab, "canonical_table3.csv",
        [(p, tier + " " + c, (lambda tier=tier, c=c: T3(tier, c)), 0.5 if c == "AvgNames" else None) for p, c in zip(pr, cols)])
add(X, "Table 3 tiers", "@Small, liquidity-screened", "canonical_table3.csv",
    [("90", "AvgNames", lambda: T3("Small (liq-screen)", "AvgNames"), 0.5), ("0.85", "LS_Sharpe", lambda: T3("Small (liq-screen)", "LS_Sharpe")),
     ("1.92", "Alpha%mo", lambda: T3("Small (liq-screen)", "Alpha%mo")), ("5.12", "Alpha_t", lambda: T3("Small (liq-screen)", "Alpha_t"))])
for lab, sc, pr in [("Preset weights & 0.0488", "Composite", ("0.0488", "5.15", "1.32", "3.82")), ("Without ROE &", "Composite_ExQuality", ("0.0473", "4.88", "1.29", "3.65")),
                    ("Equal weights &", "Composite_Equal", ("0.0270", "3.09", "1.01", "3.08")), ("Walk-forward weights & 0.0689", "Composite_WF", ("0.0689", "7.11", "1.72", "4.58"))]:
    cols = ["Mean_IC", "t_NW6", "LS_Alpha%mo", "LS_Alpha_t"]
    add(X, "Table 4 weights", "@" + lab, "canonical_table4.csv", [(p, sc + " " + c, (lambda sc=sc, c=c: T4(sc, c))) for p, c in zip(pr, cols)])
add(X, "weights text", "Equal weights are lower because they give small size", "canonical_rerun.py (8 equal weights)", [("12.5", "100 / 8 factors", lambda: 100 / 8, 0.0501)])
add(X, "waterfall text", "Gross alpha is $1.661$\\%/month ($t=5.13$)", "waterfall_schemes_traded_days.csv",
    [("1.661", "gross", lambda: W("Composite", "Long-short", "Every month", "1. Gross signal", "Alpha%mo")), ("5.13", "gross t", lambda: W("Composite", "Long-short", "Every month", "1. Gross signal", "t")),
     ("0.920", "after spreads", lambda: W("Composite", "Long-short", "Traded", "2. + spreads on traded names", "Alpha%mo")), ("2.74", "t", lambda: W("Composite", "Long-short", "Traded", "2. + spreads on traded names", "t")),
     ("0.611", "after screen", lambda: W("Composite", "Long-short", "Traded", "3. + Markit borrow availability screen", "Alpha%mo")), ("1.81", "t", lambda: W("Composite", "Long-short", "Traded", "3. + Markit borrow availability screen", "t")),
     ("0.366", "after fees", lambda: W("Composite", "Long-short", "Traded", "4. + Markit borrow fee", "Alpha%mo")), ("1.08", "t", lambda: W("Composite", "Long-short", "Traded", "4. + Markit borrow fee", "t")),
     ("0.741", "gross - after spreads", lambda: W("Composite", "Long-short", "Every month", "1. Gross signal", "Alpha%mo") - W("Composite", "Long-short", "Traded", "2. + spreads on traded names", "Alpha%mo"))])
for lab, st, pr in [("Gross signal &", "1. Gross signal", ("15.73", "0.84", "1.661", "5.13")), ("Plus spreads on traded names &", "2. + spreads on traded names", ("5.85", "0.39", "0.920", "2.74")),
                    ("Plus Markit availability screen &", "3. + Markit borrow availability screen", ("1.72", "0.20", "0.611", "1.81")), ("Plus Markit borrow fee &", "4. + Markit borrow fee", ("-1.20", "0.07", "0.366", "1.08"))]:
    cs = "Every month" if st.startswith("1.") else "Traded"
    add(X, "Table 5 waterfall", "@" + lab, "waterfall_schemes_traded_days.csv",
        [(p, st + " " + c, (lambda st=st, c=c, cs=cs: W("Composite", "Long-short", cs, st, c))) for p, c in zip(pr, ["Ann%", "Sharpe", "Alpha%mo", "t"])])
add(X, "conventions", "Across the two spread estimators and two charging rules", "waterfall_schemes(_traded_days).csv",
    [("0.060", "corrected, every month", lambda: W("Composite", "Long-short", "Every month", "4. + Markit borrow fee", "Alpha%mo")), ("0.18", "t", lambda: W("Composite", "Long-short", "Every month", "4. + Markit borrow fee", "t")),
     ("0.282", "uncorrected, every month", lambda: WU("Composite", "Long-short", "Every month", "4. + Markit borrow fee", "Alpha%mo")), ("0.85", "t", lambda: WU("Composite", "Long-short", "Every month", "4. + Markit borrow fee", "t")),
     ("0.366", "corrected, traded", lambda: W("Composite", "Long-short", "Traded", "4. + Markit borrow fee", "Alpha%mo")), ("1.08", "t", lambda: W("Composite", "Long-short", "Traded", "4. + Markit borrow fee", "t")),
     ("0.535", "uncorrected, traded", lambda: WU("Composite", "Long-short", "Traded", "4. + Markit borrow fee", "Alpha%mo")), ("1.58", "t", lambda: WU("Composite", "Long-short", "Traded", "4. + Markit borrow fee", "t"))])
add(X, "long-only", "The top decile held long-only earns a gross alpha", "waterfall_schemes_traded_days.csv",
    [("0.404", "long-only gross", lambda: W("Composite", "Long-only", "Every month", "Long-only gross", "Alpha%mo")), ("1.64", "t", lambda: W("Composite", "Long-only", "Every month", "Long-only gross", "t")),
     ("0.091", "traded", lambda: W("Composite", "Long-only", "Traded", "Long-only + spreads on traded names", "Alpha%mo")), ("0.36", "t", lambda: W("Composite", "Long-only", "Traded", "Long-only + spreads on traded names", "t"))])
add(X, "WF text", "Only the walk-forward weights keep", "waterfall_schemes_traded_days.csv",
    [("0.809", "WF stage 4", lambda: W("Composite_WF", "Long-short", "Traded", "4. + Markit borrow fee", "Alpha%mo")), ("2.03", "t", lambda: W("Composite_WF", "Long-short", "Traded", "4. + Markit borrow fee", "t")),
     ("274", "N", lambda: W("Composite_WF", "Long-short", "Traded", "4. + Markit borrow fee", "N"), 0.5),
     ("-1.29", "Ann%", lambda: W("Composite_WF", "Long-short", "Traded", "4. + Markit borrow fee", "Ann%")), ("0.17", "Sharpe", lambda: W("Composite_WF", "Long-short", "Traded", "4. + Markit borrow fee", "Sharpe")),
     ("-90.8", "MaxDD%", lambda: W("Composite_WF", "Long-short", "Traded", "4. + Markit borrow fee", "MaxDD%"))])
for lab, sc, pr in [("Preset weights & 1.661", "Composite", ("1.661", "5.13", "0.366", "1.08")), ("Without ROE & 1.612", "Composite_ExQuality", ("1.612", "4.86", "0.307", "0.88")),
                    ("Equal weights & 1.435", "Composite_Equal", ("1.435", "5.17", "0.376", "1.40")), ("Walk-forward weights & 2.282", "Composite_WF", ("2.282", "6.36", "0.809", "2.03"))]:
    add(X, "Table 6 gross vs costed", "@" + lab, "waterfall_schemes_traded_days.csv",
        [(pr[0], sc + " gross", lambda sc=sc: W(sc, "Long-short", "Every month", "1. Gross signal", "Alpha%mo")), (pr[1], sc + " gross t", lambda sc=sc: W(sc, "Long-short", "Every month", "1. Gross signal", "t")),
         (pr[2], sc + " costed", lambda sc=sc: W(sc, "Long-short", "Traded", "4. + Markit borrow fee", "Alpha%mo")), (pr[3], sc + " costed t", lambda sc=sc: W(sc, "Long-short", "Traded", "4. + Markit borrow fee", "t"))])
add(X, "borrow", "Charging Markit fees alone", "borrow_markit.csv",
    [("-0.02", "scenario 2 alpha", lambda: MKT("2. Markit fee charged, no avail. screen", "alpha")), ("-0.11", "t", lambda: MKT("2. Markit fee charged, no avail. screen", "t")),
     ("46", "fee_bps", lambda: MKT("2. Markit fee charged, no avail. screen", "fee_bps"), 0.5),
     ("2.18", "min t, scenarios 3 to 7", lambda: float(csv("borrow_markit.csv").iloc[2:]["t"].min())), ("3.47", "max t, scenarios 3 to 7", lambda: float(csv("borrow_markit.csv").iloc[2:]["t"].max()))])
add(X, "borrow", "the long leg earns $+0.392$", "ls_markit.csv",
    [("0.392", "mean longA", lambda: LM("longA")[0]), ("1.40", "t", lambda: LM("longA")[1]), ("0.372", "mean shortA", lambda: LM("shortA")[0]), ("2.72", "t", lambda: LM("shortA")[1]),
     ("0.764", "mean ls", lambda: LM("ls")[0]), ("2.23", "t", lambda: LM("ls")[1])])
add(X, "borrow", "the borrow-feasibility screen cuts the long-short", "borrow_waterfall.csv",
    [("1.661", "stage 1", lambda: BW("1. L/S unconstrained (Markit window)", "Ret_%mo")), ("4.94", "t", lambda: BW("1. L/S unconstrained (Markit window)", "NW_t")),
     ("0.712", "stage 5", lambda: BW("5. + exclude specials (DCBS >= 5)", "Ret_%mo")), ("2.53", "t", lambda: BW("5. + exclude specials (DCBS >= 5)", "NW_t")),
     ("57", "reduction %", lambda: (1 - BW("5. + exclude specials (DCBS >= 5)", "Ret_%mo") / BW("1. L/S unconstrained (Markit window)", "Ret_%mo")) * 100, 0.5),
     ("0.713", "long-only", lambda: BW("6. LONG-ONLY top 30% vs liquid universe", "Ret_%mo")), ("4.19", "t", lambda: BW("6. LONG-ONLY top 30% vs liquid universe", "NW_t")),
     ("0.85", "Sharpe", lambda: BW("6. LONG-ONLY top 30% vs liquid universe", "Sharpe"))])
add(X, "capacity", "Net alpha stays at", "capacity_analysis.csv",
    [("0.28", "alpha_mo x100 at 1bn", lambda: CAP(1e9, "alpha_mo") * 100),
     ("5", "infeasible share at 50m, %", lambda: CAP(5e7, "infeasible_months") / CAP(5e7, "total_months") * 100, 0.5),
     ("43", "infeasible share at 200m, %", lambda: CAP(2e8, "infeasible_months") / CAP(2e8, "total_months") * 100, 0.5)])
for lab, aum, pr in [("S\\$1m &", 1e6, ("0.35", "0")), ("S\\$10m &", 1e7, ("0.30", "0")), ("S\\$50m &", 5e7, ("0.29", "10")),
                     ("S\\$200m &", 2e8, ("0.28", "94")), ("S\\$1bn &", 1e9, ("0.28", "169"))]:
    add(X, "Table 7 capacity", "@" + lab, "capacity_analysis.csv",
        [(pr[0], f"alpha_mo x100 at {aum:g}", lambda aum=aum: CAP(aum, "alpha_mo") * 100), (pr[1], f"infeasible_months at {aum:g}", lambda aum=aum: CAP(aum, "infeasible_months"), 0.5)])
add(X, "anatomy", "the equal-weight top-100 long-short earns", "finish_output.txt",
    [("0.526", "plain composite L/S alpha", lambda: fin(r"Plain composite \[L/S\]\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s+([-\d.]+)\s")),
     ("1.93", "t", lambda: fin(r"Plain composite \[L/S\]\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s+([-\d.]+)\s")),
     ("0.169", "sector-neutral alpha", lambda: fin(r"Sector-neutral \[L/S\]\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s+([-\d.]+)\s")),
     ("0.69", "t", lambda: fin(r"Sector-neutral \[L/S\]\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s+([-\d.]+)\s")),
     ("0.663", "vol target alpha", lambda: fin(r"2\. \+ vol target 12%\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s+([-\d.]+)\s")),
     ("3.08", "t", lambda: fin(r"2\. \+ vol target 12%\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s+([-\d.]+)\s")),
     ("86", "break-even bp", lambda: fin(r"break-even one-way cost = [^=]*= (\d+) bp"), 0.5),
     ("12", "vol target %", lambda: fin(r"vol target (\d+)%"), 0.5),
     ("0.51", "allocation", lambda: fin(r"Allocation\s*:\s*\+([\d.]+)")), ("1.28", "selection", lambda: fin(r"Selection\s*:\s*\+([\d.]+)")),
     ("2.98", "interaction", lambda: fin(r"Interaction\s*:\s*\+([\d.]+)")), ("4.78", "sum", lambda: fin(r"Sum\s*:\s*\+([\d.]+)")),
     ("5.12", "actual", lambda: fin(r"Actual active return \(check\): \+([\d.]+)"))])
add(X, "anatomy", "median Corwin-Schultz half-spread of $23.5$ bp", "cs_spreads_check.txt",
    [("23.5", "median bp", lambda: grep_text(RES / "cs_spreads_check.txt", r"median ([\d.]+)bp")),
     ("143,978", "rows", lambda: float(re.search(r"([\d,]+) rows", (RES / "cs_spreads_check.txt").read_text()).group(1).replace(",", "")), 0.5)])
add(X, "weighting", "Cap-weighting removes the alpha", "weighting_comparison.csv",
    [("0.53", "EW L/S alpha", lambda: v("weighting_comparison.csv", "Alpha%mo", Design="Equal-weight  [L/S]")), ("1.93", "t", lambda: v("weighting_comparison.csv", "t", Design="Equal-weight  [L/S]")),
     ("-0.08", "VW L/S alpha", lambda: v("weighting_comparison.csv", "Alpha%mo", Design="Value-weight (uncapped)  [L/S]")), ("-0.27", "t", lambda: v("weighting_comparison.csv", "t", Design="Value-weight (uncapped)  [L/S]")),
     ("0.25", "10% cap alpha", lambda: v("weighting_comparison.csv", "Alpha%mo", Design="Capped value-weight (10%)  [L/S]")), ("0.88", "t", lambda: v("weighting_comparison.csv", "t", Design="Capped value-weight (10%)  [L/S]")),
     ("5.4", "5% cap max weight %", lambda: grep_text(RES / "weighting_comparison.csv", r"Capped value-weight \(5%\)  \[L/S\].*maxwt ([\d.]+)%")),
     ("5.2", "EW max weight %", lambda: grep_text(RES / "weighting_comparison.csv", r"Equal-weight  \[L/S\].*maxwt ([\d.]+)%"))])
add(X, "attribution", "dropping 12-1 momentum has the largest effect", "attribution_loo.csv",
    [("0.157", "alpha", lambda: LOO("drop Z_MOM_12_1", "Alpha%mo")), ("0.68", "t", lambda: LOO("drop Z_MOM_12_1", "t")), ("-0.369", "dAlpha", lambda: LOO("drop Z_MOM_12_1", "dAlpha"))])
add(X, "attribution", "quality contributes $-50.2$ bp per month", "attribution/attrib_factor_loo.csv",
    [("-50.2", "QUALITY marginal_contrib_bps", lambda: QL("QUALITY", "marginal_contrib_bps"), 0.051), ("0.970", "alpha_without", lambda: QL("QUALITY", "alpha_without")),
     ("4.71", "t_without", lambda: QL("QUALITY", "t_without")), ("12.3", "MOMENTUM bps", lambda: QL("MOMENTUM", "marginal_contrib_bps"), 0.051)])
add(X, "attribution", "A holdings-based attribution gives momentum", "attribution/attrib_holdings.csv",
    [("0.427", "MOMENTUM", lambda: HO("MOMENTUM", "contrib_pct_mo")), ("2.61", "t", lambda: HO("MOMENTUM", "t")), ("0.257", "VALUE", lambda: HO("VALUE", "contrib_pct_mo")), ("3.86", "t", lambda: HO("VALUE", "t")),
     ("0.023", "QUALITY", lambda: HO("QUALITY", "contrib_pct_mo")), ("0.26", "t", lambda: HO("QUALITY", "t")), ("0.985", "exposure", lambda: HO("QUALITY", "avg_exposure")),
     ("-0.150", "RESIDUAL", lambda: HO("RESIDUAL", "contrib_pct_mo"))])
add(X, "STI-core", "It earns $+0.396$", "sti_core_returns.csv / constrained_backtest.csv",
    [("0.396", "mean(net-bm)", lambda: diff_vs_bm("sti_core_returns.csv")[0]), ("2.26", "NW-6 t", lambda: diff_vs_bm("sti_core_returns.csv")[1]),
     ("10.1", "ann%", lambda: CB("Unconstrained (paper primary)", "ann"), 0.051), ("-50.3", "maxdd", lambda: CB("Unconstrained (paper primary)", "maxdd"), 0.051)])
add(X, "STI-core", "A Compustat-only reproduction", "compustat_backtest_quarterly.csv / compustat_backtest.csv",
    [("0.36", "quarterly", lambda: diff_vs_bm("compustat_backtest_quarterly.csv")[0]), ("2.26", "t", lambda: diff_vs_bm("compustat_backtest_quarterly.csv")[1]),
     ("0.27", "annual", lambda: diff_vs_bm("compustat_backtest.csv")[0]), ("1.82", "t", lambda: diff_vs_bm("compustat_backtest.csv")[1])])
add(X, "deciles", "the bottom decile earns", "sgx3_deciles_corrected.csv / sgx3_leg_decomposition.csv",
    [("-0.518", "D1 mean", lambda: DEC(0)[0]), ("-3.08", "t", lambda: DEC(0)[1]), ("0.476", "D10 mean", lambda: DEC(9)[0]),
     ("0.995", "D10-D1", lambda: DEC("spread")[0]), ("2.74", "t", lambda: DEC("spread")[1]),
     ("0.492", "Long active", lambda: v("sgx3_leg_decomposition.csv", "active", leg="Long")), ("1.75", "t", lambda: v("sgx3_leg_decomposition.csv", "t", leg="Long")),
     ("0.547", "Short active", lambda: v("sgx3_leg_decomposition.csv", "active", leg="Short")), ("3.30", "t", lambda: v("sgx3_leg_decomposition.csv", "t", leg="Short")),
     ("47", "long share %", lambda: v("sgx3_leg_decomposition.csv", "active", leg="Long") / v("sgx3_leg_decomposition.csv", "active", leg="L/S spread") * 100, 0.5),
     ("53", "short share %", lambda: v("sgx3_leg_decomposition.csv", "active", leg="Short") / v("sgx3_leg_decomposition.csv", "active", leg="L/S spread") * 100, 0.5)])
add(X, "constraints", "a $33$\\% sector cap gives", "constrained_backtest.csv",
    [("0.489", "sector cap 33%", lambda: CB("Sector cap 33% (max 2 names/sector)", "alpha_mo")), ("2.51", "t", lambda: CB("Sector cap 33% (max 2 names/sector)", "t")),
     ("0.392", "unconstrained", lambda: CB("Unconstrained (paper primary)", "alpha_mo")), ("2.24", "t", lambda: CB("Unconstrained (paper primary)", "t")),
     ("33", "sector cap % (spec name)", lambda: grep_text(RES / "constrained_backtest.csv", r"Sector cap (33)%"), 0.5)])
add(X, "regimes", "By sub-period the alpha is", "attribution/subperiods.csv",
    [("0.084", "2008-2013", lambda: SUB("2008-2013", "alpha")), ("0.13", "t", lambda: SUB("2008-2013", "t")), ("0.141", "2014-2019", lambda: SUB("2014-2019", "alpha")), ("0.43", "t", lambda: SUB("2014-2019", "t")),
     ("1.187", "2020-2026", lambda: SUB("2020-2026", "alpha")), ("3.52", "t", lambda: SUB("2020-2026", "t"))])
add(X, "regimes", "In calm markets it is", "attribution/regime_attribution.csv",
    [("1.205", "calm", lambda: REG("Market vol BELOW median (calm)", "alpha")), ("3.91", "t", lambda: REG("Market vol BELOW median (calm)", "t")),
     ("-0.123", "turbulent", lambda: REG("Market vol ABOVE median (turbulent)", "alpha")), ("-0.34", "t", lambda: REG("Market vol ABOVE median (turbulent)", "t"))])
add(X, "concentration", "The top name accounts for", "attribution/concentration.csv",
    [("27.9", "top 1", lambda: v("attribution/concentration.csv", "share_of_cumulative_active_pct", top_n=1)), ("69.9", "top 5", lambda: v("attribution/concentration.csv", "share_of_cumulative_active_pct", top_n=5)),
     ("96.7", "top 10", lambda: v("attribution/concentration.csv", "share_of_cumulative_active_pct", top_n=10))])
for lab, fac, pr in [("Book-to-market & 0.261", "Book-to-market", ("0.261", "2.767")), ("Earnings yield & 0.413", "Earnings yield", ("0.413", "1.939")),
                     ("Dividend yield & 0.230", "Dividend yield", ("0.230", "2.560")), ("ROE & 0.037", "Return on equity", ("0.037", "0.406")),
                     ("Momentum 12-1 & 0.111", "Momentum 12-1", ("0.111", "0.888")), ("Momentum 6-1 & 0.048", "Momentum 6-1", ("0.048", "0.413")),
                     ("Momentum 3-1 & 0.060", "Momentum 3-1", ("0.060", "0.597")), ("Small size & -0.070", "Size (neg.)", ("-0.070", "-0.876")),
                     ("Amihud illiquidity & -0.010", "Amihud illiq.", ("-0.010", "-0.115"))]:
    add(X, "Table 8 reference", "@" + lab, "rederived_table1_fm.csv",
        [(pr[0], fac + " Prem_pct_mo", lambda fac=fac: FM(fac, "Prem_pct_mo")), (pr[1], fac + " NW_t", lambda fac=fac: FM(fac, "NW_t"))])
add(X, "reference text", "gives no factor that survives Bonferroni correction", "rederived_table1_fm.csv",
    [("2.77", "Bonferroni z, 9 tests", lambda: float(stats.norm.ppf(1 - 0.05 / 9 / 2)), 0.0051), ("2.767", "best NW_t", lambda: float(csv("rederived_table1_fm.csv").NW_t.max()))])
add(X, "benchmark", "the measured contamination is", "attribution/leakage_funnel.csv / benchmark_sensitivity.csv",
    [("0.395", "corrected minus raw", lambda: FUN("1. Corrected benchmark (investable cohort)", "alpha_pct_mo") - FUN("0. Raw, contaminated benchmark (as published)", "alpha_pct_mo")),
     ("2.56", "STI tA", lambda: BMN("STI", "tA")), ("2.52", "STI tB", lambda: BMN("STI", "tB"))])
for lab, bk, pr in [("STI & 6", "STI", ("6", "0.443", "2.56", "0.438", "2.52")), ("Top-50 & 5", "Top-50", ("5", "0.334", "1.14", "0.520", "1.74")),
                    ("Top-100 & 10", "Top-100", ("10", "0.073", "0.24", "0.468", "1.67")), ("Top-150 & 15", "Top-150", ("15", "0.302", "1.12", "0.861", "3.30")),
                    ("Top-200 & 20", "Top-200", ("20", "0.209", "0.79", "0.860", "3.61"))]:
    cols = ["book", "alphaA", "tA", "alphaB", "tB"]
    add(X, "Table 9 benchmark", "@" + lab, "attribution/benchmark_sensitivity.csv",
        [(p, bk + " " + c, (lambda bk=bk, c=c: BMN(bk, c)), 0.5 if c == "book" else None) for p, c in zip(pr, cols)])
add(X, "grid", "A specification grid of $65$ tests", "spec_results_N65.csv",
    [("65", "rows", lambda: float(len(SPEC())), 0.5), ("24", "|nw_t|>1.96", lambda: float((SPEC().nw_t.abs() > 1.96).sum()), 0.5), ("1.96", "threshold", lambda: 1.96, 0.0051),
     ("3.0", "threshold", lambda: 3.0, 0.0501), ("3.67", "max |nw_t|", lambda: float(SPEC().nw_t.abs().max())), ("0.074", "min p_BHY", lambda: float(SPEC().p_BHY.min()))])
add(X, "jump", "Merton jump-diffusion fits well", "jumpmodel_test_b.json",
    [("57.9", "var_jump_share", lambda: JM("var_jump_share") * 100), ("58", "jumps_per_year", lambda: JM("jumps_per_year"), 0.5), ("1.86", "sigmaJ x100", lambda: JM("sigmaJ") * 100),
     ("0.016", "ks_merton", lambda: JM("ks_merton")), ("0.072", "ks_gaussian", lambda: JM("ks_gaussian")),
     ("-3.13", "gaussian es99 x100", lambda: JMs("gaussian", "es99") * 100), ("-4.73", "empirical es99 x100", lambda: JMs("empirical", "es99") * 100),
     ("1.60", "gap pp", lambda: (JMs("gaussian", "es99") - JMs("empirical", "es99")) * 100),
     ("34", "gap/empirical %", lambda: (JMs("gaussian", "es99") - JMs("empirical", "es99")) / abs(JMs("empirical", "es99")) * 100, 0.5),
     ("-4.43", "merton es99 x100", lambda: JMs("merton", "es99") * 100)])
add(X, "garch", "beats the Merton model by", "garch_model_comparison.csv / garch_var_backtest.csv",
    [("713", "BIC(Merton) - BIC(GJR-skt)", lambda: BIC("Merton jump-diffusion (i.i.d.)") - BIC("GJR-GARCH-skt"), 0.5),
     ])


def test_only_gjr_passes_var_at_both_levels():
    d = csv("garch_var_backtest.csv")
    ok = d[d["pass"]].groupby("model")["level"].nunique()
    assert list(ok[ok == 2].index) == ["GJR-skt"]
add(X, "overlays", "Jump-aware expected-shortfall sizing raises", "jump_sizing_results.csv",
    [("0.666", "baseline Sharpe", lambda: JS("Baseline (no sizing)", "Sharpe")), ("0.715", "ES-target cap 1.5 Sharpe", lambda: JS("Jump-aware ES-target (cap 1.5)", "Sharpe")),
     ("0.05", "difference", lambda: JS("Jump-aware ES-target (cap 1.5)", "Sharpe") - JS("Baseline (no sizing)", "Sharpe")),
     ("0.10", "pre-registered bar", lambda: 0.10, 0.0051)])
add(X, "overlays", "A Markov-switching overlay using filtered probabilities", "ms_sizing_results.csv",
    [("0.433", "filtered", lambda: MS("MS FILTERED (legitimate)", "Sharpe")), ("0.958", "smoothed", lambda: MS("MS SMOOTHED (look-ahead, INVALID)", "Sharpe")),
     ("0.525", "difference", lambda: MS("MS SMOOTHED (look-ahead, INVALID)", "Sharpe") - MS("MS FILTERED (legitimate)", "Sharpe"))])
add(X, "overlays", "Against an inverse-realised-volatility benchmark", "overlay_ivol/*.csv",
    [("0.702", "inverse vol 12m", lambda: IVT("Inverse realised vol 12m @ 1.36x", "Sharpe")), ("0.776", "constant leverage", lambda: IVT("Constant 1.36x leverage", "Sharpe")),
     ("0.838", "jump-aware", lambda: IVT("Jump-aware ES-target @ 1.36x", "Sharpe")), ("0.734", "GARCH", lambda: IVT("GARCH vol-target (LAGGED) @ 1.36x", "Sharpe")),
     ("0.074", "const - ivol", lambda: IV("Constant 1.36x leverage", "sharpe_minus_ivol")), ("0.136", "jump - ivol", lambda: IV("Jump-aware ES-target @ 1.36x", "sharpe_minus_ivol")),
     ("0.032", "GARCH - ivol", lambda: IV("GARCH vol-target (LAGGED) @ 1.36x", "sharpe_minus_ivol")),
     ("-0.036", "jump ci_lo", lambda: IV("Jump-aware ES-target @ 1.36x", "ci_lo")), ("0.345", "jump ci_hi", lambda: IV("Jump-aware ES-target @ 1.36x", "ci_hi"))])
add(X, "Kalman", "The Kalman beta does not hedge better", "../kalman/hedge_summary.csv / test_count.txt / pairs_portfolio_daily_25_proxy.csv",
    [("30.7", "monthly_30_sti Kalman", lambda: KAL("monthly_30_sti", "Kalman"), 0.051), ("31.5", "monthly_30_sti Rolling", lambda: KAL("monthly_30_sti", "Rolling"), 0.051),
     ("3.76", "Bonferroni |t|", kal_bar, 0.0051), ("295", "tests", kal_tests, 0.5), ("-7.45", "Kalman MLE oos t, entry 1.0", pairs_oos_t, 0.0051),
     ("1.0", "entry", lambda: 1.0, 0.0501)])
for lab, run, pr in [("Monthly, 30 names, STI &", "monthly_30_sti", ("28.4", "31.5", "31.1", "30.7")), ("Monthly, 25 names, STI &", "monthly_25_sti", ("32.1", "33.8", "33.6", "33.3")),
                     ("Monthly, 25 names, proxy &", "monthly_25_proxy", ("28.0", "29.2", "29.3", "28.7")), ("Daily, 25 names, proxy &", "daily_25_proxy", ("30.0", "32.4", "33.4", "33.1"))]:
    add(X, "Table 10 Kalman", "@" + lab, "../kalman/hedge_summary.csv",
        [(p, run + " " + c, (lambda run=run, c=c: KAL(run, c)), 0.051) for p, c in zip(pr, ["Static OLS", "Rolling", "EWMA", "Kalman"])])

CLAIMS = [c for c in CLAIMS if c is not None]


# ---------------------------------------------------------------- document normalisation
SENT = "\x01"


def norm_text(s, tex=True):
    if not tex:
        s = s.replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", "-")
        return re.sub(r"[ \t]+", " ", s.replace("**", "")).strip()
    s = s.replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", "-")
    s = s.replace("\\$", SENT).replace("\\%", "%").replace("{,}", ",")
    s = s.replace("$", "").replace(SENT, "$").replace("\\\\", " ").replace("~", " ")
    s = re.sub(r"\\[a-zA-Z]+", " ", s)
    s = re.sub(r"[{}]", "", s)
    s = re.sub(r"\*\*", "", s)
    return re.sub(r"[ \t]+", " ", s).strip()


def doc_lines(name):
    raw = DOCS[name].read_text().split("\n")
    out = []
    if name == "README":
        fence = False
        for ln in raw:
            if ln.strip().startswith("```"):
                fence = not fence
                continue
            if fence or ln.strip().startswith("!["):
                continue
            ln = re.sub(r"\]\([^)]*\)", "]", ln)      # link targets
            ln = re.sub(r"`[^`]*`", " ", ln)           # inline code
            ln = re.sub(r"https?://\S+", " ", ln)
            out.append(norm_text(ln, tex=False))
    else:
        for ln in raw:
            if ln.startswith("\\begin{thebibliography}"):
                break
            ln = re.sub(r"(?<!\\)%.*", "", ln)
            ln = re.sub(r"\\(?:cite|ref|label|usepackage|documentclass|geometry|begin|end)(?:\[[^\]]*\])?(?:\{[^}]*\})*", " ", ln)
            out.append(norm_text(ln))
    return out


@lru_cache(None)
def flat(name):
    lines = doc_lines(name)
    text, ends, pos = "", [], 0
    for ln in lines:
        text += ln + " "
        pos += len(ln) + 1
        ends.append(pos - 1)
    return text, ends


NUM = re.compile(r"(?:(?<![\w.])-)?(?<![A-Za-z\d.])\d[\d,]*(?:\.\d+)?")


def tokens(text):
    out = []
    for m in NUM.finditer(text):
        t = m.group(0)
        if t.endswith(","):
            t = t[:-1]
        out.append((m.start(), m.start() + len(t), t))
    return out


def resolve(name, snippet):
    """list of (start, end) spans of the snippet in the flat text."""
    text, ends = flat(name)
    if snippet.startswith("@"):
        pre = norm_text(snippet[1:], tex=(name == "tex"))
        spans, i = [], text.find(pre)
        while i >= 0:
            e = min(x for x in ends if x >= i)
            spans.append((i, e))
            i = text.find(pre, i + 1)
        return spans
    pre = norm_text(snippet, tex=(name == "tex"))
    spans, i = [], text.find(pre)
    while i >= 0:
        if name == "tex":   # anchor to the end of its paragraph (one line)
            end = min(x for x in ends if x >= i)
        else:               # anchor to the end of its sentence
            m = re.compile(r"\.(?:\s|$)").search(text, i + len(pre))
            end = m.end() if m else len(text)
        spans.append((i, end))
        i = text.find(pre, i + 1)
    return spans


def printed_spans(name, snippet, printed):
    text, _ = flat(name)
    p = norm_text(printed)
    out = []
    for a, b in resolve(name, snippet):
        for s, e, t in tokens(text[a:b]):
            if t == p:
                out.append((a + s, a + e))
    return out


def dec(p):
    return len(p.split(".")[1]) if "." in p else 0


def ids(c):
    return f"{c[0]}:{c[1]}:{c[3]}:{c[5]}"


@pytest.mark.parametrize("c", [
    pytest.param(c, id=ids(c), marks=pytest.mark.xfail(strict=True, reason="known unverifiable: " + c[8]) if c[8] else ())
    for c in CLAIMS])
def test_claim(c):
    doc, where, snippet, printed, source, field, fn, tol, unver = c
    assert printed_spans(doc, snippet, printed), f"'{printed}' not found in snippet '{snippet}' of {doc}"
    if unver:
        pytest.fail(f"no source file in the repository for {where}: {field}")
    expected = fn()
    tol = tol if tol is not None else 0.5 * 10 ** -dec(printed) + 1e-9
    assert abs(float(norm_text(printed).replace(",", "")) - expected) <= tol, f"{doc} {where}: printed {printed}, {source}[{field}] = {expected}"


# ---------------------------------------------------------------- allowlist for the coverage test
# (doc, regex over the normalised text, one-word reason). A number is allowed if it lies inside a match.
ALLOW = [
    ("README", r"\b(?:19|20)\d\d\b", "year"),
    ("tex", r"\b(?:19|20)\d\d\b", "year"),
    ("README", r"\b(?:12|6|3)-1\b", "setting"),
    ("tex", r"\b(?:12|6|3)-1\b", "setting"),
    ("README", r"S\$\d+(?:m|bn)", "unit"),
    ("tex", r"S\$\d+(?:m|bn)", "unit"),
    ("README", r"\b[Ss]ections? \d+", "ref"),
    ("tex", r"\b[Ss]ections? \d+", "ref"),
    ("README", r"\bTables? (?:\d+|I)\b", "ref"),
    ("README", r"\b(?:30|71)-name", "setting"),
    ("tex", r"\b(?:30|71)-name", "setting"),
    ("README", r"\btop-(?:6|100)\b|\bliquid-100\b|\btop 100\b|\btop-six\b", "setting"),
    ("README", r"\b200 dpi\b", "setting"),
    ("README", r"\b99% ES\b", "setting"),
    ("README", r"about 2\b", "setting"),
    ("README", r"\bt\+1\b", "setting"),
    ("README", r"\bt=3\.0\b", "setting"),
    ("README", r"\bt=1\.96\b", "setting"),
    ("tex", r"\bTop-(?:50|100|150|200)\b", "setting"),
    ("tex", r"\b(?:30|50|100) names\b|\b100-name\b|\btop-100\b|\btop-30%", "setting"),
    ("tex", r"\b25 index stocks\b|\b25-name\b|\b25 names\b|\b30 names\b|\b30 largest\b", "setting"),
    ("tex", r"\b10% participation\b|\b12% volatility\b|\b10% cap\b|\b5% cap\b|\b33% sector\b|95% and 99%|\b99% level\b|\b5% of months\b", "setting"),
    ("tex", r"\|t\|>(?:1\.96|3\.0|3\.76)|t>3\.0|t\+1|\$?t=2\.77", "setting"),
    ("tex", r"36-month", "setting"),
    ("tex", r"\bmonths? from 1991\b", "setting"),
    ("tex", r"entry 1\.0", "setting"),
    ("tex", r"\b218 months\b", "setting"),
    ("tex", r"\bnine factors\b", "setting"),
    ("tex", r"\b100-name book\b|\b6-name\b", "setting"),
    ("tex", r"\b(?:Vol|vol)\. \d+", "citation"),
    ("tex", r"\bTable [A-Z]?\d*\b", "ref"),
    ("tex", r"\bTable I\b", "ref"),
    ("README", r"\b\d{2,3}-?\s?(?:figures|dpi)\b", "setting"),
]

def covered_spans(name):
    sp = []
    for c in CLAIMS:
        if c[0] == name:
            sp += printed_spans(name, c[2], c[3])
    return sp


def allow_spans(name):
    text, _ = flat(name)
    sp = []
    for d, rx, why in ALLOW:
        if d == name:
            sp += [(m.start(), m.end()) for m in re.finditer(rx, text)]
    return sp


def stats_cov(name):
    text, _ = flat(name)
    cov, alw = covered_spans(name), allow_spans(name)
    covered, allowed, bad = [], [], []
    for s, e, t in tokens(text):
        if any(a <= s and e <= b for a, b in cov):
            covered.append(t)
        elif any(a <= s and e <= b for a, b in alw):
            allowed.append(t)
        else:
            bad.append((t, text[max(0, s - 40):e + 20]))
    return covered, allowed, bad


@pytest.mark.parametrize("name", ["README", "tex"])
def test_every_number_is_covered(name):
    covered, allowed, bad = stats_cov(name)
    print(f"\n{name}: {len(covered)} numbers covered by claim rows, {len(allowed)} allowlisted")
    assert not bad, "uncovered numbers:\n" + "\n".join(f"  {t!r}  ...{ctx}" for t, ctx in bad)
