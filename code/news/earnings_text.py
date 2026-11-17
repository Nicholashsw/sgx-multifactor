"""Earnings-announcement text per firm-day and the net-income change parsed from it.

Shared by check_tone.py and drift_test.py. The documents are built as in score_tone.py;
the regex is the one of the old TF-IDF baseline (src/data/capiq_keydev_build/baseline.py,
commit ae2a169). Reads no returns.
"""

import re

import numpy as np
import pandas as pd

from _paths import LABELLED

UNIT = {"thousand": 1e3, "million": 1e6, "billion": 1e9}
AMT = r"(?:[A-Z]{3}\s?)?(-?\d[\d,]*(?:\.\d+)?)\s*(thousand|million|billion)?"
NI = re.compile(r"net (income|profit|loss)[^.]{0,80}?(?:was|of|at)?\s*" + AMT
                + r"[^.]{0,60}?(?:compared to|against|from|versus)[^.]{0,40}?" + AMT, re.I)


def ni_change(t):
    """(net income now - a year ago) / |a year ago|, clipped to [-5, 5]; NaN if not parsed."""
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


def documents():
    """One row per index earnings firm-day: gvkey, day0, text (same as score_tone.py)."""
    lab = pd.read_parquet(LABELLED, columns=["gvkey", "day0", "in_index", "type", "headline", "description"])
    e = lab[lab.type.eq("Announcement of Earnings") & lab.in_index & lab.day0.notna()].copy()
    text = e.description.fillna("").str.strip()
    e["text"] = text.where(text != "", e.headline.fillna("")).str.replace("_x000d_", " ").str.split().str.join(" ")
    return e.groupby(["gvkey", "day0"]).text.agg(lambda s: " ".join(dict.fromkeys(s))).reset_index()
