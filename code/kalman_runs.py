"""
All runs of the Kalman hedge ratio extension (results/kalman/PREREG.md), in one place.

  monthly_30_sti         Bloomberg monthly, 30 names, STI hedge (the original study)
  monthly_25_sti         Bloomberg monthly, the 25 matched names, STI hedge
  monthly_25_proxy       Compustat month-end TR, 25 names, LOO proxy hedge
  daily_25_proxy         Compustat daily, LOO proxy, hedge rebalanced daily
  daily_25_proxy_weekly  as above, hedge rebalanced every 5 days (beta hedge only)

The Compustat runs start in January 2001, like the Bloomberg panel, so the middle two
runs isolate the universe and the proxy from the change in frequency.

Writes everything to results/kalman/, including test_count.txt with the Bonferroni
threshold over the daily tests. Usage:  python code/kalman_runs.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

import kalman_hedge as kh
from kalman_data import BBG_XLSM, CONM, PROXY_LABEL, load_compustat

OUT = Path(__file__).resolve().parent.parent / "results" / "kalman"
START = "2001-01-01"
METHODS = ["Static OLS", "Rolling", "EWMA", "Kalman"]
DM_COLS = ["DM Kalman vs Rolling", "DM Kalman vs EWMA", "DM Kalman vs Static"]


def label(df, market):
    df = df.copy()
    df.insert(0, "market", market)
    return df


def save(df, name, index=True):
    df.to_csv(OUT / name, index=index)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    names25 = list(CONM)

    # Bloomberg monthly, STI hedge
    tri, sti = kh.load_bloomberg_monthly(BBG_XLSM)
    mkt = sti.pct_change().reindex(tri.index)
    runs = {"monthly_30_sti": kh.run(tri, mkt, "monthly", OUT, "monthly_30_sti"),
            "monthly_25_sti": kh.run(tri[names25], mkt, "monthly", OUT, "monthly_25_sti")}
    markets = {"monthly_30_sti": "STI price index", "monthly_25_sti": "STI price index"}

    # Compustat, leave-one-out proxy
    for tag, freq in (("monthly_25_proxy", "monthly"), ("daily_25_proxy", "daily")):
        tr, proxy, _, _ = load_compustat(freq)
        tr, proxy = tr[tr.index >= START], proxy[proxy.index >= START]
        runs[tag] = kh.run(tr, proxy, freq, OUT, tag)
        markets[tag] = PROXY_LABEL
        if freq == "daily":
            weekly, _ = kh.beta_hedge_test(tr.pct_change(fill_method=None), proxy, "daily", rebalance=5)
            runs["daily_25_proxy_weekly"] = (weekly, None, None, None)
            markets["daily_25_proxy_weekly"] = PROXY_LABEL

    # label every output with its market series
    for tag, (hedge, pairs, port, diag) in runs.items():
        save(label(hedge, markets[tag]), f"hedge_{tag}.csv")
        if pairs is not None:
            save(label(pairs, markets[tag]), f"pairs_{tag}.csv", index=False)
            save(label(port, markets[tag]), f"pairs_portfolio_{tag}.csv", index=False)
            save(label(diag, markets[tag]), f"pair_diagnostics_{tag}.csv", index=False)

    # one table across frequencies: mean OOS hedge effectiveness over single names
    summary = pd.DataFrame({
        tag: {**{m: h.drop("EW book")[m].mean() for m in METHODS},
              "EW book Kalman": h.loc["EW book", "Kalman"], "EW book Rolling": h.loc["EW book", "Rolling"],
              "names": len(h) - 1, "median n_oos": h["n_oos"].median(), "market": markets[tag]}
        for tag, (h, *_rest) in runs.items()}).T
    save(summary, "hedge_summary.csv")

    # test count over the daily runs only, and the Bonferroni threshold
    lines, n = [], 0
    for tag in ("daily_25_proxy", "daily_25_proxy_weekly"):
        k = int(runs[tag][0][DM_COLS].notna().sum().sum())
        lines.append(f"{tag}: {k} hedge DM tests ({len(runs[tag][0])} targets x {len(DM_COLS)})")
        n += k
    pairs, port = runs["daily_25_proxy"][1], runs["daily_25_proxy"][2]
    k = int(pairs.query("period == 'oos'")["t_nw"].notna().sum())
    lines.append(f"daily_25_proxy: {k} pair x method x entry OOS tests "
                 f"({pairs['pair'].nunique()} pairs x {pairs['method'].nunique()} methods x {pairs['entry'].nunique()} entries)")
    n += k
    k = int(port.query("period == 'oos'")["t_nw"].notna().sum())
    lines.append(f"daily_25_proxy: {k} pairs portfolio OOS tests (method x entry)")
    n += k
    alpha = 0.05 / n
    crit = norm.ppf(1 - alpha / 2)
    text = "\n".join(["Tests counted over the daily runs only (PREREG.md):", *lines,
                      f"total: {n}", f"Bonferroni: p < 0.05 / {n} = {alpha:.3g}, two-sided |t| > {crit:.2f}",
                      f"market series: {PROXY_LABEL}", ""])
    (OUT / "test_count.txt").write_text(text)
    print(text)
    print(summary.to_string())
    return runs, n, crit


if __name__ == "__main__":
    main()
