"""
Diagnostic for plain 12-1 momentum in the hold-out (holding months 2020-01 to 2026-06).
Changes no scored number: it rebuilds the books of resmom_compare.py and checks that each
month's gross return matches book() before using them.

Equal weight: the 5 best and 5 worst months by net return, each leg's return, and what drove
them, in aggregate. All three schemes: net Sharpe with and without 2020-03 to 2020-12.
The names that contributed most go to holdout_diagnostic_names.md, which is gitignored:
single-stock returns are licensed vendor data and are not published.

Run: python code/resmom_diagnostic.py    writes results/resmom/holdout_diagnostic.md and
                                         results/resmom/holdout_diagnostic_names.md (local)
"""
import sys

import numpy as np
import pandas as pd

import holdout
import resmom_compare as rc
from weights import SCHEMES

EXCLUDE = (pd.Timestamp("2020-03-01"), pd.Timestamp("2020-12-31"))


def legs(forms, scheme):
    """Per holding month: each name's leg, weight, return and contribution to the long-short."""
    rows = []
    for d, (e, w, _) in forms.items():
        e = e.sort_values("MOM_12_1", ascending=False)
        k = max(5, len(e) // 10)
        lo, sh = e.head(k), e.tail(k)
        sh = sh[sh.avail_l.fillna(0) > 0]
        if len(sh) < rc.MIN_SHORTS:
            continue
        for name, leg, sign in (("long", lo, 1), ("short", sh, -1)):
            wt = SCHEMES[scheme](w[leg.index])
            r = leg.next_ret.dropna()
            wt = wt[r.index] / wt[r.index].sum()
            rows += [{"Date": d + pd.offsets.MonthEnd(1), "leg": name, "SecID": s,
                      "w": wt[s], "ret": r[s], "contrib": sign * wt[s] * r[s]} for s in r.index]
    return pd.DataFrame(rows)


def sharpe(x):
    return x.mean() / x.std() * np.sqrt(12)


def main():
    rets, member, p = rc.load(final=True)
    forms = rc.formations(rets, member, p)
    names = pd.read_csv(rc.PANEL, usecols=["SecID", "conm"]).drop_duplicates("SecID").set_index("SecID").conm

    out = ["# Hold-out diagnostic: plain 12-1 momentum, 2020-01 to 2026-06", "",
           "Diagnostic only, written after the hold-out was scored (PREREG.md). Nothing here changes "
           "a scored number. Code: `code/resmom_diagnostic.py`.", ""]

    books = {s: holdout.reported(rc.book(forms, "MOM_12_1", s), True) for s in SCHEMES}
    b = books["equal"]
    c = legs(forms, "equal")
    c = c[c.Date >= holdout.START]
    lr = c.groupby(["Date", "leg"]).apply(lambda g: (g.w * g.ret).sum()).unstack()
    gap = (lr["long"] - lr["short"]).reindex(b.index) - b.gross
    assert gap.abs().max() < 1e-12, "rebuilt legs do not match book()"

    out += ["## Net Sharpe with 2020-03 to 2020-12 left out", "",
            "| weights | months | net Sharpe, all | months left | net Sharpe, ex 2020-03 to 2020-12 | net ann %, ex |",
            "|---|---|---|---|---|---|"]
    for s, r in books.items():
        ex = r[(r.index < EXCLUDE[0]) | (r.index > EXCLUDE[1])].net
        ann = ((1 + ex).prod() ** (12 / len(ex)) - 1) * 100
        out.append(f"| {s} | {len(r)} | {sharpe(r.net):.2f} | {len(ex)} | {sharpe(ex):.2f} | {ann:.2f} |")

    rows, local = [], []
    for title, months in (("best", b.net.nlargest(5).index), ("worst", b.net.nsmallest(5).index)):
        head = ["", f"## Five {title} months, equal weight", ""]
        rows += head + ["| month | net % | gross % | long leg % | short leg % |", "|---|---|---|---|---|"]
        local += head + ["| month | names |", "|---|---|"]
        for m in months:
            rows.append(f"| {m:%Y-%m} | {b.net[m] * 100:+.2f} | {b.gross[m] * 100:+.2f} | "
                        f"{lr.loc[m, 'long'] * 100:+.2f} | {lr.loc[m, 'short'] * 100:+.2f} |")
            g = c[c.Date == m].assign(abs=lambda x: x.contrib.abs()).nlargest(3, "abs")
            local.append(f"| {m:%Y-%m} | " + "; ".join(
                f"{names.get(s, s)} ({leg}, ret {r * 100:+.0f}%, {x * 100:+.2f} pp)"
                for s, leg, r, x in zip(g.SecID, g.leg, g.ret, g.contrib)) + " |")

    best, worst = b.net.nlargest(5).index, b.net.nsmallest(5).index
    top = c[c.Date.isin(best.union(worst))].assign(abs=lambda x: x.contrib.abs())
    top = top.loc[top.groupby("Date")["abs"].idxmax()]
    squeezed = lr.loc[worst, "short"] > 0
    n = c.groupby(["Date", "leg"]).size().unstack()
    rows += ["", "Leg returns are gross and reweighted over names with a return, as in `resmom_compare.py`.", "",
             f"What drove them: in the five best months the long leg made {lr.loc[best, 'long'].mean() * 100:.1f}% "
             f"on average against {lr.loc[best, 'short'].mean() * 100:+.1f}% for the short leg; in {squeezed.sum()} "
             f"of the five worst months the short leg rose ({lr.loc[worst[squeezed], 'short'].min() * 100:.1f}% to "
             f"{lr.loc[worst[squeezed], 'short'].max() * 100:.1f}%). In these ten months the largest single name "
             f"moved the long-short by {top['abs'].min() * 100:.1f} to {top['abs'].max() * 100:.1f} points.", "",
             f"Leg sizes in the hold-out: long median {n.long.median():.0f} names; short median "
             f"{n.short.median():.0f}, minimum {n.short.min():.0f}, at most 6 names in {(n.short <= 6).sum()} "
             f"of {len(n)} months. The borrow screen keeps the short leg small, so one short can move "
             "a month by several points.", ""]
    path = rc.OUT / "holdout_diagnostic.md"
    path.write_text("\n".join(out + rows))
    # per-name detail stays local (gitignored): vendor returns for single stocks are not published
    names_path = rc.OUT / "holdout_diagnostic_names.md"
    names_path.write_text("\n".join(["# Hold-out diagnostic, top contributing names (local only)", ""] + local + [
        "", "The three largest contributions to the long-short that month; pp is weight times return, "
        "signed for the leg (a falling short adds).", ""]))
    print("\n".join(out + rows))
    print(f"\nSaved {path.relative_to(rc.REPO)} and {names_path.relative_to(rc.REPO)} (gitignored)", file=sys.stderr)

if __name__ == "__main__":
    main()
