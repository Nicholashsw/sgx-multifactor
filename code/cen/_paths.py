"""File locations for the Cen replication and extension. Folders come from config.py."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from config import (BLOOMBERG_SGX_EQUITIES, DERIVED_SGX_EQUITIES, WRDS_SGX_EQUITIES,  # noqa: E402
                    WRDS_WORLD_INDICES)

SECD = WRDS_SGX_EQUITIES / "wrds_compustat_sg_secdaily_d_1984_2026.csv"
MARKIT = WRDS_SGX_EQUITIES / "wrds_markit_sg_secfinance_d_2002_2026.csv"
INDEX = WRDS_WORLD_INDICES / "wrds_compustat_world_index_constituents_a_1990_2026.csv"
BENCH = WRDS_WORLD_INDICES / "wrds_compustat_world_indices_m_1986_2026.csv"
MEMBERSHIP = BLOOMBERG_SGX_EQUITIES / "bloomberg_sgx_index_membership_a_2003_2025.csv"

RETS = DERIVED_SGX_EQUITIES / "derived_sgx_daily_rets_d_2000_2026.parquet"
PANEL = DERIVED_SGX_EQUITIES / "derived_sgx_broad_panel_m_1991_2026.csv"
XW = DERIVED_SGX_EQUITIES / "derived_sgx_crosswalk_secid_isin_sedol_static.csv"
SPREADS_TRADED = DERIVED_SGX_EQUITIES / "derived_sgx_cs_spreads_traded_m_1993_2026.csv"
FSSTI_MAP = DERIVED_SGX_EQUITIES / "derived_sgx_fssti_gvkey_map_a_2008_2018.csv"

RESULTS = REPO / "results" / "cen_replication"
