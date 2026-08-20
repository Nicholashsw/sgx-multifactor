"""
make_synthetic.py

Generates SYNTHETIC replicas of the two panel files whose real versions
contain licensed vendor data (Bloomberg, CEIC) and therefore never ship.

The replicas match the real files column-for-column so the pipeline code
runs end to end for anyone cloning the repository. Every value is drawn
from a seeded random generator. Nothing here is market data. No result
computed on these files means anything. The tickers are fabricated
(SYN01 SP Equity ... SYN30 SP Equity) so the files cannot be mistaken
for a real export.

Run: python make_synthetic.py
Outputs: synthetic_panel_stock.csv, synthetic_macro_monthly.csv
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(20260819)

PANEL_COLS = [
    "Date", "Ticker", "PX_LAST", "PE_RATIO", "SourceIndex_x", "Sector",
    "Industry", "SourceIndex_y", "TOT_RETURN", "MKT_CAP_SGDmn", "PX_TO_BOOK",
    "DIV_YIELD", "PX_VOLUME", "Return_1M", "Return_3M", "MOM_12_1", "MOM_6_1",
    "MOM_3_1", "LogMktCap", "BM_Ratio", "LogVolume", "Amihud",
]
MACRO_COLS = [
    "SPX", "VIX", "DXY", "FDTR", "SPY", "SPX_Ret_1M", "SPX_Ret_3M",
    "SPX_Ret_12M", "VIX_MA3", "DXY_Ret_3M", "Regime_RiskOn", "Regime_VIX_High",
    "SG_IPI", "SG_PMI", "SG_CPI_YoY", "SG_NODX_Elec", "SG_Visitors_CN",
    "SG_Visitors_Total", "USDSGD", "SG_GDP_YoY", "SG_SORA_3M", "SG_NEER",
    "SG_SGS_2Y", "SG_SGS_10Y", "SG_M2_YoY", "SG_CoreCPI_YoY",
    "SG_GDP_GovtConsump", "SG_GDP_PrivConsump", "SG_GDP_GFCF", "CN_IPI_YoY",
    "CN_PPI_YoY", "CN_PMI", "JP_Tankan", "SG_CoreCPI2", "SG_CPI2", "SG_GDP2",
    "US_M2_YoY", "US_Unemployment", "US_ISM_PMI", "US_CoreCPI_YoY",
    "US_CPI_YoY", "SG_YieldSpread", "SG_PMI_Change", "CN_PMI_Change",
    "SG_SORA_Change", "US_ISM_Change", "SG_CPI_Surprise",
    "Regime_SGRates_Rising", "Regime_SGGrowth", "Regime_ChinaGrowth",
]

SECTORS = {
    "Financials": "Diversified Banks", "Real Estate": "REITs",
    "Industrials": "Conglomerates", "Consumer Staples": "Food Retail",
    "Utilities": "Electric Utilities", "Information Technology": "Electronics",
}

DATES = pd.date_range("2001-01-31", "2026-01-31", freq="ME")


def build_macro() -> pd.DataFrame:
    n = len(DATES)
    m = pd.DataFrame(index=DATES)
    m.index.name = "Date"
    m["SPX"] = 1300 * np.exp(np.cumsum(RNG.normal(0.005, 0.04, n)))
    m["VIX"] = np.clip(20 + np.cumsum(RNG.normal(0, 2, n)) * 0.1, 10, 60)
    m["DXY"] = 95 * np.exp(np.cumsum(RNG.normal(0, 0.015, n)))
    m["FDTR"] = np.clip(2 + np.cumsum(RNG.normal(0, 0.1, n)) * 0.1, 0, 6)
    m["SPY"] = m["SPX"] / 10
    m["SPX_Ret_1M"] = m["SPX"].pct_change()
    m["SPX_Ret_3M"] = m["SPX"].pct_change(3)
    m["SPX_Ret_12M"] = m["SPX"].pct_change(12)
    m["VIX_MA3"] = m["VIX"].rolling(3).mean()
    m["DXY_Ret_3M"] = m["DXY"].pct_change(3)
    m["Regime_RiskOn"] = ((m["VIX"] < 20) & (m["SPX_Ret_3M"] > 0)).astype(int)
    m["Regime_VIX_High"] = (m["VIX"] > 25).astype(int)
    for col, base, sd in [
        ("SG_IPI", 100, 3), ("SG_PMI", 50, 1.5), ("SG_CPI_YoY", 2, 1),
        ("SG_NODX_Elec", 5, 8), ("SG_Visitors_CN", 300, 60),
        ("SG_Visitors_Total", 1400, 200), ("USDSGD", 1.35, 0.02),
        ("SG_GDP_YoY", 3, 2), ("SG_SORA_3M", 1.5, 0.4), ("SG_NEER", 100, 2),
        ("SG_SGS_2Y", 1.8, 0.5), ("SG_SGS_10Y", 2.5, 0.5),
        ("SG_M2_YoY", 6, 2), ("SG_CoreCPI_YoY", 1.8, 0.8),
        ("SG_GDP_GovtConsump", 3, 2), ("SG_GDP_PrivConsump", 3, 2),
        ("SG_GDP_GFCF", 2, 4), ("CN_IPI_YoY", 7, 3), ("CN_PPI_YoY", 2, 3),
        ("CN_PMI", 50.5, 1.2), ("JP_Tankan", 8, 10), ("SG_CoreCPI2", 1.8, 0.8),
        ("SG_CPI2", 2, 1), ("SG_GDP2", 3, 2), ("US_M2_YoY", 6, 3),
        ("US_Unemployment", 5, 1.5), ("US_ISM_PMI", 53, 4),
        ("US_CoreCPI_YoY", 2.2, 0.8), ("US_CPI_YoY", 2.4, 1.2),
    ]:
        m[col] = base + np.cumsum(RNG.normal(0, sd, n)) * 0.05
    m["SG_YieldSpread"] = m["SG_SGS_10Y"] - m["SG_SGS_2Y"]
    m["SG_PMI_Change"] = m["SG_PMI"].diff()
    m["CN_PMI_Change"] = m["CN_PMI"].diff()
    m["SG_SORA_Change"] = m["SG_SORA_3M"].diff()
    m["US_ISM_Change"] = m["US_ISM_PMI"].diff()
    m["SG_CPI_Surprise"] = (m["SG_CPI_YoY"]
                            - m["SG_CPI_YoY"].rolling(3).mean().shift(1))
    m["Regime_SGRates_Rising"] = (m["SG_SORA_Change"] > 0).astype(int)
    m["Regime_SGGrowth"] = (m["SG_PMI"] > 50).astype(int)
    m["Regime_ChinaGrowth"] = (m["CN_PMI"] > 50).astype(int)
    return m.reset_index()[["Date"] + MACRO_COLS]


def build_panel(macro: pd.DataFrame) -> pd.DataFrame:
    rows = []
    sector_list = list(SECTORS.items())
    n = len(DATES)
    for k in range(1, 31):
        ticker = f"SYN{k:02d} SP Equity"
        sector, industry = sector_list[k % len(sector_list)]
        ret = RNG.normal(0.005, 0.06, n)
        px = 5 * np.exp(np.cumsum(ret))
        tri = 100 * np.exp(np.cumsum(ret + 0.003))
        mc0 = RNG.uniform(1000, 40000)
        pb0 = RNG.uniform(0.6, 2.5)
        dy0 = RNG.uniform(1.5, 6.0)
        pe0 = RNG.uniform(8, 22)
        for i, d in enumerate(DATES):
            vol = RNG.uniform(1e6, 4e7)
            rows.append({
                "Date": d, "Ticker": ticker,
                "PX_LAST": round(px[i], 3),
                "PE_RATIO": round(pe0 * (1 + RNG.normal(0, 0.05)), 2),
                "SourceIndex_x": "SYN_INDEX", "Sector": sector,
                "Industry": industry, "SourceIndex_y": "SYN_INDEX",
                "TOT_RETURN": round(tri[i], 3),
                "MKT_CAP_SGDmn": round(mc0 * px[i] / px[0], 1),
                "PX_TO_BOOK": round(pb0 * (1 + RNG.normal(0, 0.03)), 3),
                "DIV_YIELD": round(dy0 * (1 + RNG.normal(0, 0.03)), 3),
                "PX_VOLUME": round(vol, 0),
            })
    p = pd.DataFrame(rows).sort_values(["Ticker", "Date"]).reset_index(drop=True)
    g = p.groupby("Ticker")
    p["Return_1M"] = g["TOT_RETURN"].pct_change(1)
    p["Return_3M"] = g["TOT_RETURN"].pct_change(3)
    p["MOM_12_1"] = g["TOT_RETURN"].pct_change(12).groupby(p["Ticker"]).shift(1)
    p["MOM_6_1"] = g["TOT_RETURN"].pct_change(6).groupby(p["Ticker"]).shift(1)
    p["MOM_3_1"] = g["TOT_RETURN"].pct_change(3).groupby(p["Ticker"]).shift(1)
    p["LogMktCap"] = np.log(p["MKT_CAP_SGDmn"].clip(lower=1))
    p["BM_Ratio"] = 1.0 / p["PX_TO_BOOK"].clip(lower=0.1)
    p["LogVolume"] = np.log(p["PX_VOLUME"].clip(lower=1))
    p["Amihud"] = p["Return_1M"].abs() / p["PX_VOLUME"].clip(lower=1e6)
    p = pd.merge(p, macro, on="Date", how="left")
    return p[PANEL_COLS + MACRO_COLS]


def main():
    macro = build_macro()
    macro.to_csv("synthetic_macro_monthly.csv", index=False)
    print(f"synthetic_macro_monthly.csv: {len(macro)} rows x "
          f"{len(macro.columns)} cols")
    panel = build_panel(macro)
    panel.to_csv("synthetic_panel_stock.csv", index=False)
    print(f"synthetic_panel_stock.csv: {len(panel):,} rows x "
          f"{len(panel.columns)} cols, {panel['Ticker'].nunique()} tickers")
    print("SYNTHETIC DATA. Not market data. See DATA.md.")


if __name__ == "__main__":
    main()
