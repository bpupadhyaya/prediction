import SwiftUI

// MARK: - Crypto Radar (scan & rank by model conviction)
//
// Mirrors the web "Crypto Radar": fetches the whole crypto universe, runs the
// on-device 1-week model on each coin, and ranks the results by the calibrated
// P(up) descending (most bullish → most bearish). Per-coin fetch failures are
// skipped so one bad coin never stops the sweep. Reuses YahooFinanceFetcher and
// PredictionEngine — no new data layer, no changes to the engine.

// The crypto universe to scan — mirrors the existing crypto module universe.
private let radarCryptoUniverse: [(symbol: String, label: String)] = [
    ("BTC-USD", "Bitcoin"), ("ETH-USD", "Ethereum"),
    ("SOL-USD", "Solana"), ("BNB-USD", "BNB"),
    ("XRP-USD", "XRP"), ("ADA-USD", "Cardano"),
    ("DOGE-USD", "Dogecoin"), ("AVAX-USD", "Avalanche"),
    ("DOT-USD", "Polkadot"), ("LINK-USD", "Chainlink"),
    ("LTC-USD", "Litecoin"), ("BCH-USD", "Bitcoin Cash"),
    ("TRX-USD", "TRON"), ("XLM-USD", "Stellar"),
    ("XMR-USD", "Monero"), ("ETC-USD", "Ethereum Classic"),
    ("FIL-USD", "Filecoin"), ("ATOM-USD", "Cosmos"),
    ("UNI7083-USD", "Uniswap"), ("AAVE-USD", "Aave"),
    ("ALGO-USD", "Algorand"), ("VET-USD", "VeChain"),
    ("HBAR-USD", "Hedera"), ("NEAR-USD", "NEAR"),
]

private struct RadarRow: Identifiable {
    var id: String { symbol }
    let symbol: String
    let name: String
    let direction: String      // "UP" / "DOWN"
    let probUp: Double          // calibrated P(up)
}

struct CryptoRadarView: View {
    /// Tapping a row asks the host to open that coin's detail screen.
    var onSelect: ((String) -> Void)? = nil

    @Environment(\.dismiss) private var dismiss

    @State private var rows: [RadarRow] = []
    @State private var isScanning = false
    @State private var scanned = 0
    @State private var total = radarCryptoUniverse.count
    @State private var started = false

    var body: some View {
        NavigationStack {
            ZStack(alignment: .top) {
                Color(red: 0.043, green: 0.118, blue: 0.212).ignoresSafeArea()

                VStack(spacing: 0) {
                    headerCard
                    if isScanning && rows.isEmpty {
                        Spacer()
                        ProgressView("Scanning \(scanned)/\(total)…")
                            .tint(.white)
                            .foregroundStyle(.white.opacity(0.7))
                        Spacer()
                    } else {
                        list
                    }
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Close") { dismiss() }
                        .foregroundStyle(.white)
                }
            }
            .toolbarBackground(Color(red: 0.043, green: 0.118, blue: 0.212), for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
        }
        .task {
            if !started { started = true; await scan() }
        }
    }

    private var headerCard: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 10) {
                ZStack {
                    Circle()
                        .fill(LinearGradient(colors: [Color(red: 0.024, green: 0.235, blue: 0.294),
                                                      Color(red: 0.063, green: 0.675, blue: 0.788)],
                                             startPoint: .topLeading, endPoint: .bottomTrailing))
                        .frame(width: 40, height: 40)
                    Image(systemName: "dot.radiowaves.left.and.right")
                        .font(.system(size: 18))
                        .foregroundStyle(Color(red: 0.404, green: 0.875, blue: 0.941))
                }
                VStack(alignment: .leading, spacing: 2) {
                    Text("Crypto Radar").font(.title3.bold()).foregroundStyle(.white)
                    Text(isScanning
                         ? "1-week outlook · ranked by P(up) · \(scanned)/\(total)"
                         : "1-week outlook · ranked by P(up)")
                        .font(.caption)
                        .foregroundStyle(.white.opacity(0.6))
                }
                Spacer()
            }
        }
        .padding(.horizontal, 16)
        .padding(.top, 8)
        .padding(.bottom, 10)
    }

    private var list: some View {
        ScrollView {
            LazyVStack(spacing: 8) {
                ForEach(Array(rows.enumerated()), id: \.element.id) { idx, row in
                    radarCard(rank: idx + 1, row: row)
                        .contentShape(Rectangle())
                        .onTapGesture { onSelect?(row.symbol) }
                }
                Text("Same on-device model, calibrated — ranks the strongest 1-week bullish → bearish read. Probabilistic — not financial advice.")
                    .font(.caption2)
                    .foregroundStyle(.white.opacity(0.35))
                    .multilineTextAlignment(.center)
                    .padding(.vertical, 14)
            }
            .padding(.horizontal, 12)
        }
    }

    private func radarCard(rank: Int, row: RadarRow) -> some View {
        HStack(spacing: 12) {
            Text("\(rank)")
                .font(.subheadline.weight(.bold).monospacedDigit())
                .foregroundStyle(.white.opacity(0.55))
                .frame(width: 26, alignment: .center)
            VStack(alignment: .leading, spacing: 3) {
                Text(row.name)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(.white)
                Text(row.symbol)
                    .font(.caption2)
                    .foregroundStyle(.white.opacity(0.5))
            }
            Spacer()
            directionBadge(row)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .background(Color(red: 0.075, green: 0.141, blue: 0.247))
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }

    @ViewBuilder
    private func directionBadge(_ row: RadarRow) -> some View {
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

    // MARK: - Scan

    private func scan() async {
        isScanning = true
        scanned = 0
        rows = []

        await withTaskGroup(of: RadarRow?.self) { group in
            for inst in radarCryptoUniverse {
                group.addTask {
                    // Per-coin failures are skipped so one bad coin never stops the scan.
                    guard let bars = try? await YahooFinanceFetcher.fetchPriceBars(ticker: inst.symbol),
                          bars.count >= 253 else { return nil }
                    let newestFirst = bars.sorted { $0.date > $1.date }
                    guard let pred = PredictionEngine.shared.predict(fromBars: newestFirst, ticker: inst.symbol)
                    else { return nil }
                    return RadarRow(symbol: inst.symbol, name: inst.label,
                                    direction: pred.direction, probUp: pred.probability)
                }
            }

            var collected: [RadarRow] = []
            for await maybe in group {
                scanned += 1
                if let r = maybe {
                    collected.append(r)
                    // Update the ranked list progressively as results stream in.
                    rows = collected.sorted { $0.probUp > $1.probUp }
                }
            }
        }

        isScanning = false
    }
}

