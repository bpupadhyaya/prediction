# Geopolitical, Political, and Regulatory Factors Affecting Stock Markets

**Research area:** Factor catalog for stock market prediction feature engineering
**Coverage:** 73 individual parameters across geopolitical, political, and regulatory dimensions
**Purpose:** Exhaustive enumeration for feature selection, data sourcing, and model design

---

## How to Use This Document

Each factor entry covers:
- **Mechanism:** How the factor moves equity prices
- **Data frequency and source:** Where to get it, how often it updates
- **Repricing speed:** How quickly markets incorporate the shock
- **Most affected sectors:** Which GICS sectors bear the largest impact

Factors are grouped into 8 thematic blocks.

---

## Block 1: Armed Conflict and Military Risk (11 factors)

### 1. Interstate War Outbreak
**Mechanism:** Direct destruction of physical capital; flight-to-safety into US Treasuries and gold; risk premium expansion across all equities; supply chain ruptures in war-adjacent regions; oil price spike if Middle East or key transit choke points involved.
**Data:** Uppsala Conflict Data Program (UCDP), Armed Conflict Location and Event Data (ACLED) — daily event updates. GDELT Project for media-derived conflict intensity. Geopolitical Risk Index (GPR) by Caldara and Iacoviello (free, FRED series GPRI).
**Repricing speed:** Minutes to hours for outbreak news; weeks to months for sustained repricing as uncertainty persists.
**Most affected:** Energy, Defense and Aerospace, Airlines, Shipping, Insurance (war risk premiums), Emerging Market equities in proximate regions.

### 2. Civil War and Internal Armed Conflict
**Mechanism:** Political instability premium on sovereign debt flows through to equity discount rates; disruption of domestic demand and labor supply; capital flight from domestic investors into hard currency assets; currency devaluation amplifies losses for foreign equity holders.
**Data:** UCDP Georeferenced Event Dataset, Political Instability Task Force (PITF), Fund for Peace Fragile States Index (annual), World Bank Political Stability and Absence of Violence indicator (annual, with interpolation).
**Repricing speed:** Days to weeks as conflict escalates; slow grind as markets price prolonged uncertainty.
**Most affected:** Local market equities, Banks (sovereign-credit linkage), Consumer Discretionary (domestic demand collapse).

### 3. Military Escalation Indicators (Short of War)
**Mechanism:** Elevated military posturing (exercises, naval deployments, missile tests) raises tail-risk premium without full conflict impact; options volatility spikes; safe-haven flows begin.
**Data:** Stockholm International Peace Research Institute (SIPRI) military spending database (annual); Jane's Defense & Security Intelligence (proprietary); Nuclear Threat Initiative Nuclear Security Index; social media / news event extraction (GDELT military-coded events).
**Repricing speed:** Hours to days; fades if de-escalation signals emerge.
**Most affected:** Defense, Energy (if Persian Gulf or Strait of Hormuz threatened), Korean peninsula plays (South Korean KOSPI).

### 4. Terrorism and Domestic Political Violence
**Mechanism:** Consumer confidence drops; transportation and Tourism demand falls immediately; elevated security spending; insurance losses; for high-casualty events, short-term market shock (9/11 case study: S&P fell ~11% in the week after reopening).
**Data:** Global Terrorism Database (GTD, National Consortium for the Study of Terrorism), START center; RAND terrorism databases; Terrorism and Political Violence (TPV) index by Aon/Willis Towers Watson (proprietary, annual).
**Repricing speed:** Hours (immediate shock); 1–3 weeks for full recovery in most cases absent subsequent attacks.
**Most affected:** Airlines, Hotels and Leisure, Insurance, Retail (consumer confidence channel).

### 5. Nuclear Proliferation Events
**Mechanism:** Extreme tail risk; rare but catastrophic scenario that causes unprecedented risk-premium spikes; any credible nuclear test or deployment threat triggers flight-to-safety globally.
**Data:** Bulletin of the Atomic Scientists Doomsday Clock (annual); IAEA Safeguards reporting; Arms Control Association event monitoring.
**Repricing speed:** Instantaneous on news; prolonged if standoff continues.
**Most affected:** All equity markets (systemic); Defense stocks paradoxically may rise on rearmament expectations.

### 6. Geopolitical Risk Index (GPR) — Composite
**Mechanism:** Synthetic index aggregating media references to geopolitical tensions; empirically shown (Caldara and Iacoviello, 2022, American Economic Review) to reduce investment, employment, and equity prices when elevated; increases equity risk premium by 0.5-1% for a 1 standard deviation GPR shock.
**Data:** Monthly GPR index from Matteo Iacoviello's Federal Reserve Board page (free download); daily high-frequency version available; country-specific GPR series for 41 countries.
**Repricing speed:** GPR is a lagging summary but underlying news events reprice instantly.
**Most affected:** Small-cap stocks (less liquid, harder to hedge), Emerging Markets, Global cyclicals.

### 7. Coup d'État and Sudden Government Change
**Mechanism:** Immediate uncertainty about property rights, contract enforcement, regulatory continuity; capital flight; currency collapse; equity market suspension in some cases.
**Data:** Center for Systemic Peace Coups d'État dataset; Political Risk Services (PRS) Group; Varieties of Democracy (V-Dem) sudden-change indicators.
**Repricing speed:** Within hours of announcement; can persist months as new regime establishes policy.
**Most affected:** Local financial markets; foreign investors with EM equity exposure; commodity producers in affected country (nationalization risk).

### 8. Cyberattack on Critical Infrastructure
**Mechanism:** Disruption of financial market infrastructure (SWIFT, exchanges), energy grids, supply chains; increasing frequency; Colonial Pipeline (2021) caused gasoline futures spike; Exchange outages directly halt trading.
**Data:** Recorded Future threat intelligence (proprietary); CISA advisories (free); Cyber Threat Intelligence Integration Center; Booz Allen Hamilton Cyber 5 Index (proprietary).
**Repricing speed:** Immediate for targeted sectors; tail risk repricing for Cyber insurance sector.
**Most affected:** Utilities, Energy, Financial Services (if banking infrastructure targeted), Technology.

### 9. Maritime Security and Chokepoint Disruption
**Mechanism:** Attacks on shipping in Strait of Hormuz, Suez Canal, Strait of Malacca immediately spike oil and LNG prices and shipping costs; supply chain disruptions for manufacturers dependent on just-in-time imports.
**Data:** International Maritime Bureau piracy reports (quarterly); Bab-el-Mandeb incident reporting via ACLED; Baltic Dry Index (daily, free via Bloomberg/FRED) as proxy for shipping disruption.
**Repricing speed:** Immediate for energy and shipping; 2-4 weeks for downstream manufacturing input cost repricing.
**Most affected:** Energy, Shipping (Maersk, ZIM), Semiconductors (Taiwan Strait scenario), Autos (parts supply).

### 10. Refugee and Migration Crisis (Geopolitical Origin)
**Mechanism:** Massive refugee flows strain host-country fiscal budgets; political destabilization of recipient governments (far-right political response); labor supply shifts in origin countries; remittance flows collapse.
**Data:** UNHCR refugee data portal (monthly); IOM Displacement Tracking Matrix; European Border and Coast Guard Agency (Frontex) crossing data.
**Repricing speed:** Weeks to months; primarily political channel rather than direct market channel.
**Most affected:** Host-country financial stocks (fiscal concerns), defense contractors (border security spending), Housing (supply effects).

### 11. Space and Satellite Conflict (Emerging)
**Mechanism:** Anti-satellite weapons tests create debris risks for commercial satellite operators; GPS disruption affects precision agriculture, finance (timestamp synchronization), aviation; growing dependency of capital markets on satellite communications.
**Data:** US Space Command public debris tracking; Secure World Foundation space policy tracker; SpacePolicy.institute.
**Repricing speed:** Days for directly affected companies; structural tail risk for GPS-dependent industries.
**Most affected:** Satellite operators (Viasat, SES), Aviation, Agriculture (precision farming), Financial infrastructure.

---

## Block 2: Trade Policy, Tariffs, and Sanctions (10 factors)

### 12. Bilateral Tariff Increases
**Mechanism:** Directly raises input costs for importers; reduces export competitiveness; shifts profit margins across supply chains; empirically, US-China 2018-2019 tariff escalation caused S&P 500 to fall ~1-2% on major tariff announcement days; exchange rate partly offsets.
**Data:** USITC tariff schedule (HTS); WTO tariff binding databases; Peterson Institute for International Economics tariff tracker; Federal Register tariff announcements (same-day).
**Repricing speed:** Minutes on announcement; 1-4 weeks for full supply chain repricing.
**Most affected:** Industrials, Consumer Discretionary (electronics, apparel), Agriculture (reciprocal retaliation targets), Steel and Aluminum (direct targets or beneficiaries of protection).

### 13. Multilateral Trade Agreement Formation and Collapse
**Mechanism:** Trade agreement formation reduces trade friction, boosts corporate earnings for export-oriented firms; collapse (e.g., WTO Doha Round failure, NAFTA renegotiation threat) introduces uncertainty that suppresses investment.
**Data:** WTO Regional Trade Agreements database (free); USTR trade policy agenda releases; Office of the United States Trade Representative FOIA releases.
**Repricing speed:** Days on announcement; months for full repricing as legal text details emerge.
**Most affected:** Multinationals with complex supply chains, Agriculture, Auto sector (parts sourcing), Pharma (IP protection clauses).

### 14. Export Control Restrictions (Technology)
**Mechanism:** US Entity List additions prevent US companies from supplying technology to blacklisted firms; reduces revenue for semiconductor and equipment companies (Huawei effect: ASML, QUALCOMM, Broadcom all repriced); also affects import-dependent downstream manufacturers.
**Data:** BIS Entity List (free, updated continuously); ECCN classification changes in Export Administration Regulations; CHIPS Act implementation guidance; Semiconductor Industry Association policy tracker.
**Repricing speed:** Minutes on Entity List update; weeks for full supply chain impact analysis.
**Most affected:** Semiconductors, Semiconductor Equipment, Defense Electronics, Telecom Equipment.

### 15. Economic Sanctions (Country-Level)
**Mechanism:** OFAC-administered sanctions freeze assets, prohibit transactions; direct revenue loss for companies with sanctioned-country exposure; secondary sanctions risk (non-US entities also face penalties) forces global compliance behavior; commodity supply disruption if energy-exporting country sanctioned.
**Data:** OFAC Specially Designated Nationals (SDN) list (free, daily updates); US Treasury sanctions press releases; EU sanctions register; UN Security Council sanctions committee reports.
**Repricing speed:** Immediate for directly sanctioned entities; days to weeks for secondary effects.
**Most affected:** Energy (if Russia/Iran/Venezuela targeted), Financial Services (clearing and correspondent banking), Mining (cobalt from DRC, nickel from Russia).

### 16. Currency Manipulation Designation
**Mechanism:** US Treasury designation of trading partner as currency manipulator (requires meeting 3 criteria) increases likelihood of retaliatory tariffs and trade friction; signals diplomatic deterioration.
**Data:** US Treasury semi-annual Foreign Exchange Report (April and October); IMF Article IV consultation reports on exchange rate assessments.
**Repricing speed:** Days on report release; market often anticipates based on Treasury preview signals.
**Most affected:** Export-heavy domestic sectors of designated country, US import-competing industries.

### 17. Supply Chain Decoupling Policy (Friendshoring)
**Mechanism:** Government mandates or incentives to reshore or friend-shore production increases costs short-term but may reduce tail risk; increases capex demand for domestic manufacturing; reduces profitability of globally integrated supply chains.
**Data:** White House supply chain executive orders; CHIPS Act and Inflation Reduction Act implementation (domestic content requirements); European Critical Raw Materials Act; Japan's economic security legislation tracker.
**Repricing speed:** Weeks to months as legislation details emerge; immediate for announcement effects.
**Most affected:** Semiconductors, Electric Vehicles, Pharmaceutical APIs, Rare Earth mining.

### 18. Carbon Border Adjustment Mechanisms (CBAM)
**Mechanism:** EU's Carbon Border Adjustment Mechanism imposes carbon cost on imports from countries without equivalent carbon pricing; raises costs for carbon-intensive exporters; reshapes global trade flows in steel, aluminum, cement, chemicals, fertilizers.
**Data:** EU CBAM Regulation (CBAM.eu); ICAP Emissions Trading Worldwide registry; World Bank Carbon Pricing Dashboard.
**Repricing speed:** Gradual (phase-in periods); but announcement effects immediate for most exposed sectors.
**Most affected:** Steel, Aluminum, Cement, Fertilizers, Electricity-intensive exporters.

### 19. Intellectual Property Regime Changes
**Mechanism:** Compulsory licensing of pharmaceuticals reduces drug profitability; WTO TRIPS flexibility invocations during health crises; Chinese IP enforcement improvements or deteriorations affect tech sector investment risk.
**Data:** USTR Special 301 Report (annual); WTO TRIPS Council notifications; USPTO International IP Index by US Chamber of Commerce.
**Repricing speed:** Weeks to months as legal implications are absorbed.
**Most affected:** Pharma/Biotech, Software, Entertainment (copyright), Medical Devices.

### 20. Sanctions Relief and Normalization
**Mechanism:** Opposite of sanctions imposition; market access opens; oil supply increases if energy exporter; asset price reset as previously excluded markets reprice to global multiples.
**Data:** OFAC delisting notices; State Department diplomatic announcements; Iran nuclear deal monitoring (JCPOA status tracker).
**Repricing speed:** Immediate for energy commodity prices; weeks for equity repricing.
**Most affected:** Energy, Financial Services (reemerging market access), Aerospace and Defense (arms sales).

### 21. WTO Dispute Resolution Outcomes
**Mechanism:** WTO Appellate Body rulings authorize retaliatory tariffs against losing parties; affects specific industry sectors named in authorized retaliation lists; creates ongoing litigation risk for targeted firms.
**Data:** WTO Dispute Settlement database (free, all panel reports public); USTR press releases on dispute outcomes.
**Repricing speed:** Days on major ruling; targeted sectors reprice quickly.
**Most affected:** Steel, Aircraft (Boeing/Airbus dispute archetype), Agriculture (Hormones/GMO disputes).

---

## Block 3: Electoral Cycles and Political Transitions (9 factors)

### 22. US Presidential Election Cycle Effect
**Mechanism:** Empirically documented 4-year equity return pattern: Year 1 weakest (policy uncertainty post-election), Year 2 weakest midpoint, Year 3 pre-election strongest (president stimulates economy), Year 4 moderate; Hirsch Presidential Election Cycle is widely cited though disputed statistically.
**Data:** Hirsch's Stock Trader's Almanac; CRSP historical return database by calendar year; political party vs. market return databases.
**Repricing speed:** Gradual seasonal effect; discrete jumps on election night outcomes.
**Most affected:** Defense (party influences procurement), Energy (fossil fuel vs. clean energy policy), Healthcare (ACA/pharmaceutical pricing risk), Financials (regulatory appetite).

### 23. US Midterm Election Outcomes
**Mechanism:** Divided government historically associated with lower policy uncertainty (gridlock prevents extreme legislation) and paradoxically higher equity returns; legislative risk recalibration.
**Data:** Cook Political Report forecasts (daily in election year); congressional seat counts; FiveThirtyEight forecasts.
**Repricing speed:** Overnight on election results; gradual as legislative implications emerge.
**Most affected:** Healthcare, Financial Services, Energy (regulatory sectors most sensitive to legislative power).

### 24. European Parliamentary and National Elections (Major Economies)
**Mechanism:** French presidential elections affect EU fiscal architecture; German elections affect manufacturing policy and energy transition; Italian elections elevate sovereign debt risk (BTP-Bund spread); far-right wins increase Euroscepticism and break-up risk premium.
**Data:** European Parliament election results; Politico Europe poll-of-polls; EU Council voting weight changes; BTP-Bund spread (FRED: IRLTLT01ITM156N).
**Repricing speed:** Immediate post-election; sovereign spread repricing within hours.
**Most affected:** European financials (bank-sovereign doom loop), Industrials, Euro-denominated assets generally.

### 25. Emerging Market Electoral Risk
**Mechanism:** Election of populist or heterodox-economic candidates in major EM economies (Brazil, Mexico, Turkey, South Africa) triggers sharp currency depreciation and equity multiple compression; nationalisation risk repricing; fiscal profligacy concerns.
**Data:** MSCI Emerging Markets constituent country election calendars; IADB political economy tracker; Freedom House Freedom in the World annual report; V-Dem electoral democracy index.
**Repricing speed:** Days ahead of election on polling shifts; immediate on result announcement.
**Most affected:** EM Equity funds, Commodity producers in affected country, Banks (sovereign-credit linkage).

### 26. Political Polarization and Legislative Gridlock
**Mechanism:** Extreme polarization increases probability of government shutdowns, debt ceiling standoffs, delayed fiscal response to recession; markets price uncertainty premium; US government shutdown episodes show modest but measurable equity effects.
**Data:** DW-NOMINATE polarization scores (congressional voting data); Brookings Institution gridlock tracker; Government Accountability Office shutdown cost reports; FRED: Federal Government Shutdown indicator.
**Repricing speed:** Days as shutdown approach becomes likely; immediate on resolution.
**Most affected:** Government Contractors, Healthcare (Medicare/Medicaid spending dependent), Research institutions.

### 27. Populist Policy Risk
**Mechanism:** Populist governments enact windfall taxes on corporate profits (e.g., UK energy windfall tax, EU bank windfall tax), price controls, export bans, and expropriation; reduces equity valuations in targeted industries.
**Data:** IMF Fiscal Monitor (populism chapter); Cesifo DICE database on government interventions; EIU Democracy Index.
**Repricing speed:** Days to weeks as policy details emerge.
**Most affected:** Energy, Banking, Utilities, Mining (resource-rich countries especially vulnerable).

### 28. US Debt Ceiling Crises
**Mechanism:** Approaching debt ceiling creates US Treasury default risk; T-bill rates spike for maturities spanning ceiling date; equity markets reprice on default tail risk; 2011 episode: S&P downgrade plus ceiling fight caused ~20% equity correction.
**Data:** US Treasury Daily Treasury Statement (DTS); Bipartisan Policy Center debt ceiling countdown; CBO budget and economic outlook.
**Repricing speed:** Gradual as ceiling date approaches; acute in final 2-4 weeks; immediate resolution rally.
**Most affected:** Money Market Funds, Government Contractors, Financial Services (T-bill collateral concerns), Risk assets broadly.

### 29. Government Shutdown Episodes
**Mechanism:** GDP drag (~0.1-0.2% per week from GDP); federal contractor revenue loss; consumer confidence effect; market historically shrugs off short shutdowns but prices longer ones.
**Data:** OMB budget circulars; CBO shutdown cost estimates; FRED payroll employment (government component).
**Repricing speed:** Contained within days for short shutdowns; building pressure after 2+ weeks.
**Most affected:** Defense Contractors, Research Services, National Parks tourism, Federal Employee consumer spending.

### 30. Constitutional Crisis and Rule of Law Deterioration
**Mechanism:** Property rights uncertainty increases; contract enforcement becomes unreliable; foreign investment withdraws; equity risk premium expands for domestic markets.
**Data:** World Justice Project Rule of Law Index (annual); Varieties of Democracy Liberal Democracy Index; Freedom House Nations in Transit.
**Repricing speed:** Gradual, over months to years; acute at pivotal events (court packing, election refusal).
**Most affected:** Domestic financial systems, Real Estate, Foreign-investor-heavy indices.

---

## Block 4: Regulatory Regime Changes (11 factors)

### 31. Antitrust Enforcement Intensity
**Mechanism:** Elevated antitrust scrutiny blocks M&A (deal premium evaporates), forces divestitures, reduces pricing power; EU and US have had distinct cycles of intensity; FAANG stocks trade at discount during high-scrutiny periods.
**Data:** DOJ Antitrust Division enforcement statistics (annual); FTC enforcement actions database; EU DG COMP case register (all free); American Bar Association antitrust section statistics.
**Repricing speed:** Days on specific investigation announcements; structural repricing over months.
**Most affected:** Technology (platform monopolies), Telecommunications, Healthcare (hospital mergers), Financial Services (banking consolidation).

### 32. Financial Sector Regulation Cycle (Basel/Dodd-Frank)
**Mechanism:** Higher capital requirements reduce bank return-on-equity; Volcker Rule restricts proprietary trading; leverage ratio requirements compress bank earnings; deregulation episodes (2018 Dodd-Frank rollback) expand bank valuations.
**Data:** BIS Basel Committee regulatory implementation tracker; Federal Register proposed/final rules; FDIC capital rule proposals; Bank for International Settlements Annual Economic Report.
**Repricing speed:** Weeks to months as rulemaking details emerge; immediate on key votes.
**Most affected:** Banks, Insurance Companies, Asset Managers, Broker-Dealers.

### 33. Pharmaceutical Drug Pricing Regulation
**Mechanism:** Medicare drug price negotiation authority (Inflation Reduction Act) directly reduces revenue for negotiated drugs; price cap proposals cause sector-wide multiple compression; policy uncertainty suppresses pharma R&D investment.
**Data:** CMS Medicare Negotiation announcements; CBO scoring of drug pricing proposals; FDA drug approval rate statistics; IQVIA drug spending reports.
**Repricing speed:** Days on legislative votes or CMS announcements; anticipatory repricing over bill consideration period.
**Most affected:** Large-cap Pharma (AbbVie, Bristol-Myers Squibb), PBMs, Specialty Pharma.

### 34. Environmental Regulation (EPA/EU ETS)
**Mechanism:** Emissions regulations increase compliance costs for heavy industry; clean power rules reshape utility capital spending; SEC climate disclosure requirements increase reporting costs and potentially valuation adjustments; IRA production tax credits benefit clean energy.
**Data:** EPA regulatory calendar and proposed rules; EU ETS allowance price (€/tonne CO2, daily via EEX); SEC climate rule development tracker; EPA Greenhouse Gas Reporting Program.
**Repricing speed:** Anticipatory (proposal → final rule): months; immediate on unexpected rule reversals.
**Most affected:** Utilities, Energy (coal most at risk), Auto Manufacturers, Chemicals, Steel.

### 35. Data Privacy and Technology Regulation
**Mechanism:** GDPR-style regulations impose compliance costs and restrict business models reliant on personal data monetization; China's PIPL limits data transfer; FTC enforcement against dark patterns; data localization laws increase infrastructure costs.
**Data:** IAPP Privacy Tracker (international privacy law database); EU Data Protection Board enforcement statistics; FTC privacy enforcement actions; China PIPL implementation bulletins.
**Repricing speed:** Days to weeks per enforcement action; structural repricing over regulatory cycle.
**Most affected:** Technology Platforms (Meta, Alphabet), AdTech, E-commerce, Data Brokers.

### 36. AI Regulation and Governance
**Mechanism:** EU AI Act compliance costs; US executive orders on AI safety; sector-specific AI restrictions (autonomous weapons, financial AI); export controls on AI chips; regulatory approval requirements for high-stakes AI (healthcare, finance).
**Data:** EU AI Act implementation timeline (eur-lex.europa.eu); White House OSTP AI policy tracker; NIST AI Risk Management Framework adoption; Brookings AI governance tracker.
**Repricing speed:** Months as regulations develop; immediate on enforcement actions or export control expansions.
**Most affected:** Technology, Healthcare (AI diagnostics), Financial Services (algorithmic trading), Autonomous Vehicles.

### 37. Cryptocurrency and Digital Asset Regulation
**Mechanism:** SEC enforcement actions redefine which tokens are securities; exchange licensing requirements create barriers to entry; spot ETF approvals expand institutional access (Bitcoin ETF approval: +20% in days); CBDC development affects payment system incumbents.
**Data:** SEC enforcement actions database; CFTC cryptocurrency rulemaking; MiCA (EU crypto regulation) implementation calendar; BIS CBDC tracker.
**Repricing speed:** Immediate for specific enforcement actions; anticipatory for rule proposals.
**Most affected:** Crypto exchanges, Fintech, Traditional Financial Services (disruption risk), Payment Networks.

### 38. Healthcare and Insurance Regulation
**Mechanism:** ACA stability/repeal risk affects hospital and insurer margins; CMS reimbursement rate changes directly affect provider revenues; FDA approval rates affect pharmaceutical pipeline values; 340B drug pricing program changes affect hospital systems.
**Data:** CMS Final Payment Rules (annual); FDA approval statistics (monthly); Kaiser Family Foundation ACA tracking; CBO insurance market analyses.
**Repricing speed:** Days on CMS rule finals; immediate on FDA actions.
**Most affected:** Hospitals, Managed Care Organizations, Pharmaceutical Manufacturers, Medical Devices.

### 39. Energy Sector Regulatory Changes
**Mechanism:** Renewable portfolio standards affect utility capital spending; pipeline approval processes create long-tailed regulatory risk for midstream; FERC rate determinations affect utility profitability; LNG export terminal approvals affect supply growth.
**Data:** FERC docket database; DOE LNG approval tracker; NERC reliability standards; EIA regulatory impact analyses.
**Repricing speed:** Weeks to months for major regulatory decisions; immediate for surprise reversals.
**Most affected:** Utilities, Midstream Energy, Oil and Gas E&P, Renewable Energy Developers.

### 40. Labor and Employment Regulation
**Mechanism:** Federal minimum wage increases affect labor-intensive retailers and restaurants; NLRB interpretation of gig worker classification (employee vs. contractor) affects platform labor cost structures; non-compete restrictions affect talent mobility and compensation structures.
**Data:** DOL regulatory agenda; NLRB press releases; State minimum wage change databases; EPI minimum wage tracker.
**Repricing speed:** Days to weeks on classification rulings; gradual for wage floor changes.
**Most affected:** Consumer Staples (Retail), Restaurants, Gig Platform Companies (Uber, Lyft, DoorDash), Healthcare Staffing.

### 41. Tax Policy Changes (Corporate)
**Mechanism:** Corporate tax rate changes directly affect after-tax earnings and P/E ratios; 2017 TCJA cut (35% to 21%) added ~10-15% to S&P 500 EPS immediately; repatriation tax holidays trigger buyback waves; GILTI minimum tax affects multinational profit shifting.
**Data:** JCT revenue estimates on tax legislation; Tax Foundation analysis; OECD Pillar Two implementation tracker (global minimum tax); Treasury proposed regulations.
**Repricing speed:** Immediate on bill passage; anticipatory over legislative debate.
**Most affected:** All sectors (corporate tax universal); disproportionate impact on domestically focused companies with high effective rates.

---

## Block 5: Energy Geopolitics (8 factors)

### 42. OPEC+ Production Decisions
**Mechanism:** Surprise production cuts or increases move oil prices by 3-8% within days; equity repricing for energy sector immediate; downstream impact on inflation expectations and monetary policy (secondary channel); airline cost impacts.
**Data:** OPEC Monthly Oil Market Report; IEA Oil Market Report; EIA Weekly Petroleum Status Report (free, every Wednesday); Bloomberg OPEC production survey.
**Repricing speed:** Immediate (within minutes of OPEC press conference); energy equities within hours.
**Most affected:** Energy (E&P and Integrated), Airlines, Chemicals (petrochemical feedstock), Consumer Discretionary (fuel costs).

### 43. Natural Gas Pipeline Geopolitics
**Mechanism:** Russia-Ukraine gas transit disruptions (Nord Stream, Yamal pipeline) cause European energy crisis; price spikes in TTF natural gas affect industrial competitiveness; energy-intensive industries face input cost shocks; LNG shipping demand increases.
**Data:** ENTSOG gas flow data (daily, European natural gas flows); EIA Natural Gas Weekly Update; TTF front-month natural gas futures (ICE); Bruegel gas storage monitor.
**Repricing speed:** Immediate for LNG and gas futures; weeks for industrial sector cost repricing.
**Most affected:** Utilities (European), Chemicals, Fertilizer Producers, Steel (electric arc furnaces), LNG shipping.

### 44. LNG Market Development and Geopolitical LNG Flows
**Mechanism:** US LNG export capacity expansion realigns global gas markets; Qatar's LNG contracts link to geopolitical relationships; Australia-Japan LNG long-term contracts create price floors; stranded LNG cargoes during demand shocks.
**Data:** DOE LNG export data (monthly); Shell LNG Outlook (annual); GIIGNL Annual Report; Kpler LNG tracking (proprietary but widely cited).
**Repricing speed:** Gradual (infrastructure cycles are multi-year); spot cargo market reprices daily.
**Most affected:** LNG Producers (Cheniere, QatarEnergy JVs), Utilities, Shipping (LNG tankers), Chemical feedstock users.

### 45. Strategic Petroleum Reserve (SPR) Releases
**Mechanism:** IEA coordinated SPR release or unilateral US release temporarily suppresses oil prices; reversal (SPR refill) creates demand; political tool used in election years; capacity reduction reduces future buffer.
**Data:** EIA Weekly Petroleum Status Report (SPR stock levels, free); DOE SPR release announcements (press releases); IEA Oil Market Report (IEA release coordination).
**Repricing speed:** Immediate on announcement; gradual reversal as release ends.
**Most affected:** Energy (E&P), Energy Services, Consumer Discretionary (fuel price relief).

### 46. Rare Earth and Critical Mineral Geopolitics
**Mechanism:** China's dominance in rare earth processing (>85% market share) creates supply vulnerability; export controls on gallium, germanium, graphite trigger supply chain repricing; Congo cobalt control creates EV battery supply risk; Indonesia nickel export bans (implemented 2020).
**Data:** US Geological Survey Mineral Commodity Summaries (annual, free); China Ministry of Commerce export license announcements; DOE Critical Materials Assessment; European Raw Materials Alliance.
**Repricing speed:** Immediate for export control announcements; weeks for full downstream repricing.
**Most affected:** Electric Vehicle Manufacturers, Semiconductor Manufacturers, Defense Electronics, Battery Producers.

### 47. Arctic Resource Development and Geopolitical Competition
**Mechanism:** Melting Arctic opens new shipping routes (Northern Sea Route) and resource access; Russia-NATO tensions over Arctic claims affect development; investment uncertainty for Arctic oil projects under ESG pressure plus geopolitical friction.
**Data:** Arctic Council working group reports; USGS Arctic resource estimates; Northern Sea Route transit data from Russian Arctic and Antarctic Research Institute.
**Repricing speed:** Multi-year structural; specific incident repricing within days.
**Most affected:** Energy E&P (Arctic plays), Shipping, Mining (Arctic mineral access).

### 48. Energy Transition Policy Acceleration/Deceleration
**Mechanism:** IRA renewable tax credits (US): +$369 billion investment stimulus for clean energy sector; policy reversal risk under administration change; EU Green Deal implementation pace; China clean energy deployment scale affects global panel and battery costs.
**Data:** Bloomberg NEF New Energy Outlook; IEA World Energy Outlook (annual); REN21 Renewables Global Status Report; S&P Global Platts Energy Transition Outlook.
**Repricing speed:** Immediate on major policy reversals; structural over multi-year transition.
**Most affected:** Renewable Energy (solar, wind), Utilities, EV Manufacturers, Oil and Gas (terminal value repricing).

### 49. Nuclear Energy Policy Shifts
**Mechanism:** Germany's nuclear exit (2023) raised European power prices and increased reliance on fossil imports; France's nuclear extension decisions affect EDF valuation significantly; US nuclear relicensing affects baseload power pricing; SMR (small modular reactor) policy support creates new sector.
**Data:** World Nuclear Association reactor database; NRC license renewal tracker; IEA nuclear power projections; French energy regulatory commission CRE reports.
**Repricing speed:** Weeks to months for policy decisions; immediate for unexpected facility closures.
**Most affected:** Utilities, Uranium Miners (Cameco, Kazatomprom), Nuclear Services Companies, Coal Power (substitute demand).

---

## Block 6: Macroeconomic Policy and Fiscal Factors (8 factors)

### 50. Central Bank Independence Threats
**Mechanism:** Political interference with central bank mandates raises inflation expectations; currency depreciation; sovereign risk premium expansion; Turkey (2021) case study: Erdogan's pressure on TCMB caused 44% lira depreciation and equity collapse in USD terms.
**Data:** BIS Papers on central bank independence; IMF Article IV consultations; Dincer-Eichengreen Central Bank Independence dataset (research); Political pressure event database.
**Repricing speed:** Immediate for currency; days for equity repricing.
**Most affected:** Financial Sector, Domestic Consumer companies (inflation sensitive), Foreign-currency debt issuers.

### 51. Sovereign Debt Crisis Escalation
**Mechanism:** Debt-to-GDP ratio approaching threshold triggers bond market panic; yield spike increases refinancing costs; austerity programs reduce growth; equity markets fall as growth collapses; contagion to neighboring economies.
**Data:** IMF World Economic Outlook debt data (biannual); BIS debt statistics (quarterly); Reinhart-Rogoff crisis database (historical academic); IMF Debt Sustainability Analysis (country-specific).
**Repricing speed:** Gradual buildup; acute crisis phase reprices within hours once confidence collapses.
**Most affected:** Local financial stocks, Government-linked companies, All domestic equities (growth channel).

### 52. Fiscal Stimulus Package Announcements
**Mechanism:** Large fiscal programs boost aggregate demand and corporate earnings expectations; CARES Act (US 2020) stabilized equity markets within days of passage; EU Recovery Fund (2020) drove European equity rebound; multiplier effects vary by spending composition.
**Data:** CBO cost estimates; OMB budget documents; EU Commission fiscal notifications; IMF Fiscal Monitor fiscal stance data.
**Repricing speed:** Immediate on announcement; weeks as scale/composition details confirm.
**Most affected:** Construction and Infrastructure, Consumer Discretionary, Defense (defense spending component), Healthcare (stimulus targeting).

### 53. Austerity Programs and Fiscal Consolidation
**Mechanism:** Spending cuts reduce government demand multiplier; public sector wage freezes affect consumer spending; privatization programs create market opportunities but also uncertainty; IMF conditionality programs signal extreme fiscal stress.
**Data:** IMF country reports and program documents; EU Excessive Deficit Procedure notifications; OECD Economic Policy Committee output gap assessments.
**Repricing speed:** Gradual as program details emerge; immediate on IMF program announcement (mixed signals: relief on crisis resolution, concern on growth drag).
**Most affected:** Government Contractors, Utilities (privatization), Consumer Staples (household income compression), Healthcare (public spending cuts).

### 54. Tax Policy — Capital Gains and Dividend Taxation
**Mechanism:** Capital gains tax rate increases cause pre-emptive selling as investors realize gains before rate hike takes effect; dividend tax changes affect yield-sensitive sectors; carried interest and pass-through income rules affect PE/VC investment decisions.
**Data:** JCT revenue estimates; IRS Statistics of Income; Tax Policy Center analysis; Treasury proposed regulations.
**Repricing speed:** Immediate on legislative signals; selling pressure builds as effective date approaches.
**Most affected:** High-yield equities (dividend tax sensitive), Real Estate (capital gains sensitivity), Private Equity-backed companies.

### 55. Government Procurement and Defense Spending
**Mechanism:** Defense authorization acts determine spending across segments; sequestration risk caps spending; NATO 2% GDP commitment drives allied defense budgets; Ukraine war has driven European rearmament (Rheinmetall +300% 2022-2024).
**Data:** DoD budget submission and appropriations acts; NATO Defense Expenditure reports (annual); SIPRI military expenditure database.
**Repricing speed:** Weeks on budget announcements; immediate on supplemental appropriations for active conflicts.
**Most affected:** Defense and Aerospace (direct), Cybersecurity (growing share), Semiconductors (defense electronics).

### 56. Inflation Control Legislation and Price Controls
**Mechanism:** Price controls directly cap revenue for targeted industries; rent control reduces real estate investment returns; pharmaceutical price controls (IRA) reduce drug revenue; windfall profit taxes on energy companies.
**Data:** Federal Register price control regulations; CPI component analysis (FRED); OECD product market regulation database.
**Repricing speed:** Immediate on announcement for targeted sectors; weeks for second-order effects.
**Most affected:** Energy, Pharmaceuticals, Utilities, Real Estate Investment Trusts.

### 57. Country Risk Ratings (Sovereign and Political Risk)
**Mechanism:** ICRG, Moody's, S&P, and Fitch sovereign risk ratings affect cost of capital for domestic corporations; downgrade triggers forced selling by investment-grade mandates; political risk insurance premiums affect FDI flows.
**Data:** PRS Group International Country Risk Guide (ICRG) — proprietary but widely used; Moody's/S&P/Fitch sovereign rating actions (free releases); World Bank Governance Indicators (annual); Economist Intelligence Unit Country Risk Ratings.
**Repricing speed:** Immediate on rating action; anticipatory trading in CDS markets.
**Most affected:** EM banks (sovereign-bank linkage), local currency bonds, Foreign equity investors with mandate constraints.

---

## Block 7: Technology Sovereignty and Diplomatic Factors (8 factors)

### 58. Technology Decoupling (US-China Tech Cold War)
**Mechanism:** Semiconductor export controls, equipment bans, forced divestiture (TikTok), and research collaboration restrictions create a bifurcating technology ecosystem; dual supply chain costs increase; companies with China revenue face uncertainty premium.
**Data:** BIS Entity List; USTR 301 investigation into China technology practices; CSIS China tech threat tracker; SIA China revenue exposure by company.
**Repricing speed:** Immediate on BIS actions; gradual structural repricing over years.
**Most affected:** Semiconductors (NVDA, AVGO, ASML, AMAT), Software, Telecom Equipment, Cloud Computing.

### 59. Data Localization and Digital Sovereignty Laws
**Mechanism:** Requirements to store data domestically increase cloud infrastructure costs; fragments global platforms; increases operational complexity for multinationals; Russian SORM, China Cybersecurity Law, and India DPDP Act all impose localization.
**Data:** IAPP global privacy law database; Digital Trade Estimates database (ECIPE); USITC digital trade reports; OECD digital policy tracker.
**Repricing speed:** Weeks to months as compliance requirements crystallize.
**Most affected:** Cloud Providers (AWS, Azure, Google Cloud), Enterprise Software, Social Media Platforms.

### 60. US-China Diplomatic Relations Barometer
**Mechanism:** Diplomatic deterioration (balloon incident, Taiwan strait tensions) correlates with equity volatility spikes; S&P 500 tech sector disproportionately exposed through China revenue dependency; diplomatic improvement (Biden-Xi meeting) provides risk-on relief rally.
**Data:** CSIS Asia Maritime Transparency Initiative; Taiwan Strait tensions tracker; US-China Business Council policy tracker; American Chamber of Commerce in China annual survey.
**Repricing speed:** Hours on specific incidents; days for broader diplomatic signals.
**Most affected:** Technology, Consumer Discretionary (Apple supply chain), Retail (China sourcing).

### 61. Bilateral Investment Treaty (BIT) Modifications
**Mechanism:** Investment treaties protect foreign direct investment; treaty withdrawal or modification increases expropriation risk; ISDS (investor-state dispute settlement) mechanisms allow corporate claims against governments — their weakening increases political risk premium.
**Data:** UNCTAD Investment Policy Hub — all BITs and treaties database (free); ICSID arbitration case database; OECD FDI Regulatory Restrictiveness Index.
**Repricing speed:** Weeks to months; primarily affects FDI-dependent sectors.
**Most affected:** Mining, Infrastructure, Financial Services with EM operations.

### 62. Diplomatic Sanctions Coalitions (Multilateral)
**Mechanism:** Coordinated sanctions by G7/EU/US are more effective and harder to evade than unilateral actions; Russia 2022 SWIFT exclusion demonstrated severity; coalition fractures allow sanction evasion and reduce impact.
**Data:** EU sanctions monitor; G7 summit communique databases; UN Security Council resolution tracking; Carnegie Endowment for International Peace sanctions database.
**Repricing speed:** Immediate on announcement; gradual as evasion routes and enforcement intensity become apparent.
**Most affected:** Energy, Financial Services (correspondent banking), Defense Equipment Exporters, Agricultural Trade.

### 63. Foreign Investment Screening (CFIUS and Equivalents)
**Mechanism:** CFIUS blocks or conditionally approves foreign acquisitions of US companies in sensitive sectors; equivalent bodies in EU (FDI screening regulation), UK (NSI Act), and Australia (FIRB) are expanding scope; risk of deal blocking affects M&A premium.
**Data:** CFIUS annual report to Congress; Treasury CFIUS press releases; EU FDI Screening Working Group reports; OECD FDI transparency mapping.
**Repricing speed:** Days on CFIUS referral announcement; weeks for disposition.
**Most affected:** Technology (cybersecurity, AI, semiconductors), Defense Supply Chain, Critical Infrastructure.

### 64. Immigration Policy and High-Skill Worker Access
**Mechanism:** H-1B visa restrictions raise labor costs for US tech companies; immigration crackdowns affect agricultural labor supply; talent mobility restrictions impair startup formation; brain drain from restrictive source countries affects human capital.
**Data:** USCIS visa statistics (annual); National Foundation for American Policy H-1B analyses; Migration Policy Institute immigration statistics.
**Repricing speed:** Gradual through wage pressure and hiring cost channels; policy announcement effects immediate for most labor-intensive sectors.
**Most affected:** Technology (H-1B dependent), Agriculture (undocumented labor supply), Healthcare (immigrant physician shortage), Homebuilding (construction labor).

### 65. Internet Governance and Platform Regulation
**Mechanism:** EU Digital Services Act content moderation obligations increase compliance costs; Section 230 reform risk in US threatens platform liability shields; internet fragmentation (splinternet) increases operational complexity for global platforms.
**Data:** EU DSA/DMA implementation tracker (ec.europa.eu); FTC Section 5 enforcement actions; Freedom House Freedom on the Net index (annual).
**Repricing speed:** Days on enforcement actions; structural over regulatory cycle.
**Most affected:** Social Media Platforms, E-commerce, Online Advertising (Google, Meta).

---

## Block 8: Climate Policy, Pandemic Preparedness, and Emerging Risks (8 factors)

### 66. International Climate Agreements and NDC Commitments
**Mechanism:** Paris Agreement implementation and Nationally Determined Contributions (NDCs) drive carbon pricing expectations; COP negotiation outcomes affect renewable energy investment visibility; US Paris Agreement exit/re-entry creates discontinuous policy uncertainty.
**Data:** UNFCCC NDC Registry (all countries' commitments, free); Climate Action Tracker (independent assessment); IRENA renewable capacity statistics.
**Repricing speed:** COP outcomes: days; annual NDC updates: weeks.
**Most affected:** Fossil Fuel E&P (stranded asset risk), Utilities, Industrial Companies (carbon cost), Renewable Energy (positive).

### 67. Carbon Pricing and Emissions Trading Systems
**Mechanism:** EU ETS carbon price (currently EUR 60-70/tonne) directly increases costs for covered industries; California cap-and-trade; China ETS launch (world's largest by volume); carbon price uncertainty creates investment planning risk.
**Data:** EU ETS allowance price (EEX, daily); ICAP ETS map and price tracker; World Bank State and Trends of Carbon Pricing (annual); RGGI allowance auction results.
**Repricing speed:** Daily for ETS participants; quarterly for pass-through to product pricing.
**Most affected:** Power Generators, Steel, Cement, Chemicals, Aviation (EU ETS coverage).

### 68. Physical Climate Risk and Extreme Weather
**Mechanism:** Hurricane/wildfire/flood events cause insured losses repricing; persistent drought affects agricultural commodity prices and food companies; heat stress reduces labor productivity; sea-level rise affects coastal real estate value.
**Data:** Munich Re NatCatSERVICE (catastrophe loss database, annual report free); NOAA storm event database; IPCC climate risk assessments; Four Twenty Seven physical risk scores (now Moody's).
**Repricing speed:** Immediate for acute events; gradual for chronic physical risk repricing.
**Most affected:** Insurance (reinsurance), Real Estate (coastal exposure), Agriculture, Utilities (water stress), Infrastructure.

### 69. Pandemic Risk and Biosecurity Policy
**Mechanism:** COVID-19 demonstrated pandemic's market impact capacity (S&P fell 34% in 5 weeks); future pandemic risk is a priced tail event; WHO International Health Regulations modifications affect speed of global response; biodefense spending creates sector opportunities.
**Data:** WHO Disease Outbreak News (free); CDC pandemic threat assessments; Johns Hopkins Center for Health Security; Global Health Security Index.
**Repricing speed:** Within hours to days of severity assessment; depends heavily on transmissibility/mortality signals.
**Most affected:** Airlines, Hotels, Restaurants (negative), Healthcare/Biotech/Pharma (positive), E-commerce and Remote Work tech (positive).

### 70. Water Scarcity and Resource Conflict
**Mechanism:** Nile Basin tensions (GERD dam dispute) threaten Egyptian agriculture stability; India-Pakistan water treaties under stress; water scarcity drives migration and political instability; corporate water risk affects production capacity for water-intensive industries.
**Data:** UN Food and Agriculture Organization AQUASTAT database; World Resources Institute Aqueduct Water Risk tool; Pacific Institute water conflict chronology.
**Repricing speed:** Gradual (structural); acute in drought years.
**Most affected:** Agricultural Companies, Food and Beverage (water-intensive), Utilities, Mining (water licensing risk).

### 71. Demographic and Immigration Policy Intersection
**Mechanism:** Aging population fiscal pressures (pension, healthcare) drive long-term sovereign risk; anti-immigration policies tighten labor markets and accelerate automation investment; demographic divergence between aging DM and young EM drives capital flow shifts.
**Data:** UN World Population Prospects (biennial); OECD Pensions at a Glance; Brookings demographic economic projections.
**Repricing speed:** Structural (5-10 year horizon); discrete policy changes reprice within weeks.
**Most affected:** Healthcare (eldercare demand), Automation and Robotics, Real Estate (household formation), Consumer Staples (demographic shifts).

### 72. Food Security and Agricultural Policy
**Mechanism:** Export bans (Ukraine grain export halt, India rice export ban) cause global food price spikes affecting agricultural commodity ETFs and food companies; agricultural subsidy policy changes affect sector profitability; fertilizer sanctions (Russia) affect agricultural input costs.
**Data:** FAO Food Price Index (monthly, free); USDA World Agricultural Supply and Demand Estimates (monthly); World Food Programme food security monitoring.
**Repricing speed:** Days for commodity futures; weeks for equity repricing.
**Most affected:** Agricultural Commodity Producers, Fertilizer Companies, Food and Beverage Manufacturers, Agricultural Equipment.

### 73. Disinformation, Political Narrative Warfare, and Market Manipulation Risk
**Mechanism:** State-sponsored disinformation campaigns can induce false market panic (fake Bloomberg tweet 2013 AP hack: S&P fell 143 points in minutes); coordinated narrative control affects investor confidence in regulatory/policy outlook; social media-driven retail coordination (meme stocks) exploits sentiment signals.
**Data:** DFRLab (Atlantic Council) disinformation tracking; Stanford Internet Observatory; CISA election integrity advisories; SEC investigation reports on market manipulation.
**Repricing speed:** Minutes for acute disinformation-driven price moves; detection and reversal within hours in most cases.
**Most affected:** Individual equities targeted by coordinated campaigns; Financials (trust-sensitive); Small-cap (lower liquidity amplifies manipulation).

---

## Summary Table: Repricing Speed Distribution

| Speed Category | Number of Factors | Examples |
|---|---|---|
| Minutes to hours | 18 | War outbreak, OPEC cut, OFAC sanctions, GPR spikes, tariff announcements |
| Hours to days | 22 | Election outcomes, antitrust investigations, regulatory rulings, cyberattacks |
| Days to weeks | 20 | Legislative debates, treaty negotiations, rating agency actions, policy proposals |
| Weeks to months | 9 | Structural regulatory changes, austerity programs, demographic policy |
| Multi-year structural | 4 | Energy transition, demographics, digital decoupling, climate physical risk |

## Summary Table: Most Affected Sectors by Factor Count

| Sector | Factors With Primary/Major Exposure |
|---|---|
| Energy | 12 (OPEC, sanctions, pipeline geopolitics, carbon regulation, SPR, rare earths, nuclear) |
| Technology | 11 (export controls, antitrust, AI regulation, data sovereignty, decoupling, CFIUS) |
| Financial Services | 11 (sovereign risk, banking regulation, sanctions, debt ceiling, currency manipulation) |
| Healthcare / Pharma | 8 (drug pricing, FDA, pandemic, ACA, GDPR/HIPAA, austerity) |
| Industrials / Defense | 8 (war, defense spending, trade war, infrastructure stimulus, export controls) |
| Consumer Discretionary | 7 (tariffs, terrorism, government shutdown, immigration, minimum wage, supply chain) |
| Utilities | 6 (carbon pricing, energy regulation, nuclear, water scarcity, climate physical risk) |
| Agriculture | 5 (food security, export bans, fertilizer, water scarcity, immigration labor) |

---

## Key Data Sources for Systematic Factor Monitoring

| Priority | Source | Coverage | Access |
|---|---|---|---|
| High | GDELT Project | Global event data, geopolitical coding | Free, daily |
| High | Caldara-Iacoviello GPR Index | Geopolitical risk composite | Free, FRED GPRI |
| High | FRED (Federal Reserve) | US macro, sovereign data, market indicators | Free, API |
| High | OFAC SDN List | Sanctions | Free, daily updates |
| High | ACLED | Conflict event data | Free (research) |
| High | EU ETS (EEX) | Carbon pricing | Free historical |
| Medium | ICRG (PRS Group) | Country political risk ratings | Proprietary (academic license) |
| Medium | V-Dem Dataset | Democracy and institutional quality | Free (academic) |
| Medium | WTO dispute database | Trade dispute outcomes | Free |
| Medium | UCDP | Armed conflict data | Free (research) |
| Medium | BIS Entity List | Export control | Free |
| Medium | Munich Re NatCatSERVICE | Catastrophe loss events | Free annual report |
| Lower | SIPRI | Military spending, arms transfers | Free annual |
| Lower | Freedom House | Political freedom indicators | Free annual |
| Lower | World Justice Project | Rule of law index | Free annual |

---

## Implementation Notes for Feature Engineering

**Signal timeliness mismatch:** Factors updating annually (ICRG, Freedom House) must be forward-interpolated or converted to regime-level dummy variables. Do not use point-in-time annual values as if they have daily resolution.

**Confounding with macro factors:** Geopolitical factors often trigger macro responses (Fed rate cuts during crises, fiscal stimulus). Separate the geopolitical shock from the monetary/fiscal response in models — both are signal sources but operate on different timescales.

**Endogeneity:** Equity market declines themselves can trigger political crises (recession-driven political instability). Treat lagged market returns as a potential control when modeling political stability indicators.

**Regime-switching appropriateness:** Many of these factors are most predictive during high-tension regimes. A regime-switching model (Markov-switching or threshold model) that activates geopolitical features when GPR is elevated may outperform a single model across all regimes.

**Text/NLP extraction path:** For real-time factor monitoring, GDELT is the primary free source. Country-specific event coding using the CAMEO event coding taxonomy (Conflict and Mediation Event Observations) allows quantification of diplomatic cooperation vs. conflict on a daily basis for 250+ countries.
