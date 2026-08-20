"""PIT panel builder for the ACTUAL SGX3_2.xlsm schema.

Sheets present: Universe_PIT (Ticker, FirstSeen, LastSeen, DelistDate[unpopulated]),
PriceData_PIT (Date, Ticker, PX_LAST, TOT_RET_IDX, MKT_CAP, PX_TO_BOOK, DIV_YIELD,
PX_VOLUME), Fundamentals_PIT (Date, Ticker, PE_RATIO, ROE, DEBT_TO_EQ, PX_TO_BOOK_Q).

No Classification or Benchmark sheet, so sectors come from two sources (audited below)
and the STI benchmark from bloombergapi4_fixed.xlsm.
"""
import numpy as np
import pandas as pd
from openpyxl import load_workbook

GICS = {10: "Energy", 15: "Materials", 20: "Industrials", 25: "Consumer Discretionary",
        30: "Consumer Staples", 35: "Health Care", 40: "Financials",
        45: "Information Technology", 50: "Communication Services", 55: "Utilities",
        60: "Real Estate"}

# Compustat conm for tickers absent from the Bloomberg Classification sheet.
# The ticker->company link is public knowledge; the SECTOR itself is read from
# Compustat Global Fundamentals Annual (fic=SGP), not assigned by hand.
CS_LINK = {
    "CAPL": "CAPITALAND LTD", "CCT": "CAPITALAND COMMERCIAL TRUST",
    "CD": "COMFORTDELGRO CORP LTD", "CMA": "CAPITAMALLS ASIA LTD",
    "COS": "COSCO SHIPPING INTL (SGP)", "FNN": "FRASER & NEAVE LTD",
    "GLP": "GLOBAL LOGISTIC PROPERTIES", "HPHT": "HUTCHISON PORT HLDGS TRUST",
    "JCNC": "JARDINE CYCLE & CARRIAGE LTD", "KPLD": "KEPPEL LAND LTD",
    "MRT": "MAPLETREE PAN ASIA", "NOL": "NEPTUNE ORIENT LINES LTD",
    "OLAM": "OLAM GROUP LTD", "OLAMR": "OLAM GROUP LTD",
    "SIE": "SIA ENGINEERING CO LTD", "SPH": "SINGAPORE PRESS HOLDINGS LTD",
    "STH": "STARHUB LTD", "YLLG": "YANLORD LAND GROUP LTD",
}
# Compustat's gsector is a pre-2016 GICS vintage that filed property trusts under
# Financials. Bloomberg's sheet uses the current vintage. Overridden for consistency,
# printed in the audit so the change is visible.
VINTAGE_FIX = {"CMA SP Equity": "Real Estate", "KPLD SP Equity": "Real Estate"}


def read_sheet(wb, name, cols):
    ws = wb[name]
    n = len(cols)
    data = [r[:n] for r in ws.iter_rows(min_row=2, values_only=True) if r[0] is not None]
    df = pd.DataFrame(data, columns=cols)
    if "Date" in cols:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])
    for c in cols:
        if c in ("Date", "Ticker", "Sector"):
            continue
        df[c] = pd.to_numeric(
            df[c].apply(lambda v: np.nan if isinstance(v, str) and "#" in v else v),
            errors="coerce")
    return df


def build_sector_map(verbose=True):
    wb2 = load_workbook("bloombergapi4_fixed.xlsm", data_only=True, read_only=True)
    bbg = {str(r[0]).strip(): r[2]
           for r in wb2["Classification"].iter_rows(min_row=2, values_only=True)
           if r[0] and "SP Equity" in str(r[0])}
    cs = pd.read_csv("cs_sector_map.csv")
    cs["sec"] = cs.gsector.map(lambda x: GICS.get(int(x)) if pd.notna(x) else None)
    lut = cs.set_index("conm")["sec"].to_dict()

    out, audit = dict(bbg), []
    for tk, conm in CS_LINK.items():
        full = f"{tk} SP Equity"
        if full in out:
            continue
        sec = lut.get(conm)
        if sec:
            out[full] = sec
            audit.append({"Ticker": full, "source": "Compustat", "conm": conm, "Sector": sec})
    for tk, sec in VINTAGE_FIX.items():
        if tk in out:
            audit.append({"Ticker": tk, "source": "GICS-vintage override",
                          "conm": CS_LINK.get(tk.split()[0], ""),
                          "Sector": f"{out[tk]} -> {sec}"})
            out[tk] = sec
    if verbose and audit:
        print("sector map audit (names not in the Bloomberg sheet):")
        print(pd.DataFrame(audit).to_string(index=False))
    return out


def truncate_padding(px, tol=1e-9):
    """Bloomberg pads a dead ticker's last price forward. Cut at the last real move."""
    keep, log = [], []
    for t, g in px.sort_values("Date").groupby("Ticker"):
        v = g["PX_LAST"].to_numpy(float)
        moved = np.where(np.abs(np.diff(v)) > tol)[0]
        last = (moved[-1] + 1) if len(moved) else len(g) - 1
        if len(g) - 1 - last > 0:
            log.append({"Ticker": t, "padded_months": len(g) - 1 - last,
                        "true_last": g["Date"].iloc[last].date()})
        keep.append(g.iloc[:last + 1])
    return pd.concat(keep, ignore_index=True), pd.DataFrame(log)


def build_pit(embargo=4, delist="truncate", start="2008-03-31", verbose=True):
    wb = load_workbook("SGX3_2.xlsm", data_only=True, read_only=True)
    px = read_sheet(wb, "PriceData_PIT",
                    ["Date", "Ticker", "PX_LAST", "TOT_RETURN", "MKT_CAP_USDmn",
                     "PB_mo", "DY_mo", "PX_VOLUME"])
    fn = read_sheet(wb, "Fundamentals_PIT",
                    ["Date", "Ticker", "PE_q", "ROE_q", "DEBT_TO_EQ", "PB_q"])
    mem = pd.DataFrame([{"Ticker": str(r[0]).strip(),
                         "First": pd.to_datetime(r[1]), "Last": pd.to_datetime(r[2])}
                        for r in wb["Universe_PIT"].iter_rows(min_row=2, values_only=True)
                        if r[0] and "SP" in str(r[0])])

    wbb = load_workbook("bloombergapi4_fixed.xlsm", data_only=True, read_only=True)
    bm = pd.DataFrame([{"Date": pd.Timestamp(r[0]), "STI": float(r[1])}
                       for r in wbb["Benchmark"].iter_rows(min_row=2, values_only=True)
                       if r[0] is not None and r[1] is not None])
    bm["Date"] = bm["Date"] + pd.offsets.MonthEnd(0)
    bm = bm.sort_values("Date")
    bm["STI_Ret"] = bm["STI"].pct_change()

    for d in (px, fn):
        d["Date"] = d["Date"] + pd.offsets.MonthEnd(0)
        d["Ticker"] = d["Ticker"].astype(str).str.strip()
    px = px.sort_values(["Ticker", "Date"]).drop_duplicates(["Ticker", "Date"])
    fn = fn.sort_values(["Ticker", "Date"]).drop_duplicates(["Ticker", "Date"])

    px, padlog = truncate_padding(px)
    if verbose:
        print(f"padding truncated: {len(padlog)} tickers, "
              f"{int(padlog.padded_months.sum()) if len(padlog) else 0} name-months removed")

    fn["AvailFrom"] = fn["Date"] + pd.offsets.MonthEnd(embargo)
    parts = []
    for t, p in px.groupby("Ticker"):
        f = fn[fn.Ticker == t][["AvailFrom", "PE_q", "ROE_q", "PB_q"]].sort_values("AvailFrom")
        p = p.sort_values("Date")
        parts.append(p.assign(PE_q=np.nan, ROE_q=np.nan, PB_q=np.nan) if f.empty else
                     pd.merge_asof(p, f, left_on="Date", right_on="AvailFrom",
                                   direction="backward",
                                   tolerance=pd.Timedelta("200D")).drop(columns=["AvailFrom"]))
    p = pd.concat(parts, ignore_index=True)

    secmap = build_sector_map(verbose=verbose)
    p["Sector"] = p["Ticker"].map(secmap).fillna("Unclassified")
    if verbose:
        unk = sorted(p.loc[p.Sector == "Unclassified", "Ticker"].unique())
        print(f"unclassified sector: {len(unk)} names -> {', '.join(x.split()[0] for x in unk)}")

    p = p.sort_values(["Ticker", "Date"]).reset_index(drop=True)
    p["Ret"] = p.groupby("Ticker")["TOT_RETURN"].pct_change()

    # delisting return on the terminal month of any name dying before sample end
    sample_end = p["Date"].max()
    last_obs = p.groupby("Ticker")["Date"].transform("max")
    dead = last_obs < sample_end - pd.offsets.MonthEnd(1)
    terminal = dead & (p["Date"] == last_obs)
    n_dead = p.loc[terminal, "Ticker"].nunique()
    if delist == "minus100":
        p.loc[terminal, "Ret"] = -1.00
    elif delist == "truncate":
        p = p[~terminal]
    if verbose:
        print(f"delisting convention '{delist}' applied to {n_dead} terminal name-months")

    mem["First"] = mem["First"] + pd.offsets.MonthEnd(-1)
    mem["Last"] = mem["Last"] + pd.offsets.MonthEnd(0)
    p = p.merge(mem, on="Ticker", how="left")
    before = len(p)
    p = p[(p["Date"] >= p["First"]) & (p["Date"] <= p["Last"])]
    if verbose:
        print(f"PIT membership filter: {before:,} -> {len(p):,} name-months")

    p = p.sort_values(["Ticker", "Date"]).reset_index(drop=True)
    p["MOM_12_1"] = p.groupby("Ticker")["TOT_RETURN"].pct_change(11).shift(1)
    p["MOM_6_1"] = p.groupby("Ticker")["TOT_RETURN"].pct_change(5).shift(1)
    p["BM"] = 1.0 / p["PB_mo"].clip(lower=0.05)
    p["DY"] = p["DY_mo"]
    p["EY"] = 1.0 / p["PE_q"].where(p["PE_q"] > 0)
    p["ROE"] = p["ROE_q"]
    p["SIZE"] = -np.log(p["MKT_CAP_USDmn"].clip(lower=1))
    p["ADV_USDmn"] = p["PX_VOLUME"] * p["PX_LAST"] / 21 / 1e6 / 1.35
    p["LIQ"] = np.log(p["ADV_USDmn"].clip(lower=0.01))
    p = p.merge(bm[["Date", "STI_Ret"]], on="Date", how="left")
    p = p[p["Date"] >= start]
    if verbose:
        print(f"PIT panel: {len(p):,} rows | {p.Ticker.nunique()} names | "
              f"{p.Date.min().date()}-{p.Date.max().date()} | "
              f"median {p.groupby('Date').size().median():.0f} names/month")
    return p, padlog
