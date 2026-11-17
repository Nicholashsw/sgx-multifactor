"""
Match Capital IQ Key Developments firms to Compustat gvkeys.

The extract carries SGX tickers and names but no Capital IQ company id, so the WRDS
gvkey link cannot be joined. Names are matched instead, then checked against
dividends: a Capital IQ firm's ex-dividend dates should fall on days Compustat shows
a dividend going ex for the matched gvkey.

Reads the Key Developments extract and the outputs of daily_returns.py (paths in
_paths.py). Writes derived_sgx_keydev_gvkey_map_static.csv, one row per Capital IQ firm,
with a status column:
  dividends  at least 5 ex-dividend dates inside the Compustat window, 60% or more hit
             a Compustat ex-dividend day within 3 days
  name       exact cleaned-name match with overlapping dates, and no clear dividend
             contradiction (fewer than 5 dates to check, or at least 30% hit)
  rejected   enough dividends to check, and either under 30% hit or under 60% hit
             without an exact name
  weak       anything else
Only dividends and name go into the tests.

Run: python code/news/match_firms.py
"""

import re

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process

from _paths import DIVS, KEYDEV, MAP, RETS

ABBR = {"HLDGS": "HOLDINGS", "HLDG": "HOLDING", "INTL": "INTERNATIONAL", "GRP": "GROUP", "CORP": "CORPORATION",
        "TECH": "TECHNOLOGY", "TECHNOLOGIES": "TECHNOLOGY", "IND": "INDUSTRIES", "INDS": "INDUSTRIES",
        "DEV": "DEVELOPMENT", "ENGRG": "ENGINEERING", "ENGR": "ENGINEERING", "MGMT": "MANAGEMENT",
        "INVT": "INVESTMENT", "INVTS": "INVESTMENTS", "SVCS": "SERVICES", "SVC": "SERVICE", "RES": "RESOURCES",
        "PPTY": "PROPERTY", "PPTYS": "PROPERTIES", "PROP": "PROPERTIES", "MFG": "MANUFACTURING",
        "ELEC": "ELECTRONICS", "COMM": "COMMUNICATIONS", "SING": "SINGAPORE", "S'PORE": "SINGAPORE"}
DROP = {"LTD", "LIMITED", "PTE", "PLC", "INC", "THE", "CO", "COMPANY", "SA", "NV", "BHD", "BERHAD",
        "CORPORATION", "HOLDINGS", "HOLDING", "GROUP", "S", "SPORE", "SINGAPORE"}


def clean(name):
    s = name.upper().replace("&", " AND ").replace("REAL ESTATE INVESTMENT TRUST", "REIT")
    words = [ABBR.get(w, w) for w in re.sub(r"[^A-Z0-9' ]", " ", s).split()]
    return " ".join([w for w in words if w not in DROP] or words)


def similarity(a, b, **_):
    partial = fuzz.partial_ratio(a, b) if len(b) >= 12 and a[:6] == b[:6] else 0
    return max(fuzz.token_sort_ratio(a, b), partial)


kd = pd.read_parquet(KEYDEV, columns=["date", "type", "sgx_ticker", "sgx_company"]).dropna(subset=["sgx_company"])
kd["day"] = kd.date.dt.normalize()
ciq = kd.groupby(["sgx_ticker", "sgx_company"]).day.agg(["min", "max", "size"]).reset_index()
exdiv = kd[kd.type.str.startswith("Ex-Dividend")].groupby(["sgx_ticker", "sgx_company"]).day.apply(np.unique)

rets = pd.read_parquet(RETS, columns=["gvkey", "conm", "datadate"])
cs = rets.groupby("gvkey").agg(conm=("conm", "last"), min=("datadate", "min"), max=("datadate", "max")).reset_index()
cs["clean"] = cs.conm.map(clean)
divs = pd.read_parquet(DIVS).groupby("gvkey").datadate.apply(lambda s: np.sort(s.values))


def dividend_hits(ciq_dates, gvkey, start, end):
    """Share of Capital IQ ex-dividend dates inside the Compustat window that hit a
    Compustat ex-dividend day within 3 days, and how many dates were checked."""
    ciq_dates = ciq_dates[(ciq_dates >= start) & (ciq_dates <= end)]
    cs_dates = divs.get(gvkey)
    if cs_dates is None or len(ciq_dates) == 0:
        return 0.0, len(ciq_dates)
    i = np.clip(np.searchsorted(cs_dates, ciq_dates), 1, len(cs_dates) - 1)
    gap = np.minimum(abs(cs_dates[i] - ciq_dates), abs(cs_dates[i - 1] - ciq_dates))
    return float(np.mean(gap <= np.timedelta64(3, "D"))), len(ciq_dates)


rows = []
for r in ciq.itertuples(index=False):
    name = clean(r.sgx_company)
    ex = exdiv.get((r.sgx_ticker, r.sgx_company), np.array([], dtype="datetime64[ns]"))
    for _, score, i in process.extract(name, cs.clean.tolist(), scorer=similarity, limit=3):
        c = cs.iloc[i]
        overlap = (min(r.max, c["max"]) - max(r.min, c["min"])).days > 0
        hit, n_ex = dividend_hits(ex, c.gvkey, c["min"].to_datetime64(), c["max"].to_datetime64())
        rows.append((r.sgx_ticker, r.sgx_company, r.size, c.gvkey, c.conm, score, overlap,
                     n_ex, hit, name == c.clean))
m = pd.DataFrame(rows, columns=["sgx_ticker", "sgx_company", "n_events", "gvkey", "conm", "score",
                                "overlap", "n_exdiv", "div_hit", "exact"])

checkable = m.n_exdiv >= 5
m["status"] = np.select(
    [checkable & (m.div_hit >= 0.6) & m.overlap,
     m.exact & m.overlap & ~(checkable & (m.div_hit < 0.3)),
     checkable & ((m.div_hit < 0.3) | ~m.exact)],
    ["dividends", "name", "rejected"], default="weak")
rank = m.status.map({"dividends": 0, "name": 1, "weak": 2, "rejected": 3})
best = (m.assign(rank=rank).sort_values(["rank", "div_hit", "score"], ascending=[True, False, False])
        .drop_duplicates(["sgx_ticker", "sgx_company"]).drop(columns="rank"))
best.to_csv(MAP, index=False)

summary = best.groupby("status").agg(firms=("sgx_ticker", "size"), events=("n_events", "sum"))
print(summary.to_string())
kept = best[best.status.isin(["dividends", "name"])]
print(f"kept {len(kept)} firms, {kept.gvkey.nunique()} gvkeys, {kept.n_events.sum():,} events")
dupes = kept[kept.gvkey.duplicated(keep=False)].sort_values("gvkey")
print(f"gvkeys claimed by more than one Capital IQ firm: {dupes.gvkey.nunique()}")
