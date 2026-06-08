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
