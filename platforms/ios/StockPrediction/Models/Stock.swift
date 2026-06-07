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
