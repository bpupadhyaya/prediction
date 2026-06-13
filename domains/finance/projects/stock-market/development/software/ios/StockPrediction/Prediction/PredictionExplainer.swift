import Foundation

/// One feature's marginal contribution to the calibrated up-probability,
/// measured by replacing that feature with its neutral training baseline.
struct FeatureContribution {
    let feature: String
    let label: String
    let value: Float
    /// score(features) - score(features with this feature set to baseline).
    /// Positive => this feature pushes the prediction UP relative to neutral.
    let delta: Double
    var pushesUp: Bool { delta >= 0 }
}

/// Perturbation-based "why this prediction" explainer.
///
/// For each of the 16 features it asks: how would the calibrated up-probability
/// change if this single feature were at its neutral baseline instead of its
/// actual value? The signed change is the feature's contribution. This is a
/// simple, model-agnostic local attribution that reuses the live ONNX session
/// through the supplied `score` closure (which must return a CALIBRATED probUp).
enum PredictionExplainer {

    /// Computes per-feature contributions, sorted by |delta| descending.
    /// - Parameters:
    ///   - features: the 16-feature vector (MOBILE_FEATURES order).
    ///   - horizon: unused for scoring here (the closure already bakes it in),
    ///     kept for call-site clarity and future use.
    ///   - score: closure returning the calibrated probUp for a feature vector.
    static func contributions(
        features: [Float],
        horizon: String,
        score: ([Float]) -> Double
    ) -> [FeatureContribution] {
        let names = ModelMeta.shared.features
        guard !names.isEmpty, features.count == names.count else { return [] }

        let base = score(features)
        var result: [FeatureContribution] = []
        result.reserveCapacity(names.count)

        for i in 0..<names.count {
            let name = names[i]
            var perturbed = features
            perturbed[i] = ModelMeta.shared.baseline(for: name)
            let neutral = score(perturbed)
            let delta = base - neutral
            result.append(
                FeatureContribution(
                    feature: name,
                    label: ModelMeta.shared.label(for: name),
                    value: features[i],
                    delta: delta
                )
            )
        }

        return result.sorted { abs($0.delta) > abs($1.delta) }
    }

    /// One plain-English sentence describing the top 2-3 drivers and whether
    /// each supports or opposes the predicted direction.
    static func rationale(direction: String, contributions: [FeatureContribution]) -> String {
        let up = direction.uppercased() == "UP"
        let leaning = up ? "Leaning UP" : "Leaning DOWN"

        let top = Array(contributions.prefix(3)).filter { abs($0.delta) > 1e-6 }
        guard !top.isEmpty else {
            return "\(leaning), with no single feature standing out."
        }

        // A feature "supports" the predicted direction when its push matches it.
        func supports(_ c: FeatureContribution) -> Bool { c.pushesUp == up }

        let supporting = top.filter(supports).map { $0.label.lowercasedFirst() }
        let opposing = top.filter { !supports($0) }.map { $0.label.lowercasedFirst() }

        var sentence = leaning
        if !supporting.isEmpty {
            sentence += " mainly because \(joinClause(supporting)) "
            sentence += supporting.count == 1 ? "is favorable" : "are favorable"
        } else {
            // All top drivers oppose the lean (e.g. a weak/forced call).
            sentence += " despite \(joinClause(opposing)) "
            sentence += opposing.count == 1 ? "pulling the other way" : "pulling the other way"
            return sentence + "."
        }

        if !opposing.isEmpty {
            sentence += ", partly offset by \(joinClause(opposing))"
        }
        return sentence + "."
    }

    /// "a", "a and b", or "a, b and c".
    private static func joinClause(_ items: [String]) -> String {
        switch items.count {
        case 0: return ""
        case 1: return items[0]
        case 2: return "\(items[0]) and \(items[1])"
        default:
            let head = items.dropLast().joined(separator: ", ")
            return "\(head) and \(items.last!)"
        }
    }
}

private extension String {
    /// Lowercases only the first character (keeps acronyms like "RSI" intact
    /// beyond the first letter), for mid-sentence use.
    func lowercasedFirst() -> String {
        guard let first = first else { return self }
        return first.lowercased() + dropFirst()
    }
}
