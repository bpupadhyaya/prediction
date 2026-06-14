package com.prediction.stockmarket.data.database

import androidx.room.*
import kotlinx.coroutines.flow.Flow
import java.util.Date

@Dao
interface StockDao {
    @Query("SELECT * FROM stocks WHERE ticker LIKE :q OR name LIKE :q ORDER BY CASE WHEN marketCap IS NULL THEN 1 ELSE 0 END, marketCap DESC LIMIT 20")
    suspend fun search(q: String): List<StockEntity>

    @Query("SELECT * FROM stocks WHERE ticker = :ticker LIMIT 1")
    suspend fun findByTicker(ticker: String): StockEntity?

    @Upsert
    suspend fun upsertAll(stocks: List<StockEntity>)
}

@Dao
interface PriceDao {
    @Query("SELECT * FROM prices WHERE ticker = :ticker ORDER BY date DESC LIMIT :days")
    suspend fun getPrices(ticker: String, days: Int): List<PriceBarEntity>

    @Query("SELECT * FROM prices WHERE ticker = :ticker ORDER BY date DESC LIMIT 1")
    suspend fun getLatest(ticker: String): PriceBarEntity?

    @Upsert
    suspend fun upsertAll(bars: List<PriceBarEntity>)
}

@Dao
interface PredictionDao {
    @Query("SELECT * FROM predictions WHERE horizon = :horizon ORDER BY ABS(probability - 0.5) DESC")
    suspend fun getAll(horizon: String): List<PredictionEntity>

    @Query("SELECT * FROM predictions WHERE ticker = :ticker AND horizon = :horizon LIMIT 1")
    suspend fun get(ticker: String, horizon: String): PredictionEntity?

    @Query("SELECT * FROM predictions WHERE horizon = :horizon ORDER BY ABS(probability - 0.5) DESC")
    fun getAllFlow(horizon: String): Flow<List<PredictionEntity>>

    @Upsert
    suspend fun upsert(pred: PredictionEntity)

    @Upsert
    suspend fun upsertAll(preds: List<PredictionEntity>)
}

@Dao
interface WatchlistDao {
    @Query("SELECT * FROM watchlist ORDER BY addedAt DESC")
    fun getAllFlow(): Flow<List<WatchlistEntity>>

    @Query("SELECT * FROM watchlist ORDER BY addedAt DESC")
    suspend fun getAll(): List<WatchlistEntity>

    @Query("SELECT COUNT(*) FROM watchlist WHERE ticker = :ticker")
    suspend fun isWatchlisted(ticker: String): Int

    @Upsert
    suspend fun add(entry: WatchlistEntity)

    @Query("DELETE FROM watchlist WHERE ticker = :ticker")
    suspend fun remove(ticker: String)
}

@Dao
interface PortfolioDao {
    @Query("SELECT * FROM portfolio ORDER BY addedAt DESC")
    fun getAllFlow(): Flow<List<PortfolioEntity>>

    @Query("SELECT * FROM portfolio ORDER BY addedAt DESC")
    suspend fun getAll(): List<PortfolioEntity>

    @Upsert
    suspend fun upsert(holding: PortfolioEntity)

    @Query("DELETE FROM portfolio WHERE ticker = :ticker")
    suspend fun remove(ticker: String)
}

@Dao
interface TrackedPredictionDao {
    @Query("SELECT * FROM tracked_predictions ORDER BY predictedAt DESC")
    suspend fun getAll(): List<TrackedPredictionEntity>

    /** Insert-or-ignore: at most one entry per (ticker, horizon, calendar-day) via id. */
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun log(entry: TrackedPredictionEntity)

    /** Upsert used when scoring a matured prediction (replaces the existing row). */
    @Upsert
    suspend fun save(entry: TrackedPredictionEntity)

    @Query("DELETE FROM tracked_predictions")
    suspend fun clear()
}

// ─── Video Intelligence DAOs ──────────────────────────────────────────────────

@Dao
interface VideoSourceDao {
    @Query("SELECT * FROM video_sources ORDER BY createdAt DESC LIMIT :limit")
    suspend fun getRecent(limit: Int = 20): List<VideoSourceEntity>

    @Query("SELECT * FROM video_sources WHERE id = :id LIMIT 1")
    suspend fun getById(id: String): VideoSourceEntity?

    @Upsert
    suspend fun upsert(v: VideoSourceEntity)

    @Query("UPDATE video_sources SET status = :status, errorMsg = :errorMsg, fullText = :fullText WHERE id = :id")
    suspend fun updateStatus(id: String, status: String, errorMsg: String?, fullText: String?)
}

@Dao
interface VideoSignalDao {
    @Query("SELECT * FROM video_signals WHERE videoId = :videoId")
    suspend fun getByVideo(videoId: String): List<VideoSignalEntity>

    @Query("""
        SELECT vs.* FROM video_signals vs
        JOIN video_sources src ON vs.videoId = src.id
        WHERE (:ticker IS NULL OR vs.ticker = :ticker)
          AND src.createdAt >= :cutoff
        ORDER BY src.createdAt DESC
    """)
    suspend fun querySignals(ticker: String?, cutoff: Date): List<VideoSignalEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(signals: List<VideoSignalEntity>)
}

@Dao
interface ChannelTrackDao {
    @Query("SELECT * FROM channel_tracks ORDER BY createdAt DESC")
    suspend fun getAll(): List<ChannelTrackEntity>

    @Upsert
    suspend fun upsert(ct: ChannelTrackEntity)

    @Query("DELETE FROM channel_tracks WHERE channelId = :channelId")
    suspend fun remove(channelId: String)
}
