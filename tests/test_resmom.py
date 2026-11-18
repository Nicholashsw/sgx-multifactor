"""Checks for the residual momentum extension (results/resmom/PREREG.md). Synthetic data only.

Run: pytest tests/test_resmom.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))
from residuals import residual_momentum, window  # noqa: E402
from weights import SCHEMES  # noqa: E402


def returns(seed=0, days=600, names=30):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2010-01-01", periods=days)
    f = rng.normal(0, 0.01, (days, 2))
    r = f @ rng.normal(1, 0.3, (2, names)) + rng.normal(0, 0.02, (days, names))
    r = pd.DataFrame(r, index=idx, columns=[f"S{i}" for i in range(names)])
    return r.mask(rng.random(r.shape) < 0.05)  # some missing days


def test_signal_uses_no_future_data():
    r = returns()
    d = r.index[400]
    before = residual_momentum(window(r, d, 252), d, 3)
    later = r.copy()
    later.loc[later.index > d] = np.random.default_rng(1).normal(0, 0.5, later.loc[later.index > d].shape)
    after = residual_momentum(window(later, d, 252), d, 3)
    pd.testing.assert_series_equal(before, after)
    assert before.notna().all()


@pytest.mark.parametrize("scheme", list(SCHEMES))
def test_weights_sum_to_one(scheme):
    w = SCHEMES[scheme](returns().iloc[:252, :7])
    assert w.notna().all() and (w > 0).all()
    assert np.isclose(w.sum(), 1.0)
