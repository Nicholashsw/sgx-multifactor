"""Weights within one leg, from a window of daily returns (dates x names). Each sums to 1."""
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform


def equal(w):
    return pd.Series(1.0 / w.shape[1], index=w.columns)


def inverse_vol(w):
    iv = 1.0 / w.std()
    return iv / iv.sum()


def _cluster_var(cov, names):
    """Variance of the inverse-variance portfolio of the names."""
    c = cov.loc[names, names]
    ivp = 1.0 / np.diag(c)
    ivp /= ivp.sum()
    return float(ivp @ c.to_numpy() @ ivp)


def hrp(w):
    """Hierarchical risk parity (Lopez de Prado 2016): single linkage on correlation distance,
    then recursive bisection of the ordered names with inverse-variance cluster weights."""
    cov = w.cov()
    corr = w.corr().fillna(0.0).to_numpy(copy=True)
    np.fill_diagonal(corr, 1.0)
    dist = np.sqrt(((1.0 - corr) / 2.0).clip(min=0.0))
    order = list(w.columns[leaves_list(linkage(squareform(dist, checks=False), "single"))])
    out = pd.Series(1.0, index=order)
    clusters = [order]
    while clusters:
        clusters = [c[i:j] for c in clusters if len(c) > 1 for i, j in ((0, len(c) // 2), (len(c) // 2, len(c)))]
        for a, b in zip(clusters[::2], clusters[1::2]):
            va, vb = _cluster_var(cov, a), _cluster_var(cov, b)
            out[a] *= vb / (va + vb)
            out[b] *= va / (va + vb)
    return out.reindex(w.columns)


SCHEMES = {"equal": equal, "inverse_vol": inverse_vol, "hrp": hrp}
