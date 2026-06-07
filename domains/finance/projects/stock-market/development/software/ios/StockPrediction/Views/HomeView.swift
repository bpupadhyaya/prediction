import SwiftUI

struct HomeView: View {
    @EnvironmentObject var store: AppStore
    @State private var selectedHorizon = "1w"

    private let horizons = ["1d", "1w", "1m"]

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                horizonPicker

                if store.topPredictions.isEmpty {
                    emptyState
                } else {
                    predictionList
                }
            }
            .navigationTitle("Market")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button(action: store.loadLocal) {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
        }
    }

    private var horizonPicker: some View {
        Picker("Horizon", selection: $selectedHorizon) {
            ForEach(horizons, id: \.self) { h in
                Text(h.uppercased()).tag(h)
            }
        }
        .pickerStyle(.segmented)
        .padding()
    }

    private var predictionList: some View {
        List(filteredPredictions, id: \.ticker) { pred in
            NavigationLink(destination: StockDetailView(ticker: pred.ticker)) {
                PredictionRow(prediction: pred)
            }
        }
        .listStyle(.plain)
    }

    private var filteredPredictions: [Prediction] {
        store.topPredictions.filter { $0.horizon == selectedHorizon }
    }

    private var emptyState: some View {
        ContentUnavailableView(
            "No Predictions Yet",
            systemImage: "chart.line.flattrend.xyaxis",
            description: Text("Sync data to generate predictions")
        )
    }
}

struct PredictionRow: View {
    let prediction: Prediction

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(prediction.ticker)
                    .font(.headline)
                Text(String(format: "%.0f%% confidence", prediction.probability * 100))
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 4) {
                HStack(spacing: 4) {
                    Image(systemName: prediction.isBullish ? "arrow.up.circle.fill" : "arrow.down.circle.fill")
                        .foregroundStyle(prediction.isBullish ? .green : .red)
                    Text(prediction.direction)
                        .font(.subheadline.bold())
                        .foregroundStyle(prediction.isBullish ? .green : .red)
                }
                Text(String(format: "Model: %.0f%%", prediction.modelAccuracy * 100))
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
            }
        }
        .padding(.vertical, 4)
    }
}
