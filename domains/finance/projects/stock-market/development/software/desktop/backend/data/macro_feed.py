"""
Tier 1 macro + cross-asset + sentiment + geopolitical data feeds.

Sources:
  FRED CSV downloads  — yields, spreads, macro indicators, sentiment, geopolitical
  Yahoo Finance       — VIX, currencies, commodities, equities, ETFs, crypto
"""

import io
import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests
import yfinance as yf

from backend.database.duckdb_client import get_conn

logger = logging.getLogger(__name__)

# ── FRED series (direct CSV — no API key needed) ──────────────────────────────
# Format: internal_series_id → FRED series ID
_FRED_SERIES: dict[str, str] = {
    # ── Core rates & yields ──────────────────────────────────────────────────
    "DGS10":        "DGS10",         # 10Y Treasury yield
    "DGS2":         "DGS2",          # 2Y Treasury yield
    "DGS3M":        "DTB3",          # 3M T-Bill
    "DGS30":        "DGS30",         # 30Y Treasury yield
    "DGS5":         "DGS5",          # 5Y Treasury yield
    "T10YIE":       "T10YIE",        # 10Y breakeven inflation
    "T5YIE":        "T5YIE",         # 5Y breakeven inflation
    "T2YIE":        "T2YIE",         # 2Y breakeven inflation
    "DFII10":       "DFII10",        # 10Y TIPS real yield
    "DFII5":        "DFII5",         # 5Y TIPS real yield
    "T10Y3M":       "T10Y3M",        # 10Y-3M spread
    "TEDRATE":      "TEDRATE",       # TED spread
    "SOFR":         "SOFR",          # Secured Overnight Financing Rate
    "MORTGAGE30US": "MORTGAGE30US",  # 30Y mortgage rate
    "IORB":         "IORB",          # Interest on Reserve Balances
    # ── Credit spreads ───────────────────────────────────────────────────────
    "BAMLH0A0HYM2": "BAMLH0A0HYM2", # HY OAS spread
    "BAMLC0A0CM":   "BAMLC0A0CM",   # IG OAS spread
    "BAMLHE00EHYIOAS": "BAMLHE00EHYIOAS",  # EM HY sovereign spread
    "CPF3MTB3M":    "CPF3MTB3M",    # Commercial paper - T-Bill spread
    # ── Fed / money supply ───────────────────────────────────────────────────
    "WALCL":        "WALCL",         # Fed balance sheet (millions)
    "WRBUSNS":      "WRBUSNS",       # Excess reserves
    "RRPONTSYD":    "RRPONTSYD",     # Reverse repo facility
    "M2SL":         "M2SL",          # M2 money supply
    "M1SL":         "M1SL",          # M1 money supply
    "M2V":          "M2V",           # M2 velocity
    # ── Labor ────────────────────────────────────────────────────────────────
    "ICSA":         "ICSA",          # Initial jobless claims
    "CCSA":         "CCSA",          # Continuing jobless claims
    "JTSJOL":       "JTSJOL",        # JOLTS job openings
    "JTSQUR":       "JTSQUR",        # JOLTS quits rate
    "UNRATE":       "UNRATE",        # Unemployment rate
    "U6RATE":       "U6RATE",        # U6 underemployment
    "PAYEMS":       "PAYEMS",        # Nonfarm payrolls (level)
    "CIVPART":      "CIVPART",       # Labor force participation rate
    # ── Inflation ────────────────────────────────────────────────────────────
    "PCEPILFE":     "PCEPILFE",      # PCE Core (level — compute YoY)
    "PCEPI":        "PCEPI",         # PCE headline (level — compute YoY)
    "CPILFESL":     "CPILFESL",      # Core CPI (level — compute YoY)
    "CPIAUCSL":     "CPIAUCSL",      # CPI headline (level — compute YoY)
    "CUSR0000SAH1": "CUSR0000SAH1",  # CPI shelter (level — compute YoY)
    "PPIACO":       "PPIACO",        # PPI all commodities
    "MICH":         "MICH",          # Michigan 1Y inflation expectation
    # ── Activity / Output ────────────────────────────────────────────────────
    "NFCI":         "NFCI",          # Chicago Fed Financial Conditions
    "INDPRO":       "INDPRO",        # Industrial production (level)
    "TCU":          "TCU",           # Capacity utilization
    "RSXFS":        "RSXFS",         # Retail sales ex food svc (level)
    "RSAFS":        "RSAFS",         # Retail sales all (level)
    "NAPM":         "NAPM",          # ISM Manufacturing PMI
    "NAPMNO":       "NAPMNO",        # ISM New Orders sub-index
    "NAPMPI":       "NAPMPI",        # ISM Prices Paid sub-index
    "UMCSENT":      "UMCSENT",       # Michigan consumer sentiment
    "CSCICP03USM665S": "CSCICP03USM665S",  # Consumer confidence
    "PSAVERT":      "PSAVERT",       # Personal savings rate
    "PI":           "PI",             # Personal income (level)
    # ── Housing ──────────────────────────────────────────────────────────────
    "HOUST":        "HOUST",         # Housing starts
    "PERMIT":       "PERMIT",        # Building permits
    "CSUSHPINSA":   "CSUSHPINSA",    # Case-Shiller HPI (level)
    "EXHOSLUSM495S": "EXHOSLUSM495S",  # Existing home sales
    # ── Leading indicators ────────────────────────────────────────────────────
    "USSLIND":      "USSLIND",       # LEI composite
    "CFNAI":        "CFNAI",         # CFNAI activity index
    "USREC":        "USREC",         # NBER recession indicator
    "USPHCI":       "USPHCI",        # Conference Board coincident
    "USALOLITONOSTSAM": "USALOLITONOSTSAM",  # OECD CLI US
    # ── Business cycle ───────────────────────────────────────────────────────
    "ISRATIO":      "ISRATIO",       # Business inventories/sales ratio
    "DGORDER":      "DGORDER",       # Durable goods orders (level)
    "CP":           "CP",             # Corporate profits (level, quarterly)
    "A191RL1Q225SBEA": "A191RL1Q225SBEA",  # Real GDP QoQ annualized
    "BOPGSTB":      "BOPGSTB",       # Trade balance (millions)
    "FYSGDA188S":   "FYSGDA188S",    # Federal surplus/deficit % GDP
    "GFDEGDQ188S":  "GFDEGDQ188S",   # Federal debt % GDP
    # ── Credit / banking ─────────────────────────────────────────────────────
    "DRSDCILM":     "DRSDCILM",      # C&I loan standards net tightening
    "TOTCI":        "TOTCI",         # Total consumer credit
    "BUSLOANS":     "BUSLOANS",      # Commercial & industrial loans
    "TDSP":         "TDSP",          # Household debt service ratio
    "DRCCLACBS":    "DRCCLACBS",     # Delinquency rate consumer loans
    # ── Commodities (FRED spot prices) ───────────────────────────────────────
    "DCOILWTICO":   "DCOILWTICO",    # WTI crude oil spot price
    "DHHNGSP":      "DHHNGSP",       # Natural gas spot (Henry Hub)
    # ── Dollar / international ────────────────────────────────────────────────
    "DTWEXBGS":     "DTWEXBGS",      # Broad US Dollar Index
    # ── Sentiment (FRED) ─────────────────────────────────────────────────────
    "WAAABULL":     "WAAABULL",      # AAII % bullish
    "WAAABEAR":     "WAAABEAR",      # AAII % bearish
    # ── Uncertainty / geopolitical (FRED) ────────────────────────────────────
    "GEOUSPRISK":   "GEOUSPRISK",    # Geopolitical Risk Index (GPR)
    "USEPUINDXD":   "USEPUINDXD",    # Economic Policy Uncertainty Daily
    "EMVTRADEPOL":  "EMVTRADEPOL",   # EMV Trade Policy Uncertainty
    "STLFSI2":      "STLFSI2",       # St. Louis Fed Financial Stress Index
}

# ── Yahoo Finance series ──────────────────────────────────────────────────────
_YF_SERIES: dict[str, str] = {
    # ── Volatility ───────────────────────────────────────────────────────────
    "VIXCLS":   "^VIX",        # CBOE VIX
    "VVIX":     "^VVIX",       # Volatility of VIX
    "VIX3M":    "^VIX3M",      # 3-Month VIX
    "SKEW":     "^SKEW",       # CBOE SKEW index
    # ── US Dollar & Currencies ───────────────────────────────────────────────
    "DXY":      "DX-Y.NYB",    # US Dollar Index
    "EURUSD":   "EURUSD=X",    # EUR/USD
    "GBPUSD":   "GBPUSD=X",    # GBP/USD
    "USDJPY":   "USDJPY=X",    # USD/JPY
    "AUDUSD":   "AUDUSD=X",    # AUD/USD
    "USDCNH":   "USDCNH=X",    # USD/CNH (offshore yuan)
    "USDCHF":   "USDCHF=X",    # USD/CHF
    "USDMXN":   "USDMXN=X",    # USD/MXN
    # ── Precious metals ──────────────────────────────────────────────────────
    "GOLD":     "GC=F",        # Gold futures
    "SILVER":   "SI=F",        # Silver futures
    # ── Energy ───────────────────────────────────────────────────────────────
    "OIL":      "CL=F",        # WTI crude futures
    "BRENT":    "BZ=F",        # Brent crude futures
    "NATGAS":   "NG=F",        # Natural gas futures
    # ── Industrial metals / commodities ──────────────────────────────────────
    "COPPER":   "HG=F",        # Copper futures
    "ALUMINUM": "ALI=F",       # Aluminum futures
    "AGRI":     "DBA",         # Agriculture ETF
    "COMMODITY_IDX": "PDBC",   # Commodity ETF
    # ── US Equity ────────────────────────────────────────────────────────────
    "SPX":      "^GSPC",       # S&P 500
    "SPY":      "SPY",         # S&P 500 ETF
    "QQQ":      "QQQ",         # Nasdaq-100 ETF
    "IWM":      "IWM",         # Russell 2000 (small cap)
    "IVV":      "IVV",         # S&P 500 ETF (for sector ratios)
    "IWD":      "IWD",         # iShares Value
    "IWF":      "IWF",         # iShares Growth
    "MDY":      "MDY",         # S&P 400 Mid-Cap
    "DVY":      "DVY",         # Dividend ETF
    # ── US Sector ETFs ────────────────────────────────────────────────────────
    "XLK":      "XLK",         # Technology
    "XLF":      "XLF",         # Financials
    "XLE":      "XLE",         # Energy
    "XLV":      "XLV",         # Healthcare
    "XLI":      "XLI",         # Industrials
    "XLY":      "XLY",         # Consumer Discretionary
    "XLP":      "XLP",         # Consumer Staples
    "XLU":      "XLU",         # Utilities
    "XLRE":     "XLRE",        # Real Estate
    "KBE":      "KBE",         # Bank ETF
    # ── US Bonds ─────────────────────────────────────────────────────────────
    "TLT":      "TLT",         # 20+ Year Treasury ETF
    "IEF":      "IEF",         # 7-10 Year Treasury ETF
    "HYG":      "HYG",         # High Yield Bond ETF
    "LQD":      "LQD",         # IG Corporate Bond ETF
    "TIP":      "TIP",         # TIPS ETF
    # ── International equity ──────────────────────────────────────────────────
    "EWJ":      "EWJ",         # Japan (MSCI)
    "EWG":      "EWG",         # Germany
    "EWU":      "EWU",         # UK
    "EWZ":      "EWZ",         # Brazil
    "FXI":      "FXI",         # China large cap
    "EEM":      "EEM",         # EM equity
    "EWH":      "EWH",         # Hong Kong
    "EWY":      "EWY",         # South Korea
    "INDA":     "INDA",        # India
    "ACWI":     "ACWI",        # MSCI All Country World
    "VEA":      "VEA",         # MSCI Developed ex-US
    "VWO":      "VWO",         # MSCI EM
    # ── Crypto ───────────────────────────────────────────────────────────────
    "BTC":      "BTC-USD",     # Bitcoin
    "ETH":      "ETH-USD",     # Ethereum
}

_FRED_BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv"


# ── FRED fetcher ──────────────────────────────────────────────────────────────

def _fetch_fred(series_id: str, fred_id: str, days: int) -> pd.DataFrame:
    try:
        start = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        url = f"{_FRED_BASE}?id={fred_id}&vintage_date=&observation_start={start}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        df.columns = ["date", "value"]
        df["date"]  = pd.to_datetime(df["date"]).dt.tz_localize(None)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        df["series_id"] = series_id
        return df[["series_id", "date", "value"]]
    except Exception as e:
        logger.warning(f"FRED fetch failed for {series_id} ({fred_id}): {e}")
        return pd.DataFrame()


# ── Yahoo Finance fetcher ─────────────────────────────────────────────────────

def _fetch_yf(series_id: str, ticker: str, days: int) -> pd.DataFrame:
    try:
        start = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        raw = yf.download(ticker, start=start, auto_adjust=True, progress=False)
        if raw.empty:
            return pd.DataFrame()
        raw = raw.reset_index()
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = ["_".join(str(c) for c in col).strip("_") for col in raw.columns]
        date_col  = next((c for c in raw.columns if c.lower() in ("date", "datetime")), None)
        close_col = next((c for c in raw.columns if "close" in c.lower()), None)
        if not date_col or not close_col:
            return pd.DataFrame()
        df = raw[[date_col, close_col]].copy()
        df.columns = ["date", "value"]
        df["date"]  = pd.to_datetime(df["date"]).dt.tz_localize(None)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        df["series_id"] = series_id
        return df[["series_id", "date", "value"]]
    except Exception as e:
        logger.warning(f"YF fetch failed for {series_id} ({ticker}): {e}")
        return pd.DataFrame()


# ── DB upsert ─────────────────────────────────────────────────────────────────

def upsert_macro(df: pd.DataFrame) -> None:
    if df.empty:
        return
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO macro_indicators SELECT * FROM df")
    conn.commit()


# ── Derived series ────────────────────────────────────────────────────────────

def _compute_derived(conn) -> None:
    """Compute derived time series from raw fetched data."""

    def load_series(sid: str) -> pd.DataFrame:
        df = conn.execute("""
            SELECT CAST(date AS DATE) as date, value
            FROM macro_indicators WHERE series_id = ? ORDER BY date
        """, [sid]).df()
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df

    def store_derived(series_id: str, dates, values) -> None:
        df = pd.DataFrame({"series_id": series_id, "date": dates, "value": values}).dropna()
        upsert_macro(df[["series_id", "date", "value"]])

    def yoy_pct(series_id: str, out_id: str, periods: int = 12) -> None:
        s = load_series(series_id)
        if s.empty or len(s) <= periods:
            return
        s = s.set_index("date").sort_index()
        s["yoy"] = s["value"].pct_change(periods) * 100
        yoy = s["yoy"].dropna().reset_index()
        store_derived(out_id, yoy["date"], yoy["yoy"])
        logger.debug(f"Computed {out_id} ({len(yoy)} rows)")

    def mom_pct(series_id: str, out_id: str, periods: int = 1) -> None:
        s = load_series(series_id)
        if s.empty or len(s) <= periods:
            return
        s = s.set_index("date").sort_index()
        s["mom"] = s["value"].pct_change(periods) * 100
        mom = s["mom"].dropna().reset_index()
        store_derived(out_id, mom["date"], mom["mom"])

    def ret_n(series_id: str, out_id: str, n: int) -> None:
        s = load_series(series_id)
        if s.empty or len(s) <= n:
            return
        s = s.set_index("date").sort_index()
        s["ret"] = s["value"].pct_change(n)
        ret = s["ret"].dropna().reset_index()
        store_derived(out_id, ret["date"], ret["ret"])

    # ── Yield curve ───────────────────────────────────────────────────────────
    ten = load_series("DGS10")
    two = load_series("DGS2")
    if not ten.empty and not two.empty:
        merged = pd.merge_asof(ten.sort_values("date"),
                               two.rename(columns={"value": "v2"}).sort_values("date"),
                               on="date", direction="nearest")
        merged = merged.dropna(subset=["value", "v2"])
        merged["spread"] = merged["value"] - merged["v2"]
        store_derived("T10Y2Y", merged["date"], merged["spread"])
        store_derived("FEDFUNDS", merged["date"], merged["v2"])
        logger.info(f"Computed T10Y2Y ({len(merged)} rows)")

    # ── Inflation YoY ─────────────────────────────────────────────────────────
    yoy_pct("M2SL",       "M2_GROWTH_YOY",     periods=52)  # M2SL weekly → 52 periods
    yoy_pct("PCEPILFE",   "PCE_CORE_YOY",      periods=12)
    yoy_pct("PCEPI",      "PCE_HEADLINE_YOY",  periods=12)
    yoy_pct("CPILFESL",   "CORE_CPI_YOY",      periods=12)
    yoy_pct("CPIAUCSL",   "CPI_HEADLINE_YOY",  periods=12)
    yoy_pct("CUSR0000SAH1", "CPI_SHELTER_YOY", periods=12)
    yoy_pct("PPIACO",     "PPI_YOY",           periods=12)
    yoy_pct("CP",         "CORPORATE_PROFITS_YOY", periods=4)  # quarterly
    yoy_pct("PI",         "PERSONAL_INCOME_YOY", periods=12)
    yoy_pct("TOTCI",      "CONSUMER_CREDIT_GROWTH", periods=12)
    yoy_pct("BUSLOANS",   "BANK_CREDIT_GROWTH", periods=12)
    yoy_pct("INDPRO",     "INDPRO_YOY",        periods=12)
    yoy_pct("RSXFS",      "RETAIL_SALES_YOY",  periods=12)
    yoy_pct("CSUSHPINSA", "CASE_SHILLER_YOY",  periods=12)

    # ── MoM series ────────────────────────────────────────────────────────────
    mom_pct("RSAFS",   "RETAIL_SALES_MOM", periods=1)
    mom_pct("DGORDER", "DURABLE_GOODS_MOM", periods=1)
    mom_pct("PI",      "PERSONAL_INCOME_MOM", periods=1)

    # ── NFP monthly change ────────────────────────────────────────────────────
    payems = load_series("PAYEMS")
    if not payems.empty:
        payems = payems.set_index("date").sort_index()
        payems["chg"] = payems["value"].diff(1)
        chg = payems["chg"].dropna().reset_index()
        store_derived("NFP_MONTHLY", chg["date"], chg["chg"])

    # ── AAII spread ───────────────────────────────────────────────────────────
    bull = load_series("WAAABULL")
    bear = load_series("WAAABEAR")
    if not bull.empty and not bear.empty:
        merged = pd.merge_asof(bull.sort_values("date"),
                               bear.rename(columns={"value": "bear"}).sort_values("date"),
                               on="date", direction="nearest")
        merged = merged.dropna(subset=["value", "bear"])
        store_derived("AAII_SPREAD", merged["date"], merged["value"] - merged["bear"])

    # ── Cross-asset momentum (n-day returns) ──────────────────────────────────
    for sid, out, n in [
        ("DXY",      "DXY_RET20",      20),
        ("COPPER",   "COPPER_RET20",   20),
        ("OIL",      "OIL_RET20",      20),
        ("USDJPY",   "USDJPY_RET5",     5),
        ("BRENT",    "BRENT_RET20",    20),
        ("SILVER",   "SILVER_RET20",   20),
        ("NATGAS",   "NATGAS_RET20",   20),
        ("ALUMINUM", "ALUMINUM_RET20", 20),
        ("AGRI",     "AGRI_RET20",     20),
        ("EURUSD",   "EURUSD_RET20",   20),
        ("GBPUSD",   "GBPUSD_RET20",   20),
        ("AUDUSD",   "AUDUSD_RET20",   20),
        ("USDCNH",   "USDCNH_RET20",   20),
        ("USDCHF",   "USDCHF_RET20",   20),
        ("USDMXN",   "USDMXN_RET20",   20),
        ("GOLD",     "GOLD_RET20",     20),
        ("BTC",      "BTC_RET20",      20),
        ("EWJ",      "NIKKEI_RET20",   20),
        ("EWG",      "DAX_RET20",      20),
        ("EWU",      "FTSE_RET20",     20),
        ("EWZ",      "EWZ_RET20",      20),
        ("FXI",      "SHANGHAI_RET20", 20),
        ("EWH",      "HANGSENG_RET20", 20),
        ("EWY",      "KOSPI_RET20",    20),
        ("INDA",     "SENSEX_RET20",   20),
        ("ACWI",     "MSCI_WORLD_RET20", 20),
        ("EEM",      "MSCI_EM_RET20",  20),
        ("TLT",      "TLT_RET20",      20),
        ("IEF",      "IEF_RET20",      20),
        ("HYG",      "HYG_RET20",      20),
    ]:
        ret_n(sid, out, n)

    # ── Ratio series ──────────────────────────────────────────────────────────
    def compute_ratio(a_id, b_id, out_id) -> None:
        a = load_series(a_id)
        b = load_series(b_id)
        if a.empty or b.empty:
            return
        merged = pd.merge_asof(a.sort_values("date"),
                               b.rename(columns={"value": "b"}).sort_values("date"),
                               on="date", direction="nearest")
        merged = merged.dropna(subset=["value", "b"])
        ratio = merged["value"] / merged["b"].replace(0, np.nan)
        store_derived(out_id, merged["date"], ratio)

    compute_ratio("GOLD",    "SPY",     "GOLD_EQUITY_RATIO")
    compute_ratio("COPPER",  "GOLD",    "COPPER_GOLD_RATIO")
    compute_ratio("OIL",     "GOLD",    "OIL_GOLD_RATIO")
    compute_ratio("EEM",     "IVV",     "MSCI_EM_DM_RATIO")
    compute_ratio("IWM",     "SPY",     "IWM_SPY_RATIO")
    compute_ratio("IWD",     "IWF",     "IWD_IWF_RATIO")
    compute_ratio("MDY",     "IVV",     "MIDCAP_LARGECAP_RATIO")
    compute_ratio("XLY",     "XLP",     "XLY_XLP_RATIO")
    compute_ratio("XLK",     "SPY",     "XLK_SPY_RATIO")
    compute_ratio("XLF",     "SPY",     "XLF_SPY_RATIO")
    compute_ratio("XLE",     "SPY",     "XLE_SPY_RATIO")
    compute_ratio("XLV",     "SPY",     "XLV_SPY_RATIO")
    compute_ratio("XLU",     "SPY",     "XLU_SPY_RATIO")
    compute_ratio("XLP",     "SPY",     "XLP_SPY_RATIO")
    compute_ratio("HYG",     "LQD",     "HY_IG_ETF_RATIO")
    compute_ratio("GOLD",    "TIP",     "TIPS_GOLD_RATIO")
    compute_ratio("BTC",     "ETH",     "ETH_BTC_RATIO")

    # ── BTC/SPX 30-day rolling correlation ────────────────────────────────────
    btc = load_series("BTC")
    spx = load_series("SPX")
    if not btc.empty and not spx.empty:
        merged = pd.merge_asof(btc.sort_values("date"),
                               spx.rename(columns={"value": "spx"}).sort_values("date"),
                               on="date", direction="nearest")
        merged = merged.dropna(subset=["value", "spx"])
        corr = merged["value"].pct_change().rolling(30).corr(merged["spx"].pct_change())
        store_derived("BTC_SPX_CORR_30D", merged["date"], corr)

    # ── Equity/Bond 30-day rolling correlation ────────────────────────────────
    tlt = load_series("TLT")
    if not spx.empty and not tlt.empty:
        merged = pd.merge_asof(spx.sort_values("date"),
                               tlt.rename(columns={"value": "tlt"}).sort_values("date"),
                               on="date", direction="nearest")
        merged = merged.dropna(subset=["value", "tlt"])
        corr = merged["value"].pct_change().rolling(30).corr(merged["tlt"].pct_change())
        store_derived("EQUITY_BOND_CORR_30D", merged["date"], corr)

    # ── VIX term structure slope (VIX3M / VIX) ───────────────────────────────
    vix = load_series("VIXCLS")
    vix3m = load_series("VIX3M")
    if not vix.empty and not vix3m.empty:
        merged = pd.merge_asof(vix.sort_values("date"),
                               vix3m.rename(columns={"value": "v3m"}).sort_values("date"),
                               on="date", direction="nearest")
        merged = merged.dropna(subset=["value", "v3m"])
        slope = merged["v3m"] / merged["value"].replace(0, np.nan)
        store_derived("VIX_TERM_SLOPE", merged["date"], slope)

    # ── Variance risk premium (VIX^2 - realized vol^2 proxy) ─────────────────
    if not vix.empty and not spx.empty:
        merged = pd.merge_asof(vix.sort_values("date"),
                               spx.rename(columns={"value": "spx"}).sort_values("date"),
                               on="date", direction="nearest")
        merged = merged.dropna(subset=["value", "spx"])
        realized_vol = merged["spx"].pct_change().rolling(20).std() * np.sqrt(252) * 100
        vrp = merged["value"] - realized_vol
        store_derived("VARIANCE_RISK_PREMIUM", merged["date"], vrp)

    # ── Breakeven 5Y5Y forward ────────────────────────────────────────────────
    be5 = load_series("T5YIE")
    be10 = load_series("T10YIE")
    if not be5.empty and not be10.empty:
        merged = pd.merge_asof(be10.sort_values("date"),
                               be5.rename(columns={"value": "be5"}).sort_values("date"),
                               on="date", direction="nearest")
        merged = merged.dropna(subset=["value", "be5"])
        # 5Y5Y forward = 2*10Y - 5Y breakeven
        fwd = 2 * merged["value"] - merged["be5"]
        store_derived("BREAKEVEN_5Y5Y_FWD", merged["date"], fwd)

    # ── Inflation breakeven slope ─────────────────────────────────────────────
    if not be5.empty and not be10.empty:
        merged = pd.merge_asof(be5.sort_values("date"),
                               be10.rename(columns={"value": "be10"}).sort_values("date"),
                               on="date", direction="nearest")
        merged = merged.dropna(subset=["value", "be10"])
        slope = merged["be10"] - merged["value"]
        store_derived("BREAKEVEN_SLOPE", merged["date"], slope)

    # ── Gold/Real yield spread ────────────────────────────────────────────────
    dfii10 = load_series("DFII10")
    gold = load_series("GOLD")
    if not dfii10.empty and not gold.empty:
        merged = pd.merge_asof(gold.sort_values("date"),
                               dfii10.rename(columns={"value": "ry"}).sort_values("date"),
                               on="date", direction="nearest")
        merged = merged.dropna(subset=["value", "ry"])
        spread = merged["value"].pct_change(20) - merged["ry"]
        store_derived("GOLD_REAL_YIELD_SPREAD", merged["date"], spread)

    # ── Safe haven flow index (gold + TLT combined return) ───────────────────
    if not gold.empty and not tlt.empty:
        merged = pd.merge_asof(gold.sort_values("date"),
                               tlt.rename(columns={"value": "tlt"}).sort_values("date"),
                               on="date", direction="nearest")
        merged = merged.dropna(subset=["value", "tlt"])
        sfx = (merged["value"].pct_change(5) + merged["tlt"].pct_change(5)) / 2
        store_derived("SAFE_HAVEN_FLOW", merged["date"], sfx)

    # ── Job openings / unemployment ratio ─────────────────────────────────────
    jolts = load_series("JTSJOL")
    unemp = load_series("UNRATE")
    if not jolts.empty and not unemp.empty:
        merged = pd.merge_asof(jolts.sort_values("date"),
                               unemp.rename(columns={"value": "urate"}).sort_values("date"),
                               on="date", direction="backward")
        merged = merged.dropna(subset=["value", "urate"])
        # openings in thousands, unemployment rate in %, compute ratio to unemployed persons
        ratio = (merged["value"] / 1000) / merged["urate"].replace(0, np.nan)
        store_derived("JOLTS_UNEMP_RATIO", merged["date"], ratio)

    # ── Cross-asset momentum composite ────────────────────────────────────────
    mom_series_ids = ["DXY_RET20", "GOLD_RET20", "OIL_RET20", "COPPER_RET20", "BTC_RET20"]
    dfs = [load_series(s) for s in mom_series_ids]
    dfs = [d for d in dfs if not d.empty]
    if len(dfs) >= 3:
        base = dfs[0].rename(columns={"value": "v0"})
        for i, d in enumerate(dfs[1:], 1):
            base = pd.merge_asof(base.sort_values("date"),
                                  d.rename(columns={"value": f"v{i}"}).sort_values("date"),
                                  on="date", direction="nearest")
        v_cols = [c for c in base.columns if c.startswith("v")]
        composite = base[v_cols].mean(axis=1)
        store_derived("CROSS_ASSET_MOMENTUM", base["date"], composite)

    # ── Warren Buffett indicator (market cap / GDP) ────────────────────────────
    gdp = load_series("A191RL1Q225SBEA")
    if not spx.empty and not gdp.empty:
        merged = pd.merge_asof(spx.sort_values("date"),
                               gdp.rename(columns={"value": "gdp"}).sort_values("date"),
                               on="date", direction="backward")
        merged = merged.dropna(subset=["value", "gdp"])
        # Rough proxy: SPX level normalized by GDP growth
        wi = merged["value"].pct_change(252)
        store_derived("BUFFETT_INDICATOR_PROXY", merged["date"], wi)

    logger.info("Derived series computation complete")


# ── Public load functions ─────────────────────────────────────────────────────

def initial_macro_load() -> None:
    days = 365 * 7
    logger.info("Starting initial macro load (all factors)...")
    for series_id, fred_id in _FRED_SERIES.items():
        df = _fetch_fred(series_id, fred_id, days)
        upsert_macro(df)
        logger.info(f"  FRED {series_id}: {len(df)} rows")
    for series_id, yf_ticker in _YF_SERIES.items():
        df = _fetch_yf(series_id, yf_ticker, days)
        upsert_macro(df)
        logger.info(f"  YF {series_id}: {len(df)} rows")
    _compute_derived(get_conn())
    logger.info("Initial macro load complete")


def refresh_all_macro() -> None:
    days = 120
    for series_id, fred_id in _FRED_SERIES.items():
        df = _fetch_fred(series_id, fred_id, days)
        upsert_macro(df)
    for series_id, yf_ticker in _YF_SERIES.items():
        df = _fetch_yf(series_id, yf_ticker, days)
        upsert_macro(df)
    _compute_derived(get_conn())
    logger.info("Macro refresh complete")


# ── Training timeseries loader ────────────────────────────────────────────────

def load_macro_timeseries() -> pd.DataFrame:
    """
    Wide daily-forward-filled DataFrame with all macro, cross-asset, sentiment,
    and geopolitical feature columns used for training (as-of joins).
    Column names match the parameter names in parameters.ts.
    """
    conn = get_conn()

    # All series IDs needed from DB
    needed = [
        # Core raw series
        "DGS10", "DGS2", "DGS30", "DGS5", "DGS3M",
        "T10YIE", "T5YIE", "T2YIE", "DFII10", "DFII5",
        "T10Y3M", "TEDRATE", "SOFR", "MORTGAGE30US", "IORB",
        "BAMLH0A0HYM2", "BAMLC0A0CM", "BAMLHE00EHYIOAS", "CPF3MTB3M",
        "WALCL", "WRBUSNS", "RRPONTSYD", "M1SL", "M2V",
        "ICSA", "CCSA", "JTSJOL", "JTSQUR", "UNRATE", "U6RATE", "CIVPART",
        "NAPM", "NAPMNO", "NAPMPI",
        "UMCSENT", "CSCICP03USM665S", "PSAVERT",
        "HOUST", "PERMIT", "ISRATIO",
        "USSLIND", "CFNAI", "USREC", "USPHCI", "USALOLITONOSTSAM",
        "TCU", "MICH",
        "DTWEXBGS", "DRSDCILM", "TOTCI", "TDSP", "DRCCLACBS",
        "DCOILWTICO", "DHHNGSP",
        "WAAABULL", "WAAABEAR",
        "GEOUSPRISK", "USEPUINDXD", "EMVTRADEPOL", "STLFSI2",
        "GFDEGDQ188S", "FYSGDA188S",
        # Derived series
        "T10Y2Y", "FEDFUNDS",
        "M2_GROWTH_YOY", "PCE_CORE_YOY", "PCE_HEADLINE_YOY",
        "CORE_CPI_YOY", "CPI_HEADLINE_YOY", "CPI_SHELTER_YOY",
        "PPI_YOY", "CORPORATE_PROFITS_YOY", "PERSONAL_INCOME_YOY",
        "CONSUMER_CREDIT_GROWTH", "BANK_CREDIT_GROWTH", "INDPRO_YOY",
        "RETAIL_SALES_YOY", "RETAIL_SALES_MOM", "DURABLE_GOODS_MOM",
        "NFP_MONTHLY", "CASE_SHILLER_YOY", "JOLTS_UNEMP_RATIO",
        "AAII_SPREAD",
        # YF raw
        "VIXCLS", "VVIX", "VIX3M", "SKEW",
        "DXY", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCNH", "USDCHF", "USDMXN",
        "GOLD", "SILVER", "OIL", "BRENT", "NATGAS", "COPPER", "ALUMINUM",
        "AGRI", "COMMODITY_IDX",
        "SPX", "SPY", "QQQ", "IWM", "IVV", "IWD", "IWF", "MDY",
        "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLRE", "KBE",
        "TLT", "IEF", "HYG", "LQD", "TIP",
        "EWJ", "EWG", "EWU", "EWZ", "FXI", "EEM", "EWH", "EWY", "INDA", "ACWI", "VEA", "VWO",
        "BTC", "ETH",
        # YF-derived
        "DXY_RET20", "GOLD_RET20", "GOLD_EQUITY_RATIO", "COPPER_RET20", "OIL_RET20",
        "USDJPY_RET5", "BTC_SPX_CORR_30D",
        "BRENT_RET20", "SILVER_RET20", "NATGAS_RET20", "ALUMINUM_RET20",
        "AGRI_RET20", "EURUSD_RET20", "GBPUSD_RET20", "AUDUSD_RET20",
        "USDCNH_RET20", "USDCHF_RET20", "USDMXN_RET20", "BTC_RET20",
        "NIKKEI_RET20", "DAX_RET20", "FTSE_RET20", "EWZ_RET20",
        "SHANGHAI_RET20", "HANGSENG_RET20", "KOSPI_RET20", "SENSEX_RET20",
        "MSCI_WORLD_RET20", "MSCI_EM_RET20",
        "TLT_RET20", "IEF_RET20", "HYG_RET20",
        "COPPER_GOLD_RATIO", "OIL_GOLD_RATIO",
        "MSCI_EM_DM_RATIO", "IWM_SPY_RATIO", "IWD_IWF_RATIO",
        "MIDCAP_LARGECAP_RATIO", "XLY_XLP_RATIO",
        "XLK_SPY_RATIO", "XLF_SPY_RATIO", "XLE_SPY_RATIO",
        "XLV_SPY_RATIO", "XLU_SPY_RATIO", "XLP_SPY_RATIO",
        "HY_IG_ETF_RATIO", "TIPS_GOLD_RATIO", "ETH_BTC_RATIO",
        "VIX_TERM_SLOPE", "VARIANCE_RISK_PREMIUM",
        "BREAKEVEN_5Y5Y_FWD", "BREAKEVEN_SLOPE", "GOLD_REAL_YIELD_SPREAD",
        "SAFE_HAVEN_FLOW", "EQUITY_BOND_CORR_30D", "CROSS_ASSET_MOMENTUM",
        "BUFFETT_INDICATOR_PROXY",
    ]

    placeholders = ",".join("?" * len(needed))
    raw = conn.execute(f"""
        SELECT series_id, CAST(date AS DATE) as date, value
        FROM macro_indicators
        WHERE series_id IN ({placeholders})
        ORDER BY date
    """, needed).df()

    if raw.empty:
        return pd.DataFrame()

    raw["date"] = pd.to_datetime(raw["date"]).astype("datetime64[us]")
    wide = raw.pivot_table(index="date", columns="series_id", values="value", aggfunc="last")
    wide = wide.reset_index().sort_values("date")

    date_range = pd.date_range(wide["date"].min(), wide["date"].max(), freq="D", unit="us")
    wide = wide.set_index("date").reindex(date_range).ffill().reset_index()
    wide = wide.rename(columns={"index": "date"})
    wide["date"] = wide["date"].astype("datetime64[us]")

    def col(name, default=0.0):
        return wide[name].fillna(default) if name in wide.columns else pd.Series(default, index=wide.index)

    # ── Build output DataFrame ────────────────────────────────────────────────
    vix      = col("VIXCLS",      20.0)
    yc       = col("T10Y2Y",       0.0)
    fed      = col("FEDFUNDS",     3.0)
    hy       = col("BAMLH0A0HYM2", 300.0)
    ig       = col("BAMLC0A0CM",   100.0)
    tips10   = col("DFII10",       1.5)
    tips5    = col("DFII5",        1.5)
    m2_yoy   = col("M2_GROWTH_YOY", 0.0)
    icsa     = col("ICSA",         220.0)
    nfci     = col("NFCI",         0.0)
    pce_core = col("PCE_CORE_YOY", 2.0)
    walcl    = col("WALCL",        8e6)
    dxy      = col("DXY",          100.0)
    gold     = col("GOLD",         1800.0)
    copper   = col("COPPER",       4.0)
    oil_lvl  = col("OIL",          70.0)
    btc_lvl  = col("BTC",          30000.0)
    usdjpy   = col("USDJPY",       130.0)
    spx_lvl  = col("SPX",          4000.0)
    tlt_lvl  = col("TLT",          100.0)

    result = pd.DataFrame({
        "date": wide["date"],

        # ── Macro: Core Yields / Rates ────────────────────────────────────────
        "fed_rate":             fed.values,
        "us_10y_yield":         col("DGS10",    4.5).values,
        "us_2y_yield":          col("DGS2",     4.8).values,
        "us_30y_yield":         col("DGS30",    4.7).values,
        "us_5y_yield":          col("DGS5",     4.6).values,
        "yield_curve":          yc.values,
        "yield_curve_3m10y":    col("T10Y3M",   0.3).values,
        "yield_curve_inverted": (yc < 0).astype(float).values,
        "breakeven_10y":        col("T10YIE",   2.3).values,
        "breakeven_5y":         col("T5YIE",    2.3).values,
        "us_breakeven_2y":      col("T2YIE",    2.2).values,
        "tips_real_yield":      tips10.values,
        "real_yield_5y":        tips5.values,
        "term_premium_acm":     (col("DGS10", 4.5) - col("FEDFUNDS", 3.0) - pce_core).values,
        "yc_regime_code":       yc.apply(lambda v: 3. if v < -0.2 else (2. if v < 0 else (1. if v < 0.5 else 0.))).values,
        "sofr_rate":            col("SOFR",     5.3).values,
        "ted_spread":           col("TEDRATE",  0.25).values,
        "mortgage30y_rate":     col("MORTGAGE30US", 6.5).values,
        "iorb_rate":            col("IORB",     5.15).values,
        "breakeven_5y5y_forward": col("BREAKEVEN_5Y5Y_FWD", 2.3).values,
        "inflation_breakeven_slope": col("BREAKEVEN_SLOPE", 0.0).values,

        # ── Macro: Credit Spreads ─────────────────────────────────────────────
        "hy_spread":            hy.values,
        "ig_spread":            ig.values,
        "hy_spread_oas":        hy.values,
        "ccc_spread":           (hy * 2.5).values,   # Proxy: CCC ≈ 2.5x HY OAS
        "em_sovereign_spread":  col("BAMLHE00EHYIOAS", 320.0).values,
        "commercial_paper_spread": col("CPF3MTB3M", 0.1).values,
        "credit_regime":        hy.apply(lambda v: 2. if v >= 600 else (1. if v >= 350 else 0.)).values,

        # ── Macro: Fed / Liquidity ────────────────────────────────────────────
        "fed_balance_sheet":    (walcl / 1e6).values,   # Convert to $T
        "excess_reserves":      (col("WRBUSNS", 3e9) / 1e6).values,  # $T
        "reverse_repo_volume":  (col("RRPONTSYD", 5e11) / 1e12).values,  # $T
        "monetary_regime":      fed.apply(lambda v: 2. if v > 4. else (0. if v < 2. else 1.)).values,
        "monetary_policy_uncertainty": col("USEPUINDXD", 100.0).values,
        "m2_growth_yoy":        m2_yoy.values,
        "m2_velocity":          col("M2V",        1.2).values,
        "m1_money_supply":      col("M1SL",        20000.0).values,
        "bank_credit_growth":   col("BANK_CREDIT_GROWTH", 4.0).values,
        "consumer_credit_growth": col("CONSUMER_CREDIT_GROWTH", 3.5).values,
        "bank_lending_standards": col("DRSDCILM",  0.0).values,
        "loan_delinquency_rate": col("DRCCLACBS", 2.5).values,
        "household_debt_service_ratio": col("TDSP", 14.0).values,
        "nfci":                 nfci.values,
        "stl_fsi":              col("STLFSI2",    0.0).values,

        # ── Macro: Inflation ──────────────────────────────────────────────────
        "pce_core_yoy":         pce_core.values,
        "pce_headline_yoy":     col("PCE_HEADLINE_YOY", 2.5).values,
        "cpi_headline_yoy":     col("CPI_HEADLINE_YOY", 3.0).values,
        "cpi_core_yoy":         col("CORE_CPI_YOY",    3.2).values,
        "cpi_shelter_yoy":      col("CPI_SHELTER_YOY", 4.5).values,
        "ppi_yoy":              col("PPI_YOY",         2.2).values,
        "michigan_inflation_1y": col("MICH",           3.1).values,

        # ── Macro: Labor ──────────────────────────────────────────────────────
        "initial_claims":       icsa.values,
        "continuing_claims":    col("CCSA",        1700.0).values,
        "jolts_openings":       (col("JTSJOL",     8500.0) / 1000).values,  # K
        "jolts_quits_rate":     col("JTSQUR",      2.3).values,
        "unemployment_rate":    col("UNRATE",      4.0).values,
        "u6_underemployment":   col("U6RATE",      7.5).values,
        "nfp_monthly":          col("NFP_MONTHLY", 180.0).values,
        "labor_force_participation": col("CIVPART", 62.5).values,
        "job_openings_unemployment_ratio": col("JOLTS_UNEMP_RATIO", 1.5).values,

        # ── Macro: Activity / Output ──────────────────────────────────────────
        "gdp_growth_rate":      col("A191RL1Q225SBEA", 2.5).values,
        "industrial_production": col("INDPRO_YOY",    0.0).values,
        "capacity_utilization": col("TCU",            78.5).values,
        "retail_sales_mom":     col("RETAIL_SALES_MOM", 0.3).values,
        "retail_sales_yoy":     col("RETAIL_SALES_YOY", 3.0).values,
        "ism_manufacturing_pmi": col("NAPM",          50.0).values,
        "ism_new_orders":       col("NAPMNO",         50.0).values,
        "ism_prices_paid":      col("NAPMPI",         50.0).values,
        "durable_goods_orders": col("DURABLE_GOODS_MOM", 0.5).values,
        "corporate_profits_yoy": col("CORPORATE_PROFITS_YOY", 5.0).values,
        "personal_income_growth": col("PERSONAL_INCOME_YOY",  4.0).values,
        "personal_savings_rate": col("PSAVERT",       4.5).values,
        "business_inventories_ratio": col("ISRATIO",  1.35).values,
        "business_inventories_sales": col("ISRATIO",  1.35).values,  # alias
        "lei_composite":        col("USSLIND",        99.5).values,
        "cfnai":                col("CFNAI",          0.0).values,
        "nber_recession_flag":  col("USREC",          0.0).values,
        "conference_board_coincident": col("USPHCI",  100.0).values,
        "oecd_leading_indicator": col("USALOLITONOSTSAM", 100.0).values,
        "trade_balance":        (col("BOPGSTB",       -80000.0) / 1000).values,  # $B

        # ── Macro: Housing ────────────────────────────────────────────────────
        "housing_starts":       (col("HOUST",         1350.0) / 1000).values,  # K
        "building_permits":     (col("PERMIT",        1400.0) / 1000).values,  # K
        "case_shiller_hpi_yoy": col("CASE_SHILLER_YOY", 5.0).values,
        "housing_existing_sales": (col("EXHOSLUSM495S", 4000.0) / 1000).values,  # K

        # ── Macro: Fiscal ─────────────────────────────────────────────────────
        "us_debt_to_gdp":       col("GFDEGDQ188S",   120.0).values,
        "govt_spending_pct_gdp": col("FYSGDA188S",   20.0).values,

        # ── Macro: Consumer Sentiment ─────────────────────────────────────────
        "michigan_sentiment":   col("UMCSENT",        68.0).values,
        "consumer_confidence":  col("CSCICP03USM665S", 100.0).values,

        # ── Macro: Commodities (macro-level) ──────────────────────────────────
        "wti_crude_price":      col("DCOILWTICO",     70.0).values,
        "natural_gas_henry_hub": col("DHHNGSP",       2.5).values,
        "brent_crude_price":    col("BRENT",          75.0).values,
        "copper_dr_price":      copper.values,

        # ── Macro: Geopolitical uncertainty ───────────────────────────────────
        "gpr_index":            col("GEOUSPRISK",     100.0).values,
        "global_epu_macro":     col("USEPUINDXD",     100.0).values,
        "global_epu_index":     col("USEPUINDXD",     100.0).values,
        "trade_war_intensity":  col("EMVTRADEPOL",    50.0).values,

        # ── Macro: Dollar / FX (macro-level) ──────────────────────────────────
        "dxy_us_dollar_index":  dxy.values,
        "broad_dollar_index":   col("DTWEXBGS",       110.0).values,
        "eurusd_macro":         col("EURUSD",         1.08).values,
        "usdjpy_macro":         usdjpy.values,

        # ── Cross-asset: Currencies ───────────────────────────────────────────
        "eurusd_level":         col("EURUSD",         1.08).values,
        "eurusd_ret20":         col("EURUSD_RET20",   0.0).values,
        "gbpusd_ret20":         col("GBPUSD_RET20",   0.0).values,
        "usdjpy_level":         usdjpy.values,
        "usdjpy_ret5":          col("USDJPY_RET5",    0.0).values,
        "audusd_ret20":         col("AUDUSD_RET20",   0.0).values,
        "usdcnh_ret20":         col("USDCNH_RET20",   0.0).values,
        "usdchf_ret20":         col("USDCHF_RET20",   0.0).values,
        "usdmxn_ret20":         col("USDMXN_RET20",   0.0).values,
        "dxy":                  dxy.values,
        "dxy_ret20":            col("DXY_RET20",      0.0).values,

        # ── Cross-asset: Metals / Energy ──────────────────────────────────────
        "gold_level":           gold.values,
        "gold_ret20":           col("GOLD_RET20",     0.0).values,
        "gold_equity_ratio":    col("GOLD_EQUITY_RATIO", 5.0).values,
        "silver_ret20":         col("SILVER_RET20",   0.0).values,
        "crude_wti_level":      oil_lvl.values,
        "crude_brent_spread":   (col("BRENT", 75.0) - oil_lvl).values,
        "oil_ret20":            col("OIL_RET20",      0.0).values,
        "natural_gas_ret20":    col("NATGAS_RET20",   0.0).values,
        "copper_level":         copper.values,
        "copper_ret20":         col("COPPER_RET20",   0.0).values,
        "aluminum_ret20":       col("ALUMINUM_RET20", 0.0).values,
        "agricultural_index_ret20": col("AGRI_RET20", 0.0).values,
        "commodity_index_level": col("COMMODITY_IDX", 15.0).values,
        "copper_gold_ratio":    col("COPPER_GOLD_RATIO", 0.002).values,
        "oil_gold_ratio":       (oil_lvl / gold.replace(0, np.nan)).values,

        # ── Cross-asset: Global Bonds ─────────────────────────────────────────
        "us10y_cross_asset":    col("DGS10",          4.5).values,
        "us_bund_spread":       0.0,   # Need German yield data
        "treasury_jgb_spread":  0.0,
        "equity_bond_correlation_30d": col("EQUITY_BOND_CORR_30D", 0.0).values,
        "tips_gold_ratio":      col("TIPS_GOLD_RATIO", 0.0).values,

        # ── Cross-asset: International Equity ─────────────────────────────────
        "nikkei_ret20":         col("NIKKEI_RET20",   0.0).values,
        "dax_ret20":            col("DAX_RET20",      0.0).values,
        "ftse_ret20":           col("FTSE_RET20",     0.0).values,
        "shanghai_ret20":       col("SHANGHAI_RET20", 0.0).values,
        "hangseng_ret20":       col("HANGSENG_RET20", 0.0).values,
        "kospi_ret20":          col("KOSPI_RET20",    0.0).values,
        "sensex_ret20":         col("SENSEX_RET20",   0.0).values,
        "msci_world_ret20":     col("MSCI_WORLD_RET20", 0.0).values,
        "msci_em_dm_ratio":     col("MSCI_EM_DM_RATIO", 1.0).values,
        "msci_china_ret20":     col("SHANGHAI_RET20", 0.0).values,  # proxy

        # ── Cross-asset: US Sector ETFs ────────────────────────────────────────
        "xlk_spy_ratio":        col("XLK_SPY_RATIO",  1.0).values,
        "xle_spy_ratio":        col("XLE_SPY_RATIO",  1.0).values,
        "xlf_spy_ratio":        col("XLF_SPY_RATIO",  1.0).values,
        "xlv_spy_ratio":        col("XLV_SPY_RATIO",  1.0).values,
        "xlu_spy_ratio":        col("XLU_SPY_RATIO",  1.0).values,
        "xlp_spy_ratio":        col("XLP_SPY_RATIO",  1.0).values,
        "xly_xlp_ratio":        col("XLY_XLP_RATIO",  1.0).values,
        "defensive_cyclical_ratio": (col("XLU_SPY_RATIO", 1.0) + col("XLV_SPY_RATIO", 1.0) + col("XLP_SPY_RATIO", 1.0)).values / 3,
        "sector_rotation_score": (col("XLK_SPY_RATIO", 1.0) - col("XLU_SPY_RATIO", 1.0)).values,

        # ── Cross-asset: US Size/Style ────────────────────────────────────────
        "iwm_spy_ratio":        col("IWM_SPY_RATIO",  1.0).values,
        "iwd_iwf_ratio":        col("IWD_IWF_RATIO",  1.0).values,
        "midcap_largecap_ratio": col("MIDCAP_LARGECAP_RATIO", 1.0).values,

        # ── Cross-asset: Crypto ───────────────────────────────────────────────
        "btc_level":            btc_lvl.values,
        "btc_ret20":            col("BTC_RET20",       0.0).values,
        "eth_btc_ratio":        col("ETH_BTC_RATIO",   0.06).values,
        "btc_spx_corr":         col("BTC_SPX_CORR_30D", 0.0).values,

        # ── Cross-asset: Composite signals ───────────────────────────────────
        "cross_asset_momentum_composite": col("CROSS_ASSET_MOMENTUM", 0.0).values,
        "safe_haven_flow_index":  col("SAFE_HAVEN_FLOW", 0.0).values,
        "gold_real_yield_spread": col("GOLD_REAL_YIELD_SPREAD", 0.0).values,
        "emerging_market_debt_stress": col("BAMLHE00EHYIOAS", 320.0).values,

        # ── Sentiment: AAII ───────────────────────────────────────────────────
        "aaii_bull_pct":        col("WAAABULL",        38.0).values,
        "aaii_bear_pct":        col("WAAABEAR",        30.0).values,
        "aaii_bull_bear_spread": col("AAII_SPREAD",    8.0).values,

        # ── Sentiment: VIX-based ──────────────────────────────────────────────
        "vix":                  vix.values,
        "vix_regime":           vix.apply(lambda v: 0. if v < 15 else (1. if v < 25 else (2. if v < 35 else 3.))).values,
        "vvix":                 col("VVIX",            90.0).values,
        "vix_term_structure_slope": col("VIX_TERM_SLOPE", 1.1).values,
        "variance_risk_premium": col("VARIANCE_RISK_PREMIUM", 3.0).values,
        "vix_contango_m1m2":    (col("VIX3M", 20.0) / vix.replace(0, np.nan)).values,
        "skew_index":           col("SKEW",            125.0).values,

        # ── Sentiment: Warren Buffett indicator ───────────────────────────────
        "warren_buffett_indicator": col("BUFFETT_INDICATOR_PROXY", 0.0).values,

        # ── Technical breadth (market-wide, from macro feed) ─────────────────
        "vol_regime_code":      vix.apply(lambda v: 3. if v >= 35 else (2. if v >= 25 else (1. if v >= 15 else 0.))).values,

        # ── Geopolitical ──────────────────────────────────────────────────────
        "tariff_escalation_score": col("EMVTRADEPOL", 50.0).values,
    })

    return result


# ── Inference context ─────────────────────────────────────────────────────────

def get_macro_context() -> dict:
    """Most recent values for all macro/cross-asset/sentiment/geopolitical features."""
    conn = get_conn()

    def latest(sid: str, default: float = 0.0) -> float:
        row = conn.execute("""
            SELECT value FROM macro_indicators
            WHERE series_id = ? AND value IS NOT NULL
            ORDER BY date DESC LIMIT 1
        """, [sid]).fetchone()
        return float(row[0]) if row else default

    vix      = latest("VIXCLS",      20.0)
    yc       = latest("T10Y2Y",       0.0)
    fed      = latest("FEDFUNDS",     3.0)
    hy       = latest("BAMLH0A0HYM2", 300.0)
    ig       = latest("BAMLC0A0CM",   100.0)
    tips10   = latest("DFII10",       1.5)
    walcl    = latest("WALCL",        8e6)
    dxy      = latest("DXY",          100.0)
    gold     = latest("GOLD",         1800.0)
    copper   = latest("COPPER",       4.0)
    oil      = latest("OIL",          70.0)
    btc      = latest("BTC",          30000.0)
    usdjpy   = latest("USDJPY",       130.0)
    pce_core = latest("PCE_CORE_YOY", 2.0)
    m2_yoy   = latest("M2_GROWTH_YOY", 0.0)
    icsa     = latest("ICSA",         220.0)
    nfci     = latest("NFCI",         0.0)
    vvix     = latest("VVIX",         90.0)

    ctx = {
        # Core
        "vix":              vix,
        "vix_regime":       0. if vix < 15 else (1. if vix < 25 else (2. if vix < 35 else 3.)),
        "vol_regime_code":  3. if vix >= 35 else (2. if vix >= 25 else (1. if vix >= 15 else 0.)),
        "yield_curve":      yc,
        "yield_curve_3m10y": latest("T10Y3M", 0.3),
        "yield_curve_inverted": 1. if yc < 0 else 0.,
        "yc_regime_code":   3. if yc < -0.2 else (2. if yc < 0 else (1. if yc < 0.5 else 0.)),
        "fed_rate":         fed,
        "hy_spread":        hy,
        "ig_spread":        ig,
        "hy_spread_oas":    hy,
        "tips_real_yield":  tips10,
        "real_yield_5y":    latest("DFII5",    1.5),
        "m2_growth_yoy":    m2_yoy,
        "initial_claims":   icsa,
        "nfci":             nfci,
        "pce_core_yoy":     pce_core,
        "fed_balance_sheet": walcl / 1e6,
        "dxy":              dxy,
        "dxy_ret20":        latest("DXY_RET20",   0.0),
        "gold_equity_ratio": latest("GOLD_EQUITY_RATIO", 5.0),
        "copper_ret20":     latest("COPPER_RET20", 0.0),
        "usdjpy_ret5":      latest("USDJPY_RET5",  0.0),
        "oil_ret20":        latest("OIL_RET20",    0.0),
        "btc_spx_corr":     latest("BTC_SPX_CORR_30D", 0.0),
        "vvix":             vvix,
        # Additional macro
        "consumer_sentiment":    latest("UMCSENT", 80.0),
        "ism_manufacturing":     latest("NAPM",    50.0),
        "housing_starts":        latest("HOUST",   1350.0) / 1000,
        "case_shiller_hpi":      latest("CASE_SHILLER_YOY", 5.0),
        "industrial_production": latest("INDPRO_YOY", 0.0),
        "retail_sales":          latest("RETAIL_SALES_YOY", 3.0),
        "core_cpi_yoy":          latest("CORE_CPI_YOY", 2.0),
        "ppi":                   latest("PPI_YOY", 2.0),
        "breakeven_10y":         latest("T10YIE",  2.3),
        "money_velocity":        latest("M2V",     1.2),
        "total_consumer_credit": latest("CONSUMER_CREDIT_GROWTH", 3.5),
        "loan_standards":        latest("DRSDCILM", 0.0),
        "continuing_claims":     latest("CCSA",    1700.0),
        "job_openings":          latest("JTSJOL",  8500.0) / 1000,
        "broad_dollar_index":    latest("DTWEXBGS", 110.0),
        # All parameter-name-matched entries
        "unemployment_rate":     latest("UNRATE",  4.0),
        "u6_underemployment":    latest("U6RATE",  7.5),
        "cpi_headline_yoy":      latest("CPI_HEADLINE_YOY", 3.0),
        "cpi_core_yoy":          latest("CORE_CPI_YOY",    3.2),
        "cpi_shelter_yoy":       latest("CPI_SHELTER_YOY", 4.5),
        "ppi_yoy":               latest("PPI_YOY",  2.2),
        "ism_manufacturing_pmi": latest("NAPM",    50.0),
        "michigan_sentiment":    latest("UMCSENT", 68.0),
        "michigan_inflation_1y": latest("MICH",    3.1),
        "capacity_utilization":  latest("TCU",     78.5),
        "retail_sales_mom":      latest("RETAIL_SALES_MOM", 0.3),
        "consumer_confidence":   latest("CSCICP03USM665S", 100.0),
        "personal_savings_rate": latest("PSAVERT", 4.5),
        "housing_existing_sales": latest("EXHOSLUSM495S", 4000.0) / 1000,
        "wti_crude_price":       oil,
        "natural_gas_henry_hub": latest("DHHNGSP", 2.5),
        "brent_crude_price":     latest("BRENT",   75.0),
        "m1_money_supply":       latest("M1SL",    20000.0),
        "bank_credit_growth":    latest("BANK_CREDIT_GROWTH", 4.0),
        "ted_spread":            latest("TEDRATE", 0.25),
        "sofr_rate":             latest("SOFR",    5.3),
        "excess_reserves":       latest("WRBUSNS", 3e9) / 1e6,
        "reverse_repo_volume":   latest("RRPONTSYD", 5e11) / 1e12,
        "gpr_index":             latest("GEOUSPRISK", 100.0),
        "global_epu_macro":      latest("USEPUINDXD", 100.0),
        "trade_war_intensity":   latest("EMVTRADEPOL", 50.0),
        "aaii_bull_pct":         latest("WAAABULL", 38.0),
        "aaii_bear_pct":         latest("WAAABEAR", 30.0),
        "aaii_bull_bear_spread": latest("AAII_SPREAD", 8.0),
        "vix_term_structure_slope": latest("VIX_TERM_SLOPE", 1.1),
        "variance_risk_premium": latest("VARIANCE_RISK_PREMIUM", 3.0),
        "skew_index":            latest("SKEW",    125.0),
        "btc_level":             btc,
        "btc_ret20":             latest("BTC_RET20", 0.0),
        "gold_level":            gold,
        "copper_level":          copper,
        "crude_wti_level":       oil,
        "eurusd_level":          latest("EURUSD",  1.08),
        "usdjpy_level":          usdjpy,
        "dxy_us_dollar_index":   dxy,
        "eurusd_macro":          latest("EURUSD",  1.08),
        "usdjpy_macro":          usdjpy,
    }
    return ctx
