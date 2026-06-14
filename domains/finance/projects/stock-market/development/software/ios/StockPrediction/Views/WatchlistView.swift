import SwiftUI

struct WatchlistView: View {
    @EnvironmentObject var store: AppStore

    // Ranked-by-conviction mode (a personal opportunity radar over saved assets).
    // Default view stays as-is; this is an added ranked mode that scans each
    // watchlist ticker with the on-device 1-week model and ranks by P(up).
    @State private var ranked = false
    @State private var rankRows: [RankRow] = []
    @State private var isScanning = false
    @State private var scanned = 0
    @State private var total = 0

    private struct RankRow: Identifiable {
        var id: String { ticker }
        let ticker: String
        let direction: String   // "UP" / "DOWN"
        let probUp: Double        // calibrated P(up)
    }

    var body: some View {
        NavigationStack {
            Group {
                if store.watchlist.isEmpty {
                    ContentUnavailableView(
                        "Watchlist Empty",
                        systemImage: "star",
                        description: Text("Star a stock from its detail page to add it here")
                    )
                } else if ranked {
                    rankedList
                } else {
                    defaultList
                }
            }
            .navigationTitle("Watchlist")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                if !store.watchlist.isEmpty {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button {
                            toggleRanked()
                        } label: {
                            Label(ranked ? "Default" : "Rank by conviction",
                                  systemImage: "bolt.fill")
                        }
                        .tint(ranked ? .accentColor : .secondary)
                    }
                }
            }
        }
    }

    private var defaultList: some View {
        List {
            ForEach(store.watchlist, id: \.ticker) { entry in
                NavigationLink(destination: StockDetailView(ticker: entry.ticker).environmentObject(store)) {
                    WatchlistRow(ticker: entry.ticker)
                }
            }
            .onDelete { indices in
                indices.forEach { i in
                    store.toggleWatchlist(store.watchlist[i].ticker)
                }
            }
        }
        .listStyle(.plain)
    }

    private var rankedList: some View {
        Group {
            if isScanning && rankRows.isEmpty {
                VStack(spacing: 12) {
                    ProgressView("Ranking \(scanned)/\(total)…")
                    Text("1-week outlook · ranked by P(up)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if !isScanning && rankRows.isEmpty {
                ContentUnavailableView(
                    "No ranked predictions",
                    systemImage: "chart.bar.xaxis",
                    description: Text("Tickers need at least ~1 year of price history.")
                )
            } else {
                List {
                    if isScanning {
                        Section {
                            Text("Ranking \(scanned)/\(total)…")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                    ForEach(Array(rankRows.enumerated()), id: \.element.id) { idx, row in
                        NavigationLink(destination: StockDetailView(ticker: row.ticker).environmentObject(store)) {
                            rankedRow(rank: idx + 1, row: row)
                        }
                    }
                }
                .listStyle(.plain)
            }
        }
    }

    private func rankedRow(rank: Int, row: RankRow) -> some View {
        HStack(spacing: 12) {
            Text("\(rank)")
                .font(.subheadline.weight(.bold).monospacedDigit())
                .foregroundStyle(.secondary)
                .frame(width: 24, alignment: .center)
            Text(row.ticker)
                .font(.headline)
            Spacer()
            directionBadge(row)
        }
        .padding(.vertical, 4)
    }

    // Matches the Crypto Radar conviction badge styling.
    @ViewBuilder
    private func directionBadge(_ row: RankRow) -> some View {
        if row.direction == "UP" {
            badge("▲ Bullish \(Int(row.probUp * 100))%",
                  bg: Color(red: 0.078, green: 0.325, blue: 0.176),
                  fg: Color(red: 0.29, green: 0.87, blue: 0.50))
        } else {
            badge("▼ Bearish \(Int((1 - row.probUp) * 100))%",
                  bg: Color(red: 0.376, green: 0.102, blue: 0.102),
                  fg: Color(red: 0.97, green: 0.44, blue: 0.44))
        }
    }

    private func badge(_ text: String, bg: Color, fg: Color) -> some View {
        Text(text)
            .font(.caption.bold())
            .foregroundStyle(fg)
            .padding(.horizontal, 9)
            .padding(.vertical, 5)
            .background(bg)
            .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private func toggleRanked() {
        if ranked {
            ranked = false
            rankRows = []
            isScanning = false
        } else {
            ranked = true
            Task { await scan() }
        }
    }

    private func scan() async {
        let tickers = store.watchlist.map { $0.ticker }
        isScanning = true
        scanned = 0
        total = tickers.count
        rankRows = []

        await withTaskGroup(of: RankRow?.self) { group in
            for ticker in tickers {
                group.addTask {
                    // Per-ticker failures are skipped so one bad symbol never stops the scan.
                    guard let bars = try? await YahooFinanceFetcher.fetchPriceBars(ticker: ticker),
                          bars.count >= 253 else { return nil }
                    let newestFirst = bars.sorted { $0.date > $1.date }
                    guard let pred = PredictionEngine.shared.predict(fromBars: newestFirst, ticker: ticker)
                    else { return nil }
                    return RankRow(ticker: ticker, direction: pred.direction, probUp: pred.probability)
                }
            }

            var collected: [RankRow] = []
            for await maybe in group {
                scanned += 1
                if let r = maybe {
                    collected.append(r)
                    rankRows = collected.sorted { $0.probUp > $1.probUp }
                }
            }
        }

        isScanning = false
    }
}

struct WatchlistRow: View {
    @EnvironmentObject var store: AppStore
    let ticker: String

    private var prediction: Prediction? { store.prediction(for: ticker, horizon: "1w") }
    private var price: Double? { store.latestPrice(for: ticker) }

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(ticker)
                    .font(.headline)
                    .foregroundStyle(.primary)
                if let pred = prediction {
                    HStack(spacing: 4) {
                        Image(systemName: pred.isBullish ? "arrow.up.circle.fill" : "arrow.down.circle.fill")
                            .foregroundStyle(pred.isBullish ? .green : .red)
                            .font(.caption)
                        Text(String(format: "%.0f%% · %@", pred.probability * 100, pred.direction))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                } else {
                    Text("No prediction — tap to sync")
                        .font(.caption)
                        .foregroundStyle(.tertiary)
                }
            }

            Spacer()

            if let p = price {
                Text(String(format: "$%.2f", p))
                    .font(.subheadline.bold())
                    .foregroundStyle(.primary)
            } else {
                Text("—")
                    .font(.subheadline)
                    .foregroundStyle(.tertiary)
            }
        }
        .padding(.vertical, 4)
    }
}
