"""PCA residual momentum from daily returns (results/resmom/PREREG.md).

At a formation date d the PCA is fitted on the window of daily returns ending at d, so the
signal uses no data after d. Missing returns are set to zero after demeaning for the fit
only; residuals on those days stay missing.
"""
import numpy as np
import pandas as pd


def window(rets, d, n_days):
    """The last n_days rows of a dates x names return table up to and including d."""
    return rets.loc[:d].iloc[-n_days:]


def pca_residuals(w, k):
    """Daily returns in w minus their projection on the first k principal components.

    The components come from demeaned returns, but the residuals are taken from the raw
    returns, so each name keeps its own drift. Demeaned residuals sum to zero over the
    window, which would turn 12-1 momentum into minus the last month's return.
    """
    raw = w.fillna(0.0).to_numpy()
    x = (w - w.mean()).fillna(0.0).to_numpy()
    v = np.linalg.svd(x, full_matrices=False)[2][:k].T
    resid = raw - raw @ v @ v.T
    return pd.DataFrame(resid, index=w.index, columns=w.columns).where(w.notna())


def residual_momentum(w, d, k):
    """Sum of residuals from the start of month t-11 to the end of month t-1, over their std."""
    m = pd.Timestamp(d).to_period("M")
    e = pca_residuals(w, k)
    e = e[(e.index > (m - 12).end_time) & (e.index <= (m - 1).end_time)]
    return e.sum() / e.std()
