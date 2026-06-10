import SwiftUI

struct PortfolioView: View {
    @EnvironmentObject var store: AppStore
    @State private var showingAddSheet = false
    @State private var selectedHorizon = "1w"

    private var totalValue: Double {
        store.portfolio.reduce(0) { sum, h in
            let price = store.latestPrice(for: h.ticker) ?? h.costBasis
            return sum + price * h.shares
        }
    }

    private var totalCost: Double {
        store.portfolio.reduce(0) { $0 + $1.costBasis * $1.shares }
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                summaryHeader

                if store.portfolio.isEmpty {
                    emptyState
                } else {
                    holdingsList
                }
            }
            .navigationTitle("Portfolio")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button(action: { showingAddSheet = true }) {
                        Image(systemName: "plus")
                    }
                    .accessibilityLabel("Add holding")
                }
                ToolbarItem(placement: .topBarLeading) {
                    Picker("", selection: $selectedHorizon) {
                        ForEach(["1d", "1w", "1m"], id: \.self) { Text($0).tag($0) }
                    }
                    .pickerStyle(.segmented)
                    .frame(width: 120)
                    .animation(.easeInOut(duration: 0.2), value: selectedHorizon)
                }
            }
            .sheet(isPresented: $showingAddSheet) {
                AddHoldingSheet()
                    .environmentObject(store)
            }
        }
    }

    private var summaryHeader: some View {
        VStack(spacing: 8) {
            Text("Total Value")
                .font(.caption)
                .foregroundStyle(.secondary)
            Text(String(format: "$%.2f", totalValue))
                .font(.largeTitle.bold())
                .foregroundStyle(.primary)
            let gain = totalValue - totalCost
            let gainPct = totalCost > 0 ? gain / totalCost * 100 : 0
            HStack(spacing: 4) {
                Image(systemName: gain >= 0 ? "arrow.up" : "arrow.down")
                Text(String(format: "%+.2f (%+.1f%%)", gain, gainPct))
            }
            .font(.subheadline)
            .foregroundStyle(gain >= 0 ? .green : .red)
            .animation(.easeInOut(duration: 0.2), value: gain)
        }
        .frame(maxWidth: .infinity)
        .padding(16)
        .background(Color(.systemGray6))
    }

    private var holdingsList: some View {
        List {
            ForEach(store.portfolio, id: \.ticker) { holding in
                HoldingRow(holding: holding, horizon: selectedHorizon)
            }
            .onDelete { indices in
                indices.forEach { i in
                    store.removeHolding(store.portfolio[i].ticker)
                }
            }
        }
        .listStyle(.plain)
    }

    private var emptyState: some View {
        ContentUnavailableView(
            "No Holdings",
            systemImage: "briefcase",
            description: Text("Tap + to add your first holding")
        )
    }
}

struct HoldingRow: View {
    @EnvironmentObject var store: AppStore
    let holding: PortfolioHolding
    let horizon: String

    private var currentPrice: Double { store.latestPrice(for: holding.ticker) ?? holding.costBasis }
    private var marketValue: Double { currentPrice * holding.shares }
    private var gain: Double { (currentPrice - holding.costBasis) * holding.shares }
    private var gainPct: Double { holding.costBasis > 0 ? (currentPrice - holding.costBasis) / holding.costBasis * 100 : 0 }

    var body: some View {
        NavigationLink(destination: StockDetailView(ticker: holding.ticker).environmentObject(store)) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(holding.ticker)
                        .font(.headline)
                        .foregroundStyle(.primary)
                    Text(String(format: "%.2f shares @ $%.2f", holding.shares, holding.costBasis))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                VStack(alignment: .trailing, spacing: 4) {
                    Text(String(format: "$%.2f", marketValue))
                        .font(.subheadline.bold())
                        .foregroundStyle(.primary)
                    Text(String(format: "%+.1f%%", gainPct))
                        .font(.caption)
                        .foregroundStyle(gain >= 0 ? .green : .red)
                }
            }
            .padding(.vertical, 4)
        }
    }
}

struct AddHoldingSheet: View {
    @EnvironmentObject var store: AppStore
    @Environment(\.dismiss) var dismiss

    @State private var ticker = ""
    @State private var shares = ""
    @State private var costBasis = ""
    @State private var validationError: String?

    var body: some View {
        NavigationStack {
            Form {
                Section("Stock") {
                    TextField("Ticker (e.g. TSLA)", text: $ticker)
                        .autocorrectionDisabled()
                        .textInputAutocapitalization(.characters)
                }
                Section("Position") {
                    TextField("Number of shares", text: $shares)
                        .keyboardType(.decimalPad)
                    TextField("Average cost per share ($)", text: $costBasis)
                        .keyboardType(.decimalPad)
                }
                if let err = validationError {
                    Section {
                        Text(err)
                            .font(.caption)
                            .foregroundStyle(.red)
                    }
                }
            }
            .navigationTitle("Add Holding")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Add") { addHolding() }
                        .disabled(ticker.isEmpty || shares.isEmpty || costBasis.isEmpty)
                }
            }
        }
    }

    private func addHolding() {
        guard let s = Double(shares), s > 0,
              let c = Double(costBasis), c > 0,
              !ticker.isEmpty else {
            validationError = "Please enter valid positive numbers for shares and cost."
            return
        }
        store.addHolding(ticker: ticker.uppercased(), shares: s, costBasis: c)
        dismiss()
    }
}
