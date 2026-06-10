import Foundation
import Combine

// MARK: - Data Models

struct StockParameter: Codable, Identifiable {
    var id: String { name }
    let name: String
    let domain: String
    let domainLabel: String
    let label: String
    let unit: String
    let defaultValue: Double
    let layman: String
    let technical: String
}

struct ParamState {
    var weight: Int = 0               // 0–100
    var direction: String = "neutral" // "up", "down", "neutral"
    var value: Double?
}

// MARK: - Codable helpers for UserDefaults persistence

private struct ParamStateCodable: Codable {
    var weight: Int
    var direction: String
    var value: Double?
}

// MARK: - Domain Order

private let DOMAIN_ORDER: [String] = [
    "macro",
    "fundamental",
    "cross_asset",
    "technical",
    "sentiment",
    "geopolitical"
]

// MARK: - Parameter Store

final class ParameterStore: ObservableObject {

    @Published var parameters: [StockParameter] = []
    @Published var states: [String: ParamState] = [:]

    init() {
        loadParameters()
        initStates()
    }

    // MARK: - JSON Loading

    private func loadParameters() {
        guard let url = Bundle.main.url(forResource: "parameters", withExtension: "json") else {
            return
        }
        do {
            let data = try Data(contentsOf: url)
            let decoded = try JSONDecoder().decode([StockParameter].self, from: data)
            parameters = decoded
        } catch {
            // Parameters could not be decoded; app continues with empty list.
        }
    }

    // MARK: - State Management

    func initStates() {
        var fresh: [String: ParamState] = [:]
        for p in parameters {
            fresh[p.name] = ParamState(weight: 0, direction: "neutral", value: nil)
        }
        states = fresh
    }

    func setDirection(_ name: String, _ dir: String) {
        states[name, default: ParamState()].direction = dir
    }

    func setWeight(_ name: String, _ weight: Int) {
        states[name, default: ParamState()].weight = weight
    }

    // MARK: - UserDefaults Persistence

    func saveForTicker(_ ticker: String) {
        let key = "ip-\(ticker)"
        var dict: [String: [String: Any]] = [:]
        for (name, state) in states {
            var entry: [String: Any] = [
                "weight": state.weight,
                "direction": state.direction
            ]
            if let v = state.value { entry["value"] = v }
            dict[name] = entry
        }
        UserDefaults.standard.set(dict, forKey: key)
    }

    func loadForTicker(_ ticker: String) {
        let key = "ip-\(ticker)"
        guard let dict = UserDefaults.standard.dictionary(forKey: key) as? [String: [String: Any]] else {
            // No saved data — keep fresh init states
            return
        }
        for (name, entry) in dict {
            let weight = entry["weight"] as? Int ?? 0
            let direction = entry["direction"] as? String ?? "neutral"
            let value = entry["value"] as? Double
            states[name] = ParamState(weight: weight, direction: direction, value: value)
        }
    }

    // MARK: - Prediction Formula
    // Matches the web app:
    //   dirValue: up → +1, down → −1, neutral → 0
    //   normalizedScore = Σ(weight × dirValue) / Σ(weight)  [range −1..+1]
    //   probUp = (normalizedScore + 1) / 2                   [range 0..1]
    //   confidence = |normalizedScore|                        [range 0..1]
    //   direction: > +0.52 → "up", < −0.48 → "down", else "neutral"

    func computePrediction() -> (probUp: Double, confidence: Double, direction: String, paramsSet: Int) {
        let active = states.filter { $0.value.weight > 0 }
        let paramsSet = active.count

        let totalWeight = active.values.reduce(0) { $0 + $1.weight }
        guard totalWeight > 0 else {
            return (probUp: 0.5, confidence: 0.0, direction: "neutral", paramsSet: paramsSet)
        }

        let weightedSum = active.reduce(0.0) { acc, pair in
            let dirValue: Double = pair.value.direction == "up" ? 1
                                 : pair.value.direction == "down" ? -1
                                 : 0
            return acc + Double(pair.value.weight) * dirValue
        }

        let normalized = weightedSum / Double(totalWeight)  // −1..+1
        let probUp = (normalized + 1.0) / 2.0
        let confidence = abs(normalized)
        let direction: String
        if normalized > 0.52 {
            direction = "up"
        } else if normalized < -0.48 {
            direction = "down"
        } else {
            direction = "neutral"
        }

        return (probUp: probUp, confidence: confidence, direction: direction, paramsSet: paramsSet)
    }

    // MARK: - Grouped by Domain

    func groupedByDomain() -> [(domain: String, label: String, params: [StockParameter])] {
        let byDomain = Dictionary(grouping: parameters, by: { $0.domain })
        var result: [(domain: String, label: String, params: [StockParameter])] = []
        for domainKey in DOMAIN_ORDER {
            guard let params = byDomain[domainKey], !params.isEmpty else { continue }
            let label = params.first?.domainLabel ?? domainKey
            result.append((domain: domainKey, label: label, params: params))
        }
        // Append any domains not in the canonical order
        let covered = Set(DOMAIN_ORDER)
        for (key, params) in byDomain where !covered.contains(key) {
            let label = params.first?.domainLabel ?? key
            result.append((domain: key, label: label, params: params))
        }
        return result
    }
}
