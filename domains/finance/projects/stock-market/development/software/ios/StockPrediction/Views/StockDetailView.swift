import SwiftUI
import Charts

struct StockDetailView: View {
    @EnvironmentObject var store: AppStore
    let ticker: String

    @State private var prices: [PriceBar] = []
    @State private var prediction: Prediction?
    @State private var stock: Stock?
    @State private var selectedHorizon = "1w"
    @State private var isWatchlisted = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                if let s = stock {
                    stockHeader(s)
                }

                priceChart

                if let pred = prediction {
                    predictionCard(pred)
                }

                Spacer()
            }
            .padding()
        }
        .navigationTitle(ticker)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar { watchlistButton }
        .task { await loadData() }
    }

    private var watchlistButton: some ToolbarContent {
        ToolbarItem(placement: .topBarTrailing) {
            Button(action: { store.toggleWatchlist(ticker) ; isWatchlisted.toggle() }) {
                Image(systemName: isWatchlisted ? "star.fill" : "star")
                    .foregroundStyle(isWatchlisted ? .yellow : .secondary)
            }
        }
    }

    private func stockHeader(_ s: Stock) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(s.name)
                .font(.title2.bold())
            if let sector = s.sector {
                Text(sector)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            if let price = store.latestPrice(for: ticker) {
                Text(String(format: "$%.2f", price))
                    .font(.title.bold())
                    .foregroundStyle(.primary)
            }
        }
    }

    private var priceChart: some View {
        Group {
            if prices.isEmpty {
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color(.systemGray6))
                    .frame(height: 180)
                    .overlay(Text("No price data").foregroundStyle(.secondary))
            } else {
                Chart(prices.reversed(), id: \.date) { bar in
                    LineMark(
                        x: .value("Date", bar.date),
                        y: .value("Price", bar.adjClose)
                    )
                    .foregroundStyle(.blue)
                }
                .frame(height: 180)
                .chartXAxis(.hidden)
            }
        }
    }

    private func predictionCard(_ pred: Prediction) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Prediction")
                    .font(.headline)
                Spacer()
                Picker("Horizon", selection: $selectedHorizon) {
                    ForEach(["1d", "1w", "1m"], id: \.self) { Text($0).tag($0) }
                }
                .pickerStyle(.segmented)
                .frame(width: 140)
                .onChange(of: selectedHorizon) { _, _ in
                    prediction = store.prediction(for: ticker, horizon: selectedHorizon)
                }
            }

            HStack(spacing: 20) {
                VStack(alignment: .leading) {
                    Label(pred.direction, systemImage: pred.isBullish ? "arrow.up" : "arrow.down")
                        .font(.title2.bold())
                        .foregroundStyle(pred.isBullish ? .green : .red)
                    Text("Direction")
                        .font(.caption).foregroundStyle(.secondary)
                }

                Divider()

                VStack(alignment: .leading) {
                    Text(String(format: "%.0f%%", pred.probability * 100))
                        .font(.title2.bold())
                    Text("Confidence")
                        .font(.caption).foregroundStyle(.secondary)
                }

                Divider()

                VStack(alignment: .leading) {
                    Text(String(format: "%.0f%%", pred.modelAccuracy * 100))
                        .font(.title2.bold())
                    Text("Model Accuracy")
                        .font(.caption).foregroundStyle(.secondary)
                }
            }

            Text("This is a probabilistic prediction, not financial advice.")
                .font(.caption2)
                .foregroundStyle(.tertiary)
        }
        .padding()
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private func loadData() async {
        prices = store.prices(for: ticker, days: 90)
        prediction = store.prediction(for: ticker, horizon: selectedHorizon)
        isWatchlisted = store.isWatchlisted(ticker)
        stock = try? DatabaseManager.shared.stock(ticker: ticker)
    }
}
