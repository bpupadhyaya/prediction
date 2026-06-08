package com.prediction.stockmarket.data.sync

import com.prediction.stockmarket.data.database.*
import com.prediction.stockmarket.prediction.PredictionEngine
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SyncManager @Inject constructor(
    private val stockDao: StockDao,
    private val priceDao: PriceDao,
    private val predictionDao: PredictionDao,
    private val yahooFetcher: YahooFinanceFetcher,
    private val stooqFetcher: StooqFetcher,
    private val sourceManager: MarketDataSourceManager,
    private val predictionEngine: PredictionEngine
) {
    sealed class SyncResult {
        data class Success(val tagName: String) : SyncResult()
        data class Error(val message: String) : SyncResult()
    }

    private val hotTickers = listOf(
        "NVDA", "AAPL", "MSFT", "META", "GOOGL", "AMZN", "TSLA", "AMD", "NFLX",
        "HOOD", "PLTR", "ARM", "SMCI", "COIN", "MSTR", "UBER", "LYFT", "SOFI",
        "RBLX", "SNAP", "RIVN", "SOUN", "AI", "IONQ", "QUBT", "RDDT", "ACHR", "JOBY"
    )

    private val sp500Top50 = listOf(
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "JPM", "LLY",
        "V", "XOM", "UNH", "MA", "JNJ", "HD", "PG", "COST", "MRK", "ABBV",
        "BAC", "WMT", "CVX", "NFLX", "KO", "AMD", "PEP", "TMO", "ORCL", "CSCO",
        "CRM", "ABT", "ACN", "MCD", "ADBE", "TXN", "PM", "DHR", "VZ", "CAT",
        "WFC", "INTU", "SPGI", "NOW", "NEE", "AXP", "UPS", "MS", "DE", "GE"
    )

    suspend fun sync(
        onProgress: (done: Int, total: Int, currentTicker: String) -> Unit = { _, _, _ -> }
    ): SyncResult = withContext(Dispatchers.IO) {
        try {
            val tickers = (hotTickers + sp500Top50).distinct()
            val total = tickers.size
            val source = sourceManager.activeSource
            var successCount = 0

            tickers.forEachIndexed { index, ticker ->
                onProgress(index, total, ticker)
                try {
                    // Fetch price bars from the active source
                    val priceBars = when (source) {
                        MarketDataSourceType.STOOQ -> stooqFetcher.fetchPriceBars(ticker)
                        else -> yahooFetcher.fetchPriceBars(ticker)
                    }

                    if (priceBars.isNotEmpty()) {
                        // Fetch and upsert stock metadata
                        val stockEntity = yahooFetcher.fetchQuote(ticker)
                            ?: com.prediction.stockmarket.data.database.StockEntity(
                                ticker = ticker,
                                name = ticker
                            )
                        stockDao.upsertAll(listOf(stockEntity))

                        // Upsert price bars
                        priceDao.upsertAll(priceBars)

                        // Run prediction engine for each horizon
                        val sortedBars = priceBars.sortedByDescending { it.date }
                        listOf("1W", "1M", "3M").forEach { horizon ->
                            val prediction = predictionEngine.predict(ticker, horizon, sortedBars)
                            if (prediction != null) {
                                predictionDao.upsertAll(listOf(prediction))
                            }
                        }

                        successCount++
                    }
                } catch (_: Exception) {
                    // Skip failed tickers and continue
                }

                // Rate limit: 300ms between calls
                delay(300L)
            }

            onProgress(total, total, "")
            SyncResult.Success("Synced $successCount tickers from ${source.displayName}")
        } catch (e: Exception) {
            SyncResult.Error(e.message ?: "Unknown error")
        }
    }
}
