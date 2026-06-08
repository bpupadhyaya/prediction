package com.prediction.stockmarket.data.database

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters

@Database(
    entities = [StockEntity::class, PriceBarEntity::class, PredictionEntity::class,
                WatchlistEntity::class, PortfolioEntity::class],
    version = 1,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun stockDao(): StockDao
    abstract fun priceDao(): PriceDao
    abstract fun predictionDao(): PredictionDao
    abstract fun watchlistDao(): WatchlistDao
    abstract fun portfolioDao(): PortfolioDao
}
