import Foundation

/// On-device prediction using a bundled ONNX model.
/// Falls back to the pre-computed prediction stored in the local DB when the
/// model file is absent (i.e., before the first desktop sync).
final class PredictionEngine {
    static let shared = PredictionEngine()

    private let modelName = "stock_predictor"

    /// One bundled ONNX per horizon; 3m maps to the 1m model (closest trained).
    /// Falls back to the 1w model when a horizon-specific file is absent.
    private func modelURL(for horizon: String) -> URL? {
        let h = horizon.lowercased()
        let name: String
        if h.hasPrefix("1d") { name = "stock_predictor_1d" }
        else if h.hasPrefix("1m") || h.hasPrefix("3m") { name = "stock_predictor_1m" }
        else { name = modelName }
        return Bundle.main.url(forResource: name, withExtension: "onnx")
            ?? Bundle.main.url(forResource: modelName, withExtension: "onnx")
    }

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
        guard let modelURL = modelURL(for: horizon),
              let features = buildFeatures(prices: bars),
              let session = try? OnnxRuntimeSession(modelPath: modelURL.path),
              let output = try? session.run(input: features) else { return nil }

        let probUp = output[1]
        let direction = probUp >= 0.5 ? "UP" : "DOWN"
        let closesForVol = bars.map { Float($0.adjClose) }
        let volatility = closesForVol.count >= 21
            ? standardDeviation((0..<20).map { closesForVol[$0] / closesForVol[$0 + 1] - 1 })
            : 0
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

    // Feature semantics MUST match the training pipeline (desktop trainer.py) and
    // the exporter's MOBILE_FEATURES order exactly. Prices are newest-first.
    // 16 features — works for ANY instrument with >= 253 daily bars (stocks on any
    // exchange, crypto pairs, ETFs, indices) since all inputs are OHLCV-derived.
    private func buildFeatures(prices: [PriceBar]) -> [Float]? {
        guard prices.count >= 253 else { return nil }
        let closes = prices.map { Float($0.adjClose) }
        let volumes = prices.map { Float($0.volume) }
        let c0 = closes[0]

        func ret(_ n: Int) -> Float { (c0 - closes[n]) / closes[n] }
        func maDev(_ n: Int) -> Float { closes.prefix(n).reduce(0, +) / Float(n) / c0 - 1 }
        func volStd(_ n: Int) -> Float {
            sampleStd((0..<n).map { closes[$0] / closes[$0 + 1] - 1 })
        }

        let avgVol = volumes.prefix(20).reduce(0, +) / 20
        let volRatio: Float = avgVol > 0 ? volumes[0] / avgVol : 1.0
        let dollarVol = (0..<20).map { closes[$0] * volumes[$0] }
        let avgDollarVol = dollarVol.reduce(0, +) / 20
        let dollarTurnover: Float = avgDollarVol > 0 ? dollarVol[0] / avgDollarVol : 1.0
        let rsi = computeRSI(closes: Array(closes.prefix(15)))
        let high52w = closes.prefix(252).max() ?? c0
        let high52wRatio: Float = high52w > 0 ? c0 / high52w : 1.0

        return [
            ret(1), ret(5), ret(20), ret(60), ret(126), ret(252),
            maDev(5), maDev(20), maDev(50), maDev(200),
            volStd(20), volStd(60),
            volRatio, dollarTurnover,
            rsi, high52wRatio,
        ]
    }

    /// Sample standard deviation (ddof=1) — matches pandas rolling().std().
    private func sampleStd(_ values: [Float]) -> Float {
        guard values.count > 1 else { return 0 }
        let mean = values.reduce(0, +) / Float(values.count)
        let variance = values.map { ($0 - mean) * ($0 - mean) }.reduce(0, +) / Float(values.count - 1)
        return sqrt(variance)
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
        guard let modelURL = modelURL(for: horizon) else {
            return nil
        }
        let prices = try DatabaseManager.shared.prices(ticker: ticker, days: 600)
        guard let features = buildFeatures(prices: prices) else { return nil }

        // OnnxRuntime inference (requires OnnxRuntimeGenAI package)
        let session = try OnnxRuntimeSession(modelPath: modelURL.path)
        let output = try session.run(input: features)

        let probUp = output[1]   // probability of UP class
        let direction = probUp >= 0.5 ? "UP" : "DOWN"

        let closesForVol = prices.map { Float($0.adjClose) }
        let volatility = closesForVol.count >= 21
            ? standardDeviation((0..<20).map { closesForVol[$0] / closesForVol[$0 + 1] - 1 })
            : 0
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

// MARK: - OnnxRuntime session
// Real inference via the official onnxruntime Swift package. The canImport guard
// keeps the target buildable if the package is ever removed — the fallback stub
// returns a neutral 0.5/0.5, which the UI renders as "—".
#if canImport(OnnxRuntimeBindings)
import OnnxRuntimeBindings

private final class OnnxRuntimeSession {
    private let session: ORTSession

    init(modelPath: String) throws {
        let env = try ORTEnv(loggingLevel: .warning)
        session = try ORTSession(env: env, modelPath: modelPath, sessionOptions: nil)
    }

    /// Runs the bundled classifier on one feature row. Returns [probDOWN, probUP].
    func run(input: [Float]) throws -> [Float] {
        let data = NSMutableData(
            bytes: input, length: input.count * MemoryLayout<Float>.stride
        )
        let tensor = try ORTValue(
            tensorData: data,
            elementType: .float,
            shape: [1, NSNumber(value: input.count)]
        )
        let outputs = try session.run(
            withInputs: ["input": tensor],
            outputNames: ["probabilities"],
            runOptions: nil
        )
        guard let probsValue = outputs["probabilities"] else {
            throw LLMError.inferenceError("ONNX output 'probabilities' missing")
        }
        let probsData = try probsValue.tensorData() as Data
        let probs = probsData.withUnsafeBytes { Array($0.bindMemory(to: Float.self)) }
        guard probs.count >= 2 else {
            throw LLMError.inferenceError("ONNX output too short: \(probs.count)")
        }
        return probs
    }
}
#else
private final class OnnxRuntimeSession {
    init(modelPath: String) throws {}
    func run(input: [Float]) throws -> [Float] { [0.5, 0.5] }
}
#endif
