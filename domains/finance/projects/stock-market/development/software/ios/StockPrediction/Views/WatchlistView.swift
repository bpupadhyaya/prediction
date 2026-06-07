import SwiftUI

struct WatchlistView: View {
    @EnvironmentObject var store: AppStore

    var body: some View {
        NavigationStack {
            Group {
                if store.watchlist.isEmpty {
                    ContentUnavailableView(
                        "Watchlist Empty",
                        systemImage: "star",
                        description: Text("Star a stock from its detail page to add it here")
                    )
                } else {
                    List {
                        ForEach(store.watchlist, id: \.ticker) { entry in
                            NavigationLink(destination: StockDetailView(ticker: entry.ticker)) {
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
            }
            .navigationTitle("Watchlist")
        }
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
                Text(ticker).font(.headline)
                if let pred = prediction {
                    HStack(spacing: 4) {
                        Image(systemName: pred.isBullish ? "arrow.up.circle.fill" : "arrow.down.circle.fill")
                            .foregroundStyle(pred.isBullish ? .green : .red)
                            .font(.caption)
                        Text(String(format: "%.0f%%", pred.probability * 100))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Spacer()

            if let p = price {
                Text(String(format: "$%.2f", p))
                    .font(.subheadline.bold())
            }
        }
        .padding(.vertical, 4)
    }
}
