import SwiftUI

/// Read-only "How accurate is this model?" surface. Mirrors the web's
/// "Model Transparency" card: it shows the HONEST out-of-sample stats already
/// bundled in `mobile_model_meta.json` (via ModelMeta) for each horizon —
/// directional accuracy, the naive "always up" base rate, the edge over that
/// base rate, and a calibration (Brier) indicator. No model is run here.
struct ModelTransparencyView: View {
    /// (uiHorizon, label) pairs — uiHorizon resolves to a meta key in ModelMeta.
    private let horizons: [(key: String, label: String)] = [
        ("1d", "1 Day"),
        ("1w", "1 Week"),
        ("1m", "1 Month"),
    ]

    private let meta = ModelMeta.shared

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    intro

                    if meta.isLoaded {
                        ForEach(horizons, id: \.key) { h in
                            horizonCard(uiHorizon: h.key, label: h.label)
                        }
                        footnote
                    } else {
                        Text("Model metadata is unavailable.")
                            .font(.subheadline)
                            .foregroundStyle(PredictionTheme.textSecondary)
                            .padding(.top, 8)
                    }
                }
                .padding(20)
            }
            .background(PredictionTheme.homeBg.ignoresSafeArea())
            .navigationTitle("Model Accuracy")
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    private var intro: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("How accurate is this model?")
                .font(.title3.bold())
                .foregroundStyle(PredictionTheme.textPrimary)
            Text("honest, out-of-sample")
                .font(.caption)
                .foregroundStyle(PredictionTheme.accent)
            Text("Measured on a time-ordered hold-out the model never trained on (no look-ahead). \"Edge\" is how far it beats the naive \"always up\" guess — the bar a coin-flip on a drifting market would clear.")
                .font(.footnote)
                .foregroundStyle(PredictionTheme.textSecondary)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    private func horizonCard(uiHorizon: String, label: String) -> some View {
        let acc = meta.accuracy(horizon: uiHorizon)
        let baseRate = meta.testUpRate(horizon: uiHorizon)
        let brierRaw = meta.brierRaw(horizon: uiHorizon)
        let brierCal = meta.brierCalibrated(horizon: uiHorizon)

        return VStack(alignment: .leading, spacing: 12) {
            Text(label)
                .font(.headline)
                .foregroundStyle(PredictionTheme.textPrimary)

            HStack(spacing: 0) {
                stat("Accuracy", pct(acc), color: PredictionTheme.accent)
                divider
                stat("Base rate", baseRate.map(pct) ?? "—")
                divider
                stat("Edge", edgeText(acc: acc, base: baseRate),
                     color: edgeColor(acc: acc, base: baseRate))
            }

            if let r = brierRaw, let c = brierCal {
                HStack(spacing: 6) {
                    Image(systemName: "checkmark.seal.fill")
                        .font(.system(size: 12))
                        .foregroundStyle(PredictionTheme.accent)
                    Text(String(format: "Calibrated · Brier %.3f → %.3f", r, c))
                        .font(.caption)
                        .foregroundStyle(PredictionTheme.textSecondary)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(Color.white.opacity(0.06))
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .stroke(Color.white.opacity(0.10), lineWidth: 1)
                )
        )
    }

    private func stat(_ label: String, _ value: String,
                      color: Color = PredictionTheme.textPrimary) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.system(size: 18, weight: .bold))
                .foregroundStyle(color)
                .monospacedDigit()
            Text(label)
                .font(.caption2)
                .foregroundStyle(PredictionTheme.textMuted)
        }
        .frame(maxWidth: .infinity)
    }

    private var divider: some View {
        Rectangle()
            .fill(Color.white.opacity(0.10))
            .frame(width: 1, height: 34)
    }

    private var footnote: some View {
        let n = meta.nTest(horizon: "1w")
        let nText = n.map { "Hold-out ≈ \(formatted($0)) samples per horizon · " } ?? ""
        return Text(nText + "probabilities are Platt-calibrated so the shown % matches real frequencies · 16 OHLCV features, on-device. Directional edge is small by nature — markets are near-efficient, and honesty about that is the point.")
            .font(.caption2)
            .foregroundStyle(PredictionTheme.textMuted)
            .fixedSize(horizontal: false, vertical: true)
            .padding(.top, 4)
    }

    // MARK: - Formatting

    private func pct(_ v: Double) -> String { String(format: "%.1f%%", v * 100) }

    private func edgeText(acc: Double, base: Double?) -> String {
        guard let base else { return "—" }
        let d = acc - base
        let sign = d >= 0 ? "+" : "−"
        return String(format: "%@%.1f pts", sign, abs(d) * 100)
    }

    private func edgeColor(acc: Double, base: Double?) -> Color {
        guard let base else { return PredictionTheme.textPrimary }
        return acc - base >= 0 ? PredictionTheme.accent : PredictionTheme.textPrimary
    }

    private func formatted(_ n: Int) -> String {
        let f = NumberFormatter()
        f.numberStyle = .decimal
        return f.string(from: NSNumber(value: n)) ?? "\(n)"
    }
}
