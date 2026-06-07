import SwiftUI

// MARK: - Data

private let hotTickers = [
    "NVDA", "AAPL", "MSFT", "META", "GOOGL", "AMZN", "TSLA", "AMD", "NFLX",
    "HOOD", "PLTR", "ARM", "SMCI", "COIN", "MSTR", "UBER", "LYFT", "SOFI",
    "RBLX", "SNAP", "RIVN", "SOUN", "AI", "IONQ", "QUBT", "RDDT", "ACHR", "JOBY",
]

private struct PreIPOCompany: Identifiable {
    let id = UUID()
    let name: String
    let sector: String
    let description: String
    let status: String
    let estValuation: String
}

private let preIPO: [PreIPOCompany] = [
    PreIPOCompany(name: "OpenAI",     sector: "AI / LLM",      description: "Maker of ChatGPT, GPT-4o, and Sora",                     status: "Pre-IPO",   estValuation: "$157B"),
    PreIPOCompany(name: "Anthropic",  sector: "AI / LLM",      description: "AI safety company, maker of Claude",                     status: "Pre-IPO",   estValuation: "$61B"),
    PreIPOCompany(name: "SpaceX",     sector: "Aerospace",     description: "Rockets, Starship, Starlink satellite internet",          status: "Pre-IPO",   estValuation: "$350B"),
    PreIPOCompany(name: "Stripe",     sector: "Fintech",       description: "Global payments infrastructure for internet businesses", status: "Pre-IPO",   estValuation: "$65B"),
    PreIPOCompany(name: "Databricks", sector: "Data / AI",     description: "Unified data analytics and AI platform",                 status: "Pre-IPO",   estValuation: "$62B"),
    PreIPOCompany(name: "Canva",      sector: "Design / SaaS", description: "Online visual design and content creation platform",     status: "Pre-IPO",   estValuation: "$26B"),
    PreIPOCompany(name: "Chime",      sector: "Neobank",       description: "Mobile-first banking and financial services",            status: "Pre-IPO",   estValuation: "$25B"),
    PreIPOCompany(name: "Klarna",     sector: "Fintech",       description: "Buy now, pay later — filed for US IPO",                 status: "Filed IPO", estValuation: "$20B"),
    PreIPOCompany(name: "Discord",    sector: "Social",        description: "Community and gaming communication platform",            status: "Pre-IPO",   estValuation: "$15B"),
    PreIPOCompany(name: "Epic Games", sector: "Gaming",        description: "Fortnite, Unreal Engine, Epic Games Store",             status: "Private",   estValuation: "$32B"),
]

// MARK: - HomeView

struct HomeView: View {
    @EnvironmentObject var store: AppStore
    @State private var selectedTab = 0
    @State private var selectedHorizon = "1w"

    private let horizons = ["1d", "1w", "1m"]

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Top-level sub-tab picker
                Picker("Section", selection: $selectedTab) {
                    Text("Top Signals").tag(0)
                    Text("Hot Stocks").tag(1)
                    Text("Pre-IPO").tag(2)
                }
                .pickerStyle(.segmented)
                .padding()

                switch selectedTab {
                case 0: topSignalsSection
                case 1: hotStocksSection
                default: preIPOSection
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

    // MARK: - Top Signals

    private var topSignalsSection: some View {
        VStack(spacing: 0) {
            horizonPicker

            if store.topPredictions.isEmpty {
                emptyState
            } else {
                predictionList
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
        .padding(.horizontal)
        .padding(.bottom, 8)
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

    // MARK: - Hot Stocks

    private var hotStocksSection: some View {
        let predictions = hotTickers.compactMap { ticker -> (String, Prediction)? in
            guard let p = store.prediction(for: ticker, horizon: "1w") else { return nil }
            return (ticker, p)
        }
        let withPred = predictions.count
        let withoutPred = hotTickers.count - withPred

        return VStack(spacing: 0) {
            HStack {
                Text("\(withPred) with predictions · \(withoutPred) not yet synced")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Spacer()
            }
            .padding(.horizontal)
            .padding(.vertical, 8)

            List {
                ForEach(hotTickers, id: \.self) { ticker in
                    if let pred = store.prediction(for: ticker, horizon: "1w") {
                        NavigationLink(destination: StockDetailView(ticker: ticker)) {
                            PredictionRow(prediction: pred)
                        }
                    } else {
                        HotTickerUnavailableRow(ticker: ticker)
                    }
                }
            }
            .listStyle(.plain)
        }
    }

    // MARK: - Pre-IPO

    private var preIPOSection: some View {
        ScrollView {
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                ForEach(preIPO) { company in
                    PreIPOCard(company: company)
                }
            }
            .padding()
        }
    }
}

// MARK: - Supporting Views

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

private struct HotTickerUnavailableRow: View {
    let ticker: String

    var body: some View {
        HStack {
            Text(ticker)
                .font(.headline)
            Spacer()
            Text("Not in local database")
                .font(.caption)
                .foregroundStyle(.secondary)
                .italic()
        }
        .padding(.vertical, 4)
        .opacity(0.6)
    }
}

private struct PreIPOCard: View {
    let company: PreIPOCompany

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(company.name)
                    .font(.subheadline.bold())
                    .lineLimit(1)
                Spacer()
                statusBadge
            }

            Text(company.sector)
                .font(.caption2)
                .foregroundStyle(.blue)

            Text(company.description)
                .font(.caption2)
                .foregroundStyle(.secondary)
                .lineLimit(3)
                .fixedSize(horizontal: false, vertical: true)

            Spacer(minLength: 4)

            HStack {
                Text("Est.")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Spacer()
                Text(company.estValuation)
                    .font(.caption.bold())
                    .foregroundStyle(.primary)
            }
        }
        .padding(12)
        .frame(maxWidth: .infinity, minHeight: 130, alignment: .topLeading)
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var statusBadge: some View {
        let color: Color = switch company.status {
        case "Filed IPO": .orange
        case "Private":   .purple
        default:          .blue
        }
        return Text(company.status)
            .font(.caption2.bold())
            .foregroundStyle(color)
            .padding(.horizontal, 5)
            .padding(.vertical, 2)
            .background(color.opacity(0.12))
            .clipShape(Capsule())
    }
}
