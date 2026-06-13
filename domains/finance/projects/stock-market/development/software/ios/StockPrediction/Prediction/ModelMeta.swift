import Foundation

/// Loads the bundled `mobile_model_meta.json` produced by the desktop trainer.
/// Provides honest out-of-sample accuracy, probability calibration, and
/// per-feature neutral baselines used by the perturbation explainer.
///
/// Calibration: calibratedProbUp = sigmoid(w * rawProbUp + b).
/// All lookups use the SAME horizon key the engine uses for model selection
/// ("1d" -> 1d, "1m"/"3m" -> 1m, otherwise 1w), so a "3m" request resolves to
/// the "1m" calibration/accuracy entry.
final class ModelMeta {
    static let shared = ModelMeta()

    struct Calibration {
        let w: Double
        let b: Double
    }

    struct HorizonMeta {
        let backtestAccuracy: Double
        let calibration: Calibration
    }

    /// Ordered feature names (MOBILE_FEATURES order). Empty if meta missing.
    let features: [String]
    /// Neutral reference value per feature (training-set mean).
    private let baselines: [String: Float]
    /// Per metadata-horizon-key meta ("1d", "1w", "1m").
    private let horizons: [String: HorizonMeta]

    /// Human-readable labels per feature name (exact strings from the spec).
    static let labels: [String: String] = [
        "return_1d": "1-day momentum",
        "return_5d": "1-week momentum",
        "return_20d": "1-month momentum",
        "return_60d": "3-month momentum",
        "return_126d": "6-month momentum",
        "return_252d": "12-month momentum",
        "ma_5": "Price vs 5-day avg",
        "ma_20": "Price vs 20-day avg",
        "ma_50": "Price vs 50-day avg",
        "ma_200": "Price vs 200-day avg",
        "volatility_20": "20-day volatility",
        "volatility_60": "60-day volatility",
        "volume_ratio": "Volume vs average",
        "dollar_volume_turnover": "Dollar-volume turnover",
        "rsi": "RSI (momentum)",
        "high_52w_ratio": "Proximity to 52-week high",
    ]

    private init() {
        guard let url = Bundle.main.url(forResource: "mobile_model_meta", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            features = []
            baselines = [:]
            horizons = [:]
            return
        }

        features = (root["features"] as? [String]) ?? []

        if let raw = root["baselines"] as? [String: Any] {
            var b: [String: Float] = [:]
            for (k, v) in raw {
                if let n = (v as? NSNumber)?.floatValue { b[k] = n }
            }
            baselines = b
        } else {
            baselines = [:]
        }

        if let raw = root["horizons"] as? [String: Any] {
            var h: [String: HorizonMeta] = [:]
            for (key, value) in raw {
                guard let dict = value as? [String: Any],
                      let acc = (dict["backtest_accuracy"] as? NSNumber)?.doubleValue,
                      let cal = dict["calibration"] as? [String: Any],
                      let w = (cal["w"] as? NSNumber)?.doubleValue,
                      let b = (cal["b"] as? NSNumber)?.doubleValue else { continue }
                h[key] = HorizonMeta(
                    backtestAccuracy: acc,
                    calibration: Calibration(w: w, b: b)
                )
            }
            horizons = h
        } else {
            horizons = [:]
        }
    }

    // MARK: - Horizon key

    /// Maps a UI/engine horizon string to the metadata key. Mirrors the engine's
    /// model selection: 1d -> "1d", 1m/3m -> "1m", everything else -> "1w".
    private func metaKey(for horizon: String) -> String {
        let h = horizon.lowercased()
        if h.hasPrefix("1d") { return "1d" }
        if h.hasPrefix("1m") || h.hasPrefix("3m") { return "1m" }
        return "1w"
    }

    // MARK: - Public API

    /// Out-of-sample directional accuracy for the horizon. 0 if meta missing.
    func accuracy(horizon: String) -> Double {
        horizons[metaKey(for: horizon)]?.backtestAccuracy ?? 0
    }

    /// Maps a raw model probability to an honest, calibrated probability.
    /// Identity (returns the input) if meta is missing for the horizon.
    func calibrate(rawProbUp: Double, horizon: String) -> Double {
        guard let cal = horizons[metaKey(for: horizon)]?.calibration else {
            return rawProbUp
        }
        let z = cal.w * rawProbUp + cal.b
        return 1.0 / (1.0 + exp(-z))
    }

    /// Neutral reference value for a feature (0 if unknown).
    func baseline(for feature: String) -> Float {
        baselines[feature] ?? 0
    }

    /// Human label for a feature name, falling back to the raw name.
    func label(for feature: String) -> String {
        Self.labels[feature] ?? feature
    }

    /// Whether usable metadata was loaded.
    var isLoaded: Bool { !features.isEmpty && !horizons.isEmpty }
}
