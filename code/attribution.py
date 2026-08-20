"""
Alpha attribution and leakage framework, on the rebuilt real Bloomberg STI panel.

PART 0 states the strategy as an exact rulebook (answering "how is the methodology
executed") and implements it. Everything after is decomposition of THAT run.

Scope honesty: this panel is 30 CURRENT STI members with no delisting returns and no
daily high/low. Therefore per-name Corwin-Schultz spreads, borrow availability, market
impact, and any leg-level survivorship decomposition are NOT computable here.
"""
import datetime
from functools import reduce

import numpy as np
import pandas as pd
from scipy import stats
from openpyxl import load_workbook

pd.set_option("display.width", 230)
WB = "bloombergapi4_fixed.xlsm"
RF_ANN = 0.01412            # MASB3M, single point from the RiskFree sheet (limitation)
RF_M = RF_ANN / 12


def read_block(ws, start_col, metric, stride=3, data_start=4, max_rows=310, max_tickers=30):
    frames = []
    for t in range(max_tickers):
        dcol, vcol = start_col + t * stride, start_col + t * stride + 1
        tick = ws.cell(row=2, column=dcol).value
        if not tick or "SP Equity" not in str(tick):
            break
        dates, vals = [], []
        for r in range(data_start, data_start + max_rows):
            d = ws.cell(row=r, column=dcol).value
            v = ws.cell(row=r, column=vcol).value
            if d is None:
                break
            try:
                d = pd.Timestamp(d) if isinstance(d, (datetime.datetime, datetime.date)) else pd.to_datetime(d)
            except Exception:
                break
            try:
                v = np.nan if (v is None or isinstance(v, str)) else float(v)
            except Exception:
                v = np.nan
            dates.append(d); vals.append(v)
        if dates:
            frames.append(pd.DataFrame({"Date": dates, metric: vals, "Ticker": str(tick).strip()}))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def build_panel(embargo=4):
    wb = load_workbook(WB, data_only=True)
    ws = wb["PriceData"]
    m = reduce(lambda l, r: pd.merge(l, r, on=["Date", "Ticker"], how="outer"),
               [read_block(ws, c, k) for k, c in
                [("PX_LAST", 1), ("TOT_RETURN", 93), ("MKT_CAP_USDmn", 185),
                 ("PB_mo", 277), ("DY_mo", 369), ("PX_VOLUME", 461)]])
    m["Date"] = pd.to_datetime(m["Date"]) + pd.offsets.MonthEnd(0)
    m = m.sort_values(["Ticker", "Date"]).drop_duplicates(["Ticker", "Date"])

    wf = wb["Fundamentals"]
    q = reduce(lambda l, r: pd.merge(l, r, on=["Date", "Ticker"], how="outer"),
               [read_block(wf, c, k, max_rows=110) for k, c in
                [("PE_q", 1), ("ROE_q", 93), ("PB_q", 185)]])
    q["FiscalEnd"] = pd.to_datetime(q["Date"]) + pd.offsets.MonthEnd(0)
    q = q.drop(columns=["Date"]).sort_values(["Ticker", "FiscalEnd"]).drop_duplicates(["Ticker", "FiscalEnd"])
    q["AvailFrom"] = q["FiscalEnd"] + pd.offsets.MonthEnd(embargo)

    parts = []
    for t, p in m.groupby("Ticker"):
        f = q[q.Ticker == t][["AvailFrom", "PE_q", "ROE_q"]].sort_values("AvailFrom")
        p = p.sort_values("Date")
        parts.append(p.assign(PE_q=np.nan, ROE_q=np.nan) if f.empty else
                     pd.merge_asof(p, f, left_on="Date", right_on="AvailFrom",
                                   direction="backward",
                                   tolerance=pd.Timedelta("200D")).drop(columns=["AvailFrom"]))
    p = pd.concat(parts, ignore_index=True)

    wc = wb["Classification"]
    cls = pd.DataFrame([{"Ticker": str(r[0]).strip(), "Sector": r[2]}
                        for r in wc.iter_rows(min_row=2, values_only=True)
                        if r[0] and "SP Equity" in str(r[0])])
    p = p.merge(cls, on="Ticker", how="left")

    b = pd.DataFrame([{"Date": pd.Timestamp(r[0]), "STI": float(r[1])}
                      for r in wb["Benchmark"].iter_rows(min_row=2, values_only=True)
                      if r[0] is not None and r[1] is not None])
    b["Date"] = b["Date"] + pd.offsets.MonthEnd(0)
    b["STI_Ret"] = b["STI"].pct_change()
    p = p.merge(b[["Date", "STI_Ret"]], on="Date", how="left")

    p = p.sort_values(["Ticker", "Date"]).reset_index(drop=True)
    # r_t is the return realised FROM t-1 TO t
    p["Ret"] = p.groupby("Ticker")["TOT_RETURN"].pct_change()
    p["MOM_12_1"] = p.groupby("Ticker")["TOT_RETURN"].pct_change(11).shift(1)
    p["MOM_6_1"] = p.groupby("Ticker")["TOT_RETURN"].pct_change(5).shift(1)
    p["BM"] = 1.0 / p["PB_mo"].clip(lower=0.05)
    p["DY"] = p["DY_mo"]
    p["EY"] = 1.0 / p["PE_q"].where(p["PE_q"] > 0)
    p["ROE"] = p["ROE_q"]
    p["SIZE"] = -np.log(p["MKT_CAP_USDmn"].clip(lower=1))
    p["ADV_USDmn"] = p["PX_VOLUME"] * p["PX_LAST"] / 21 / 1e6 / 1.35   # crude SGD->USD
    p["LIQ"] = np.log(p["ADV_USDmn"].clip(lower=0.01))
    return p


# ============================================================ PART 0: RULEBOOK
WEIGHTS = {"BM": 0.20, "DY": 0.10, "EY": 0.10, "ROE": 0.20,
           "MOM_12_1": 0.15, "MOM_6_1": 0.10, "SIZE": 0.05, "LIQ": 0.10}
N_LONG = N_SHORT = 6
MIN_NAMES = 12
START = "2002-01-31"


def winsor(s, lo=0.01, hi=0.99):
    return s.clip(s.quantile(lo), s.quantile(hi))


def cs_z(s):
    sd = s.std()
    return (s - s.mean()) / sd if sd > 1e-9 else s * 0.0


def score(panel, weights, sector_neutral=False):
    p = panel.copy()
    grp = ["Date", "Sector"] if sector_neutral else ["Date"]
    zc, ws_ = [], []
    for f, w in weights.items():
        raw = p.groupby("Date")[f].transform(winsor)
        p[f"Z_{f}"] = p.assign(_r=raw).groupby(grp)["_r"].transform(cs_z)
        zc.append(f"Z_{f}"); ws_.append(w)
    Z = p[zc]
    W = np.array(ws_)
    avail = Z.notna().to_numpy() * W
    denom = avail.sum(1)
    p["Composite"] = np.where(denom > 0, np.nansum(Z.to_numpy() * W, axis=1) / np.where(denom > 0, denom, 1), np.nan)
    p.loc[denom <= 0, "Composite"] = np.nan
    return p


def run(panel, weights, sector_neutral=False, cost_bps=0.0, universe_filter=None,
        n_long=N_LONG, n_short=N_SHORT):
    """Month-end formation at t; hold t -> t+1; equal weight; monthly full reconstitution."""
    p = score(panel, weights, sector_neutral)
    p = p[p.Date >= START]
    if universe_filter is not None:
        p = p[universe_filter(p)]
    dates = sorted(p.Date.unique())
    ret_map = {d: g.set_index("Ticker")["Ret"] for d, g in p.groupby("Date")}

    rows, contrib, prev_l, prev_s = [], [], set(), set()
    for i, d in enumerate(dates[:-1]):
        cur = p[p.Date == d].dropna(subset=["Composite"])
        if len(cur) < MIN_NAMES:
            rows.append({"Date": dates[i + 1], "Long": RF_M, "Short": np.nan,
                         "LS": np.nan, "Bench": np.nan, "TO_L": 0.0, "Cash": 1})
            prev_l, prev_s = set(), set()
            continue
        cur = cur.sort_values("Composite", ascending=False)
        L = cur.head(n_long)["Ticker"].tolist()
        S = cur.tail(n_short)["Ticker"].tolist()
        nxt = ret_map[dates[i + 1]]

        to_l = len(set(L) - prev_l) / n_long if prev_l else 1.0
        to_s = len(set(S) - prev_s) / n_short if prev_s else 1.0
        cl = to_l * cost_bps / 1e4
        cs_ = to_s * cost_bps / 1e4

        rl = nxt.reindex(L).mean()
        rs = nxt.reindex(S).mean()
        bench = nxt.reindex(cur["Ticker"]).mean()

        for t_, w_ in [(t, 1.0 / n_long) for t in L]:
            contrib.append({"Date": dates[i + 1], "Ticker": t_, "Leg": "Long",
                            "w": w_, "r": nxt.get(t_, np.nan), "c": w_ * nxt.get(t_, np.nan)})
        for t_ in S:
            contrib.append({"Date": dates[i + 1], "Ticker": t_, "Leg": "Short",
                            "w": -1.0 / n_short, "r": nxt.get(t_, np.nan),
                            "c": -nxt.get(t_, np.nan) / n_short})

        rows.append({"Date": dates[i + 1], "Long": rl - cl, "Short": -rs - cs_,
                     "LS": (rl - cl) + (-rs - cs_), "Bench": bench,
                     "TO_L": to_l, "Cash": 0})
        prev_l, prev_s = set(L), set(S)

    res = pd.DataFrame(rows)
    return res, pd.DataFrame(contrib)


def stats_block(r, bench=None, label=""):
    r = r.dropna()
    ex = r - RF_M
    out = {"Strategy": label, "N": len(r),
           "AnnRet%": ((1 + r).prod() ** (12 / len(r)) - 1) * 100,
           "AnnVol%": r.std() * np.sqrt(12) * 100,
           "Sharpe": ex.mean() / r.std() * np.sqrt(12),
           "t(mean)": r.mean() / (r.std() / np.sqrt(len(r))),
           "MaxDD%": ((1 + r).cumprod() / (1 + r).cumprod().cummax() - 1).min() * 100,
           "Hit%": (r > 0).mean() * 100}
    if bench is not None:
        b = bench.reindex(r.index).dropna()
        rr, bb = r.align(b, join="inner")
        X = np.column_stack([np.ones(len(bb)), bb - RF_M])
        beta_hat = np.linalg.lstsq(X, (rr - RF_M).to_numpy(), rcond=None)[0]
        resid = (rr - RF_M).to_numpy() - X @ beta_hat
        se = np.sqrt(np.sum(resid ** 2) / (len(rr) - 2) * np.linalg.inv(X.T @ X)[0, 0])
        out["Alpha%/mo"] = beta_hat[0] * 100
        out["t(alpha)"] = beta_hat[0] / se
        out["Beta"] = beta_hat[1]
    return out


if __name__ == "__main__":
    panel = build_panel(embargo=4)
    print(f"panel {panel.shape} | {panel.Ticker.nunique()} names | "
          f"{panel.Date.min().date()}–{panel.Date.max().date()}")

    print("\n" + "=" * 100)
    print("PART 1  BASE RUN — fully specified rules, gross of costs")
    print("=" * 100)
    res, contrib = run(panel, WEIGHTS, cost_bps=0.0)
    res = res.set_index("Date")
    tbl = pd.DataFrame([
        stats_block(res["Long"], res["Bench"], "Long-only top-6 (gross)"),
        stats_block(res["LS"], res["Bench"], "Long-short 6v6 (gross)"),
        stats_block(res["Bench"], res["Bench"], "Equal-weight universe"),
    ])
    print(tbl.round(3).to_string(index=False))
    print(f"\navg monthly long turnover {res.TO_L.mean():.1%} | "
          f"cash months {int(res.Cash.sum())}")
    res.to_csv("attr_base_returns.csv")
    contrib.to_csv("attr_contributions.csv", index=False)

    print("\n" + "=" * 100)
    print("PART 2  CONTRIBUTION DECOMPOSITION  (w_{t-1} x r_t, sums to portfolio return)")
    print("=" * 100)
    c = contrib.merge(panel[["Date", "Ticker", "Sector", "ADV_USDmn", "MKT_CAP_USDmn"]],
                      on=["Date", "Ticker"], how="left")
    chk = c[c.Leg == "Long"].groupby("Date")["c"].sum()
    print(f"reconciliation: max |sum(contrib) - portfolio ret| = "
          f"{(chk - res['Long'].reindex(chk.index)).abs().max():.2e}")

    for lens, col in [("SECTOR", "Sector")]:
        agg = (c[c.Leg == "Long"].groupby(col)["c"].agg(["sum", "count"]))
        agg["ann_pp"] = agg["sum"] / (len(chk) / 12) * 100
        agg["share%"] = agg["sum"] / agg["sum"].sum() * 100
        agg["name_months"] = agg["count"]
        print(f"\nLong-leg contribution by {lens}:")
        print(agg[["ann_pp", "share%", "name_months"]].sort_values("ann_pp", ascending=False).round(2).to_string())

    top = c[c.Leg == "Long"].groupby("Ticker")["c"].sum().sort_values(ascending=False)
    top_ann = top / (len(chk) / 12) * 100
    print("\nTop-5 / bottom-3 individual contributors (annualised pp):")
    print(pd.concat([top_ann.head(5), top_ann.tail(3)]).round(2).to_string())
    print(f"top 3 names = {top.head(3).sum()/top.sum():.0%} of total long-leg P&L")

    print("\n" + "=" * 100)
    print("PART 3  LEAVE-ONE-FACTOR-OUT")
    print("=" * 100)
    full = res["Long"].dropna()
    rows = []
    for f in WEIGHTS:
        w2 = {k: v for k, v in WEIGHTS.items() if k != f}
        r2, _ = run(panel, w2, cost_bps=0.0)
        r2 = r2.set_index("Date")["Long"]
        a, b = full.align(r2, join="inner")
        d = a - b
        rows.append({"Dropped": f, "Weight": WEIGHTS[f],
                     "AnnRet_without%": ((1 + b).prod() ** (12 / len(b)) - 1) * 100,
                     "Delta_ann_pp": ((1 + a).prod() ** (12 / len(a)) - 1) * 100
                                     - ((1 + b).prod() ** (12 / len(b)) - 1) * 100,
                     "Sharpe_without": (b.mean() - RF_M) / b.std() * np.sqrt(12),
                     "t(diff)": stats.ttest_1samp(d.dropna(), 0).statistic})
    lofo = pd.DataFrame(rows).sort_values("Delta_ann_pp", ascending=False)
    print(f"full-strategy ann return {((1+full).prod()**(12/len(full))-1)*100:.2f}%  "
          f"Sharpe {(full.mean()-RF_M)/full.std()*np.sqrt(12):.3f}")
    print(lofo.round(3).to_string(index=False))
    lofo.to_csv("attr_lofo.csv", index=False)

    # ============================================================ PART 4 REGIMES
    print("\n" + "=" * 100)
    print("PART 4  REGIME CONDITIONING  (regimes defined from macro data BEFORE inspecting P&L)")
    print("=" * 100)
    mac = pd.read_csv("macro_monthly.csv", parse_dates=["Date"])
    mac["Date"] = mac["Date"] + pd.offsets.MonthEnd(0)
    mac = mac[["Date", "SG_SGS_10Y", "VIX", "SG_PMI"]].drop_duplicates("Date").sort_values("Date")
    mac["RatesRising"] = (mac["SG_SGS_10Y"].diff(3) > 0).astype(int)
    mac["HighRate"] = (mac["SG_SGS_10Y"] >
                       mac["SG_SGS_10Y"].rolling(60, min_periods=36).median()).astype(int)
    mac["HighVol"] = (mac["VIX"] > 20).astype(int)
    mac["Expansion"] = (mac["SG_PMI"] > 50).astype(int)
    R = res.reset_index().merge(mac, on="Date", how="left").set_index("Date")

    rows = []
    for rg in ["RatesRising", "HighRate", "HighVol", "Expansion"]:
        for v in (0, 1):
            msk = R[rg] == v
            for lbl, col in [("LongOnly", "Long"), ("LongShort", "LS")]:
                s = R.loc[msk, col].dropna()
                b = R.loc[msk, "Bench"].dropna()
                if len(s) < 24:
                    continue
                a, bb = s.align(b, join="inner")
                rows.append({"Regime": f"{rg}={v}", "Book": lbl, "N": len(a),
                             "AnnRet%": a.mean() * 12 * 100,
                             "Sharpe": (a.mean() - RF_M) / a.std() * np.sqrt(12),
                             "vs_EW_pp": (a.mean() - bb.mean()) * 12 * 100,
                             "t(active)": stats.ttest_1samp((a - bb).dropna(), 0).statistic})
    reg = pd.DataFrame(rows)
    print(reg.round(3).to_string(index=False))
    reg.to_csv("attr_regimes.csv", index=False)

    print("\nSector contribution conditional on the rate regime (long leg, annualised pp):")
    cc = c[c.Leg == "Long"].merge(mac[["Date", "HighRate", "RatesRising"]], on="Date", how="left")
    for rg in ["RatesRising"]:
        piv = cc.pivot_table(index="Sector", columns=rg, values="c", aggfunc="sum")
        cnt = cc.groupby(rg)["Date"].nunique()
        for v in piv.columns:
            piv[v] = piv[v] / (cnt[v] / 12) * 100
        piv.columns = [f"{rg}={int(v)}" for v in piv.columns]
        print(piv.round(2).sort_values(piv.columns[-1], ascending=False).to_string())

    # ============================================================ PART 5 FUNNEL
    print("\n" + "=" * 100)
    print("PART 5  ALPHA LEAKAGE FUNNEL")
    print("=" * 100)

    def quintile_spread(pnl_panel, weights, embargo_panel=None):
        p = score(embargo_panel if embargo_panel is not None else pnl_panel, weights)
        p = p[p.Date >= START].dropna(subset=["Composite", "Ret"])
        out = {}
        for d, g in p.groupby("Date"):
            if len(g) < 15:
                continue
            g = g.assign(Q=pd.qcut(g["Composite"], 5, labels=[1, 2, 3, 4, 5], duplicates="drop"))
            mm = g.groupby("Q", observed=True)["Ret"].mean()
            if 5 in mm.index and 1 in mm.index:
                out[d] = mm[5] - mm[1]
        return pd.Series(out)

    panel_L0 = build_panel(embargo=0)
    stages = []

    s = quintile_spread(None, WEIGHTS, embargo_panel=panel_L0).shift(-1).dropna()
    stages.append(("1. Raw quintile spread, no reporting lag", s))
    s = quintile_spread(None, WEIGHTS, embargo_panel=panel).shift(-1).dropna()
    stages.append(("2. + 4-month fundamental embargo", s))
    stages.append(("3. + concentration to top-6 vs bottom-6", res["LS"].dropna()))
    rsn, _ = run(panel, WEIGHTS, sector_neutral=True, cost_bps=0.0)
    stages.append(("4. + sector-neutral scoring", rsn.set_index("Date")["LS"].dropna()))
    for cb in (20, 40, 60):
        rc, _ = run(panel, WEIGHTS, sector_neutral=True, cost_bps=cb)
        stages.append((f"5. + {cb}bp one-way costs", rc.set_index("Date")["LS"].dropna()))

    def liq_filter(p):
        thr = p.groupby("Date")["ADV_USDmn"].transform(lambda x: x.quantile(0.33))
        return p["ADV_USDmn"] >= thr
    rl, _ = run(panel, WEIGHTS, sector_neutral=True, cost_bps=40,
                universe_filter=liq_filter, n_long=5, n_short=5)
    stages.append(("6. + drop illiquid third, 40bp", rl.set_index("Date")["LS"].dropna()))

    frows = []
    for lbl, s in stages:
        s = s.dropna()
        frows.append({"Stage": lbl, "N": len(s), "Mean%/mo": s.mean() * 100,
                      "AnnVol%": s.std() * np.sqrt(12) * 100,
                      "Sharpe": s.mean() / s.std() * np.sqrt(12),
                      "t": s.mean() / (s.std() / np.sqrt(len(s)))})
    fun = pd.DataFrame(frows)
    fun["Leak_pp/mo"] = fun["Mean%/mo"].diff()
    print(fun.round(3).to_string(index=False))
    fun.to_csv("attr_funnel.csv", index=False)
    print("\nNOT COMPUTABLE on this panel: per-name Corwin-Schultz spreads (no daily high/low),")
    print("market impact/capacity, borrow availability and fee, delisting returns.")

    # ============================================================ PART 6 REPEAT
    print("\n" + "=" * 100)
    print("PART 6  REPEATABILITY")
    print("=" * 100)
    L = res["Long"].dropna(); B = res["Bench"].reindex(L.index)
    act = (L - B).dropna()

    subs = [("2002-2013", act[:"2013-12-31"]), ("2014-2026", act["2014-01-01":]),
            ("pre-COVID (<2020-02)", act[:"2020-01-31"]), ("2020-02 onward", act["2020-02-01":])]
    rows = [{"Sample": k, "N": len(v), "Active_pp/yr": v.mean() * 12 * 100,
             "t": stats.ttest_1samp(v, 0).statistic} for k, v in subs]
    print(pd.DataFrame(rows).round(3).to_string(index=False))

    print("\nLeave-one-sector-out (sector removed from the eligible universe):")
    rows = []
    for sec in panel.Sector.dropna().unique():
        if panel[panel.Sector == sec].Ticker.nunique() < 2:
            continue
        rs, _ = run(panel[panel.Sector != sec], WEIGHTS, cost_bps=0.0)
        rs = rs.set_index("Date")
        a = (rs["Long"] - rs["Bench"]).dropna()
        rows.append({"Removed": sec, "Active_pp/yr": a.mean() * 12 * 100,
                     "t": stats.ttest_1samp(a, 0).statistic,
                     "Sharpe": (rs["Long"].dropna().mean() - RF_M) / rs["Long"].dropna().std() * np.sqrt(12)})
    print(pd.DataFrame(rows).sort_values("Active_pp/yr").round(3).to_string(index=False))

    print("\nLeave-top-contributors-out:")
    rows = []
    for k in (1, 3, 5):
        drop = top.head(k).index.tolist()
        rs, _ = run(panel[~panel.Ticker.isin(drop)], WEIGHTS, cost_bps=0.0)
        rs = rs.set_index("Date")
        a = (rs["Long"] - rs["Bench"]).dropna()
        rows.append({"Dropped": f"top {k}", "Names": ", ".join(x.split()[0] for x in drop),
                     "Active_pp/yr": a.mean() * 12 * 100,
                     "t": stats.ttest_1samp(a, 0).statistic})
    print(pd.DataFrame(rows).round(3).to_string(index=False))

    roll = act.rolling(60).mean() * 12 * 100
    print(f"\nrolling 60m active return: min {roll.min():.2f}pp  max {roll.max():.2f}pp  "
          f"share of windows > 0: {(roll.dropna() > 0).mean():.0%}")
    roll.to_csv("attr_rolling.csv")
