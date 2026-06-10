# Macroeconomic & Monetary System Factors — Stock Market Prediction

**Domain:** Finance / Stock Market  
**Purpose:** Exhaustive catalog of macro and monetary factors that affect equity prices and returns  
**Scope:** Domestic (US-primary) + Global  
**Target count:** 80–100 individual parameters  
**Author:** Generated via quantitative finance research synthesis

---

## Factor Table Key

| Column | Meaning |
|--------|---------|
| Factor | Name |
| Mechanism | How it affects stock prices/returns |
| Frequency | Real-time / Daily / Weekly / Monthly / Quarterly / Annual |
| Public Data | Whether free historical data exists (source noted) |
| Indicator Type | Leading (L) / Lagging (Lag) / Coincident (C) |

---

## 1. DOMESTIC MACROECONOMIC INDICATORS (US)

| # | Factor | Mechanism | Frequency | Public Data | Type |
|---|--------|-----------|-----------|-------------|------|
| 1 | **Real GDP Growth Rate** | Core driver of corporate revenue growth; strong GDP → higher earnings expectations → equity premium. GDP surprise vs. consensus more important than level. | Quarterly (advance/revised/final) | Yes — BEA / FRED (GDP) | Lag |
| 2 | **GDP Nowcast** | Real-time GDP estimate before official release; high-frequency proxy used by Fed and markets. Atlanta Fed GDPNow widely followed. | Weekly (updated) | Yes — Atlanta Fed GDPNow, NY Fed Nowcast | L |
| 3 | **Unemployment Rate (U-3)** | Low unemployment → consumer spending strength → corporate earnings. Rising unemployment signals recession, contracts multiples. | Monthly | Yes — BLS / FRED (UNRATE) | Lag |
| 4 | **U-6 Underemployment Rate** | Broader labor slack measure; captures gig/part-time underemployment; more sensitive to labor market deterioration than U-3. | Monthly | Yes — BLS / FRED (U6RATE) | Lag |
| 5 | **Nonfarm Payrolls (NFP)** | Monthly jobs added; single most market-moving economic release. Beat/miss vs. consensus drives intraday equity moves. | Monthly | Yes — BLS / FRED (PAYEMS) | C |
| 6 | **Initial Jobless Claims** | Weekly leading indicator of labor market health; spike signals layoffs beginning; closely watched for early recession signal. | Weekly | Yes — DOL / FRED (ICSA) | L |
| 7 | **Continuing Jobless Claims** | Tracks how long unemployed workers stay unemployed; rising trend signals worsening labor market. | Weekly | Yes — FRED (CCSA) | L |
| 8 | **JOLTS Job Openings** | Measures labor demand; high openings = tight labor market = wage pressure = margin compression risk. | Monthly | Yes — BLS / FRED (JTSJOL) | L |
| 9 | **Quits Rate (JOLTS)** | Workers quitting voluntarily = confidence in labor market. High quits = wage pressure and tight labor, bearish for margins. | Monthly | Yes — BLS / FRED (JTSQUR) | L |
| 10 | **CPI (Headline)** | Broad inflation measure; high CPI → Fed tightening → higher discount rates → lower equity valuations (especially growth stocks). | Monthly | Yes — BLS / FRED (CPIAUCSL) | Lag |
| 11 | **CPI Core (ex-Food & Energy)** | Fed's preferred CPI measure; more stable signal for structural inflation trends; primary input to Fed rate decisions. | Monthly | Yes — BLS / FRED (CPILFESL) | Lag |
| 12 | **CPI Shelter Component** | Largest CPI component; lags actual rent changes by ~12 months due to lease renewal timing; markets try to strip it out to see "real" inflation. | Monthly | Yes — BLS / FRED (CUSR0000SAH1) | Lag |
| 13 | **PCE Deflator (Headline)** | Fed's preferred inflation measure over CPI; broader basket; drives Fed policy more than CPI. | Monthly | Yes — BEA / FRED (PCEPI) | Lag |
| 14 | **PCE Core (ex-Food & Energy)** | Fed's primary inflation target variable (target: 2%); determines rate path; most direct driver of Fed policy expectations. | Monthly | Yes — BEA / FRED (PCEPILFE) | Lag |
| 15 | **PPI (Producer Price Index)** | Leading indicator of CPI — producer cost increases pass through to consumer prices; also directly affects corporate margins. | Monthly | Yes — BLS / FRED (PPIACO) | L |
| 16 | **Import Price Index** | Measures price changes for imported goods; inflation pass-through from global supply chains and FX. | Monthly | Yes — BLS / FRED (IR) | L |
| 17 | **Export Price Index** | Affects competitiveness of US exporters; USD strength/weakness feeds here; impacts S&P 500 earnings (~40% from abroad). | Monthly | Yes — BLS / FRED | L |
| 18 | **ISM Manufacturing PMI** | Purchasing Managers Index for manufacturing; >50 = expansion; single strongest monthly leading indicator for US industrial activity. | Monthly | Yes — ISM (free) / FRED (MANEMP) | L |
| 19 | **ISM Services PMI** | Services sector is ~80% of US economy; services PMI often more important than manufacturing for overall activity. | Monthly | Yes — ISM (free) | L |
| 20 | **ISM New Orders Subindex** | Forward-looking component of ISM; new orders placed today = production/revenue in coming months. Strongest leading sub-component. | Monthly | Yes — ISM (free) | L |
| 21 | **ISM Prices Paid Subindex** | Measures input cost inflation reported by purchasing managers; leads CPI by 1–3 months. | Monthly | Yes — ISM (free) | L |
| 22 | **Industrial Production Index** | Measures output of US factories, mines, utilities; closely tracks earnings of industrial and materials sectors. | Monthly | Yes — Fed / FRED (INDPRO) | C |
| 23 | **Capacity Utilization Rate** | % of industrial capacity in use; >80% = inflationary bottleneck signal; low = excess slack, deflationary. | Monthly | Yes — Fed / FRED (TCU) | C |
| 24 | **Retail Sales** | Consumer spending on goods; drives ~70% of GDP; beat/miss moves consumer discretionary and staples sectors hard. | Monthly | Yes — Census / FRED (RSAFS) | C |
| 25 | **Retail Sales ex-Autos & Gas** | "Core core" retail sales, stripping volatile components; cleaner signal of underlying consumer demand. | Monthly | Yes — Census / FRED | C |
| 26 | **Consumer Confidence Index** | Conference Board survey; measures willingness to spend; leads retail sales by 1–2 months. | Monthly | Yes — Conference Board (free summary) / FRED (CSCICP03USM665S) | L |
| 27 | **University of Michigan Consumer Sentiment** | Alternative consumer sentiment survey; 1-year and 5-year inflation expectations sub-components critical for Fed. | Monthly (preliminary + final) | Yes — Univ. of Michigan / FRED (UMCSENT) | L |
| 28 | **Michigan 1-Year Inflation Expectations** | Consumer-embedded inflation expectations; if unanchored (>3%), forces Fed action regardless of actual CPI. | Monthly | Yes — FRED (MICH) | L |
| 29 | **Michigan 5-10 Year Inflation Expectations** | Long-run inflation expectations; "anchored" expectations are core to Fed credibility — deanchoring is very bearish for equities. | Monthly | Yes — FRED | L |
| 30 | **Personal Income** | Household income from all sources; drives sustainable consumer spending; measures economy-wide purchasing power. | Monthly | Yes — BEA / FRED (PI) | C |
| 31 | **Personal Savings Rate** | % of disposable income saved; low rate = consumers running on fumes (short-term bullish, medium-term fragile); high = potential demand surge. | Monthly | Yes — BEA / FRED (PSAVERT) | L |
| 32 | **Housing Starts** | New residential construction; one of the most forward-looking indicators; declines sharply before recessions. Multiplier effect on jobs and durable goods. | Monthly | Yes — Census / FRED (HOUST) | L |
| 33 | **Building Permits** | Even more leading than starts (permit precedes construction); strong signal for economic direction 3–6 months forward. | Monthly | Yes — Census / FRED (PERMIT) | L |
| 34 | **Existing Home Sales** | Volume of home transactions; drives related industries (furniture, appliances, brokers); sensitive to mortgage rate changes. | Monthly | Yes — NAR / FRED (EXHOSLUSM495S) | C |
| 35 | **Case-Shiller Home Price Index** | Measures home price appreciation; housing wealth effect influences consumer spending; systemic risk if sharp decline. | Monthly (2-month lag) | Yes — S&P / FRED (CSUSHPISA) | Lag |
| 36 | **Durable Goods Orders** | Orders for long-lived manufactured goods; volatile but important; ex-defense, ex-aircraft "core capex" is key for business investment. | Monthly | Yes — Census / FRED (DGORDER) | L |
| 37 | **Core Capex Orders (Nondefense Capital Goods ex-Aircraft)** | Best real-time proxy for business investment intentions; leading for productivity and earnings growth. | Monthly | Yes — Census / FRED | L |
| 38 | **Chicago Fed National Activity Index (CFNAI)** | 85-indicator composite index; 3-month average below -0.7 historically signals recession. Deeply data-dense. | Monthly | Yes — Chicago Fed / FRED (CFNAI) | C |
| 39 | **Leading Economic Index (LEI)** | Conference Board's 10-indicator composite; 3 consecutive monthly declines historically precede recession; widely used. | Monthly | Yes — Conference Board / FRED (USSLIND) | L |
| 40 | **Conference Board Coincident Index** | 4-indicator composite confirming current economic state; used to date recessions alongside NBER. | Monthly | Yes — Conference Board / FRED | C |
| 41 | **NBER Recession Indicator** | Official binary recession flag (but declared after the fact with ~6-12 month lag); useful for regime analysis in backtests. | Irregular (post hoc) | Yes — NBER / FRED (USREC) | Lag |
| 42 | **Business Inventories** | Rising inventories signal expected demand or glut risk; inventory-to-sales ratio inversion often precedes production cuts. | Monthly | Yes — Census / FRED (BUSINV) | Lag |
| 43 | **Trade Balance (Current Account)** | Trade deficit/surplus affects GDP, USD, and sector earnings; persistent deficit = dollar pressure and external demand signal. | Monthly | Yes — BEA / FRED (BOPGSTB) | Lag |
| 44 | **Government Spending / Fiscal Deficit** | Deficit spending stimulates demand (positive for equities short-term) but raises debt supply (negative for bonds and long rates). | Monthly/Quarterly | Yes — Treasury / FRED (FYFSD) | C |
| 45 | **Corporate Profits (BEA, NIPA)** | Economy-wide pre-tax profits; leads S&P 500 EPS; measures aggregate margin trends across the economy. | Quarterly | Yes — BEA / FRED (CP) | Lag |

---

## 2. MONETARY POLICY FACTORS

| # | Factor | Mechanism | Frequency | Public Data | Type |
|---|--------|-----------|-----------|-------------|------|
| 46 | **Federal Funds Rate (Target)** | Core risk-free rate; higher rates raise discount rates → compress equity multiples; lower rates → multiple expansion. | FOMC meetings (~8/year) | Yes — Fed / FRED (FEDFUNDS) | L |
| 47 | **Fed Funds Futures (CME)** | Market-implied probability distribution of future Fed rate decisions; drives equity risk premium and rate expectations. | Real-time | Yes — CME FedWatch (free) | L |
| 48 | **Fed Balance Sheet (Total Assets)** | QE expansion increases balance sheet → liquidity injection → equity inflation; QT contraction removes liquidity → headwind. | Weekly (H.4.1 release) | Yes — Fed / FRED (WALCL) | L |
| 49 | **Fed Reserve Bank Credit** | Tracks actual credit extended by the Fed; granular balance sheet measure; leads market liquidity conditions. | Weekly | Yes — Fed / FRED (RESPPANWW) | L |
| 50 | **Excess Reserves (Bank Reserves at Fed)** | Banks' idle reserves parked at Fed; very high reserves = ample system liquidity; declining reserves can tighten financial conditions. | Weekly | Yes — FRED (EXCSRESNS, WRBUSNS) | L |
| 51 | **FOMC Dot Plot Median** | Fed officials' median projection for future rates; revision in median dots drives rate expectations and equity multiples. | Quarterly (SEP releases) | Yes — Fed.gov (free) | L |
| 52 | **Fed Communication Hawkishness Index** | Quantified tone of FOMC statements and minutes (NLP-based); hawkish shift → negative for equities, particularly growth. | Per FOMC meeting | Partially (minutes are free; NLP index varies) | L |
| 53 | **Quantitative Easing / Tightening Pace** | Monthly rate of asset purchases or runoff; $1T of QE historically associated with ~10% S&P 500 uplift (empirically estimated). | Monthly | Yes — Fed H.4.1 / FRED | L |
| 54 | **Interest on Reserve Balances (IORB)** | Rate Fed pays banks on reserves; effectively the floor on Fed funds; affects bank profitability and credit supply. | Per FOMC meeting | Yes — Fed / FRED (IOER) | L |
| 55 | **Reverse Repo Facility Rate & Volume** | Volume of overnight reverse repos signals excess system liquidity; very high RRP = banks have no place to park cash (bullish); declining = tightening. | Daily | Yes — NY Fed / FRED (RRPONTSYD) | L |
| 56 | **ECB Deposit Facility Rate** | European risk-free rate floor; ECB tightening lifts EUR rates → affects global bond market equilibrium → US equity risk premium. | ECB meetings | Yes — ECB (free) | L |
| 57 | **ECB Balance Sheet Size** | ECB's PEPP/APP asset purchase programs inject EUR liquidity that can flow globally into risk assets. | Weekly | Yes — ECB (free) | L |
| 58 | **Bank of Japan Policy Rate & YCC Band** | BOJ's Yield Curve Control (YCC) policy caps JGB yields; unwinding YCC raises global long rates as Japanese investors repatriate; historically triggers volatility. | BOJ meetings | Yes — BOJ (free) | L |
| 59 | **BOJ Balance Sheet / JGB Holdings** | World's largest central bank balance sheet relative to GDP; BOJ normalization = global tightening shock. | Weekly | Yes — BOJ (free) | L |
| 60 | **PBOC 1-Year Loan Prime Rate** | China's policy rate analog; PBOC easing → Chinese stimulus → commodity demand → EM and US industrial stocks benefit. | Monthly | Yes — PBOC / FRED | L |
| 61 | **PBOC Required Reserve Ratio (RRR)** | PBOC's primary credit control tool; cuts to RRR inject RMB liquidity → credit expansion → Chinese and EM equities positive. | Irregular | Yes — PBOC (free) | L |
| 62 | **Bank of England Base Rate** | UK policy rate; affects GBP, UK equities, and risk appetite in European markets; also signals global coordinated policy direction. | BOE MPC meetings | Yes — BOE (free) | L |
| 63 | **RBA Cash Rate** | Reserve Bank of Australia; Australia is a commodity exporter — RBA policy signals commodity cycle expectations; affects AUD and US commodity stocks indirectly. | Monthly | Yes — RBA (free) | L |
| 64 | **Swiss National Bank Policy Rate** | SNB manages CHF safe-haven flows; SNB interventions affect EUR/CHF and global risk-off dynamics. | Quarterly | Yes — SNB (free) | L |
| 65 | **Global Central Bank Policy Rate Differential** | Rate differential between Fed and other major CBs (Fed - ECB, Fed - BOJ, Fed - BOE); drives capital flows, USD strength, and US equity valuation vs. global. | Continuous | Derived from above sources | L |
| 66 | **Monetary Policy Uncertainty Index** | Baker-Bloom-Davis index measuring uncertainty about monetary policy; high uncertainty → elevated equity risk premium → lower valuations. | Monthly | Yes — policyuncertainty.com (free) | L |

---

## 3. YIELD CURVE & INTEREST RATE STRUCTURE FACTORS

| # | Factor | Mechanism | Frequency | Public Data | Type |
|---|--------|-----------|-----------|-------------|------|
| 67 | **2Y-10Y Treasury Yield Spread** | Most widely followed recession predictor; inversion precedes recessions by 6–18 months; very strong leading signal for bear markets. | Daily | Yes — FRED (T10Y2Y) | L |
| 68 | **3M-10Y Treasury Spread (NY Fed model)** | NY Fed recession probability model uses this spread; empirically stronger recession predictor than 2Y-10Y in some studies. | Daily | Yes — FRED (T10Y3M) | L |
| 69 | **10-Year Treasury Yield (Nominal)** | Discount rate for all long-duration assets; rising yields directly compress P/E multiples, especially for growth/tech stocks. | Real-time / Daily | Yes — FRED (DGS10) | C |
| 70 | **2-Year Treasury Yield** | Most sensitive to near-term Fed rate expectations; drives bank earnings and short-duration asset returns. | Real-time / Daily | Yes — FRED (DGS2) | L |
| 71 | **30-Year Treasury Yield** | Discount rate for ultra-long-duration assets; anchor for mortgage rates and pension fund liability management. | Real-time / Daily | Yes — FRED (DGS30) | C |
| 72 | **5-Year Breakeven Inflation Rate** | Market-implied 5-year inflation expectation (5Y TIPS spread); Fed watches this; equity risk premium adjusts when breakevens move. | Daily | Yes — FRED (T5YIE) | L |
| 73 | **10-Year Breakeven Inflation Rate** | Market-implied 10-year inflation expectation; signal for long-run inflation regime; key input to equity valuation models. | Daily | Yes — FRED (T10YIE) | L |
| 74 | **5Y5Y Forward Inflation Expectation** | Market-implied inflation rate 5 years from now for the 5 years following; Fed's preferred market-based inflation anchor signal. | Daily | Yes — FRED (T5YIFR) | L |
| 75 | **Real 10-Year Yield (TIPS)** | 10Y nominal yield minus 10Y breakeven; rising real yields are the most direct headwind for equities (Dalio's "yield squeeze" mechanism). | Daily | Yes — FRED (DFII10) | C |
| 76 | **Real 5-Year Yield (TIPS)** | Shorter-horizon real rate; sensitive to near-term Fed tightening cycle; primary driver of tech/growth stock drawdowns. | Daily | Yes — FRED (DFII5) | L |
| 77 | **Term Premium (ACM Model)** | Adrian-Crump-Moench term premium: the extra compensation bond investors demand for duration risk. Compressed term premium = yield curve suppression = equity friendly; rising = headwind. | Daily | Yes — NY Fed (free) | L |
| 78 | **Fed Funds / SOFR Rate (Overnight)** | Actual overnight funding rate; deviation from target signals stress; SOFR replaced LIBOR as the primary US short-rate benchmark. | Daily | Yes — FRED (SOFR) | C |

---

## 4. CREDIT MARKET FACTORS

| # | Factor | Mechanism | Frequency | Public Data | Type |
|---|--------|-----------|-----------|-------------|------|
| 79 | **Investment Grade Credit Spread (OAS)** | Option-Adjusted Spread over Treasuries for IG bonds; widening = credit stress → higher equity risk premium → lower stocks. ICE BofA IG index widely used. | Daily | Yes — FRED (BAMLC0A0CM) | L |
| 80 | **High Yield (Junk) Credit Spread (OAS)** | HY spreads are the best real-time market-based recession probability. >600bps historically associated with recession; powerful leading indicator. | Daily | Yes — FRED (BAMLH0A0HYM2) | L |
| 81 | **CCC-rated Credit Spread** | Lowest-grade segment of HY; most sensitive to credit cycle; spikes before systemic stress; signal of deteriorating corporate credit quality. | Daily | Yes — FRED (BAMLH0A3HYC) | L |
| 82 | **EM Sovereign Spread (EMBI)** | Spread of emerging market sovereign bonds over Treasuries; widening signals global risk aversion → outflows from EM and risk assets. | Daily | Yes — JP Morgan EMBI (Bloomberg; limited free access via FRED proxies) | L |
| 83 | **Corporate Bond Issuance Volume** | High issuance = credit market is open and functioning = equities friendly; sudden shutoff signals credit crisis. | Weekly | Partially — SIFMA (free monthly) | L |
| 84 | **Leveraged Loan Market Spread** | Loans to speculative-grade companies; widening signals stress in private credit and leveraged buyout ecosystem; leading for PE and financial stocks. | Weekly | Partially — LSTA data (partial free) | L |
| 85 | **CLO (Collateralized Loan Obligation) Issuance** | CLO issuance funds leveraged loans; decline signals credit tightening across leveraged corporate sector. | Monthly | Partially — SIFMA (free) | L |
| 86 | **Commercial Paper Rates / Spreads** | Ultra-short corporate funding rates; spread over T-bills signals short-term corporate stress; spike = liquidity crunch (e.g., 2008, March 2020). | Daily | Yes — FRED (DCPF3M, DPCREDIT) | L |
| 87 | **Bank Lending Standards (SLOOS Survey)** | Fed's Senior Loan Officer Opinion Survey; tightening standards = credit contraction → negative for consumer spending and investment. | Quarterly | Yes — Fed / FRED | L |
| 88 | **Consumer Credit Growth** | Growth in revolving and non-revolving credit; slowing credit growth = consumer spending headwind. | Monthly | Yes — Fed / FRED (TOTALSL) | Lag |
| 89 | **Delinquency Rate on Loans (Bank)** | Rising delinquencies = credit quality deterioration; leads to bank loan losses → financial sector weakness and economic slowdown. | Quarterly | Yes — Fed / FRED (DRCCLACBS) | Lag |
| 90 | **Charge-Off Rate on Loans** | Realized loan losses at banks; lags delinquencies; signals financial sector earnings compression. | Quarterly | Yes — Fed / FRED (CORCCACBS) | Lag |
| 91 | **Financial Stress Index (STLFSI, NFCI)** | Composite indexes of financial system stress (St. Louis Fed STLFSI, Chicago Fed NFCI); high stress → risk-off equity environment. | Weekly | Yes — FRED (STLFSI, NFCI) | C |
| 92 | **MOVE Index (Treasury Volatility)** | ICE BofA MOVE index — implied volatility of Treasury bonds; elevated MOVE → bond market uncertainty → equity volatility correlation. | Daily | Yes — CBOE/ICE (free daily via financial data APIs) | L |

---

## 5. MONEY SUPPLY & BANK CREDIT FACTORS

| # | Factor | Mechanism | Frequency | Public Data | Type |
|---|--------|-----------|-----------|-------------|------|
| 93 | **M2 Money Supply (Level & YoY Growth)** | Broad money supply; M2 growth correlates with nominal economic growth and inflation; contraction historically rare and associated with deflationary recessions (1929, 2022). | Monthly | Yes — Fed / FRED (M2SL) | L |
| 94 | **M1 Money Supply** | Narrower money supply (cash + demand deposits); velocity of M1 is more real-time indicator of transaction activity. | Monthly | Yes — Fed / FRED (M1SL) | L |
| 95 | **Money Supply Velocity (M2)** | How fast money circulates; declining velocity even with rising M2 means inflation not transmitting — opposite (rising velocity + rising M2) = inflationary surge. | Quarterly | Yes — FRED (M2V) | Lag |
| 96 | **Bank Credit Growth** | Total credit extended by US commercial banks; bank credit growth is the primary mechanism of money creation; slowdown = economic contraction risk. | Weekly | Yes — FRED (TOTBKCR) | L |
| 97 | **Global Money Supply (G4 M2)** | Sum of US + EU + Japan + China M2 in USD terms; when global M2 expands → positive for global equities and risk assets; key macro liquidity signal. | Monthly | Derived — individual CB data (free) | L |
| 98 | **Eurodollar Market Volume** | Offshore USD deposits; eurodollar market is the shadow funding system of global trade; tightening = global USD funding stress. | No direct public data (inferred from SOFR futures) | Partially (SOFR futures, CME free) | L |
| 99 | **TED Spread (T-Bill vs. Eurodollar Rate)** | Spread between 3-month T-bill and 3-month LIBOR/SOFR; measures banking sector stress and perceived counterparty risk. | Daily | Yes — FRED (TEDRATE, though LIBOR phase-out; replaced by SOFR equivalents) | L |
| 100 | **Repo Market Rate / Repo Stress** | Overnight repurchase agreement rates; spikes indicate collateral scarcity or funding stress (e.g., Sept 2019 repo squeeze); precedes broader liquidity stress. | Daily | Yes — NY Fed (SOFR, BGCR, TGCR, free) | L |

---

## 6. CURRENCY / FX FACTORS

| # | Factor | Mechanism | Frequency | Public Data | Type |
|---|--------|-----------|-----------|-------------|------|
| 101 | **DXY Dollar Index** | USD strength vs. basket of major currencies; strong dollar = earnings headwind for US multinationals (~40% of S&P 500 revenues are international); also tightens global USD liquidity. | Real-time / Daily | Yes — FRED (DTWEXBGS) / Yahoo Finance | C |
| 102 | **EUR/USD Rate** | Most liquid currency pair; EUR weakness → dollar strength → US equity earnings headwind; also proxies for European financial stress. | Real-time / Daily | Yes — FRED (DEXUSEU) | C |
| 103 | **USD/JPY Rate (Yen Carry Trade)** | Yen carry trade proxy; rapid JPY strengthening = carry trade unwind → forced selling of risk assets globally (as in August 2024). | Real-time / Daily | Yes — FRED (DEXJPUS) | L |
| 104 | **USD/CNY Fixing** | PBOC's daily CNY fix; devaluation signals economic stress in China → commodity selloff → EM contagion. | Daily | Yes — PBOC / FRED (DEXCHUS) | L |
| 105 | **USD Broad Real Effective Exchange Rate (REER)** | Trade-weighted, inflation-adjusted USD rate; better measure of US competitiveness than nominal DXY; links to trade balance and corporate margins. | Monthly | Yes — BIS / FRED (RBUSBIS) | Lag |
| 106 | **JPY Real Effective Exchange Rate** | Persistent JPY weakness → Japanese export competitiveness; but also signals ongoing BOJ ultra-easy policy and potential normalization risk. | Monthly | Yes — BIS / FRED | L |
| 107 | **EM Currency Index** | Broad EM FX basket; EM currency weakness → capital outflows from EM → risk-off globally; also signals commodity cycle. | Daily | Partially — BIS, Bloomberg proxies | L |
| 108 | **FX Implied Volatility (1M)** | Options-derived FX vol for major pairs; elevated FX vol = currency uncertainty = risk-off signal; often co-moves with equity vol. | Daily | Partially — CBOE, broker feeds (some free) | L |

---

## 7. GLOBAL MACROECONOMIC FACTORS

| # | Factor | Mechanism | Frequency | Public Data | Type |
|---|--------|-----------|-----------|-------------|------|
| 109 | **China Caixin Manufacturing PMI** | Private-sector PMI for Chinese manufacturing; China is the world's largest manufacturer; significant signal for global commodity demand and EM equities. | Monthly | Yes — Caixin (free headline) | L |
| 110 | **China Official NBS PMI** | State PMI for China; covers larger state enterprises; together with Caixin gives full picture of Chinese manufacturing. | Monthly | Yes — NBS China (free) | L |
| 111 | **Eurozone PMI (Composite)** | Services + manufacturing PMI for EU economy; EU is second-largest economic bloc; contraction in EU PMI signals global slowdown risk. | Monthly | Yes — S&P Global / Markit (free flash estimate) | L |
| 112 | **Japan Tankan Survey** | BOJ's quarterly business conditions survey; sentiment of large Japanese manufacturers; global capex and supply chain signal. | Quarterly | Yes — BOJ (free) | L |
| 113 | **Global PMI Composite (JPMorgan/S&P)** | Aggregated global manufacturing and services PMI; single best summary of global economic activity momentum. | Monthly | Yes — S&P Global (free headline) | L |
| 114 | **Baltic Dry Index** | Shipping rates for dry bulk commodities (iron ore, coal, grain); leading indicator of global trade volume and commodity demand. | Daily | Yes — Baltic Exchange / free via investing.com | L |
| 115 | **Global Trade Volume Growth (CPB)** | CPB World Trade Monitor; measures actual international trade flows; deceleration precedes earnings disappointments for global companies. | Monthly | Yes — CPB Netherlands (free) | L |
| 116 | **OECD Leading Indicator (CLI)** | Composite leading indicator for OECD economies; 6-month leading signal for economic turning points. | Monthly | Yes — OECD.stat (free) | L |
| 117 | **Global Economic Policy Uncertainty Index** | Baker-Bloom-Davis index across 20 countries; high uncertainty → elevated equity risk premium → lower P/E multiples globally. | Monthly | Yes — policyuncertainty.com (free) | L |

---

## 8. BANKING SYSTEM HEALTH INDICATORS

| # | Factor | Mechanism | Frequency | Public Data | Type |
|---|--------|-----------|-----------|-------------|------|
| 118 | **Bank CDS Spreads (Major US Banks)** | Credit Default Swap spreads on G-SIB banks (JPM, BAC, C, WFC); widening signals perceived bank default risk → financial contagion concern. | Daily | Partially — Markit (limited free); Bloomberg | L |
| 119 | **KBW Bank Index / BKX** | Market-cap weighted index of US bank stocks; bank stocks are a leading proxy for economic health and credit conditions; bank underperformance precedes economic slowdown. | Real-time / Daily | Yes — free via exchanges / Yahoo Finance | L |
| 120 | **Interbank Lending Rate (SOFR vs. OIS Spread)** | SOFR-OIS spread measures interbank credit risk; widening signals banks fear lending to each other (2008 analog). | Daily | Yes — NY Fed / FRED | L |
| 121 | **Bank Capital Ratios (CET1)** | Common Equity Tier 1 ratios of major banks; low/declining ratios → constrained lending capacity → credit crunch risk. | Quarterly (regulatory filings) | Yes — FFIEC / Fed stress test results (free) | Lag |
| 122 | **Fed Stress Test Results (DFAST/CCAR)** | Annual fed stress tests on G-SIB banks; failure = dividend suspension, buyback halt → bank stock selloff. | Annual | Yes — Fed (free) | Lag |
| 123 | **Shadow Banking System Size (NBFI)** | Non-bank financial intermediaries (money market funds, hedge funds, PE); FSB estimates; shadow credit expansion or contraction affects total credit supply. | Annual (FSB) / partial quarterly | Yes — FSB Global Monitoring Report (free) | Lag |

---

## 9. COMMODITY & SUPPLY-SIDE MACRO FACTORS

| # | Factor | Mechanism | Frequency | Public Data | Type |
|---|--------|-----------|-----------|-------------|------|
| 124 | **WTI Crude Oil Price** | Energy costs feed directly into PPI and CPI; high oil = margin compression for non-energy companies; also proxy for global demand. | Real-time / Daily | Yes — EIA / FRED (DCOILWTICO) | C |
| 125 | **Brent Crude Oil Price** | Global benchmark; more relevant for international companies and geopolitical risk pricing. | Real-time / Daily | Yes — EIA / FRED (DCOILBRENTEU) | C |
| 126 | **Natural Gas Prices (Henry Hub)** | Utility, industrial, and chemical sector margins; energy inflation for consumers and businesses. | Daily | Yes — EIA / FRED (DHHNGSP) | C |
| 127 | **Copper Price** | "Dr. Copper" — strongest commodity leading indicator for global economic growth; copper demand tracks industrial activity closely. | Daily | Yes — LME / FRED (PCOPPUSDM) | L |
| 128 | **Global Supply Chain Pressure Index (GSCPI)** | NY Fed index measuring supply chain disruption across shipping costs, delivery times, backlogs; supply chain stress = inflation + earnings miss risk. | Monthly | Yes — NY Fed (free, GSCPI) | L |
| 129 | **CRB Commodity Index** | Broad commodity basket; commodity supercycles drive inflation regime shifts and sector rotation (energy/materials vs. tech/growth). | Daily | Yes — Reuters/Jefferies CRB (free via financial sites) | C |

---

## 10. DEBT MARKET & FISCAL STRUCTURAL FACTORS

| # | Factor | Mechanism | Frequency | Public Data | Type |
|---|--------|-----------|-----------|-------------|------|
| 130 | **Total US Debt-to-GDP** | Structural constraint on fiscal capacity; very high debt-to-GDP (>130%) limits fiscal stimulus options; Reinhart-Rogoff threshold debates. | Quarterly | Yes — BIS, IMF / FRED | Lag |
| 131 | **Federal Deficit as % of GDP** | Running large deficits during expansion is unusual and inflationary; also increases Treasury supply → upward pressure on yields. | Monthly/Annual | Yes — CBO, Treasury / FRED (FYFSGDA188S) | C |
| 132 | **Treasury Issuance Volume (Net)**  | When Treasury issues more debt than Fed buys, private sector must absorb supply → upward yield pressure → equity multiple compression. | Monthly | Yes — Treasury / TreasuryDirect (free) | L |
| 133 | **Household Debt Service Ratio** | % of disposable income consumed by debt payments; high ratio → consumer spending constraint → earnings growth slowdown. | Quarterly | Yes — Fed / FRED (TDSP) | Lag |
| 134 | **Corporate Debt-to-EBITDA Leverage** | Economy-wide corporate leverage; high leverage = fragility to rate increases; leads credit downgrades and spread widening. | Quarterly | Yes — Fed Flow of Funds (Z.1) / FRED | Lag |
| 135 | **Interest Coverage Ratio (Economy-wide)** | Earnings before interest / interest expense for the corporate sector; when EBIT/interest < 1.5x economy-wide = systemic fragility. | Quarterly | Yes — BIS, Fed Z.1 (derived) | Lag |

---

## Summary Statistics

| Category | Factor Count |
|----------|-------------|
| Domestic Macro (US) | 45 |
| Monetary Policy (Fed + Global CBs) | 21 |
| Yield Curve & Rate Structure | 12 |
| Credit Markets | 14 |
| Money Supply & Bank Credit | 8 |
| Currency / FX | 8 |
| Global Macro | 9 |
| Banking System Health | 6 |
| Commodity & Supply Side | 6 |
| Debt & Fiscal Structural | 7 |
| **Total** | **136** |

---

## FRED Series Quick Reference

A partial list of the most important FRED series for programmatic ingestion:

```
FEDFUNDS, WALCL, SOFR, RRPONTSYD
DGS2, DGS10, DGS30, T10Y2Y, T10Y3M
T10YIE, T5YIE, T5YIFR, DFII10, DFII5
CPIAUCSL, CPILFESL, PCEPILFE, PPIACO
GDP, GDPC1, UNRATE, U6RATE, PAYEMS, ICSA, CCSA
JTSJOL, JTSQUR
M2SL, M1SL, M2V, TOTBKCR
BAMLC0A0CM, BAMLH0A0HYM2, BAMLH0A3HYC
STLFSI, NFCI, CFNAI, USSLIND, USREC
INDPRO, TCU, HOUST, PERMIT, DGORDER
RSAFS, PSAVERT, PI, UMCSENT, MICH
DTWEXBGS, DEXUSEU, DEXJPUS, DEXCHUS
DCOILWTICO, DCOILBRENTEU, DHHNGSP
TOTALSL, TDSP, FYFSGDA188S
BUSLOANS, CORCCACBS, DRCCLACBS
```

---

## Indicator Timing Matrix

| Horizon | Best Leading Indicators |
|---------|------------------------|
| 1–5 days | Fed Funds Futures, SOFR, VIX, HY spreads, SOFR-OIS, USD/JPY, Fed repo |
| 1–4 weeks | ISM PMI, JOLTS, NFP, Treasury yields, IG/HY spreads, MOVE index |
| 1–3 months | Yield curve (2Y-10Y), LEI, CFNAI, CLI, housing starts, building permits, Core Capex |
| 3–12 months | Yield curve inversion duration, bank lending standards, M2 growth, Fed balance sheet, global PMIs |
| >12 months | Debt-to-GDP, interest coverage, delinquency rates, demographics |

---

## Academic Literature Basis

Key papers informing this catalog:
- **Estrella & Mishkin (1998)** — yield curve as recession predictor (3M-10Y)
- **Ang, Piazzesi, Wei (2006)** — term structure and business cycles
- **Campbell & Shiller (1988)** — earnings yields and discount rates
- **Bernanke & Kuttner (2005)** — monetary policy surprises and equity returns
- **Baker, Bloom, Davis (2016)** — policy uncertainty and stock prices
- **Adrian & Shin (2010)** — bank leverage cycles and asset prices
- **Fama & French (1989)** — business conditions and expected returns
- **Asness, Moskowitz, Pedersen (2013)** — value and momentum everywhere (including macro factors)
- **Cooper & Priestley (2009)** — output gap and expected stock returns
- **Ludvigson & Ng (2009)** — macro factors and bond risk premia

---

*Last updated: 2026-06-08*  
*Source: Quantitative finance research synthesis — FRED, BLS, BEA, Fed, BIS, IMF, ECB, BOJ, academic literature*
