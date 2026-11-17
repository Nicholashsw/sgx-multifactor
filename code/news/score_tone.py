"""
Tone of each earnings announcement, for the drift test in results/news_text/PREREG.md.

One row per firm and day 0. All "Announcement of Earnings" records for a firm on the same
day 0 are joined (descriptions, duplicates dropped; the headline stands in when a record
has no description). Only the main test sample is scored: the firm is in the
point-in-time index list on day 0. Returns are never read here.

Two scores, fixed in advance and never fitted to returns:
  lm_tone       Loughran-McDonald Master Dictionary word lists, as shipped in
                pysentiment2 0.1.1: (positive words - negative words) / all words
  finbert_tone  ProsusAI/finbert at revision 0bc2ac10: the average over sentences of
                P(positive) - P(negative)

FinBERT runs on the CPU, the same setup for every chunk. The documents are split
into fixed chunks and each chunk is saved as it finishes, so a stopped run picks up at the
first missing chunk. When every chunk is there they are joined into one file.

Run: python code/news/score_tone.py
"""

import argparse
import hashlib
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pysentiment2
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from _paths import LABELLED, TONE

FINBERT = "ProsusAI/finbert"
REVISION = "0bc2ac10dda6929bcb1f77ccc43c7ec5c424f031"
LM_FILE = Path(pysentiment2.__file__).parent / "static" / "LM.csv"
CHUNK = 400

ap = argparse.ArgumentParser()
ap.add_argument("--minutes", type=float, default=600, help="stop starting new chunks after this long")
args = ap.parse_args()
start = time.time()
parts_dir = TONE.parent / (TONE.stem + "_parts")
parts_dir.mkdir(exist_ok=True)


def build_documents():
    lab = pd.read_parquet(LABELLED, columns=["gvkey", "day0", "in_index", "type", "headline", "description"])
    e = lab[lab.type.eq("Announcement of Earnings") & lab.in_index & lab.day0.notna()].copy()
    text = e.description.fillna("").str.strip()
    e["text"] = text.where(text != "", e.headline.fillna("")).str.replace("_x000d_", " ").str.split().str.join(" ")
    docs = (e.groupby(["gvkey", "day0"])
            .agg(n_records=("text", "size"), text=("text", lambda s: " ".join(dict.fromkeys(s))))
            .reset_index().sort_values(["day0", "gvkey"]).reset_index(drop=True))
    return docs


def lm_scores(texts):
    lm = pd.read_csv(LM_FILE, usecols=["Word", "Negative", "Positive"], keep_default_na=False)
    pos, neg = set(lm.Word[lm.Positive != 0]), set(lm.Word[lm.Negative != 0])
    rows = []
    for t in texts:
        words = re.findall(r"[A-Z]+", t.upper())
        p, n = sum(w in pos for w in words), sum(w in neg for w in words)
        rows.append((len(words), p, n, (p - n) / max(len(words), 1)))
    return pd.DataFrame(rows, columns=["n_words", "lm_pos", "lm_neg", "lm_tone"])


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    keep = [s for s in parts if len(s.split()) >= 4]
    return keep or [text]


def finbert_scores(texts, tok, model, pos_i, neg_i, batch=64):
    """Score every sentence once, in length-sorted batches, then average per document."""
    sents = [(doc, s) for doc, t in enumerate(texts) for s in sentences(t)]
    order = sorted(range(len(sents)), key=lambda i: len(sents[i][1]))
    net = np.empty(len(sents))
    with torch.inference_mode():
        for b in range(0, len(order), batch):
            idx = order[b:b + batch]
            enc = tok([sents[i][1] for i in idx], padding=True, truncation=True, max_length=128, return_tensors="pt")
            p = torch.softmax(model(**enc.to(model.device)).logits, dim=-1).cpu().numpy()
            net[idx] = p[:, pos_i] - p[:, neg_i]
    s = pd.DataFrame({"doc": [d for d, _ in sents], "net": net}).groupby("doc").net.agg(["size", "mean"])
    return s.reindex(range(len(texts))).set_axis(["n_sentences", "finbert_tone"], axis=1).reset_index(drop=True)


docs = build_documents()
n_chunks = -(-len(docs) // CHUNK)
todo = [k for k in range(n_chunks) if not (parts_dir / f"part_{k:03d}.parquet").exists()]
print(f"{len(docs):,} firm-days, {n_chunks} chunks, {len(todo)} left")

if todo:
    device = "cpu"
    tok = AutoTokenizer.from_pretrained(FINBERT, revision=REVISION)
    model = AutoModelForSequenceClassification.from_pretrained(FINBERT, revision=REVISION).eval().to(device)
    print(f"FinBERT on {device}")
    labels = {v.lower(): k for k, v in model.config.id2label.items()}
    for k in todo:
        if time.time() - start > args.minutes * 60:
            break
        chunk = docs.iloc[k * CHUNK:(k + 1) * CHUNK].reset_index(drop=True)
        scored = pd.concat([chunk[["gvkey", "day0", "n_records"]], lm_scores(chunk.text),
                            finbert_scores(chunk.text, tok, model, labels["positive"], labels["negative"])], axis=1)
        scored.to_parquet(parts_dir / f"part_{k:03d}.parquet", index=False)
        print(f"chunk {k + 1}/{n_chunks} saved, {time.time() - start:.0f}s")

done = sorted(parts_dir.glob("part_*.parquet"))
if len(done) == n_chunks:
    tone = pd.concat([pd.read_parquet(p) for p in done], ignore_index=True)
    assert len(tone) == len(docs) and not tone.duplicated(["gvkey", "day0"]).any()
    tone.to_parquet(TONE, index=False)
    lm_hash = hashlib.sha256(LM_FILE.read_bytes()).hexdigest()[:12]
    print(f"done: {len(tone):,} firm-days, LM file sha256 {lm_hash}, FinBERT {REVISION[:8]}")
    print(tone[["lm_tone", "finbert_tone", "n_sentences", "n_words"]].describe().round(3).to_string())
    print(f"corr(lm_tone, finbert_tone) = {tone.lm_tone.corr(tone.finbert_tone):.3f}")
else:
    print(f"{len(done)}/{n_chunks} chunks saved; run again")
