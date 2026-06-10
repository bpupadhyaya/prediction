import SwiftUI

struct SearchView: View {
    @EnvironmentObject var store: AppStore
    @State private var query = ""
    @State private var results: [Stock] = []
    @State private var isSearching = false

    var body: some View {
        NavigationStack {
            List(results, id: \.ticker) { stock in
                NavigationLink(destination: StockDetailView(ticker: stock.ticker).environmentObject(store)) {
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(stock.ticker)
                                .font(.headline)
                                .foregroundStyle(.primary)
                            Spacer()
                            if let cap = stock.marketCap {
                                Text(formatMarketCap(cap))
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        Text(stock.name)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                        if let sector = stock.sector {
                            Text(sector)
                                .font(.caption2)
                                .foregroundStyle(.tertiary)
                        }
                    }
                    .padding(.vertical, 4)
                }
            }
            .listStyle(.plain)
            .searchable(text: $query, prompt: "Ticker or company name")
            .onChange(of: query) { _, newValue in
                guard !newValue.isEmpty else { results = []; return }
                isSearching = true
                results = store.search(query: newValue)
                isSearching = false
            }
            .navigationTitle("Lookup")
            .navigationBarTitleDisplayMode(.large)
            .overlay {
                if query.isEmpty {
                    ContentUnavailableView(
                        "Search Stocks",
                        systemImage: "magnifyingglass",
                        description: Text("Enter a ticker symbol or company name")
                    )
                } else if !query.isEmpty && results.isEmpty && !isSearching {
                    ContentUnavailableView.search(text: query)
                }
            }
        }
    }

    private func formatMarketCap(_ cap: Double) -> String {
        switch cap {
        case 1e12...: return String(format: "$%.1fT", cap / 1e12)
        case 1e9...:  return String(format: "$%.1fB", cap / 1e9)
        case 1e6...:  return String(format: "$%.1fM", cap / 1e6)
        default:      return String(format: "$%.0f", cap)
        }
    }
}
