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

        migrator.registerMigration("v2") { db in
            try db.create(table: "video_sources", ifNotExists: true) { t in
                t.column("id", .text).primaryKey()
                t.column("url", .text).notNull().unique()
                t.column("videoId", .text).notNull()
                t.column("title", .text).notNull()
                t.column("channelName", .text).notNull()
                t.column("channelId", .text)
                t.column("speakerName", .text)
                t.column("publishedAt", .text)
                t.column("durationSec", .integer)
                t.column("viewCount", .integer)
                t.column("status", .text).notNull().defaults(to: "pending")
                t.column("errorMsg", .text)
                t.column("transcriptModel", .text)
                t.column("fullText", .text)
                t.column("createdAt", .datetime).notNull()
            }
            try db.create(table: "video_signals", ifNotExists: true) { t in
                t.column("id", .text).primaryKey()
                t.column("videoId", .text).notNull()
                t.column("ticker", .text)
                t.column("parameterName", .text).notNull()
                t.column("domain", .text).notNull()
                t.column("direction", .text).notNull()
                t.column("weight", .integer).notNull()
                t.column("confidence", .double).notNull()
                t.column("keyQuote", .text)
                t.column("extractedAt", .datetime).notNull()
            }
            try db.create(table: "channel_tracks", ifNotExists: true) { t in
                t.column("channelId", .text).primaryKey()
                t.column("channelName", .text).notNull()
                t.column("speakerName", .text)
                t.column("autoProcess", .boolean).notNull().defaults(to: true)
                t.column("timeRangeYears", .integer).notNull().defaults(to: 5)
                t.column("createdAt", .datetime).notNull()
            }
            try db.create(index: "video_signals_videoId", on: "video_signals", columns: ["videoId"], ifNotExists: true)
            try db.create(index: "video_signals_ticker", on: "video_signals", columns: ["ticker"], ifNotExists: true)
        }

        migrator.registerMigration("v3") { db in
            try db.create(table: "tracked_predictions", ifNotExists: true) { t in
                t.column("id", .text).primaryKey()
                t.column("ticker", .text).notNull()
                t.column("horizon", .text).notNull()
                t.column("direction", .text).notNull()
                t.column("probability", .double).notNull()
                t.column("priceAtPrediction", .double).notNull()
                t.column("predictedAt", .datetime).notNull()
                t.column("maturesAt", .datetime).notNull()
                t.column("resolved", .boolean).notNull().defaults(to: false)
                t.column("actualPrice", .double)
                t.column("actualReturnPct", .double)
                t.column("correct", .boolean)
                t.column("resolvedAt", .datetime)
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

    // MARK: - Video Sources

    func saveVideoSource(_ v: VideoSourceRecord) throws {
        try dbQueue.write { db in
            var record = v
            try record.save(db)
        }
    }

    func updateVideoSourceStatus(id: String, status: String, errorMsg: String?, fullText: String?) throws {
        try dbQueue.write { db in
            try db.execute(
                sql: """
                     UPDATE video_sources
                     SET status = :status, errorMsg = :errorMsg, fullText = :fullText
                     WHERE id = :id
                     """,
                arguments: ["status": status, "errorMsg": errorMsg, "fullText": fullText, "id": id]
            )
        }
    }

    func getVideoSources(limit: Int = 20) throws -> [VideoSourceRecord] {
        try dbQueue.read { db in
            try VideoSourceRecord
                .order(Column("createdAt").desc)
                .limit(limit)
                .fetchAll(db)
        }
    }

    // MARK: - Video Signals

    func saveVideoSignals(_ signals: [VideoSignalRecord]) throws {
        try dbQueue.write { db in
            // PersistableRecord.encode(to:) excludes join helpers automatically
            for var s in signals { try s.save(db) }
        }
    }

    func getVideoSignals(ticker: String?, days: Int?) throws -> [VideoSignalRecord] {
        try dbQueue.read { db in
            var request = VideoSignalRecord
                .order(Column("extractedAt").desc)

            if let ticker = ticker, !ticker.isEmpty {
                request = request.filter(Column("ticker") == ticker.uppercased())
            }
            if let days = days, days > 0 {
                let cutoff = Date().addingTimeInterval(-Double(days) * 86_400)
                request = request.filter(Column("extractedAt") >= cutoff)
            }

            var records = try request.limit(100).fetchAll(db)

            // Enrich with video metadata via a secondary lookup
            let videoIds = Array(Set(records.map(\.videoId)))
            if !videoIds.isEmpty {
                let sources = try VideoSourceRecord
                    .filter(videoIds.contains(Column("id")))
                    .fetchAll(db)
                let sourceMap = Dictionary(uniqueKeysWithValues: sources.map { ($0.id, $0) })
                records = records.map { r in
                    var enriched = r
                    if let src = sourceMap[r.videoId] {
                        enriched.videoTitle = src.title
                        enriched.channelName = src.channelName
                        enriched.publishedAt = src.publishedAt
                    }
                    return enriched
                }
            }

            return records
        }
    }

    // MARK: - Track Record

    /// Insert-or-ignore: at most one entry per (ticker, horizon, calendar-day) via the
    /// composite id. Never overwrites a possibly-resolved row for the same day.
    func logTrackedPrediction(_ p: TrackedPrediction) throws {
        try dbQueue.write { db in
            try p.insert(db, onConflict: .ignore)
        }
    }

    /// Upsert used when scoring a matured prediction (replaces the existing row).
    func saveTrackedPrediction(_ p: TrackedPrediction) throws {
        try dbQueue.write { db in try p.save(db) }
    }

    func trackedPredictions() throws -> [TrackedPrediction] {
        try dbQueue.read { db in
            try TrackedPrediction.order(Column("predictedAt").desc).fetchAll(db)
        }
    }

    func clearTrackedPredictions() throws {
        try dbQueue.write { db in
            _ = try TrackedPrediction.deleteAll(db)
        }
    }

    // MARK: - Channel Tracks

    func saveChannelTrack(_ ct: ChannelTrackRecord) throws {
        try dbQueue.write { db in
            var record = ct
            try record.save(db)
        }
    }

    func getChannelTracks() throws -> [ChannelTrackRecord] {
        try dbQueue.read { db in
            try ChannelTrackRecord.order(Column("createdAt").desc).fetchAll(db)
        }
    }

    func removeChannelTrack(channelId: String) throws {
        try dbQueue.write { db in
            try ChannelTrackRecord.filter(Column("channelId") == channelId).deleteAll(db)
        }
    }
}
