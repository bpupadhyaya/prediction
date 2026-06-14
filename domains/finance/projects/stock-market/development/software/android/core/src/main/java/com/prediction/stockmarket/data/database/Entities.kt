package com.prediction.stockmarket.data.database

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.TypeConverter
import java.util.Date

// --- Type Converters ---

class Converters {
    @TypeConverter fun fromDate(d: Date?): Long? = d?.time
    @TypeConverter fun toDate(ms: Long?): Date? = ms?.let { Date(it) }
}

// --- Entities ---

@Entity(tableName = "stocks")
data class StockEntity(
    @PrimaryKey val ticker: String,
    val name: String,
    val sector: String? = null,
    val industry: String? = null,
    val marketCap: Double? = null,
    val updatedAt: Date? = null
)

@Entity(tableName = "prices", primaryKeys = ["ticker", "date"])
data class PriceBarEntity(
    val ticker: String,
    val date: Date,
    val open: Double,
    val high: Double,
    val low: Double,
    val close: Double,
    val adjClose: Double,
    val volume: Long
)

@Entity(tableName = "predictions", primaryKeys = ["ticker", "horizon"])
data class PredictionEntity(
    val ticker: String,
    val horizon: String,
    val direction: String,
    val probability: Double,
    val expectedReturnLow: Double,
    val expectedReturnHigh: Double,
    val volatility: Double,
    val modelAccuracy: Double,
    val generatedAt: Date
)

@Entity(tableName = "watchlist")
data class WatchlistEntity(
    @PrimaryKey val ticker: String,
    val addedAt: Date
)

@Entity(tableName = "portfolio")
data class PortfolioEntity(
    @PrimaryKey val ticker: String,
    val shares: Double,
    val costBasis: Double,
    val addedAt: Date
)

/**
 * One prediction the user viewed, logged on-device and scored against the real
 * outcome once its horizon elapses. Mirrors the web `TrackedPrediction`.
 * id = "ticker-horizon-yyyyMMdd" dedupes to one entry per calendar day.
 */
@Entity(tableName = "tracked_predictions")
data class TrackedPredictionEntity(
    @PrimaryKey val id: String,
    val ticker: String,
    val horizon: String,            // "1d" | "1w" | "1m"
    val direction: String,          // "UP" | "DOWN" | "NEUTRAL"
    val probability: Double,        // calibrated, 0.0–1.0
    val priceAtPrediction: Double,
    val predictedAt: Date,
    val maturesAt: Date,
    val resolved: Boolean,
    val actualPrice: Double?,
    val actualReturnPct: Double?,
    val correct: Boolean?,
    val resolvedAt: Date?
)

// ─── Video Intelligence Entities ─────────────────────────────────────────────

@Entity(tableName = "video_sources")
data class VideoSourceEntity(
    @PrimaryKey val id: String,
    val url: String,
    val videoId: String,
    val title: String,
    val channelName: String,
    val channelId: String,
    val speakerName: String,
    val publishedAt: String,
    val durationSec: Int,
    val viewCount: Long,
    /** pending | transcribing | extracting | done | error */
    val status: String,
    val errorMsg: String?,
    val transcriptModel: String?,
    val fullText: String?,
    val createdAt: Date
)

@Entity(tableName = "video_signals", primaryKeys = ["id"])
data class VideoSignalEntity(
    val id: String,
    val videoId: String,
    val ticker: String?,
    val parameterName: String,
    val domain: String,
    /** "up" or "down" */
    val direction: String,
    /** Signal strength 0–100 */
    val weight: Int,
    /** Speaker confidence 0.0–1.0 */
    val confidence: Double,
    val keyQuote: String,
    val extractedAt: Date
)

@Entity(tableName = "channel_tracks")
data class ChannelTrackEntity(
    @PrimaryKey val channelId: String,
    val channelName: String,
    val speakerName: String,
    val autoProcess: Boolean,
    /** How many years back to scan for videos */
    val timeRangeYears: Int,
    val createdAt: Date
)
