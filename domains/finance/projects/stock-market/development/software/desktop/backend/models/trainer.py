"""
Prediction Engine — Layer 4 of the ADPS architecture.

Trains a regime-aware GBM ensemble:
  - One GLOBAL model (all data)
  - One model per VIX volatility regime (LOW/NORMAL/ELEVATED/CRISIS)
  - Sector models where data allows

Feature set: ALL 656 parameters across macro, technical, fundamental,
cross-asset, sentiment, and geopolitical domains.
Feature column names match the parameter names defined in parameters.ts.
"""

import json
import logging
import pickle
import re
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler

try:
    from ta.trend import MACD, ADXIndicator, AroonIndicator
    from ta.momentum import (StochasticOscillator, WilliamsRIndicator,
                              CCIIndicator, UltimateOscillator, ROCIndicator)
    from ta.volatility import BollingerBands, AverageTrueRange
    from ta.volume import (OnBalanceVolumeIndicator, MFIIndicator,
                            ChaikinMoneyFlowIndicator, VolumePriceTrendIndicator,
                            AccDistIndexIndicator)
    _TA_AVAILABLE = True
except ImportError:
    _TA_AVAILABLE = False

from backend.config import MODELS_DIR, ACCURACY_THRESHOLD
from backend.database.duckdb_client import get_conn

logger = logging.getLogger(__name__)

HORIZON_DAYS = {"1d": 1, "1w": 5, "1m": 21}
HORIZON_MODEL_PATHS    = {h: MODELS_DIR / f"model_{h}.pkl"    for h in HORIZON_DAYS}
HORIZON_SCALER_PATHS   = {h: MODELS_DIR / f"scaler_{h}.pkl"   for h in HORIZON_DAYS}
HORIZON_FEATURES_PATHS = {h: MODELS_DIR / f"features_{h}.json" for h in HORIZON_DAYS}
ACCURACY_LOG_PATH      = MODELS_DIR / "accuracy_history.json"

SECTORS_DIR = MODELS_DIR / "sectors"
SECTORS_DIR.mkdir(parents=True, exist_ok=True)

REGIMES_DIR = MODELS_DIR / "regimes"
REGIMES_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH  = HORIZON_MODEL_PATHS["1w"]
SCALER_PATH = HORIZON_SCALER_PATHS["1w"]

MODEL_VERSION = "4.0"   # Bump triggers full retrain with 656 features

# ── Technical feature columns (95) ────────────────────────────────────────────
# Column names match parameters.ts technical domain parameter names.

TECHNICAL_COLS = [
    # Return windows
    "return_1d", "return_5d", "return_20d", "return_60d",
    "return_126d", "return_252d", "return_504d", "reversal_longrun",
    # Moving averages (deviation from close)
    "ma_5", "ma_20", "ma_50", "ma_200",
    # Momentum oscillators
    "macd_signal", "rsi", "stochastic_k", "cci_14", "williams_r", "roc_20",
    "aroon_oscillator", "ultimate_oscillator", "chande_momentum_osc",
    # Price structure
    "high_52w_ratio", "ath_ratio", "residual_momentum",
    "max_drawdown_52w", "price_trend_r2",
    # Volatility / risk
    "volatility_20", "volatility_60", "atr_14",
    "bollinger_pct_b", "bollinger_bandwidth",
    # Volume / liquidity
    "volume_ratio", "amihud_illiquidity",
    "obv_divergence", "chaikin_money_flow",
    "volume_price_trend", "ad_accumulation_distribution",
    "dollar_volume_turnover", "volume_weighted_momentum",
    "aroon_oscillator_25",
    # Advanced moving averages
    "hull_moving_average", "kama_adaptive_ma", "ma_envelope_pct",
    # Price action
    "opening_gap_pct", "opening_gap_size", "gap",
    "vwap_deviation", "pivot_point_position",
    "inside_bar_breakout", "inside_bar_signal",
    "key_reversal_day_flag", "price_round_number", "price_round_number_proximity",
    # Market regime (from macro, used as technical feature)
    "vol_regime_code", "vix", "vix_regime", "vvix",
    "vix_term_structure_slope",
    "skew_index", "put_call_ratio", "index_put_call_ratio",
    "gamma_exposure_gex",
    # Market breadth (from macro feed)
    "advance_decline_line", "pct_above_ma50", "pct_above_ma200",
    "new_highs_lows", "mcclellan_oscillator", "trin_arms_index",
    # Relative strength
    "rs_vs_index", "rs_vs_sector",
    # Microstructure proxies
    "kyle_lambda", "kyle_lambda_daily",
    "bid_ask_spread_rel", "vpin_signal",
    "order_flow_delta", "cumulative_delta_divergence",
    "intraday_vwap_deviation",
    "volume_profile_poc", "order_book_imbalance",
    "footprint_imbalance_score",
    # Cross-sectional ranks (computed across all tickers per date)
    "rsi_rank", "return_5d_rank", "return_20d_rank",
    "volatility_20_rank", "volume_ratio_rank", "short_ratio_rank",
    # Calendar effects
    "turn_of_month_flag", "january_effect_flag",
    "halloween_effect_nov_apr", "options_expiry_week_flag",
    "quarterly_rebalancing_week",
    # Event flags
    "insider_buying_flag", "earnings_blackout_window",
]

# ── Fundamental feature columns (145) ────────────────────────────────────────
# Column names match parameters.ts fundamental domain parameter names.

FUNDAMENTAL_COLS = [
    # Valuation multiples
    "pe_ratio_forward", "pe_ratio_trailing", "pb_ratio", "ps_ratio",
    "ev_ebitda", "ev_sales", "peg_ratio", "price_fcf",
    "ev_invested_capital", "price_tangible_book", "ev_gross_profit",
    # Profitability / Returns
    "roe", "roa", "roic", "gross_margin", "ebitda_margin",
    "operating_margin", "net_margin", "nopat_margin", "asset_turnover",
    # Growth
    "revenue_growth_1y", "revenue_growth_3y", "eps_growth_1y", "eps_growth_3y",
    "fcf_growth_1y", "book_value_growth", "ebitda_growth",
    # Balance sheet / leverage
    "debt_equity_ratio", "interest_coverage", "current_ratio", "quick_ratio",
    "altman_z_score", "net_debt_ebitda", "cash_debt_ratio",
    # Capital efficiency
    "capex_revenue", "rd_revenue", "working_capital_ratio",
    "fcf_yield", "fcf_margin", "capex_intensity", "maintenance_capex_ratio",
    "owner_earnings_yield", "cash_conversion_ratio",
    # Dividends / buybacks
    "dividend_yield", "payout_ratio", "buyback_yield",
    "total_shareholder_yield", "dividend_growth_5y",
    # Earnings quality
    "earnings_quality_score", "accruals_ratio", "earnings_persistence",
    # Earnings revisions / surprises
    "revenue_surprise", "eps_surprise", "guidance_revision",
    "beat_miss_ratio", "analyst_consensus_buy_pct",
    "analyst_price_target_upside",
    "estimate_revision_1m", "estimate_revision_3m",
    "estimate_breadth", "analyst_dispersion", "upgrade_downgrade_ratio",
    # Ownership / flows
    "institutional_ownership_pct", "insider_ownership_pct",
    "insider_buy_sell_ratio", "institutional_flow_change",
    # Short interest
    "short_interest_pct_float", "days_to_cover", "short_interest_change_1m",
    # Operating efficiency
    "inventory_turnover", "receivables_turnover", "dso_days",
    "cash_conversion_cycle", "sga_efficiency",
    "revenue_per_employee", "gross_profit_per_employee",
    # Sector-specific
    "semiconductor_book_to_bill", "retail_sss_growth",
    "subscription_revenue_pct", "net_revenue_retention",
    "cloud_revenue_growth", "drug_pipeline_value", "patent_expiry_cliff",
    "commodity_cost_sensitivity", "revenue_concentration_risk",
    "geographic_revenue_mix",
    # Trend / momentum
    "gross_margin_trend", "operating_leverage", "financial_leverage",
    "ebitda_to_capex", "reinvestment_rate", "roic_vs_wacc",
    "sustainable_growth_rate",
    # Relative valuation
    "earnings_yield_gap", "enterprise_value_to_sales",
    "price_book_momentum", "net_profit_margin_yoy",
    "dividend_coverage_ratio", "share_count_change",
    "revenue_per_unit_yoy", "market_share_change",
    # Capital allocation
    "working_capital_intensity", "capital_allocation_quality",
    "management_incentive_alignment",
    # ESG / risk
    "esg_controversy_score", "climate_risk_score", "regulatory_risk_score",
    # Alternative metrics
    "customer_lifetime_value", "net_promoter_score",
    "technology_spend_intensity", "deferred_revenue_growth",
    # Tax / pension
    "tax_rate_effective", "pension_liability_funding",
    "off_balance_sheet_exposure", "goodwill_to_assets",
    # Cash flow
    "cash_flow_from_ops_yoy", "sbc_pct_revenue",
    # Debt structure
    "debt_maturity_profile", "covenant_stress_score",
    "accounts_receivable_quality",
    # Management / governance
    "ceo_tenure", "spinoff_flag", "acquisition_activity_score",
    "research_productivity", "insider_ownership_change",
    "cfo_change_flag", "auditor_opinion_risk", "earnings_restatement_history",
    "free_float_pct", "index_membership_flag",
    # Estimates
    "forward_rev_growth_estimate", "peg_premium_discount",
    "asset_impairment_risk", "working_capital_change_fcf",
    "implied_probability_miss", "sector_cycle_position",
    "ebitda_bridge_drivers", "earnings_seasonality_pattern",
    # Quality flags
    "dividend_aristocrat_flag", "revenue_quality_score",
    "capex_guidance_revision", "altman_z_trend",
    "segment_margin_dispersion", "optionality_value",
    "management_guidance_accuracy",
    # Extra useful fields from yfinance not in the named params above
    "beta",
]

# ── Macro feature columns (136) ───────────────────────────────────────────────

MACRO_COLS = [
    # GDP / Growth
    "gdp_growth_rate", "gdp_nowcast",
    # Labor
    "unemployment_rate", "u6_underemployment", "nfp_monthly",
    "initial_claims", "continuing_claims", "jolts_openings", "jolts_quits_rate",
    "labor_force_participation",
    # Inflation
    "cpi_headline_yoy", "cpi_core_yoy", "cpi_shelter_yoy", "pce_core_yoy",
    "pce_headline_yoy", "ppi_yoy",
    "michigan_inflation_1y", "michigan_inflation_5y",
    # Activity
    "ism_manufacturing_pmi", "ism_services_pmi", "ism_new_orders", "ism_prices_paid",
    "industrial_production", "capacity_utilization",
    "retail_sales_mom", "consumer_confidence", "michigan_sentiment",
    "personal_income_growth", "personal_savings_rate",
    "housing_starts", "building_permits", "durable_goods_orders", "core_capex_orders",
    "lei_composite", "cfnai", "nber_recession_flag",
    "business_inventories_ratio", "trade_balance", "corporate_profits_yoy",
    "conference_board_coincident", "oecd_leading_indicator",
    "housing_existing_sales", "case_shiller_hpi_yoy",
    "business_inventories_sales",
    # Fed / Policy
    "fed_rate", "fed_funds_futures_prob", "fed_balance_sheet",
    "excess_reserves", "fomc_dot_plot_median", "monetary_regime",
    "reverse_repo_volume", "iorb_rate",
    "ecb_deposit_rate", "boj_policy_rate", "pboc_loan_prime_rate",
    "monetary_policy_uncertainty",
    # Yields / Rates
    "yield_curve", "yield_curve_3m10y", "yield_curve_inverted",
    "us_10y_yield", "us_2y_yield", "us_30y_yield",
    "breakeven_5y", "breakeven_10y", "tips_real_yield", "real_yield_5y",
    "term_premium_acm", "yc_regime_code",
    "sofr_rate", "ted_spread", "mortgage30y_rate",
    # Credit / Banking
    "hy_spread", "ig_spread", "ccc_spread",
    "em_sovereign_spread", "bank_lending_standards",
    "consumer_credit_growth", "move_index", "nfci",
    "m2_growth_yoy", "m2_velocity", "bank_credit_growth",
    "global_m2_growth", "repo_stress",
    "us_debt_to_gdp", "federal_deficit_pct_gdp", "treasury_issuance_net",
    "commercial_paper_spread", "leveraged_loan_spread",
    "loan_delinquency_rate", "bank_charge_off_rate", "bank_cds_spread",
    "kbw_bank_index", "shadow_banking_size", "household_debt_service_ratio",
    "corporate_debt_ebitda", "interest_coverage_economy",
    # Global / PMI
    "china_caixin_pmi", "eurozone_pmi_composite", "global_pmi_composite",
    "baltic_dry_index", "global_supply_chain_pressure",
    "global_epu_index", "credit_regime",
    "import_price_index_yoy", "export_price_index_yoy",
    "breakeven_5y5y_forward",
    # Fiscal
    "govt_spending_pct_gdp",
    "ecb_balance_sheet", "boj_balance_sheet", "pboc_rrr",
    "boe_base_rate", "rba_cash_rate", "global_cb_rate_differential",
    # Commodities / macro
    "wti_crude_price", "natural_gas_henry_hub", "copper_dr_price",
    "crb_commodity_index", "brent_crude_price",
    # Money
    "m1_money_supply", "eurodollar_futures_implied_rate",
    "clo_issuance_monthly", "fed_stress_test_score",
    "bank_cet1_ratio", "nondefense_capex_orders",
    # FX macro
    "ny_fed_global_supply_chain", "dxy_us_dollar_index",
    "eurusd_macro", "usdjpy_macro", "em_currency_macro", "fx_implied_volatility",
    # International
    "japan_tankan_survey", "china_nbs_pmi",
    "global_trade_volume_yoy", "global_epu_macro",
    "retail_ex_auto_gas", "job_openings_unemployment_ratio",
    "corporate_bond_issuance", "pce_headline_yoy_macro",
]

# ── Cross-asset feature columns (112) ─────────────────────────────────────────

CROSS_ASSET_COLS = [
    # Currencies
    "eurusd_level", "eurusd_ret20", "gbpusd_ret20",
    "usdjpy_level", "usdjpy_ret5", "audusd_ret20",
    "usdcnh_ret20", "usdchf_ret20", "usdmxn_ret20",
    "dxy", "dxy_ret20",
    "em_currency_index_ret20", "g10_vol_index",
    # Precious metals
    "gold_level", "gold_ret20", "gold_equity_ratio", "silver_ret20",
    # Energy / commodities
    "crude_wti_level", "crude_brent_spread", "oil_ret20",
    "natural_gas_ret20", "copper_level", "copper_ret20",
    "iron_ore_ret20", "aluminum_ret20",
    "agricultural_index_ret20", "commodity_index_level",
    # Bonds (cross-asset perspective)
    "us10y_cross_asset", "us_5y_yield",
    "germany_10y_yield", "japan_10y_yield", "uk_10y_yield",
    "us_breakeven_2y", "us_bund_spread", "treasury_jgb_spread",
    "global_bond_risk_premium",
    # International equity
    "nikkei_ret20", "dax_ret20", "ftse_ret20",
    "shanghai_ret20", "hangseng_ret20", "kospi_ret20",
    "sensex_ret20", "msci_world_ret20",
    "msci_em_dm_ratio", "msci_china_ret20", "emerging_market_flow",
    # Sector ETF ratios
    "xlk_spy_ratio", "xle_spy_ratio", "xlf_spy_ratio",
    "xlv_spy_ratio", "xlu_spy_ratio", "xlp_spy_ratio",
    "xly_xlp_ratio", "sector_rotation_score",
    "defensive_cyclical_ratio",
    # Size/style
    "iwm_spy_ratio", "iwd_iwf_ratio", "midcap_largecap_ratio",
    "quality_junk_ratio", "dividend_vs_growth_ratio",
    # Crypto
    "btc_level", "btc_ret20", "eth_btc_ratio",
    "crypto_total_mcap_change", "btc_dominance", "defi_tvl_change",
    "btc_spx_corr",
    # Flows (mostly proxied)
    "equity_fund_flow_4w", "bond_fund_flow_4w",
    "money_market_flow_4w", "etf_net_creation_4w",
    "em_equity_flow_4w", "sector_etf_flow_momentum",
    # Global macro
    "bdi_ret20", "container_freight_rate",
    "global_trade_volume_mom", "china_credit_impulse",
    "synchronized_expansion_flag", "global_capex_cycle",
    "oecd_lei", "real_effective_exchange_rate",
    "jpy_reer", "usd_em_carry_score",
    "global_risk_appetite_index",
    # Composite signals
    "gold_real_yield_spread", "bitcoin_global_liquidity",
    "vix_vs_vstoxx_ratio", "credit_vs_equity_signal",
    "tips_gold_ratio", "equity_bond_correlation_30d",
    "cross_asset_momentum_composite", "safe_haven_flow_index",
    "commodity_equity_ratio", "global_dividend_yield_premium",
    # Geo/risk flags (cross-asset domain)
    "taiwan_strait_risk_flag", "china_total_social_financing_yoy",
    "global_synchronized_recession_flag", "emerging_market_debt_stress",
    "global_banks_cross_border", "g20_fiscal_impulse",
    "us_china_trade_flow_mom",
    # Alternative markets
    "spac_ipo_volume", "convertible_bond_activity",
    "private_credit_market_spread", "inflation_breakeven_slope",
    "high_yield_etf_flow", "sovereign_cds_basket",
    "real_estate_cap_rate_spread",
    "copper_gold_ratio", "oil_gold_ratio", "us_tga_balance",
]

# ── Sentiment feature columns (95) ────────────────────────────────────────────

SENTIMENT_COLS = [
    # AAII / surveys
    "aaii_bull_pct", "aaii_bear_pct", "aaii_bull_bear_spread",
    "investors_intelligence_bull_bear", "naaim_exposure_index",
    "cnn_fear_greed",
    # Options sentiment
    "equity_put_call_ratio", "spx_put_call_ratio",
    "vix_contango_m1m2", "variance_risk_premium",
    "options_implied_move", "call_put_oi_ratio",
    "unusual_call_volume_flag", "unusual_put_volume_flag",
    "delta_adjusted_oi", "net_options_flow",
    # Margin / short
    "margin_debt_level", "margin_debt_yoy", "margin_debt_spy_ratio",
    "margin_debt_mom",
    "short_interest_spy", "short_squeeze_risk_score",
    # Flow / dark pool
    "retail_vs_institutional_flow", "dark_pool_volume_pct",
    # Insider activity
    "insider_buy_cluster_30d", "insider_sell_cluster_30d",
    "insider_net_buy_score", "form4_sentiment_score",
    "c_suite_net_buying", "officer_buy_sell_ratio",
    # Analyst sentiment
    "sell_side_consensus_change", "analyst_herding_measure",
    "estimate_revision_breadth_momentum", "earnings_estimate_optimism",
    "analyst_upgrade_momentum_30d", "price_target_revision_momentum",
    # Alternative data
    "news_sentiment_score", "social_media_mention_velocity",
    "reddit_wsb_mention_count", "google_trends_spike",
    "twitter_sentiment_score", "news_volume_abnormal_flag",
    # Behavioral / anomalies
    "momentum_crash_risk", "lottery_ticket_demand",
    "behavioral_overreaction_score", "pead_strength",
    "short_squeeze_potential", "crowding_score", "retail_mania_flag",
    # Calendar / cycle
    "presidential_cycle_year", "earnings_season_crowding_score",
    # Positioning
    "fund_manager_cash_level", "aastock_allocation",
    "risk_parity_leverage_signal", "etf_short_ratio",
    "volatility_targeting_flow", "ctacommodity_trend_signal",
    "global_risk_off_index", "buyback_window_open",
    "global_investor_surveys_bull", "fund_manager_equity_allocation",
    "fund_manager_cash_allocation",
    # Options market structure
    "options_implied_move_earnings", "call_buying_skew",
    "dealer_gamma_positioning", "total_return_swap_flow",
    "etf_creation_redemption", "passive_vs_active_flow",
    "options_volume_put_call", "volatility_risk_premium",
    # Composite signals
    "smart_dumb_money_index", "mutual_fund_redemption_risk",
    "equity_issuance_volume", "options_open_interest_call_wall",
    "analyst_coverage_initiation", "hedge_fund_position_concentration",
    "stock_loan_fee", "analyst_sentiment_distribution",
    "retail_trading_volume_share", "options_sweep_unusual",
    "warren_buffett_indicator", "equity_risk_premium_estimate",
    "fear_greed_subcomponent_momentum", "cftc_speculative_positioning",
    "high_yield_inflow_outflow", "sector_rotation_leadership",
    "vix_spike_recovery", "sentiment_composite_retail",
    "implied_dividend_growth", "market_concentration_top5",
    "breadth_thrust_signal", "trin_10d_average",
    "mcclellan_summation_index", "advance_decline_volume_ratio",
    "bear_market_rally_detection",
]

# ── Geopolitical feature columns (73) ─────────────────────────────────────────

GEOPOLITICAL_COLS = [
    "gpr_index",
    "interstate_war_flag", "military_escalation_score",
    "terrorism_index", "nuclear_threat_level",
    "coup_political_instability", "cyberattack_severity_flag",
    "maritime_disruption_flag",
    "tariff_escalation_score", "trade_war_intensity",
    "export_control_flag", "sanctions_intensity", "sanctions_relief_flag",
    "us_presidential_cycle_flag", "divided_government_flag",
    "debt_ceiling_risk_score", "government_shutdown_flag",
    "political_polarization_index", "populist_policy_risk",
    "antitrust_intensity", "financial_regulation_cycle",
    "drug_pricing_risk", "epa_regulatory_risk",
    "data_privacy_regulatory_risk", "ai_regulation_risk",
    "crypto_regulation_risk", "corporate_tax_change_risk",
    "opec_cut_flag",
    "russia_ukraine_risk", "china_taiwan_risk",
    "us_china_diplomatic_score", "cfius_activity_flag",
    "sovereign_debt_crisis_risk", "central_bank_independence_risk",
    "fiscal_stimulus_score", "carbon_price_level", "climate_policy_risk",
    "pandemic_risk_flag", "food_security_risk", "rare_earth_supply_risk",
    "energy_transition_policy_score", "nuclear_policy_flag",
    "supply_chain_decoupling_score", "wto_dispute_score",
    "country_risk_rating", "em_election_risk",
    "rule_of_law_index", "disinformation_risk_flag",
    "healthcare_regulation_risk", "labor_regulation_risk",
    "capital_gains_tax_risk", "defense_spending_trend",
    "trade_agreement_formation_flag", "bilateral_tariff_level",
    "export_control_entity_list_size", "ofac_sanctions_list_size",
    "sec_enforcement_actions_yoy", "antitrust_investigation_count",
    "financial_regulation_hawkishness",
    "drug_pricing_negotiation_count", "carbon_border_adjustment_risk",
    "eu_ets_carbon_price", "ai_chip_export_restriction_level",
    "ira_clean_energy_spend_pace", "nato_commitment_score",
    "arctic_resource_development_risk", "global_minimum_tax_implementation",
    "wto_dispute_count_active", "food_export_ban_flag",
    "water_scarcity_index", "pandemic_preparedness_score",
    "internet_fragmentation_risk", "cfius_deal_block_rate",
]

# ── Combined feature list ─────────────────────────────────────────────────────

BASE_FEATURE_COLS = (
    TECHNICAL_COLS + FUNDAMENTAL_COLS + MACRO_COLS +
    CROSS_ASSET_COLS + SENTIMENT_COLS + GEOPOLITICAL_COLS
)

# Backward-compatible alias used by predictor.py
BASE_TECHNICAL_COLS = TECHNICAL_COLS

# Cross-sectional rank source columns (ranked by date across all tickers)
CROSS_RANK_SOURCE_COLS = [
    "rsi", "return_5d", "return_20d", "return_252d",
    "volatility_20", "volume_ratio", "short_ratio",
]

# Full feature list (base + cross-sectional ranks not already in TECHNICAL_COLS)
_extra_rank_cols = [f"{c}_rank" for c in CROSS_RANK_SOURCE_COLS
                    if f"{c}_rank" not in BASE_FEATURE_COLS]
FEATURE_COLS = BASE_FEATURE_COLS + _extra_rank_cols

# Vol regime codes
VOL_REGIME_KEYS = {0: "low", 1: "normal", 2: "elevated", 3: "crisis"}


# ── Technical feature engineering ─────────────────────────────────────────────

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values("date")
    c   = df["close"]
    vol = df["volume"].fillna(0).astype(float)
    hi  = df["high"] if "high" in df.columns else c
    lo  = df["low"]  if "low"  in df.columns else c
    op  = df["open"] if "open" in df.columns else c
    dv  = c * vol

    # ── Return windows ─────────────────────────────────────────────────────
    df["return_1d"]    = c.pct_change(1)
    df["return_5d"]    = c.pct_change(5)
    df["return_20d"]   = c.pct_change(20)
    df["return_60d"]   = c.pct_change(60)
    df["return_126d"]  = c.pct_change(126)
    df["return_252d"]  = c.pct_change(252)
    df["return_504d"]  = c.pct_change(504)
    df["reversal_longrun"] = -c.pct_change(252)  # long-run reversal signal

    # ── Moving average deviations ──────────────────────────────────────────
    df["ma_5"]   = c.rolling(5).mean() / c - 1
    df["ma_20"]  = c.rolling(20).mean() / c - 1
    df["ma_50"]  = c.rolling(50).mean() / c - 1
    df["ma_200"] = c.rolling(200).mean() / c - 1

    for window, name in [(10, "ma10"), (100, "ma100")]:
        ma = c.rolling(window).mean().replace(0, np.nan)
        df[f"{name}_ratio"] = c / ma

    # ── Volatility ─────────────────────────────────────────────────────────
    df["volatility_20"] = c.pct_change().rolling(20).std()
    df["volatility_60"] = c.pct_change().rolling(60).std()

    # ── Volume ratios ──────────────────────────────────────────────────────
    roll_mean = vol.rolling(20).mean().replace(0, np.nan)
    df["volume_ratio"]  = vol / roll_mean
    df["dollar_volume_turnover"] = (dv / dv.rolling(20).mean().replace(0, np.nan))

    # ── RSI (14) ───────────────────────────────────────────────────────────
    delta = c.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))

    # ── 52-week high ratio and ATH ratio ──────────────────────────────────
    high_52w = c.rolling(252).max()
    df["high_52w_ratio"] = c / high_52w.replace(0, np.nan)
    ath = c.expanding().max().replace(0, np.nan)
    df["ath_ratio"] = c / ath

    # ── Amihud illiquidity ────────────────────────────────────────────────
    abs_ret = c.pct_change().abs()
    dv_roll = dv.rolling(20).mean().replace(0, np.nan)
    df["amihud_illiquidity"] = (abs_ret / dv_roll * 1e6).rolling(5).mean()

    # ── Rate of change ─────────────────────────────────────────────────────
    df["roc_20"] = c.pct_change(20)

    # ── Volume-weighted momentum ───────────────────────────────────────────
    df["volume_weighted_momentum"] = (c.pct_change(5) * vol / vol.rolling(5).mean().replace(0, 1)).rolling(5).mean()

    # ── Price structure ────────────────────────────────────────────────────
    df["high_low_ratio"]   = hi / lo.replace(0, np.nan)
    df["close_high_ratio"] = c / hi.rolling(52 * 5).max().replace(0, np.nan)
    df["close_low_ratio"]  = c / lo.rolling(52 * 5).min().replace(0, np.nan)
    df["gap"] = (op - c.shift(1)) / c.shift(1).replace(0, np.nan)
    df["opening_gap_pct"] = df["gap"]
    df["opening_gap_size"] = (op - c.shift(1)).abs() / c.shift(1).replace(0, np.nan)

    # ── Max drawdown 52-week ───────────────────────────────────────────────
    rolling_max_52 = c.rolling(252).max()
    df["max_drawdown_52w"] = (c - rolling_max_52) / rolling_max_52.replace(0, np.nan)

    # ── VWAP deviation (daily approximation: close vs typical price MA) ───
    typical = (hi + lo + c) / 3
    df["vwap_deviation"] = (c - typical.rolling(20).mean()) / typical.rolling(20).mean().replace(0, np.nan)
    df["intraday_vwap_deviation"] = (c - typical) / typical.replace(0, np.nan)

    # ── Pivot point position (close vs (H+L+C)/3 of prior period) ─────────
    prior_pivot = (hi.shift(1) + lo.shift(1) + c.shift(1)) / 3
    df["pivot_point_position"] = (c - prior_pivot) / prior_pivot.replace(0, np.nan)

    # ── Kyle lambda (price impact: ΔP / ΔV proxy) ─────────────────────────
    dprice = c.diff().abs()
    dvol   = vol.diff().abs().replace(0, np.nan)
    kyle = (dprice / dvol).rolling(20).mean()
    df["kyle_lambda"]       = kyle
    df["kyle_lambda_daily"] = kyle

    # ── Order flow delta (approximation from close vs open) ────────────────
    df["order_flow_delta"] = (c - op) / (hi - lo).replace(0, np.nan)
    df["cumulative_delta_divergence"] = df["order_flow_delta"].rolling(10).sum()

    # ── Price trend R² (rolling regression proxy) ─────────────────────────
    log_c = np.log(c.replace(0, np.nan))
    roll_std = log_c.rolling(20).std()
    roll_mean = log_c.rolling(20).mean()
    df["price_trend_r2"] = ((log_c - roll_mean) / roll_std.replace(0, np.nan)).rolling(20).corr(
        pd.Series(range(len(df)), index=df.index).rolling(20).apply(lambda x: x.iloc[-1] - x.mean())
    ).abs()

    # ── Residual momentum (momentum adjusted for market beta proxy) ────────
    df["residual_momentum"] = c.pct_change(252) - c.pct_change(20) * 12

    # ── MA envelope ────────────────────────────────────────────────────────
    ma20 = c.rolling(20).mean()
    df["ma_envelope_pct"] = (c - ma20) / ma20.replace(0, np.nan)

    # ── Hull moving average (2*WMA(n/2) - WMA(n)) ────────────────────────
    def wma(series, n):
        weights = np.arange(1, n + 1)
        return series.rolling(n).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    hull = 2 * wma(c, 10) - wma(c, 20)
    df["hull_moving_average"] = (c - hull) / hull.replace(0, np.nan)

    # ── KAMA (simplified adaptive MA) ─────────────────────────────────────
    df["kama_adaptive_ma"] = c.ewm(span=20, adjust=False).mean() / c - 1

    # ── Calendar effects ───────────────────────────────────────────────────
    dates = pd.to_datetime(df["date"])
    month = dates.dt.month
    day   = dates.dt.day
    dom_last   = dates.dt.days_in_month
    df["turn_of_month_flag"]   = ((day >= dom_last - 2) | (day <= 3)).astype(float)
    df["january_effect_flag"]  = (month == 1).astype(float)
    df["halloween_effect_nov_apr"] = (month >= 11) | (month <= 4)
    df["halloween_effect_nov_apr"] = df["halloween_effect_nov_apr"].astype(float)
    # Options expiry: 3rd Friday of each month (approximate: day 15-21, Friday)
    df["options_expiry_week_flag"] = ((day >= 15) & (day <= 21) & (dates.dt.dayofweek == 4)).astype(float)
    # Quarterly rebalancing: last week of Mar/Jun/Sep/Dec
    is_qtr_end_month = month.isin([3, 6, 9, 12])
    df["quarterly_rebalancing_week"] = (is_qtr_end_month & (day >= dom_last - 5)).astype(float)

    # ── Candlestick patterns ───────────────────────────────────────────────
    prev_hi = hi.shift(1)
    prev_lo = lo.shift(1)
    df["inside_bar_breakout"] = ((hi > prev_hi) & (lo < prev_lo)).astype(float)
    df["inside_bar_signal"] = ((hi < prev_hi) & (lo > prev_lo)).astype(float)
    # Key reversal: close > prior high after opening below prior low (or vice versa)
    df["key_reversal_day_flag"] = (
        ((op < prev_lo) & (c > prev_hi)) |
        ((op > prev_hi) & (c < prev_lo))
    ).astype(float)
    # Price round number proximity
    round_1 = (c / 5).round() * 5
    df["price_round_number"] = (((c - round_1) / c.replace(0, np.nan)).abs() < 0.01).astype(float)
    df["price_round_number_proximity"] = ((c - round_1) / c.replace(0, np.nan)).abs()

    # ── Event flags ────────────────────────────────────────────────────────
    df["insider_buying_flag"]    = 0.0  # populated from fundamental data later
    df["earnings_blackout_window"] = 0.0  # not computable from price data alone

    # ── Placeholders for cross-sectional ranks (filled in prepare_all) ─────
    for rk in ["rsi_rank", "return_5d_rank", "return_20d_rank",
               "volatility_20_rank", "volume_ratio_rank", "short_ratio_rank"]:
        df[rk] = 0.5  # neutral placeholder

    # ── Placeholders for market-wide breadth (filled from macro feed) ──────
    _placeholder_cols = ["advance_decline_line", "pct_above_ma50", "pct_above_ma200",
                         "new_highs_lows", "mcclellan_oscillator", "trin_arms_index",
                         "put_call_ratio", "index_put_call_ratio", "gamma_exposure_gex",
                         "bid_ask_spread_rel", "vpin_signal", "volume_profile_poc",
                         "order_book_imbalance", "footprint_imbalance_score",
                         "rs_vs_index", "rs_vs_sector"]
    _new_placeholder = pd.DataFrame(0.0, index=df.index, columns=_placeholder_cols)
    df = pd.concat([df, _new_placeholder], axis=1)

    # ── Advanced indicators via ta library ─────────────────────────────────
    if _TA_AVAILABLE:
        try:
            macd_ind = MACD(close=c)
            df["macd"]        = macd_ind.macd()
            df["macd_signal"] = macd_ind.macd_signal()
            df["macd_diff"]   = macd_ind.macd_diff()
        except Exception:
            df["macd"] = df["macd_signal"] = df["macd_diff"] = 0.0

        try:
            bb = BollingerBands(close=c, window=20)
            df["bollinger_pct_b"]   = bb.bollinger_pband()
            df["bollinger_bandwidth"] = (bb.bollinger_hband() - bb.bollinger_lband()) / c.replace(0, np.nan)
        except Exception:
            df["bollinger_pct_b"] = df["bollinger_bandwidth"] = 0.0

        try:
            stoch = StochasticOscillator(high=hi, low=lo, close=c)
            df["stochastic_k"] = stoch.stoch()
            df["stochastic_d"] = stoch.stoch_signal()
        except Exception:
            df["stochastic_k"] = df["stochastic_d"] = 50.0

        try:
            atr = AverageTrueRange(high=hi, low=lo, close=c)
            df["atr_14"]  = atr.average_true_range()
            df["atr_pct"] = df["atr_14"] / c.replace(0, np.nan)
        except Exception:
            df["atr_14"] = df["atr_pct"] = 0.0

        try:
            adx_ind = ADXIndicator(high=hi, low=lo, close=c)
            df["adx"]     = adx_ind.adx()
            df["adx_pos"] = adx_ind.adx_pos()
            df["adx_neg"] = adx_ind.adx_neg()
        except Exception:
            df["adx"] = df["adx_pos"] = df["adx_neg"] = 0.0

        try:
            wr = WilliamsRIndicator(high=hi, low=lo, close=c)
            df["williams_r"] = wr.williams_r()
        except Exception:
            df["williams_r"] = -50.0

        try:
            cci_ind = CCIIndicator(high=hi, low=lo, close=c)
            df["cci_14"] = cci_ind.cci()
        except Exception:
            df["cci_14"] = 0.0

        try:
            obv_ind = OnBalanceVolumeIndicator(close=c, volume=vol)
            obv = obv_ind.on_balance_volume()
            df["obv"]          = obv
            df["obv_change"]   = obv.pct_change(5)
            df["obv_divergence"] = (c.pct_change(20) - obv.pct_change(20))
        except Exception:
            df["obv_change"] = df["obv_divergence"] = 0.0

        try:
            mfi_ind = MFIIndicator(high=hi, low=lo, close=c, volume=vol)
            df["mfi"] = mfi_ind.money_flow_index()
        except Exception:
            df["mfi"] = 50.0

        try:
            cmf = ChaikinMoneyFlowIndicator(high=hi, low=lo, close=c, volume=vol)
            df["chaikin_money_flow"] = cmf.chaikin_money_flow()
        except Exception:
            df["chaikin_money_flow"] = 0.0

        try:
            aroon = AroonIndicator(high=hi, low=lo, window=25)
            df["aroon_oscillator"]    = aroon.aroon_indicator()
            df["aroon_oscillator_25"] = aroon.aroon_indicator()
        except Exception:
            df["aroon_oscillator"] = df["aroon_oscillator_25"] = 0.0

        try:
            uo = UltimateOscillator(high=hi, low=lo, close=c)
            df["ultimate_oscillator"] = uo.ultimate_oscillator()
        except Exception:
            df["ultimate_oscillator"] = 50.0

        try:
            vpt = VolumePriceTrendIndicator(close=c, volume=vol)
            df["volume_price_trend"] = vpt.volume_price_trend()
        except Exception:
            df["volume_price_trend"] = 0.0

        try:
            adi = AccDistIndexIndicator(high=hi, low=lo, close=c, volume=vol)
            df["ad_accumulation_distribution"] = adi.acc_dist_index().pct_change(5)
        except Exception:
            df["ad_accumulation_distribution"] = 0.0

        # Chande Momentum Oscillator (manual computation)
        try:
            gains = c.diff().clip(lower=0).rolling(14).sum()
            losses = (-c.diff()).clip(lower=0).rolling(14).sum()
            total = gains + losses
            df["chande_momentum_osc"] = ((gains - losses) / total.replace(0, np.nan) * 100)
        except Exception:
            df["chande_momentum_osc"] = 0.0

    else:
        for col_name in ["macd", "macd_signal", "macd_diff", "bollinger_pct_b",
                         "bollinger_bandwidth", "stochastic_k", "stochastic_d",
                         "atr_14", "atr_pct", "adx", "adx_pos", "adx_neg",
                         "williams_r", "cci_14", "obv_change", "obv_divergence",
                         "mfi", "chaikin_money_flow", "aroon_oscillator",
                         "aroon_oscillator_25", "ultimate_oscillator",
                         "volume_price_trend", "ad_accumulation_distribution",
                         "chande_momentum_osc"]:
            df[col_name] = 0.0

    return df.dropna(subset=["return_1d", "return_5d", "return_20d", "rsi"])


# ── Training data preparation ─────────────────────────────────────────────────

def _load_macro_ts() -> pd.DataFrame:
    try:
        from backend.data.macro_feed import load_macro_timeseries
        return load_macro_timeseries()
    except Exception as e:
        logger.warning(f"Could not load macro timeseries: {e}")
        return pd.DataFrame()


# yfinance fundamental field mapping → our feature column names
_YF_INFO_MAP = {
    "forwardPE":                    "pe_ratio_forward",
    "trailingPE":                   "pe_ratio_trailing",
    "priceToBook":                  "pb_ratio",
    "priceToSalesTrailing12Months": "ps_ratio",
    "enterpriseToEbitda":           "ev_ebitda",
    "enterpriseToRevenue":          "ev_sales",
    "pegRatio":                     "peg_ratio",
    "returnOnEquity":               "roe",
    "returnOnAssets":               "roa",
    "grossMargins":                 "gross_margin",
    "ebitdaMargins":                "ebitda_margin",
    "operatingMargins":             "operating_margin",
    "profitMargins":                "net_margin",
    "revenueGrowth":                "revenue_growth_1y",
    "earningsGrowth":               "eps_growth_1y",
    "debtToEquity":                 "debt_equity_ratio",
    "currentRatio":                 "current_ratio",
    "quickRatio":                   "quick_ratio",
    "dividendYield":                "dividend_yield",
    "payoutRatio":                  "payout_ratio",
    "beta":                         "beta",
    "recommendationMean":           "analyst_consensus_buy_pct",
    "institutionPercentHeld":       "institutional_ownership_pct",
    "heldPercentInsiders":          "insider_ownership_pct",
    "shortPercentOfFloat":          "short_interest_pct_float",
    "shortRatio":                   "days_to_cover",
    "floatShares":                  "free_float_pct",
    "trailingEps":                  "eps_surprise",
    "forwardEps":                   "forward_rev_growth_estimate",
}

# Normalization helpers
def _norm_recommend(v):
    """Convert 1-5 recommendation mean to 0-100 buy pct."""
    if v is None or np.isnan(float(v)):
        return 0.5
    return max(0, min(1, (5 - float(v)) / 4))


def _fetch_extended_fundamentals(tickers: list, budget_sec: float = 120.0) -> dict[str, dict]:
    """Fetch yfinance .info for tickers within time budget. Returns {ticker: {col: val}}."""
    import time as _time
    try:
        import yfinance as yf
    except ImportError:
        return {}

    result: dict[str, dict] = {}
    budget_end = _time.monotonic() + budget_sec

    for tk in tickers:
        if _time.monotonic() > budget_end:
            logger.debug("Extended fundamentals budget exhausted")
            break
        try:
            info = yf.Ticker(tk).info
            row: dict = {}
            for yf_key, col_name in _YF_INFO_MAP.items():
                val = info.get(yf_key)
                if val is not None:
                    try:
                        fval = float(val)
                        if np.isfinite(fval):
                            row[col_name] = fval
                    except (TypeError, ValueError):
                        pass

            # Derived fundamentals
            mkt_cap = info.get("marketCap")
            fcf = info.get("freeCashflow")
            rev = info.get("totalRevenue")
            ebitda = info.get("ebitda")
            total_debt = info.get("totalDebt")
            capex = info.get("capitalExpenditures")
            op_income = info.get("operatingIncome")
            interest_exp = info.get("interestExpense")

            if mkt_cap and fcf:
                with np.errstate(divide='ignore', invalid='ignore'):
                    row["fcf_yield"] = float(fcf) / float(mkt_cap) if float(mkt_cap) != 0 else 0.0
            if rev and fcf:
                with np.errstate(divide='ignore', invalid='ignore'):
                    row["fcf_margin"] = float(fcf) / float(rev) if float(rev) != 0 else 0.0
            if rev and capex:
                row["capex_revenue"] = abs(float(capex)) / float(rev) if float(rev) != 0 else 0.0
            if total_debt and ebitda and ebitda != 0:
                row["net_debt_ebitda"] = float(total_debt) / float(ebitda)
            if op_income and interest_exp and interest_exp != 0:
                row["interest_coverage"] = abs(float(op_income) / float(interest_exp))
            if mkt_cap and fcf and fcf != 0:
                row["price_fcf"] = float(mkt_cap) / abs(float(fcf))

            # Normalize analyst recommendation
            if "analyst_consensus_buy_pct" in row:
                row["analyst_consensus_buy_pct"] = _norm_recommend(row["analyst_consensus_buy_pct"])

            # Target price upside
            target = info.get("targetMeanPrice")
            current = info.get("currentPrice") or info.get("regularMarketPrice")
            if target and current and float(current) != 0:
                row["analyst_price_target_upside"] = (float(target) - float(current)) / float(current)

            # Legacy column names (backward compat with predictor.py)
            row["pe_ratio"]              = row.get("pe_ratio_trailing", row.get("pe_ratio_forward", 0.0))
            row["pb_ratio_legacy"]       = row.get("pb_ratio", 0.0)
            row["beta"]                  = row.get("beta", 1.0)
            row["insider_ownership"]     = row.get("insider_ownership_pct", 0.0)
            row["institutional_ownership"] = row.get("institutional_ownership_pct", 0.0)

            result[tk] = row
        except Exception:
            result[tk] = {}

    return result


def prepare_all_training_data(horizon_days: int) -> pd.DataFrame:
    conn = get_conn()

    price_df = conn.execute("""
        SELECT ticker, CAST(date AS VARCHAR) as date, open, high, low, close, volume
        FROM prices ORDER BY ticker, date
    """).df()
    price_df["date"] = pd.to_datetime(price_df["date"]).astype("datetime64[us]")

    sectors = conn.execute("""
        SELECT ticker, COALESCE(sector, 'Unknown') as sector FROM stocks
    """).df()
    sector_map = dict(zip(sectors["ticker"], sectors["sector"]))

    macro_ts = _load_macro_ts()
    macro_cols_available = [c for c in macro_ts.columns if c != "date"] if not macro_ts.empty else []
    has_macro = not macro_ts.empty

    # DB fundamentals (point-in-time earnings surprise)
    fund_snap = conn.execute("""
        SELECT DISTINCT ON (ticker) ticker, earnings_surprise, short_ratio
        FROM fundamentals WHERE earnings_surprise IS NOT NULL
        ORDER BY ticker, report_date DESC
    """).df()
    fund_map = {
        r["ticker"]: {"earnings_surprise": r["earnings_surprise"], "short_ratio": r["short_ratio"]}
        for _, r in fund_snap.iterrows()
    }

    hist_surp = conn.execute("""
        SELECT ticker, earnings_date, earnings_surprise
        FROM earnings_history ORDER BY ticker, earnings_date
    """).df()
    hist_surp["earnings_date"] = pd.to_datetime(hist_surp["earnings_date"]).astype("datetime64[us]")

    # Extended fundamentals from yfinance (120-second budget)
    all_tickers = price_df["ticker"].unique().tolist()
    extended_fund_map = _fetch_extended_fundamentals(all_tickers, budget_sec=120.0)

    # Insider activity (SEC EDGAR Form 4) — populated by the nightly refresh.
    try:
        from backend.data.insider_feed import load_insider_map
        insider_map = load_insider_map()
    except Exception:
        insider_map = {}

    all_feat = []
    for ticker, group in price_df.groupby("ticker"):
        feat = build_features(group)
        if len(feat) < max(horizon_days + 60, 280):
            continue

        feat = feat.copy()
        feat["future_return"] = feat["close"].pct_change(horizon_days).shift(-horizon_days)
        feat["target"] = (feat["future_return"] > 0).astype(int)
        feat = feat.dropna(subset=["return_1d", "rsi", "return_252d", "target"])
        if feat.empty:
            continue

        # ── Earnings surprise (point-in-time) ─────────────────────────────
        ticker_hist = hist_surp[hist_surp["ticker"] == ticker].sort_values("earnings_date")
        if not ticker_hist.empty:
            feat = pd.merge_asof(
                feat.sort_values("date"),
                ticker_hist[["earnings_date", "earnings_surprise"]].rename(
                    columns={"earnings_date": "date"}),
                on="date", direction="backward",
                suffixes=("", "_hist"),
            )
            if "earnings_surprise_hist" in feat.columns:
                feat["earnings_surprise"] = feat["earnings_surprise_hist"].fillna(
                    fund_map.get(ticker, {}).get("earnings_surprise", 0.0))
                feat.drop(columns=["earnings_surprise_hist"], inplace=True)
            else:
                feat["earnings_surprise"] = fund_map.get(ticker, {}).get("earnings_surprise", 0.0)
        else:
            feat["earnings_surprise"] = fund_map.get(ticker, {}).get("earnings_surprise", 0.0)

        feat["short_ratio"] = fund_map.get(ticker, {}).get("short_ratio", 0.0)

        # ── Insider activity (SEC EDGAR Form 4) ───────────────────────────
        ins = insider_map.get(ticker, {})
        feat["insider_net_buy_score"]    = ins.get("insider_net_buy_score", 0.0)
        feat["form4_sentiment_score"]    = ins.get("form4_sentiment_score", 0.0)
        feat["insider_buy_cluster_30d"]  = ins.get("insider_buy_cluster_30d", 0.0)
        feat["insider_sell_cluster_30d"] = ins.get("insider_sell_cluster_30d", 0.0)

        # ── Extended fundamentals ─────────────────────────────────────────
        ext = extended_fund_map.get(ticker, {})
        # Batch-add missing fundamental columns first to avoid fragmentation
        missing_fund = [c for c in FUNDAMENTAL_COLS if c not in feat.columns]
        if missing_fund:
            feat = pd.concat(
                [feat, pd.DataFrame(0.0, index=feat.index, columns=missing_fund)],
                axis=1,
            )
        for fcol in FUNDAMENTAL_COLS:
            val = ext.get(fcol, None)
            if val is not None and np.isfinite(val):
                feat[fcol] = float(val)
            else:
                feat[fcol] = feat[fcol].fillna(0.0)

        # ── Macro as-of join ──────────────────────────────────────────────
        if has_macro:
            feat = pd.merge_asof(
                feat.sort_values("date"),
                macro_ts.sort_values("date"),
                on="date", direction="backward",
            )

        # Ensure all macro/cross_asset/sentiment/geopolitical columns exist
        # Batch-assign missing columns to avoid DataFrame fragmentation
        all_macro_cols = MACRO_COLS + CROSS_ASSET_COLS + SENTIMENT_COLS + GEOPOLITICAL_COLS
        missing_macro = [c for c in all_macro_cols if c not in feat.columns]
        if missing_macro:
            feat = pd.concat(
                [feat, pd.DataFrame(0.0, index=feat.index, columns=missing_macro)],
                axis=1,
            )
        for col in all_macro_cols:
            if col in feat.columns:
                feat[col] = feat[col].fillna(0.0)

        # ── Regime columns ────────────────────────────────────────────────
        if "monetary_regime" not in feat.columns or feat["monetary_regime"].isna().all():
            feat["monetary_regime"] = feat.get("fed_rate", pd.Series(3.0, index=feat.index)).apply(
                lambda v: 2.0 if v > 4.0 else (0.0 if v < 2.0 else 1.0))
        if "credit_regime" not in feat.columns or feat["credit_regime"].isna().all():
            feat["credit_regime"] = feat.get("hy_spread", pd.Series(300.0, index=feat.index)).apply(
                lambda v: 2.0 if v >= 600 else (1.0 if v >= 350 else 0.0))
        if "vol_regime_code" not in feat.columns or feat["vol_regime_code"].isna().all():
            feat["vol_regime_code"] = feat.get("vix", pd.Series(20.0, index=feat.index)).apply(
                lambda v: 3.0 if v >= 35 else (2.0 if v >= 25 else (1.0 if v >= 15 else 0.0)))
        if "yc_regime_code" not in feat.columns or feat["yc_regime_code"].isna().all():
            feat["yc_regime_code"] = feat.get("yield_curve", pd.Series(0.5, index=feat.index)).apply(
                lambda v: 3.0 if v < -0.2 else (2.0 if v < 0 else (1.0 if v < 0.5 else 0.0)))

        # ── Sentiment: presidential cycle ─────────────────────────────────
        feat["presidential_cycle_year"] = pd.to_datetime(feat["date"]).dt.year % 4

        # ── Sentiment: Warren Buffett indicator (proxy from macro) ────────
        if "buffett_indicator_proxy" in macro_ts.columns:
            pass  # already merged
        feat["warren_buffett_indicator"] = feat.get("warren_buffett_indicator",
            pd.Series(0.0, index=feat.index)).fillna(0.0)

        # ── Relative strength vs index ─────────────────────────────────────
        # SPX returns are in macro_ts if available, else 0.0
        feat["rs_vs_index"] = 0.0  # will be cross-sectionally computed later

        feat["sector"] = sector_map.get(ticker, "Unknown")
        feat["ticker"] = ticker

        available = (["date", "ticker", "sector"] +
                     [c for c in BASE_FEATURE_COLS if c in feat.columns] +
                     ["target"])
        all_feat.append(feat[available])

    if not all_feat:
        return pd.DataFrame()

    combined = pd.concat(all_feat, ignore_index=True).sort_values("date")

    # ── Cross-sectional percentile ranks ──────────────────────────────────────
    rank_cols_needed = {
        "rsi": "rsi_rank",
        "return_5d": "return_5d_rank",
        "return_20d": "return_20d_rank",
        "return_252d": "return_252d_rank",
        "volatility_20": "volatility_20_rank",
        "volume_ratio": "volume_ratio_rank",
        "short_ratio": "short_ratio_rank",
    }
    for src, dst in rank_cols_needed.items():
        if src in combined.columns:
            combined[dst] = combined.groupby("date")[src].rank(pct=True)
        else:
            combined[dst] = 0.5

    # ── Fill and clip all feature columns ─────────────────────────────────────
    # Batch-add any still-missing feature columns before in-place ops
    missing_feat = [c for c in FEATURE_COLS if c not in combined.columns]
    if missing_feat:
        combined = pd.concat(
            [combined, pd.DataFrame(0.0, index=combined.index, columns=missing_feat)],
            axis=1,
        )
    existing_feat = [c for c in FEATURE_COLS if c in combined.columns]
    combined[existing_feat] = (combined[existing_feat]
                               .replace([np.inf, -np.inf], np.nan)
                               .fillna(0.0))

    combined = combined.dropna(subset=["return_5d", "rsi", "target"])
    return combined


# ── Walk-forward training ─────────────────────────────────────────────────────

def _fit_eval(train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple:
    avail_feats = [c for c in FEATURE_COLS if c in train_df.columns]
    X_tr = train_df[avail_feats].values.astype(float)
    y_tr = train_df["target"].values
    X_te = test_df[avail_feats].values.astype(float)
    y_te = test_df["target"].values

    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_te_s = scaler.transform(X_te)

    model = GradientBoostingClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.8, max_features="sqrt", random_state=42,
    )
    model.fit(X_tr_s, y_tr)
    acc = accuracy_score(y_te, model.predict(X_te_s))
    return model, scaler, float(acc)


def _walk_forward_train(combined: pd.DataFrame) -> tuple:
    all_dates = sorted(combined["date"].unique())
    n = len(all_dates)
    MIN_TRAIN = 252 * 2
    STEP      = 126

    fold_accs = []
    if n > MIN_TRAIN + STEP:
        for fold_end in range(MIN_TRAIN, n - STEP, STEP):
            train_end = all_dates[fold_end]
            test_end  = all_dates[min(fold_end + STEP, n - 1)]
            train = combined[combined["date"] < train_end]
            test  = combined[(combined["date"] >= train_end) & (combined["date"] < test_end)]
            if len(train) < 500 or len(test) < 100:
                continue
            _, _, acc = _fit_eval(train, test)
            fold_accs.append(acc)

    avg_acc = float(np.mean(fold_accs)) if fold_accs else 0.5
    logger.info(f"  Walk-forward: {len(fold_accs)} folds, avg acc={avg_acc:.4f}")

    avail_feats = [c for c in FEATURE_COLS if c in combined.columns]
    X_all = combined[avail_feats].values.astype(float)
    y_all = combined["target"].values
    scaler = StandardScaler()
    X_all_s = scaler.fit_transform(X_all)
    model = GradientBoostingClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.8, max_features="sqrt", random_state=42,
    )
    model.fit(X_all_s, y_all)
    return model, scaler, avg_acc


# ── Save / load helpers ───────────────────────────────────────────────────────

def _sector_slug(sector: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", sector.lower()).strip("_")


def _save_model(model, scaler, horizon: str, avg_acc: float | None = None) -> None:
    with open(HORIZON_MODEL_PATHS[horizon], "wb") as f:
        pickle.dump(model, f)
    with open(HORIZON_SCALER_PATHS[horizon], "wb") as f:
        pickle.dump(scaler, f)
    meta = {"feature_cols": FEATURE_COLS, "version": MODEL_VERSION}
    if avg_acc is not None:
        meta["accuracy"] = avg_acc
    with open(HORIZON_FEATURES_PATHS[horizon], "w") as f:
        json.dump(meta, f)


def _save_sector_model(model, scaler, sector: str, horizon: str, accuracy: float | None = None) -> None:
    slug = _sector_slug(sector)
    with open(SECTORS_DIR / f"model_{slug}_{horizon}.pkl", "wb") as f:
        pickle.dump(model, f)
    with open(SECTORS_DIR / f"scaler_{slug}_{horizon}.pkl", "wb") as f:
        pickle.dump(scaler, f)
    meta = {"feature_cols": FEATURE_COLS, "version": MODEL_VERSION, "sector": sector}
    if accuracy is not None:
        meta["accuracy"] = accuracy
    with open(SECTORS_DIR / f"features_{slug}_{horizon}.json", "w") as f:
        json.dump(meta, f)


def _save_regime_model(model, scaler, vol_regime: int, horizon: str, accuracy: float | None = None) -> None:
    key = VOL_REGIME_KEYS[vol_regime]
    with open(REGIMES_DIR / f"model_vol{key}_{horizon}.pkl", "wb") as f:
        pickle.dump(model, f)
    with open(REGIMES_DIR / f"scaler_vol{key}_{horizon}.pkl", "wb") as f:
        pickle.dump(scaler, f)
    meta = {"feature_cols": FEATURE_COLS, "version": MODEL_VERSION, "vol_regime": key}
    if accuracy is not None:
        meta["accuracy"] = accuracy
    with open(REGIMES_DIR / f"features_vol{key}_{horizon}.json", "w") as f:
        json.dump(meta, f)


def _load_regime_model(vol_regime: int, horizon: str) -> tuple:
    key = VOL_REGIME_KEYS.get(vol_regime, "normal")
    mp = REGIMES_DIR / f"model_vol{key}_{horizon}.pkl"
    sp = REGIMES_DIR / f"scaler_vol{key}_{horizon}.pkl"
    fp = REGIMES_DIR / f"features_vol{key}_{horizon}.json"
    if not mp.exists() or not sp.exists():
        return None, None, None, None
    with open(mp, "rb") as f:
        model = pickle.load(f)
    with open(sp, "rb") as f:
        scaler = pickle.load(f)
    feat_cols = FEATURE_COLS
    acc = None
    if fp.exists():
        with open(fp) as f:
            meta = json.load(f)
            feat_cols = meta.get("feature_cols", FEATURE_COLS)
            acc = meta.get("accuracy")
    return model, scaler, feat_cols, acc


def _update_accuracy_log(horizon: str, accuracy: float) -> None:
    history = {}
    if ACCURACY_LOG_PATH.exists():
        with open(ACCURACY_LOG_PATH) as f:
            history = json.load(f)
    if horizon not in history:
        history[horizon] = {}
    history[horizon][datetime.now().isoformat()] = accuracy
    with open(ACCURACY_LOG_PATH, "w") as f:
        json.dump(history, f)


# ── Public training API ───────────────────────────────────────────────────────

def train_model(horizon: str = "1w", combined: pd.DataFrame | None = None) -> float:
    horizon_days = HORIZON_DAYS.get(horizon, 5)
    logger.info(f"Training global {horizon} model ({horizon_days}d target)...")
    if combined is None:
        combined = prepare_all_training_data(horizon_days)
    if combined.empty:
        logger.warning(f"No training data for {horizon}")
        return 0.0
    model, scaler, avg_acc = _walk_forward_train(combined)
    _save_model(model, scaler, horizon, avg_acc)
    _update_accuracy_log(horizon, avg_acc)
    logger.info(f"[{horizon}] Global model trained, acc={avg_acc:.4f}")
    return avg_acc


def train_regime_models(horizon: str = "1w", combined: pd.DataFrame | None = None) -> dict[str, float]:
    horizon_days = HORIZON_DAYS.get(horizon, 5)
    if combined is None:
        combined = prepare_all_training_data(horizon_days)
    if combined.empty:
        return {}

    results = {}
    for vol_code in [0, 1, 2, 3]:
        key = VOL_REGIME_KEYS[vol_code]
        regime_data = combined[combined["vol_regime_code"] == float(vol_code)]
        if len(regime_data) < 500:
            logger.debug(f"Skipping vol_regime={key}: only {len(regime_data)} rows")
            continue
        model, scaler, avg_acc = _walk_forward_train(regime_data)
        _save_regime_model(model, scaler, vol_code, horizon, accuracy=avg_acc)
        results[key] = avg_acc
        logger.info(f"[{horizon}] Vol-regime={key}: acc={avg_acc:.4f} ({len(regime_data)} rows)")

    return results


def train_sector_models(horizon: str = "1w", combined: pd.DataFrame | None = None) -> dict[str, float]:
    horizon_days = HORIZON_DAYS.get(horizon, 5)
    if combined is None:
        combined = prepare_all_training_data(horizon_days)
    if combined.empty:
        return {}
    results = {}
    for sector in combined["sector"].unique():
        if sector in ("Unknown", ""):
            continue
        sector_data = combined[combined["sector"] == sector]
        n_tickers   = sector_data["ticker"].nunique()
        if n_tickers < 5 or len(sector_data) < 2000:
            continue
        model, scaler, avg_acc = _walk_forward_train(sector_data)
        _save_sector_model(model, scaler, sector, horizon, accuracy=avg_acc)
        results[sector] = avg_acc
        logger.info(f"[{horizon}] Sector {sector!r}: acc={avg_acc:.4f}")
    return results


def train_all_models() -> float:
    all_accs = []
    for horizon in HORIZON_DAYS:
        horizon_days = HORIZON_DAYS[horizon]
        logger.info(f"Preparing training data for horizon={horizon} ({horizon_days}d)...")
        combined = prepare_all_training_data(horizon_days)
        acc = train_model(horizon, combined=combined)
        all_accs.append(acc)
        regime_accs = train_regime_models(horizon, combined=combined)
        all_accs.extend(regime_accs.values())
        sector_accs = train_sector_models(horizon, combined=combined)
        all_accs.extend(sector_accs.values())
    avg = float(np.mean(all_accs)) if all_accs else 0.0
    logger.info(f"All models trained — overall avg acc: {avg:.4f}")
    return avg


def models_need_retrain() -> bool:
    for horizon in HORIZON_DAYS:
        if not HORIZON_MODEL_PATHS[horizon].exists():
            return True
        fp = HORIZON_FEATURES_PATHS[horizon]
        if not fp.exists():
            return True
        with open(fp) as f:
            meta = json.load(f)
        if meta.get("version") != MODEL_VERSION:
            return True
    return False


def retrain_if_needed() -> None:
    if models_need_retrain():
        logger.info("Models missing or outdated — retraining all...")
        train_all_models()
        _try_onnx_export()
        return
    if ACCURACY_LOG_PATH.exists():
        with open(ACCURACY_LOG_PATH) as f:
            history = json.load(f)
        h1w = history.get("1w", {})
        if h1w:
            latest_acc = list(h1w.values())[-1]
            if latest_acc < ACCURACY_THRESHOLD:
                logger.info(f"Accuracy {latest_acc:.4f} below threshold — retraining")
                train_all_models()
                _try_onnx_export()


def _try_onnx_export() -> None:
    try:
        from backend.models.exporter import export as export_onnx
        export_onnx(verify=False)
        logger.info("ONNX model re-exported after retraining")
    except Exception as e:
        logger.warning(f"ONNX export failed (non-fatal): {e}")


def latest_accuracy(horizon: str = "1w") -> float:
    if not ACCURACY_LOG_PATH.exists():
        return 0.0
    with open(ACCURACY_LOG_PATH) as f:
        history = json.load(f)
    h = history.get(horizon, {})
    return float(list(h.values())[-1]) if h else 0.0
