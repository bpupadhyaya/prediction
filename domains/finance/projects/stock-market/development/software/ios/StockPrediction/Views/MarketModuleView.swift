import SwiftUI

// MARK: - Market modules (Crypto / Earnings / Sectors / Global Markets)
//
// Real implementations of the former "Coming Soon" modules. Each module fetches
// its instrument universe from Yahoo, computes day/week performance, and runs the
// on-device model for a 1-week direction. Mirrors the Android MarketModuleScreen.

// MARK: - Universes

private struct ModuleInstrument {
    let symbol: String
    let label: String
    var sublabel: String = ""
}

private let cryptoUniverse: [ModuleInstrument] = [
    .init(symbol: "BTC-USD", label: "Bitcoin"), .init(symbol: "ETH-USD", label: "Ethereum"),
    .init(symbol: "SOL-USD", label: "Solana"), .init(symbol: "BNB-USD", label: "BNB"),
    .init(symbol: "XRP-USD", label: "XRP"), .init(symbol: "ADA-USD", label: "Cardano"),
    .init(symbol: "DOGE-USD", label: "Dogecoin"), .init(symbol: "AVAX-USD", label: "Avalanche"),
    .init(symbol: "DOT-USD", label: "Polkadot"), .init(symbol: "LINK-USD", label: "Chainlink"),
    .init(symbol: "LTC-USD", label: "Litecoin"), .init(symbol: "BCH-USD", label: "Bitcoin Cash"),
    .init(symbol: "TRX-USD", label: "TRON"), .init(symbol: "XLM-USD", label: "Stellar"),
    .init(symbol: "XMR-USD", label: "Monero"), .init(symbol: "ETC-USD", label: "Ethereum Classic"),
    .init(symbol: "FIL-USD", label: "Filecoin"), .init(symbol: "ATOM-USD", label: "Cosmos"),
    .init(symbol: "UNI7083-USD", label: "Uniswap"), .init(symbol: "AAVE-USD", label: "Aave"),
    .init(symbol: "ALGO-USD", label: "Algorand"), .init(symbol: "VET-USD", label: "VeChain"),
    .init(symbol: "HBAR-USD", label: "Hedera"), .init(symbol: "NEAR-USD", label: "NEAR"),
]

private let sectorUniverse: [ModuleInstrument] = [
    .init(symbol: "XLK", label: "Technology"), .init(symbol: "XLF", label: "Financials"),
    .init(symbol: "XLE", label: "Energy"), .init(symbol: "XLV", label: "Health Care"),
    .init(symbol: "XLI", label: "Industrials"), .init(symbol: "XLY", label: "Cons. Discretionary"),
    .init(symbol: "XLP", label: "Cons. Staples"), .init(symbol: "XLU", label: "Utilities"),
    .init(symbol: "XLRE", label: "Real Estate"), .init(symbol: "XLB", label: "Materials"),
    .init(symbol: "XLC", label: "Communications"), .init(symbol: "SPY", label: "S&P 500 (bench)"),
]

private let globalUniverse: [ModuleInstrument] = [
    .init(symbol: "^GSPC", label: "S&P 500", sublabel: "United States"),
    .init(symbol: "^IXIC", label: "Nasdaq", sublabel: "United States"),
    .init(symbol: "^DJI", label: "Dow Jones", sublabel: "United States"),
    .init(symbol: "^GSPTSE", label: "TSX", sublabel: "Canada"),
    .init(symbol: "^BVSP", label: "Bovespa", sublabel: "Brazil"),
    .init(symbol: "^FTSE", label: "FTSE 100", sublabel: "United Kingdom"),
    .init(symbol: "^GDAXI", label: "DAX", sublabel: "Germany"),
    .init(symbol: "^FCHI", label: "CAC 40", sublabel: "France"),
    .init(symbol: "^STOXX50E", label: "Euro Stoxx 50", sublabel: "Eurozone"),
    .init(symbol: "^N225", label: "Nikkei 225", sublabel: "Japan"),
    .init(symbol: "^HSI", label: "Hang Seng", sublabel: "Hong Kong"),
    .init(symbol: "000001.SS", label: "Shanghai", sublabel: "China"),
    .init(symbol: "^KS11", label: "KOSPI", sublabel: "South Korea"),
    .init(symbol: "^BSESN", label: "Sensex", sublabel: "India"),
    .init(symbol: "^NSEI", label: "NIFTY 50", sublabel: "India"),
    .init(symbol: "^AXJO", label: "ASX 200", sublabel: "Australia"),
    .init(symbol: "^TWII", label: "TAIEX", sublabel: "Taiwan"),
    .init(symbol: "^STI", label: "Straits Times", sublabel: "Singapore"),
    .init(symbol: "^JKSE", label: "IDX Composite", sublabel: "Indonesia"),
    .init(symbol: "^KLSE", label: "KLCI", sublabel: "Malaysia"),
    .init(symbol: "^MXX", label: "IPC", sublabel: "Mexico"),
    .init(symbol: "^TA125.TA", label: "TA-125", sublabel: "Israel"),
]

private let earningsUniverse: [String] = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "AMD", "NFLX",
    "JPM", "V", "WMT", "COST", "ORCL", "CRM", "ADBE", "INTC", "QCOM", "TXN",
    "HOOD", "PLTR", "COIN", "UBER", "SOFI", "RDDT",
]

// MARK: - Row model

private struct ModuleRow: Identifiable {
    var id: String { symbol }
    let symbol: String
    let name: String
    let sublabel: String
    let price: Double
    let changePct1d: Double
    let ret1w: Double
    let direction: String?
    let probability: Double?
    var earningsDate: Date? = nil
}

// MARK: - View

struct MarketModuleView: View {
    let moduleId: String
    let onBack: () -> Void

    @State private var rows: [ModuleRow] = []
    @State private var isLoading = true
    @State private var errorMessage: String?
    @State private var selectedTicker: String?

    private var module: StockModule? { stockModules.first { $0.id == moduleId } }
    // Index symbols (^GSPC, 000001.SS) have no detail screen — only plain tickers navigate.
    private var rowsTappable: Bool { moduleId != "global" }

    var body: some View {
        NavigationStack {
            ZStack(alignment: .top) {
                Color(red: 0.043, green: 0.118, blue: 0.212).ignoresSafeArea()

                VStack(spacing: 0) {
                    header
                    if isLoading {
                        Spacer()
                        ProgressView("Fetching market data…")
                            .tint(.white)
                            .foregroundStyle(.white.opacity(0.6))
                        Spacer()
                    } else if let err = errorMessage, rows.isEmpty {
                        Spacer()
                        VStack(spacing: 12) {
                            Text(err)
                                .foregroundStyle(.white.opacity(0.7))
                                .multilineTextAlignment(.center)
                            Button("Retry") { Task { await load(force: true) } }
                                .buttonStyle(.borderedProminent)
                        }
                        .padding(32)
                        Spacer()
                    } else {
                        content
                    }
                }
            }
            .navigationDestination(item: $selectedTicker) { ticker in
                StockDetailView(ticker: ticker)
            }
        }
        .task { await load() }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Button(action: onBack) {
                    HStack(spacing: 4) {
                        Image(systemName: "chevron.left")
                        Text("Home")
                    }
                    .font(.system(size: 15, weight: .medium))
                    .foregroundStyle(.white)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(.ultraThinMaterial)
                    .clipShape(Capsule())
                }
                Spacer()
                Button {
                    Task { await load(force: true) }
                } label: {
                    Image(systemName: "arrow.clockwise")
                        .foregroundStyle(.white.opacity(0.7))
                }
            }
            .padding(.horizontal, 16)
            .padding(.top, 8)

            HStack(spacing: 12) {
                if let mod = module {
                    ZStack {
                        Circle().fill(mod.gradient).frame(width: 44, height: 44)
                        Image(systemName: mod.icon)
                            .font(.system(size: 20))
                            .foregroundStyle(mod.iconColor)
                    }
                    VStack(alignment: .leading, spacing: 2) {
                        Text(mod.title).font(.title3.bold()).foregroundStyle(.white)
                        Text(mod.subtitle).font(.caption).foregroundStyle(.white.opacity(0.6))
                    }
                }
                Spacer()
            }
            .padding(.horizontal, 16)
        }
        .padding(.bottom, 8)
    }

    @ViewBuilder
    private var content: some View {
        ScrollView {
            LazyVStack(spacing: 8) {
                if moduleId == "sectors" {
                    sectorHeatMap
                    Text("Forecasts")
                        .font(.caption)
                        .foregroundStyle(.white.opacity(0.6))
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, 4)
                }
                ForEach(rows) { row in
                    instrumentCard(row)
                        .contentShape(Rectangle())
                        .onTapGesture {
                            if rowsTappable { selectedTicker = row.symbol }
                        }
                }
                Text("1-week direction from the on-device model. Probabilistic — not financial advice.")
                    .font(.caption2)
                    .foregroundStyle(.white.opacity(0.35))
                    .multilineTextAlignment(.center)
                    .padding(.vertical, 14)
            }
            .padding(.horizontal, 12)
        }
    }

    private var sectorHeatMap: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("1-week performance map")
                .font(.caption)
                .foregroundStyle(.white.opacity(0.6))
                .padding(.horizontal, 4)
            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 6), count: 3), spacing: 6) {
                ForEach(rows) { row in
                    let intensity = min(abs(row.ret1w) / 4.0, 1.0)
                    let base = row.ret1w >= 0 ? Color(red: 0.086, green: 0.639, blue: 0.290)
                                              : Color(red: 0.863, green: 0.149, blue: 0.149)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(row.symbol).font(.caption.bold()).foregroundStyle(.white)
                        Text(formatPct(row.ret1w)).font(.caption2).foregroundStyle(.white.opacity(0.85))
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(8)
                    .frame(height: 56)
                    .background(base.opacity(0.25 + 0.6 * intensity))
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                    .onTapGesture { selectedTicker = row.symbol }
                }
            }
        }
        .padding(.bottom, 8)
    }

    private func instrumentCard(_ row: ModuleRow) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 3) {
                HStack(spacing: 6) {
                    Text(row.name)
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(.white)
                    if !row.sublabel.isEmpty {
                        Text(row.sublabel).font(.caption2).foregroundStyle(.white.opacity(0.45))
                    }
                }
                HStack(spacing: 8) {
                    Text(row.symbol).font(.caption2).foregroundStyle(.white.opacity(0.5))
                    if moduleId == "earnings", let d = row.earningsDate {
                        Text("Earnings \(d.formatted(.dateTime.weekday(.abbreviated).month(.abbreviated).day()))")
                            .font(.caption2)
                            .foregroundStyle(Color(red: 0.576, green: 0.765, blue: 0.941))
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color(red: 0.102, green: 0.239, blue: 0.451))
                            .clipShape(RoundedRectangle(cornerRadius: 6))
                    }
                }
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 3) {
                Text(formatPrice(row.price))
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(.white)
                Text("\(formatPct(row.changePct1d)) today")
                    .font(.caption2)
                    .foregroundStyle(row.changePct1d >= 0 ? Color(red: 0.29, green: 0.87, blue: 0.50)
                                                          : Color(red: 0.97, green: 0.44, blue: 0.44))
            }
            directionChip(row)
                .padding(.leading, 6)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .background(Color(red: 0.075, green: 0.141, blue: 0.247))
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }

    @ViewBuilder
    private func directionChip(_ row: ModuleRow) -> some View {
        // The bundled model emits exactly 0.5 when unavailable — render neutral.
        let isNeutral = row.direction == nil || row.probability == nil ||
            (row.probability! > 0.495 && row.probability! < 0.505)
        if isNeutral {
            chipLabel("—", bg: Color(red: 0.118, green: 0.161, blue: 0.231), fg: .white.opacity(0.4))
        } else if row.direction == "UP" {
            chipLabel("▲ \(Int((row.probability ?? 0.5) * 100))%",
                      bg: Color(red: 0.078, green: 0.325, blue: 0.176),
                      fg: Color(red: 0.29, green: 0.87, blue: 0.50))
        } else {
            chipLabel("▼ \(Int((1 - (row.probability ?? 0.5)) * 100))%",
                      bg: Color(red: 0.376, green: 0.102, blue: 0.102),
                      fg: Color(red: 0.97, green: 0.44, blue: 0.44))
        }
    }

    private func chipLabel(_ text: String, bg: Color, fg: Color) -> some View {
        Text(text)
            .font(.caption.bold())
            .foregroundStyle(fg)
            .padding(.horizontal, 8)
            .padding(.vertical, 5)
            .background(bg)
            .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    // MARK: - Loading

    private func load(force: Bool = false) async {
        if !force && !rows.isEmpty { return }
        isLoading = true
        errorMessage = nil

        let result: [ModuleRow]
        switch moduleId {
        case "crypto":   result = await loadInstruments(cryptoUniverse)
        case "sectors":  result = await loadInstruments(sectorUniverse)
        case "global":   result = await loadInstruments(globalUniverse)
        case "earnings": result = await loadEarnings()
        default:         result = []
        }

        rows = result
        isLoading = false
        if result.isEmpty {
            errorMessage = "No data available — check your connection and retry."
        }
    }

    private func loadInstruments(_ universe: [ModuleInstrument]) async -> [ModuleRow] {
        await withTaskGroup(of: ModuleRow?.self) { group in
            for inst in universe {
                group.addTask {
                    guard let bars = try? await YahooFinanceFetcher.fetchPriceBars(ticker: inst.symbol),
                          bars.count >= 253 else { return nil }
                    let chrono = bars.sorted { $0.date < $1.date }
                    let last = chrono[chrono.count - 1]
                    let prev = chrono[chrono.count - 2]
                    let wk = chrono[chrono.count - 6]
                    let newestFirst = chrono.reversed().map { $0 }
                    let pred = PredictionEngine.shared.predict(fromBars: newestFirst, ticker: inst.symbol)
                    return ModuleRow(
                        symbol: inst.symbol,
                        name: inst.label,
                        sublabel: inst.sublabel,
                        price: last.close,
                        changePct1d: (last.close - prev.close) / prev.close * 100,
                        ret1w: (last.close - wk.close) / wk.close * 100,
                        direction: pred?.direction,
                        probability: pred?.probability
                    )
                }
            }
            var out: [ModuleRow] = []
            for await row in group { if let row { out.append(row) } }
            // Preserve universe order
            let order = Dictionary(uniqueKeysWithValues: universe.enumerated().map { ($1.symbol, $0) })
            return out.sorted { (order[$0.symbol] ?? 99) < (order[$1.symbol] ?? 99) }
        }
    }

    private func loadEarnings() async -> [ModuleRow] {
        let watch = (try? DatabaseManager.shared.watchlist().map(\.ticker)) ?? []
        var symbols: [String] = []
        for s in watch + earningsUniverse where !symbols.contains(s) { symbols.append(s) }

        let nowSec = Int64(Date().timeIntervalSince1970)
        let horizonSec = nowSec + 60 * 60 * 24 * 45   // next 45 days

        guard let quotes = try? await YahooFinanceFetcher.fetchQuoteLites(symbols: symbols) else { return [] }
        let upcoming = quotes
            .filter { ($0.earningsTimestamp ?? 0) >= nowSec && ($0.earningsTimestamp ?? .max) <= horizonSec }
            .sorted { ($0.earningsTimestamp ?? 0) < ($1.earningsTimestamp ?? 0) }
            .prefix(15)

        return await withTaskGroup(of: ModuleRow?.self) { group in
            for q in upcoming {
                group.addTask {
                    var direction: String? = nil
                    var probability: Double? = nil
                    if let bars = try? await YahooFinanceFetcher.fetchPriceBars(ticker: q.symbol),
                       bars.count >= 253 {
                        let newestFirst = bars.sorted { $0.date > $1.date }
                        if let pred = PredictionEngine.shared.predict(fromBars: newestFirst, ticker: q.symbol) {
                            direction = pred.direction
                            probability = pred.probability
                        }
                    }
                    return ModuleRow(
                        symbol: q.symbol,
                        name: q.name,
                        sublabel: "",
                        price: q.price,
                        changePct1d: q.changePct,
                        ret1w: 0,
                        direction: direction,
                        probability: probability,
                        earningsDate: q.earningsTimestamp.map { Date(timeIntervalSince1970: TimeInterval($0)) }
                    )
                }
            }
            var out: [ModuleRow] = []
            for await row in group { if let row { out.append(row) } }
            return out.sorted { ($0.earningsDate ?? .distantFuture) < ($1.earningsDate ?? .distantFuture) }
        }
    }
}

// MARK: - Formatting

private func formatPct(_ v: Double) -> String {
    String(format: "%+.2f%%", v)
}

private func formatPrice(_ v: Double) -> String {
    if v.isNaN { return "—" }
    if v >= 1000 { return v.formatted(.number.precision(.fractionLength(0))) }
    if v >= 1 { return v.formatted(.number.precision(.fractionLength(2))) }
    return String(format: "%.4f", v)
}
