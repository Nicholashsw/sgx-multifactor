"""The locked hold-out (results/resmom/PREREG.md).

A research run reads nothing dated on or after HOLDOUT_START. With --final the hold-out
period alone is reported; it is not used to choose anything.
"""
import pandas as pd

HOLDOUT_START = "2020-01-01"  # the repository's convention (code/cen/extend.py)
START = pd.Timestamp(HOLDOUT_START)


def readable(df, col, final):
    """Rows a run may read: all of them with --final, otherwise only dates before the hold-out."""
    return df if final else df[df[col] < START]


def reported(r, final):
    """Monthly results indexed by holding month: the hold-out with --final, otherwise development."""
    return r[r.index >= START] if final else r[r.index < START]
