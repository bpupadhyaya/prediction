package com.prediction.stockmarket.data.repository

import com.prediction.stockmarket.data.database.*
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class StockRepository @Inject constructor(
    private val stockDao: StockDao,
    private val priceDao: PriceDao,
    private val predictionDao: PredictionDao,
    private val watchlistDao: WatchlistDao,
    private val portfolioDao: PortfolioDao
) {
    suspend fun search(query: String): List<StockEntity> =
        stockDao.search("%${query.uppercase()}%")

    suspend fun prices(ticker: String, days: Int = 90): List<PriceBarEntity> =
        priceDao.getPrices(ticker.uppercase(), days)

    suspend fun latestPrice(ticker: String): PriceBarEntity? =
        priceDao.getLatest(ticker.uppercase())

    suspend fun prediction(ticker: String, horizon: String = "1w"): PredictionEntity? =
        predictionDao.get(ticker.uppercase(), horizon)

    fun predictionsFlow(horizon: String = "1w"): Flow<List<PredictionEntity>> =
        predictionDao.getAllFlow(horizon)

    fun watchlistFlow(): Flow<List<WatchlistEntity>> = watchlistDao.getAllFlow()

    suspend fun isWatchlisted(ticker: String): Boolean =
        watchlistDao.isWatchlisted(ticker.uppercase()) > 0

    suspend fun addToWatchlist(ticker: String) =
        watchlistDao.add(WatchlistEntity(ticker.uppercase(), java.util.Date()))

    suspend fun removeFromWatchlist(ticker: String) =
        watchlistDao.remove(ticker.uppercase())

    fun portfolioFlow(): Flow<List<PortfolioEntity>> = portfolioDao.getAllFlow()

    suspend fun addHolding(ticker: String, shares: Double, costBasis: Double) =
        portfolioDao.upsert(PortfolioEntity(ticker.uppercase(), shares, costBasis, java.util.Date()))

    suspend fun removeHolding(ticker: String) =
        portfolioDao.remove(ticker.uppercase())
}
