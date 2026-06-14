import Foundation
import GRDB

struct Stock: Codable, FetchableRecord, PersistableRecord {
    var ticker: String
    var name: String
    var sector: String?
    var industry: String?
    var marketCap: Double?
    var updatedAt: Date?

    static let databaseTableName = "stocks"
}

struct PriceBar: Codable, FetchableRecord, PersistableRecord {
    var ticker: String
    var date: Date
    var open: Double
    var high: Double
    var low: Double
    var close: Double
    var adjClose: Double
    var volume: Int64

    static let databaseTableName = "prices"
}

struct Prediction: Codable, FetchableRecord, PersistableRecord {
    var ticker: String
    var horizon: String
    var direction: String          // "UP" | "DOWN"
    var probability: Double
    var expectedReturnLow: Double
    var expectedReturnHigh: Double
    var volatility: Double
    var modelAccuracy: Double
    var generatedAt: Date

    static let databaseTableName = "predictions"

    var signalStrength: Double { abs(probability - 0.5) }
    var isBullish: Bool { direction == "UP" }
}

struct WatchlistEntry: Codable, FetchableRecord, PersistableRecord {
    var ticker: String
    var addedAt: Date

    static let databaseTableName = "watchlist"
}

struct PortfolioHolding: Codable, FetchableRecord, PersistableRecord {
    var ticker: String
    var shares: Double
    var costBasis: Double
    var addedAt: Date

    static let databaseTableName = "portfolio"
}

/// One prediction the user viewed, logged on-device and scored against the real
/// outcome once its horizon elapses. Mirrors the web `TrackedPrediction`.
struct TrackedPrediction: Codable, FetchableRecord, PersistableRecord {
    var id: String                 // "ticker-horizon-yyyyMMdd" (dedupes per calendar day)
    var ticker: String
    var horizon: String            // "1d" | "1w" | "1m"
    var direction: String          // "UP" | "DOWN" | "NEUTRAL"
    var probability: Double        // calibrated, 0–1 (app convention)
    var priceAtPrediction: Double
    var predictedAt: Date
    var maturesAt: Date
    var resolved: Bool
    var actualPrice: Double?
    var actualReturnPct: Double?
    var correct: Bool?
    var resolvedAt: Date?

    static let databaseTableName = "tracked_predictions"

    var isBullish: Bool { direction == "UP" }

    /// Calendar maturity: 1d→+1 day, 1w→+7 days, 1m→+30 days.
    static func maturity(for horizon: String, from start: Date) -> Date {
        let days: Int
        switch horizon {
        case "1d": days = 1
        case "1w": days = 7
        case "1m": days = 30
        default:   days = 7
        }
        return Calendar.current.date(byAdding: .day, value: days, to: start) ?? start
    }
}
