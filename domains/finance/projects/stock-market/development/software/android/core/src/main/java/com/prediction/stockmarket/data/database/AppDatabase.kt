package com.prediction.stockmarket.data.database

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

@Database(
    entities = [
        StockEntity::class,
        PriceBarEntity::class,
        PredictionEntity::class,
        WatchlistEntity::class,
        PortfolioEntity::class,
        // Video Intelligence entities (added in version 2)
        VideoSourceEntity::class,
        VideoSignalEntity::class,
        ChannelTrackEntity::class,
        // Track Record (added in version 3)
        TrackedPredictionEntity::class,
    ],
    version = 3,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun stockDao(): StockDao
    abstract fun priceDao(): PriceDao
    abstract fun predictionDao(): PredictionDao
    abstract fun watchlistDao(): WatchlistDao
    abstract fun portfolioDao(): PortfolioDao

    // Video Intelligence DAOs
    abstract fun videoSourceDao(): VideoSourceDao
    abstract fun videoSignalDao(): VideoSignalDao
    abstract fun channelTrackDao(): ChannelTrackDao

    // Track Record DAO
    abstract fun trackedPredictionDao(): TrackedPredictionDao

    companion object {
        val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL(
                    """
                    CREATE TABLE IF NOT EXISTS video_sources (
                        id TEXT PRIMARY KEY NOT NULL,
                        url TEXT NOT NULL,
                        videoId TEXT NOT NULL,
                        title TEXT NOT NULL,
                        channelName TEXT NOT NULL,
                        channelId TEXT NOT NULL,
                        speakerName TEXT NOT NULL,
                        publishedAt TEXT NOT NULL,
                        durationSec INTEGER NOT NULL,
                        viewCount INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        errorMsg TEXT,
                        transcriptModel TEXT,
                        fullText TEXT,
                        createdAt INTEGER NOT NULL
                    )
                    """.trimIndent()
                )

                db.execSQL(
                    """
                    CREATE TABLE IF NOT EXISTS video_signals (
                        id TEXT NOT NULL,
                        videoId TEXT NOT NULL,
                        ticker TEXT,
                        parameterName TEXT NOT NULL,
                        domain TEXT NOT NULL,
                        direction TEXT NOT NULL,
                        weight INTEGER NOT NULL,
                        confidence REAL NOT NULL,
                        keyQuote TEXT NOT NULL,
                        extractedAt INTEGER NOT NULL,
                        PRIMARY KEY(id)
                    )
                    """.trimIndent()
                )

                db.execSQL(
                    """
                    CREATE TABLE IF NOT EXISTS channel_tracks (
                        channelId TEXT PRIMARY KEY NOT NULL,
                        channelName TEXT NOT NULL,
                        speakerName TEXT NOT NULL,
                        autoProcess INTEGER NOT NULL,
                        timeRangeYears INTEGER NOT NULL,
                        createdAt INTEGER NOT NULL
                    )
                    """.trimIndent()
                )

                db.execSQL("CREATE INDEX IF NOT EXISTS idx_vs_ticker ON video_signals(ticker)")
                db.execSQL("CREATE INDEX IF NOT EXISTS idx_vs_video ON video_signals(videoId)")
            }
        }

        val MIGRATION_2_3 = object : Migration(2, 3) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL(
                    """
                    CREATE TABLE IF NOT EXISTS tracked_predictions (
                        id TEXT PRIMARY KEY NOT NULL,
                        ticker TEXT NOT NULL,
                        horizon TEXT NOT NULL,
                        direction TEXT NOT NULL,
                        probability REAL NOT NULL,
                        priceAtPrediction REAL NOT NULL,
                        predictedAt INTEGER NOT NULL,
                        maturesAt INTEGER NOT NULL,
                        resolved INTEGER NOT NULL,
                        actualPrice REAL,
                        actualReturnPct REAL,
                        correct INTEGER,
                        resolvedAt INTEGER
                    )
                    """.trimIndent()
                )
            }
        }
    }
}
