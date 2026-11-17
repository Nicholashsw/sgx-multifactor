"""
Does each tone score track the earnings news in the same text? A measurement check
before any return test (results/news_text/PREREG.md).

Net income now and a year ago are parsed from each firm-day's joined text with the
regex of the old TF-IDF baseline (src/data/capiq_keydev_build/baseline.py, commit
ae2a169). The change is (now - year ago) / |year ago|, clipped to [-5, 5]. Reported by
year and overall: Spearman correlation of lm_tone and finbert_tone with the sign and the
size of that change, corr(lm_tone, finbert_tone), and the share of firm-days parsed.

Reads only the tone file and the text columns of the labelled events; no returns.
Writes results/news_text/tone_validity.csv (counts and correlations only).

Run: python code/news/check_tone.py
"""

import re

import numpy as np
import pandas as pd

from _paths import LABELLED, RESULTS, TONE

UNIT = {"thousand": 1e3, "million": 1e6, "billion": 1e9}
AMT = r"(?:[A-Z]{3}\s?)?(-?\d[\d,]*(?:\.\d+)?)\s*(thousand|million|billion)?"
NI = re.compile(r"net (income|profit|loss)[^.]{0,80}?(?:was|of|at)?\s*" + AMT
                + r"[^.]{0,60}?(?:compared to|against|from|versus)[^.]{0,40}?" + AMT, re.I)


def ni_change(t):
    m = NI.search(t)
    if not m:
        return np.nan
    try:
        a = float(m.group(2).replace(",", "")) * UNIT.get((m.group(3) or "").lower(), 1)
        b = float(m.group(4).replace(",", "")) * UNIT.get((m.group(5) or "").lower(), 1)
    except ValueError:
        return np.nan
    if m.group(1).lower() == "loss":
        a = -abs(a)
    if b == 0:
        return np.nan
    return np.clip((a - b) / abs(b), -5, 5)


# Same documents as score_tone.py
lab = pd.read_parquet(LABELLED, columns=["gvkey", "day0", "in_index", "type", "headline", "description"])
e = lab[lab.type.eq("Announcement of Earnings") & lab.in_index & lab.day0.notna()].copy()
text = e.description.fillna("").str.strip()
e["text"] = text.where(text != "", e.headline.fillna("")).str.replace("_x000d_", " ").str.split().str.join(" ")
docs = e.groupby(["gvkey", "day0"]).text.agg(lambda s: " ".join(dict.fromkeys(s))).reset_index()

tone = pd.read_parquet(TONE, columns=["gvkey", "day0", "lm_tone", "finbert_tone"])
d = tone.merge(docs, on=["gvkey", "day0"], how="left", validate="one_to_one")
assert d.text.notna().all()
d["ni_chg"] = d.text.map(ni_change)
d["ni_sign"] = np.sign(d.ni_chg)
d["year"] = d.day0.dt.year


def spearman(a, b):
    ok = a.notna() & b.notna()
    return a[ok].rank().corr(b[ok].rank()) if ok.sum() > 2 else np.nan


def row(g):
    return pd.Series({
        "firm_days": len(g),
        "parsed": int(g.ni_chg.notna().sum()),
        "parsed_share": g.ni_chg.notna().mean(),
        "lm_vs_sign": spearman(g.lm_tone, g.ni_sign),
        "lm_vs_size": spearman(g.lm_tone, g.ni_chg),
        "finbert_vs_sign": spearman(g.finbert_tone, g.ni_sign),
        "finbert_vs_size": spearman(g.finbert_tone, g.ni_chg),
        "lm_vs_finbert": g.lm_tone.corr(g.finbert_tone),
    })


out = pd.concat([d.groupby("year").apply(row, include_groups=False),
                 row(d).to_frame("all").T]).rename_axis("year").reset_index()
out[["firm_days", "parsed"]] = out[["firm_days", "parsed"]].astype(int)
out = out.round(3)
out.to_csv(RESULTS / "tone_validity.csv", index=False)
print(out.to_string(index=False))
