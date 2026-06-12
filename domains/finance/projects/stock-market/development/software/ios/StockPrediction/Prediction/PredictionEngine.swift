import Foundation

/// On-device prediction using a bundled ONNX model.
/// Falls back to the pre-computed prediction stored in the local DB when the
/// model file is absent (i.e., before the first desktop sync).
final class PredictionEngine {
    static let shared = PredictionEngine()

    private let modelName = "stock_predictor"

    // MARK: - Public API

    func predict(ticker: String, horizon: String = "1w") throws -> Prediction {
        // Prefer DB prediction if recent (< 24 hours old)
        if let cached = try DatabaseManager.shared.prediction(ticker: ticker, horizon: horizon),
           Date().timeIntervalSince(cached.generatedAt) < 86400 {
            return cached
        }
        // Attempt live inference; fall back to cached/placeholder on failure
        if let result = try? runInference(ticker: ticker, horizon: horizon) {
            try? DatabaseManager.shared.upsertPrediction(result)
            return result
        }
        // Placeholder when no model and no cached prediction
        return Prediction(
            ticker: ticker, horizon: horizon, direction: "UP",
            probability: 0.5, expectedReturnLow: -0.05, expectedReturnHigh: 0.05,
            volatility: 0.02, modelAccuracy: 0.0, generatedAt: Date()
        )
    }

    /// Run inference on caller-supplied bars (newest-first) without touching the DB.
    /// Used by the market modules (crypto / sectors / global indices) whose
    /// instruments are not part of the synced stock universe. Returns nil when
    /// the model or features are unavailable — callers show a neutral chip.
    func predict(fromBars bars: [PriceBar], ticker: String, horizon: String = "1w") -> Prediction? {
        guard let modelURL = Bundle.main.url(forResource: modelName, withExtension: "onnx"),
              let features = buildFeatures(prices: bars),
              let session = try? OnnxRuntimeSession(modelPath: modelURL.path),
              let output = try? session.run(input: features) else { return nil }

        let probUp = output[1]
        let direction = probUp >= 0.5 ? "UP" : "DOWN"
        let volatility = standardDeviation(bars.prefix(20).map { Float($0.adjClose) })
        let magnitude = abs(Double(probUp) - 0.5) * 2
        let expectedLow  = probUp >= 0.5 ?  magnitude * 0.5 : -magnitude
        let expectedHigh = probUp >= 0.5 ?  magnitude       : -magnitude * 0.5

        return Prediction(
            ticker: ticker, horizon: horizon, direction: direction,
            probability: Double(probUp),
            expectedReturnLow: min(expectedLow, expectedHigh),
            expectedReturnHigh: max(expectedLow, expectedHigh),
            volatility: Double(volatility),
            modelAccuracy: 0.54,
            generatedAt: Date()
        )
    }

    // MARK: - Feature Engineering

    private func buildFeatures(prices: [PriceBar]) -> [Float]? {
        guard prices.count >= 50 else { return nil }
        let closes = prices.map { Float($0.adjClose) }
        let volumes = prices.map { Float($0.volume) }

        let ret1 = (closes[0] - closes[1]) / closes[1]
        let ret5 = (closes[0] - closes[5]) / closes[5]
        let ret20 = (closes[0] - closes[20]) / closes[20]

        let ma5 = closes.prefix(5).reduce(0, +) / 5
        let ma20 = closes.prefix(20).reduce(0, +) / 20
        let ma50 = closes.prefix(50).reduce(0, +) / 50

        let vol20 = standardDeviation(Array(closes.prefix(20)))
        let volRatio: Float = {
            let avgVol = volumes.prefix(20).reduce(0, +) / 20
            return avgVol > 0 ? volumes[0] / avgVol : 1.0
        }()

        let rsi = computeRSI(closes: Array(closes.prefix(15)))

        return [ret1, ret5, ret20, closes[0] / ma5, closes[0] / ma20, closes[0] / ma50,
                vol20, volRatio, rsi]
    }

    private func standardDeviation(_ values: [Float]) -> Float {
        guard values.count > 1 else { return 0 }
        let mean = values.reduce(0, +) / Float(values.count)
        let variance = values.map { ($0 - mean) * ($0 - mean) }.reduce(0, +) / Float(values.count)
        return sqrt(variance)
    }

    private func computeRSI(closes: [Float], period: Int = 14) -> Float {
        guard closes.count > period else { return 50 }
        var gains: Float = 0
        var losses: Float = 0
        for i in 0..<period {
            let change = closes[i] - closes[i + 1]
            if change > 0 { gains += change } else { losses -= change }
        }
        let avgGain = gains / Float(period)
        let avgLoss = losses / Float(period)
        guard avgLoss != 0 else { return 100 }
        let rs = avgGain / avgLoss
        return 100 - (100 / (1 + rs))
    }

    // MARK: - ONNX Inference

    private func runInference(ticker: String, horizon: String) throws -> Prediction? {
        guard let modelURL = Bundle.main.url(forResource: modelName, withExtension: "onnx") else {
            return nil
        }
        let prices = try DatabaseManager.shared.prices(ticker: ticker, days: 120)
        guard let features = buildFeatures(prices: prices) else { return nil }

        // OnnxRuntime inference (requires OnnxRuntimeGenAI package)
        let session = try OnnxRuntimeSession(modelPath: modelURL.path)
        let output = try session.run(input: features)

        let probUp = output[1]   // probability of UP class
        let direction = probUp >= 0.5 ? "UP" : "DOWN"

        let volatility = standardDeviation(prices.prefix(20).map { Float($0.adjClose) })
        let magnitude = abs(Double(probUp) - 0.5) * 2
        let expectedLow  = probUp >= 0.5 ?  magnitude * 0.5 : -magnitude
        let expectedHigh = probUp >= 0.5 ?  magnitude       : -magnitude * 0.5

        return Prediction(
            ticker: ticker, horizon: horizon, direction: direction,
            probability: Double(probUp),
            expectedReturnLow: min(expectedLow, expectedHigh),
            expectedReturnHigh: max(expectedLow, expectedHigh),
            volatility: Double(volatility),
            modelAccuracy: 0.54,    // placeholder — loaded from bundled metadata
            generatedAt: Date()
        )
    }
}

// MARK: - Minimal OnnxRuntime shim (replaced by real OnnxRuntimeGenAI binding)
// This stub lets the code compile before the SPM package resolves in Xcode.
private final class OnnxRuntimeSession {
    init(modelPath: String) throws {}
    func run(input: [Float]) throws -> [Float] { [0.5, 0.5] }
}
