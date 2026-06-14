import SwiftUI

/// On-device "Prediction Track Record". Mirrors the web `TrackRecordTab.svelte`:
/// every prediction the user views is logged locally, then scored against the real
/// price once its horizon elapses — the model's honest, personal hit rate.
struct TrackRecordView: View {
    @State private var record: [TrackedPrediction] = []
    @State private var loaded = false
    @State private var resolving = false
    @State private var resolveMsg = ""
    @State private var showClearConfirm = false

    private static let HORIZONS = ["1d", "1w", "1m"]

    // MARK: - Derived stats

    private var scored: [TrackedPrediction] {
        record.filter { $0.resolved && $0.direction != "NEUTRAL" && $0.correct != nil }
    }
    private var hits: Int { scored.filter { $0.correct == true }.count }
    private var hitRate: Double? { scored.isEmpty ? nil : Double(hits) / Double(scored.count) * 100 }
    private var pending: Int { record.filter { !$0.resolved }.count }

    private func horizonStat(_ h: String) -> (n: Int, rate: Double?) {
        let s = scored.filter { $0.horizon == h }
        guard !s.isEmpty else { return (0, nil) }
        let r = Double(s.filter { $0.correct == true }.count) / Double(s.count) * 100
        return (s.count, r)
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("Every prediction you view is logged on-device and scored against the real price once its horizon elapses — your model's honest, personal hit rate. Nothing leaves your phone.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)

                if resolving {
                    Text(resolveMsg)
                        .font(.caption)
                        .foregroundStyle(PredictionTheme.accent)
                }

                if loaded && record.isEmpty {
                    emptyState
                } else if !record.isEmpty {
                    summaryCard
                    predictionList
                }

                Spacer()
            }
            .padding(16)
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle("Track Record")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            if !record.isEmpty {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Clear", role: .destructive) { showClearConfirm = true }
                }
            }
        }
        .confirmationDialog(
            "Clear your entire prediction track record? This cannot be undone.",
            isPresented: $showClearConfirm,
            titleVisibility: .visible
        ) {
            Button("Clear", role: .destructive) {
                try? DatabaseManager.shared.clearTrackedPredictions()
                record = []
            }
            Button("Cancel", role: .cancel) {}
        }
        .task {
            record = (try? DatabaseManager.shared.trackedPredictions()) ?? []
            loaded = true
            await resolveMatured()
        }
    }

    // MARK: - Empty

    private var emptyState: some View {
        Text("No predictions logged yet. Open a ticker and view its prediction (any horizon) and it will appear here; come back after the horizon (1d / 1w / 1m) to see whether it was right.")
            .font(.subheadline)
            .foregroundStyle(.secondary)
            .fixedSize(horizontal: false, vertical: true)
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color(.secondarySystemGroupedBackground))
            .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Summary

    private var summaryCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(alignment: .firstTextBaseline, spacing: 16) {
                VStack(alignment: .leading, spacing: 2) {
                    Text(hitRate != nil ? String(format: "%.0f%%", hitRate!) : "—")
                        .font(.system(size: 34, weight: .heavy))
                        .foregroundStyle(PredictionTheme.accent)
                    Text(scored.isEmpty ? "hit rate" : "hit rate · \(hits)/\(scored.count) scored")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                if pending > 0 {
                    Text("\(pending) still maturing")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            HStack(spacing: 12) {
                ForEach(Self.HORIZONS, id: \.self) { h in
                    let st = horizonStat(h)
                    VStack(spacing: 3) {
                        Text(h.uppercased())
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                        Text(st.rate != nil ? String(format: "%.0f%%", st.rate!) : "—")
                            .font(.headline)
                        Text("\(st.n) scored")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                    .frame(maxWidth: .infinity)
                }
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.secondarySystemGroupedBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - List

    private var sorted: [TrackedPrediction] {
        record.sorted { $0.predictedAt > $1.predictedAt }
    }

    private var predictionList: some View {
        VStack(spacing: 0) {
            ForEach(sorted, id: \.id) { p in
                row(p)
                if p.id != sorted.last?.id { Divider() }
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 4)
        .background(Color(.secondarySystemGroupedBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private func dirLabel(_ d: String) -> String {
        switch d {
        case "UP": return "Bullish"
        case "DOWN": return "Bearish"
        default: return "Neutral"
        }
    }

    private func dirColor(_ d: String) -> Color {
        switch d {
        case "UP": return .green
        case "DOWN": return .red
        default: return .secondary
        }
    }

    @ViewBuilder
    private func row(_ p: TrackedPrediction) -> some View {
        HStack(spacing: 8) {
            Text(p.ticker)
                .font(.subheadline.weight(.semibold))
            Text(p.horizon)
                .font(.caption2)
                .foregroundStyle(.secondary)
                .padding(.horizontal, 5).padding(.vertical, 1)
                .overlay(RoundedRectangle(cornerRadius: 4).stroke(Color.secondary.opacity(0.4)))
            Text("\(dirLabel(p.direction)) \(String(format: "%.0f%%", p.probability * 100))")
                .font(.caption)
                .foregroundStyle(dirColor(p.direction))
            Spacer()
            outcome(p)
        }
        .padding(.vertical, 10)
    }

    @ViewBuilder
    private func outcome(_ p: TrackedPrediction) -> some View {
        if p.resolved && p.direction != "NEUTRAL" {
            let ret = p.actualReturnPct
            HStack(spacing: 4) {
                Image(systemName: p.correct == true ? "checkmark" : "xmark")
                if let r = ret {
                    Text(String(format: "%@%.1f%%", r >= 0 ? "+" : "", r))
                }
            }
            .font(.caption.weight(.bold).monospacedDigit())
            .foregroundStyle(p.correct == true ? .green : .red)
        } else if p.resolved {
            Text(p.actualReturnPct != nil
                 ? String(format: "%@%.1f%%", p.actualReturnPct! >= 0 ? "+" : "", p.actualReturnPct!)
                 : "—")
                .font(.caption.monospacedDigit())
                .foregroundStyle(.secondary)
        } else {
            Text("matures \(p.maturesAt.formatted(date: .abbreviated, time: .omitted))")
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
    }

    // MARK: - Resolution

    /// Score every matured-but-unresolved prediction by re-fetching the current price.
    private func resolveMatured() async {
        let now = Date()
        let due = record.filter { !$0.resolved && $0.maturesAt <= now }
        guard !due.isEmpty else { return }
        resolving = true
        resolveMsg = "Scoring \(due.count) matured prediction\(due.count > 1 ? "s" : "")…"
        for var p in due {
            do {
                let bars = try await YahooFinanceFetcher.fetchPriceBars(ticker: p.ticker)
                // bars are returned oldest→newest from the parser; latest close = last.
                guard let current = bars.last?.close, current.isFinite, current > 0 else { continue }
                let ret = (current - p.priceAtPrediction) / p.priceAtPrediction * 100
                p.actualPrice = current
                p.actualReturnPct = ret
                p.correct = p.direction == "UP" ? ret > 0 : (p.direction == "DOWN" ? ret < 0 : abs(ret) < 0.5)
                p.resolved = true
                p.resolvedAt = Date()
                try DatabaseManager.shared.saveTrackedPrediction(p)
            } catch {
                // keep pending — retry on next open
            }
        }
        record = (try? DatabaseManager.shared.trackedPredictions()) ?? record
        resolving = false
        resolveMsg = ""
    }
}
