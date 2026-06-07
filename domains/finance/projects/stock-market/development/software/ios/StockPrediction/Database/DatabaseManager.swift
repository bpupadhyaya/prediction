import Foundation
import GRDB

final class DatabaseManager {
    static let shared = DatabaseManager()

    private let dbQueue: DatabaseQueue

    private init() {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        let dbURL = docs.appendingPathComponent("stock_prediction.sqlite")
        dbQueue = try! DatabaseQueue(path: dbURL.path)
        try! migrate()
    }

    private func migrate() throws {
        var migrator = DatabaseMigrator()
        migrator.eraseDatabaseOnSchemaChange = false

        migrator.registerMigration("v1") { db in
            try db.create(table: "stocks", ifNotExists: true) { t in
                t.column("ticker", .text).primaryKey()
                t.column("name", .text).notNull()
                t.column("sector", .text)
                t.column("industry", .text)
                t.column("marketCap", .double)
                t.column("updatedAt", .datetime)
            }

            try db.create(table: "prices", ifNotExists: true) { t in
                t.column("ticker", .text).notNull()
                t.column("date", .date).notNull()
                t.column("open", .double).notNull()
                t.column("high", .double).notNull()
                t.column("low", .double).notNull()
                t.column("close", .double).notNull()
                t.column("adjClose", .double).notNull()
                t.column("volume", .integer).notNull()
                t.primaryKey(["ticker", "date"])
            }

            try db.create(table: "predictions", ifNotExists: true) { t in
                t.column("ticker", .text).notNull()
                t.column("horizon", .text).notNull()
                t.column("direction", .text).notNull()
                t.column("probability", .double).notNull()
                t.column("expectedReturnLow", .double).notNull()
                t.column("expectedReturnHigh", .double).notNull()
                t.column("volatility", .double).notNull()
                t.column("modelAccuracy", .double).notNull()
                t.column("generatedAt", .datetime).notNull()
                t.primaryKey(["ticker", "horizon"])
            }

            try db.create(table: "watchlist", ifNotExists: true) { t in
                t.column("ticker", .text).primaryKey()
                t.column("addedAt", .datetime).notNull()
            }

            try db.create(table: "portfolio", ifNotExists: true) { t in
                t.column("ticker", .text).primaryKey()
                t.column("shares", .double).notNull()
                t.column("costBasis", .double).notNull()
                t.column("addedAt", .datetime).notNull()
            }
        }

        try migrator.migrate(dbQueue)
    }

    // MARK: - Stocks

    func upsertStocks(_ stocks: [Stock]) throws {
        try dbQueue.write { db in
            for s in stocks { try s.save(db) }
        }
    }

    func searchStocks(query: String) throws -> [Stock] {
        try dbQueue.read { db in
            try Stock.filter(
                Column("ticker").like("%\(query.uppercased())%") ||
                Column("name").like("%\(query)%")
            ).order(Column("marketCap").desc).limit(20).fetchAll(db)
        }
    }

    func stock(ticker: String) throws -> Stock? {
        try dbQueue.read { db in
            try Stock.filter(Column("ticker") == ticker.uppercased()).fetchOne(db)
        }
    }

    // MARK: - Prices

    func upsertPrices(_ bars: [PriceBar]) throws {
        try dbQueue.write { db in
            for b in bars { try b.save(db) }
        }
    }

    func prices(ticker: String, days: Int = 365) throws -> [PriceBar] {
        try dbQueue.read { db in
            try PriceBar.filter(Column("ticker") == ticker.uppercased())
                .order(Column("date").desc)
                .limit(days)
                .fetchAll(db)
        }
    }

    func latestPrice(ticker: String) throws -> PriceBar? {
        try dbQueue.read { db in
            try PriceBar.filter(Column("ticker") == ticker.uppercased())
                .order(Column("date").desc)
                .fetchOne(db)
        }
    }

    // MARK: - Predictions

    func upsertPrediction(_ pred: Prediction) throws {
        try dbQueue.write { db in try pred.save(db) }
    }

    func prediction(ticker: String, horizon: String = "1w") throws -> Prediction? {
        try dbQueue.read { db in
            try Prediction.filter(
                Column("ticker") == ticker.uppercased() &&
                Column("horizon") == horizon
            ).fetchOne(db)
        }
    }

    func allPredictions(horizon: String = "1w") throws -> [Prediction] {
        try dbQueue.read { db in
            try Prediction.filter(Column("horizon") == horizon)
                .order(sql: "ABS(probability - 0.5) DESC")
                .fetchAll(db)
        }
    }

    // MARK: - Watchlist

    func watchlist() throws -> [WatchlistEntry] {
        try dbQueue.read { db in
            try WatchlistEntry.order(Column("addedAt").desc).fetchAll(db)
        }
    }

    func addToWatchlist(ticker: String) throws {
        try dbQueue.write { db in
            let entry = WatchlistEntry(ticker: ticker.uppercased(), addedAt: Date())
            try entry.save(db)
        }
    }

    func removeFromWatchlist(ticker: String) throws {
        try dbQueue.write { db in
            try WatchlistEntry.filter(Column("ticker") == ticker.uppercased()).deleteAll(db)
        }
    }

    func isWatchlisted(ticker: String) throws -> Bool {
        try dbQueue.read { db in
            try WatchlistEntry.filter(Column("ticker") == ticker.uppercased()).fetchCount(db) > 0
        }
    }

    // MARK: - Portfolio

    func portfolio() throws -> [PortfolioHolding] {
        try dbQueue.read { db in
            try PortfolioHolding.order(Column("addedAt").desc).fetchAll(db)
        }
    }

    func upsertHolding(_ holding: PortfolioHolding) throws {
        try dbQueue.write { db in try holding.save(db) }
    }

    func removeHolding(ticker: String) throws {
        try dbQueue.write { db in
            try PortfolioHolding.filter(Column("ticker") == ticker.uppercased()).deleteAll(db)
        }
    }
}
