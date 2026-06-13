import SwiftUI
import Charts

struct StockDetailView: View {
    @EnvironmentObject var store: AppStore
    let ticker: String

    @State private var prices: [PriceBar] = []
    @State private var prediction: Prediction?
    @State private var contributions: [FeatureContribution] = []
    @State private var stock: Stock?
    @State private var selectedHorizon = "1w"
    @State private var isWatchlisted = false
    @State private var showInteractive = false
    @State private var isLoading = true
    @State private var loadError: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                if isLoading {
                    loadingPlaceholder
                } else {
                    if let err = loadError {
                        errorBanner(err)
                    }

                    if let s = stock {
                        stockHeader(s)
                    }

                    priceChart

                    if let pred = prediction {
                        predictionCard(pred)
                        if !contributions.isEmpty {
                            whyCard(pred)
                        }
                    } else if !isLoading {
                        noPredictionCard
                    }

                    if !isLoading {
                        speakerHint
                    }

                    interactivePredictButton
                }

                Spacer()
            }
            .padding(16)
        }
        .navigationTitle(ticker)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar { watchlistButton }
        .task { await loadData() }
        .sheet(isPresented: $showInteractive) {
            NavigationStack {
                InteractiveParameterView(ticker: ticker)
                    .environmentObject(store)
            }
        }
    }

    // MARK: - Loading Placeholder

    private var loadingPlaceholder: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                ProgressView()
                    .scaleEffect(0.9)
                Text("Loading \(ticker)…")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            .frame(maxWidth: .infinity, alignment: .center)
            .padding(.vertical, 32)
        }
    }

    // MARK: - Error Banner

    private func errorBanner(_ message: String) -> some View {
        HStack(spacing: 8) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(.orange)
            Text(message)
                .font(.caption)
                .foregroundStyle(.primary)
            Spacer()
        }
        .padding(12)
        .background(Color.orange.opacity(0.12))
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }

    // MARK: - No-prediction placeholder

    private var noPredictionCard: some View {
        HStack(spacing: 8) {
            Image(systemName: "chart.line.flattrend.xyaxis")
                .foregroundStyle(.secondary)
            Text("No prediction available — sync data to generate one")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }

    // MARK: - Speaker Suggestion Hint

    @ViewBuilder
    private var speakerHint: some View {
        let names = SpeakerSuggestions.speakers(forTicker: ticker, sector: stock?.sector)
        if !names.isEmpty {
            HStack(spacing: 8) {
                Image(systemName: "person.wave.2.fill")
                    .font(.caption)
                    .foregroundStyle(PredictionTheme.accent)
                Text("Track for this stock: \(names.joined(separator: ", "))")
                    .font(.subheadline)
                    .foregroundStyle(.primary)
                Spacer()
            }
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(PredictionTheme.accent.opacity(0.10))
            .clipShape(RoundedRectangle(cornerRadius: 10))
        }
    }

    // MARK: - Interactive Predict Button

    private var interactivePredictButton: some View {
        Button {
            showInteractive = true
        } label: {
            HStack(spacing: 6) {
                Image(systemName: "bolt.fill")
                Text("Interactive Predict")
                    .font(.system(size: 15, weight: .semibold))
            }
            .foregroundStyle(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background(
                LinearGradient(
                    colors: [Color(red: 0.231, green: 0.510, blue: 0.965),
                             Color(red: 0.157, green: 0.376, blue: 0.784)],
                    startPoint: .leading, endPoint: .trailing
                )
            )
            .clipShape(RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(.plain)
        .sensoryFeedback(.impact(flexibility: .soft), trigger: showInteractive)
    }

    // MARK: - Watchlist Button

    private var watchlistButton: some ToolbarContent {
        ToolbarItem(placement: .topBarTrailing) {
            Button {
                store.toggleWatchlist(ticker)
                withAnimation(.easeInOut(duration: 0.2)) {
                    isWatchlisted.toggle()
                }
            } label: {
                Image(systemName: isWatchlisted ? "star.fill" : "star")
                    .foregroundStyle(isWatchlisted ? Color(red: 0.72, green: 0.53, blue: 0.04) : .secondary)
            }
            .accessibilityLabel(isWatchlisted ? "Remove from watchlist" : "Add to watchlist")
        }
    }

    // MARK: - Stock Header

    private func stockHeader(_ s: Stock) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(s.name)
                .font(.title2.bold())
                .foregroundStyle(.primary)
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

    // MARK: - Price Chart

    private var priceChart: some View {
        Group {
            if prices.isEmpty {
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color(.systemGray6))
                    .frame(height: 180)
                    .overlay(
                        Text("No price data available")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    )
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
                .chartYAxis {
                    AxisMarks(position: .trailing, values: .automatic(desiredCount: 4)) { value in
                        AxisGridLine()
                        AxisValueLabel {
                            if let price = value.as(Double.self) {
                                Text(String(format: "$%.0f", price))
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
        }
    }

    // MARK: - Prediction Card

    private func predictionCard(_ pred: Prediction) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Prediction")
                    .font(.headline)
                    .foregroundStyle(.primary)
                Spacer()
                Picker("Horizon", selection: $selectedHorizon) {
                    ForEach(["1d", "1w", "1m"], id: \.self) { Text($0).tag($0) }
                }
                .pickerStyle(.segmented)
                .frame(width: 140)
                .onChange(of: selectedHorizon) { _, _ in
                    withAnimation(.easeInOut(duration: 0.2)) {
                        prediction = store.prediction(for: ticker, horizon: selectedHorizon)
                    }
                    refreshExplanation()
                }
            }

            HStack(spacing: 20) {
                VStack(alignment: .leading) {
                    Label(pred.direction, systemImage: pred.isBullish ? "arrow.up" : "arrow.down")
                        .font(.title2.bold())
                        .foregroundStyle(pred.isBullish ? .green : .red)
                    Text("Direction")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Divider()

                VStack(alignment: .leading) {
                    Text(String(format: "%.0f%%", pred.probability * 100))
                        .font(.title2.bold())
                        .foregroundStyle(.primary)
                    Text("Confidence")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Divider()

                VStack(alignment: .leading) {
                    Text(String(format: "%.0f%%", pred.modelAccuracy * 100))
                        .font(.title2.bold())
                        .foregroundStyle(.primary)
                    Text("Model Accuracy")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            Text("This is a probabilistic prediction, not financial advice.")
                .font(.caption2)
                .foregroundStyle(.tertiary)
        }
        .padding(16)
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Why This Prediction

    private func whyCard(_ pred: Prediction) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Why this prediction")
                .font(.headline)
                .foregroundStyle(.primary)

            VStack(alignment: .leading, spacing: 8) {
                ForEach(Array(contributions.prefix(4)), id: \.feature) { c in
                    HStack(spacing: 10) {
                        Image(systemName: c.pushesUp ? "chevron.up" : "chevron.down")
                            .font(.caption.bold())
                            .foregroundStyle(c.pushesUp ? .green : .red)
                            .frame(width: 14)
                        Text(c.label)
                            .font(.subheadline)
                            .foregroundStyle(.primary)
                        Spacer()
                        Text(String(format: "%+.0f%%", c.delta * 100))
                            .font(.subheadline.monospacedDigit())
                            .foregroundStyle(c.pushesUp ? .green : .red)
                    }
                }
            }

            Text(PredictionExplainer.rationale(direction: pred.direction, contributions: contributions))
                .font(.callout)
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)

            Text(String(format: "Model accuracy (out-of-sample): %.0f%%", pred.modelAccuracy * 100))
                .font(.caption)
                .foregroundStyle(.tertiary)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    /// Recompute perturbation-based contributions for the current horizon off the
    /// main thread (16+ ONNX inferences), then publish on the main actor.
    private func refreshExplanation() {
        let symbol = ticker
        let horizon = selectedHorizon
        Task.detached(priority: .userInitiated) {
            // buildFeatures needs >= 253 newest-first bars (prices(days:) is date desc).
            let bars = (try? DatabaseManager.shared.prices(ticker: symbol, days: 600)) ?? []
            let result = PredictionEngine.shared.explain(fromBars: bars, horizon: horizon)
            await MainActor.run { contributions = result }
        }
    }

    // MARK: - Data Loading

    private func loadData() async {
        isLoading = true
        loadError = nil
        // Any-symbol support: searched global symbols (7203.T, BTC-USD, SAP.DE...)
        // are not in the synced universe — fetch ~5y from Yahoo on demand and
        // persist so the chart, prediction, and watchlist work for anything.
        let existing = store.prices(for: ticker, days: 600)
        if existing.count < 253 {
            if let bars = try? await YahooFinanceFetcher.fetchPriceBars(ticker: ticker), !bars.isEmpty {
                try? DatabaseManager.shared.upsertPrices(bars)
                if let quote = try? await YahooFinanceFetcher.fetchQuote(ticker: ticker) {
                    try? DatabaseManager.shared.upsertStocks([quote])
                }
            }
        }
        prices = store.prices(for: ticker, days: 90)
        prediction = store.prediction(for: ticker, horizon: selectedHorizon)
        isWatchlisted = store.isWatchlisted(ticker)
        do {
            stock = try DatabaseManager.shared.stock(ticker: ticker)
        } catch {
            loadError = "Could not load stock info: \(error.localizedDescription)"
        }
        isLoading = false
        if prediction != nil { refreshExplanation() }
    }
}
