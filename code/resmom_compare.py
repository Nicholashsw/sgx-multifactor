"""
Plain 12-1 momentum against PCA residual momentum, each with three weighting schemes inside
a decile long-short with Markit borrow (results/resmom/PREREG.md).

Both signals rank the same eligible names each month: point-in-time index members on their
last trading day of the formation month, with returns on at least 80% of the PCA window and
both signals defined. Costs are the repository's engine (code/cen/costs.py): Corwin-Schultz
traded-days half-spread and Markit fee from the month before formation, here charged on the
change in weight so they follow each scheme's turnover.

Run: python code/resmom_compare.py           development, holding months 2003-01 to 2019-12
     python code/resmom_compare.py --final   hold-out, once, holding months 2020-01 to 2026-06
Writes results/resmom/comparison_dev.csv or comparison_final.csv (statistics only).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent / "cen"))
from _paths import PANEL, REPO, RETS, SECD  # noqa: E402
from extend import costs_table, nw_t  # noqa: E402

import holdout  # noqa: E402
from residuals import residual_momentum, window  # noqa: E402
from weights import SCHEMES  # noqa: E402

PCA_WINDOW, PCA_K = 252, 3  # trading days in the PCA window, components removed; fixed in PREREG.md
START, END = pd.Timestamp("2003-01-01"), pd.Timestamp("2026-06-30")  # holding months
MIN_COVER, MIN_NAMES, MIN_SHORTS = 0.8, 40, 3
OUT = REPO / "results" / "resmom"


def load(final):
    """Daily returns and membership (dates x SecID) and the monthly panel with costs."""
    ids = pd.read_csv(SECD, usecols=["gvkey", "iid", "prirow", "exchg"], dtype=str)
    ids = ids[(ids.exchg == "251") & (ids.iid == ids.prirow)].drop_duplicates("gvkey")
    secid = dict(zip(ids.gvkey, ids.gvkey.astype(int).astype(str) + "_" + ids.iid))

    d = pd.read_parquet(RETS, columns=["gvkey", "datadate", "ret", "in_index"])
    d = holdout.readable(d[d.datadate <= END], "datadate", final)
    d["SecID"] = d.gvkey.map(secid)
    d = d.dropna(subset=["SecID"])
    rets = d.pivot(index="datadate", columns="SecID", values="ret")
    member = d.pivot(index="datadate", columns="SecID", values="in_index").astype(float)

    p = pd.read_csv(PANEL, usecols=["SecID", "Date", "MOM_12_1", "Return_1M"], parse_dates=["Date"])
    p = holdout.readable(p[p.Date <= END], "Date", final)
    nxt = p[["SecID", "Date", "Return_1M"]].rename(columns={"Return_1M": "next_ret"})
    nxt["Date"] = nxt.Date - pd.offsets.MonthEnd(1)  # calendar join, as canonical_rerun.py
    p = p.merge(nxt, on=["SecID", "Date"], how="left")
    p = costs_table(p, None).drop(columns="cost_month")
    return rets, member, p


def formations(rets, member, p):
    """Per formation date: the eligible names with both signals, and their return window."""
    out = {}
    for d, g in p.groupby("Date"):
        if not START <= d + pd.offsets.MonthEnd(1) <= END:
            continue
        w = window(rets, d, PCA_WINDOW)
        if len(w) < PCA_WINDOW:
            continue
        month = member.loc[d.replace(day=1):d]
        if month.empty:
            continue
        last = month.ffill().iloc[-1]  # each name's flag on its last trading day this month
        names = last.index[last == 1]
        w = w[names]
        w = w.loc[:, (w.notna().mean() >= MIN_COVER) & (w.std() > 0)]
        g = g.drop_duplicates("SecID").set_index("SecID")
        w = w[w.columns.intersection(g.index[g.MOM_12_1.notna()])]
        if w.shape[1] < MIN_NAMES:
            continue
        e = g.loc[w.columns].assign(RESMOM=residual_momentum(w, d, PCA_K)).dropna(subset=["RESMOM"])
        if len(e) < MIN_NAMES:
            continue
        out[d] = (e, w[e.index], g.cs_half_bp_l)
    return out


def book(forms, signal, scheme):
    """Monthly decile long-short; returns one row per holding month."""
    rows, prev = [], (pd.Series(dtype=float), pd.Series(dtype=float))
    for d, (e, w, hs_all) in forms.items():
        e = e.sort_values(signal, ascending=False)
        k = max(5, len(e) // 10)
        lo, sh = e.head(k), e.tail(k)
        sh = sh[sh.avail_l.fillna(0) > 0]
        if len(sh) < MIN_SHORTS:
            continue
        legs = []
        for leg, old in zip((lo, sh), prev):
            wt = SCHEMES[scheme](w[leg.index])
            hs = leg.cs_half_bp_l.fillna(leg.cs_half_bp_l.median())
            r = leg.next_ret.dropna()
            ret = (wt[r.index] * r).sum() / wt[r.index].sum() if len(r) else np.nan
            dw = wt.sub(old, fill_value=0.0).abs()
            cost = (dw * hs_all.reindex(dw.index).fillna(hs.median())).sum() / 1e4
            legs.append(dict(w=wt, ret=ret, cost=cost, to=dw.sum() / 2 if len(old) else np.nan,
                             hs=(wt * hs).sum()))
        L, S = legs
        if np.isnan(L["ret"]) or np.isnan(S["ret"]):
            continue
        fee = (S["w"] * sh.fee_l.fillna(0.0)).sum() / 12
        gross = L["ret"] - S["ret"]
        rows.append({"Date": d + pd.offsets.MonthEnd(1), "gross": gross,
                     "net": gross - L["cost"] - S["cost"] - fee,
                     "turnover": np.nanmean([L["to"], S["to"]]) if len(prev[0]) else np.nan,
                     "n": len(lo) + len(sh), "hold_hs": (L["hs"] + S["hs"]) / 2})
        prev = (L["w"], S["w"])
    return pd.DataFrame(rows).set_index("Date")


def summarise(r):
    def ann(x):
        return ((1 + x).prod() ** (12 / len(x)) - 1) * 100
    c = (1 + r.net).cumprod()
    return {"gross_ann_pct": ann(r.gross), "net_ann_pct": ann(r.net),
            "net_sharpe": r.net.mean() / r.net.std() * np.sqrt(12),
            "net_max_dd_pct": ((c - c.cummax()) / c.cummax()).min() * 100,
            "turnover_ann_pct": r.turnover.mean() * 12 * 100, "avg_holdings": r.n.mean(),
            "avg_hold_half_spread_bp": r.hold_hs.mean(), "months": len(r),
            "first": r.index.min().strftime("%Y-%m"), "last": r.index.max().strftime("%Y-%m")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true", help="report the hold-out (run once)")
    final = ap.parse_args().final
    forms = formations(*load(final))
    table = []
    for scheme in SCHEMES:
        mom = holdout.reported(book(forms, "MOM_12_1", scheme), final)
        res = holdout.reported(book(forms, "RESMOM", scheme), final)
        # the borrow screen skips different months for each signal, so compare on the months both have
        common = mom.index.intersection(res.index)
        diff = res.net[common] - mom.net[common]
        table.append({"signal": "momentum_12_1", "weights": scheme, **summarise(mom)})
        table.append({"signal": "residual_momentum", "weights": scheme, **summarise(res),
                      "common_months": len(common), "net_diff_pct_mo": diff.mean() * 100,
                      "net_diff_nw_t": nw_t(diff, 6)})
    table = pd.DataFrame(table).sort_values("signal", kind="stable").round(2)
    OUT.mkdir(exist_ok=True)
    path = OUT / f"comparison_{'final' if final else 'dev'}.csv"
    table.to_csv(path, index=False)
    print(f"{'HOLD-OUT' if final else 'Development'} | PCA window {PCA_WINDOW} days, {PCA_K} components")
    print("Costs: Corwin-Schultz traded-days half-spread on |change in weight| per leg, "
          "Markit fee on shorts, shorts only in lendable names. Gross = same book before costs.")
    print(table.to_string(index=False))
    print(f"\nSaved {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
