"""File locations for the announcement-text study. Folders come from config.py."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from config import CAPIQ_SGX_EQUITIES, DERIVED_SGX_EQUITIES, WRDS_SGX_EQUITIES, WRDS_WORLD_INDICES  # noqa: E402

SECD = WRDS_SGX_EQUITIES / "wrds_compustat_sg_secdaily_d_1984_2026.csv"
INDEX = WRDS_WORLD_INDICES / "wrds_compustat_world_index_constituents_a_1990_2026.csv"
KEYDEV = CAPIQ_SGX_EQUITIES / "capiq_sgx_keydev_evt_1990_2026.parquet"

RETS = DERIVED_SGX_EQUITIES / "derived_sgx_daily_rets_d_2000_2026.parquet"
DIVS = DERIVED_SGX_EQUITIES / "derived_sgx_div_dates_d_2000_2026.parquet"
MAP = DERIVED_SGX_EQUITIES / "derived_sgx_keydev_gvkey_map_static.csv"
LABELLED = DERIVED_SGX_EQUITIES / "derived_sgx_keydev_labelled_evt_2002_2026.parquet"
TONE = DERIVED_SGX_EQUITIES / "derived_sgx_keydev_tone_evt_2002_2026.parquet"
PANEL = DERIVED_SGX_EQUITIES / "derived_sgx_broad_panel_m_1991_2026.csv"
IBES = WRDS_SGX_EQUITIES / "wrds_ibes_sg_statsum_m_2002_2026.zip"
SUE = DERIVED_SGX_EQUITIES / "derived_sgx_ibes_sue_evt_2002_2026.parquet"

RESULTS = REPO / "results" / "news_text"
