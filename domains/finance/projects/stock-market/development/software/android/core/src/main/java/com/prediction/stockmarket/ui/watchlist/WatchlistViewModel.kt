package com.prediction.stockmarket.ui.watchlist

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.prediction.stockmarket.data.database.PredictionEntity
import com.prediction.stockmarket.data.database.WatchlistEntity
import com.prediction.stockmarket.data.repository.StockRepository
import com.prediction.stockmarket.data.sync.YahooFinanceFetcher
import com.prediction.stockmarket.prediction.PredictionEngine
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import javax.inject.Inject

@HiltViewModel
class WatchlistViewModel @Inject constructor(
    private val repo: StockRepository,
    private val fetcher: YahooFinanceFetcher,
    private val engine: PredictionEngine,
) : ViewModel() {

    val watchlist: StateFlow<List<WatchlistEntity>> =
        repo.watchlistFlow().stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    private val _prices = MutableStateFlow<Map<String, Double>>(emptyMap())
    val prices: StateFlow<Map<String, Double>> = _prices

    private val _predictions = MutableStateFlow<Map<String, PredictionEntity>>(emptyMap())
    val predictions: StateFlow<Map<String, PredictionEntity>> = _predictions

    private val _errorMessage = MutableStateFlow<String?>(null)
    val errorMessage: StateFlow<String?> = _errorMessage

    // ─── Rank by conviction ──────────────────────────────────────────────────
    // A ranked mode that scans every watchlist ticker, runs the on-device
    // 1-week model on freshly fetched bars, and orders by calibrated P(up)
    // descending — a personal opportunity radar over saved assets. Reuses
    // YahooFinanceFetcher + PredictionEngine; no engine/data-layer changes.

    private val _rankState = MutableStateFlow(RankState())
    val rankState: StateFlow<RankState> = _rankState

    fun toggleRanked() {
        if (_rankState.value.enabled) {
            _rankState.value = RankState()
        } else {
            rankByConviction()
        }
    }

    private fun rankByConviction() {
        val tickers = watchlist.value.map { it.ticker }
        if (tickers.isEmpty()) {
            _rankState.value = RankState(enabled = true, isScanning = false, scanned = 0, total = 0)
            return
        }
        _rankState.value = RankState(
            enabled = true, isScanning = true, scanned = 0, total = tickers.size, rows = emptyList(),
        )
        viewModelScope.launch {
            val collected = java.util.Collections.synchronizedList(mutableListOf<RankRow>())
            withContext(Dispatchers.IO) {
                tickers.map { ticker ->
                    async {
                        val row = try {
                            val bars = fetcher.fetchPriceBars(ticker, range = "2y")
                            if (bars.size < 253) null
                            else {
                                val pred = engine.predict(ticker, "1W", bars.sortedByDescending { it.date })
                                if (pred?.direction == null) null
                                else RankRow(ticker, pred.direction, pred.probability)
                            }
                        } catch (_: Exception) {
                            // Per-ticker failures are skipped so one bad symbol never stops the scan.
                            null
                        }
                        if (row != null) collected.add(row)
                        val ranked = synchronized(collected) { collected.sortedByDescending { it.probUp } }
                        val cur = _rankState.value
                        _rankState.value = cur.copy(scanned = cur.scanned + 1, rows = ranked)
                    }
                }.awaitAll()
            }
            _rankState.value = _rankState.value.copy(isScanning = false)
        }
    }

    init {
        viewModelScope.launch {
            watchlist.collectLatest { list ->
                try {
                    _prices.value = list.associate { entry ->
                        entry.ticker to (repo.latestPrice(entry.ticker)?.adjClose ?: 0.0)
                    }
                    _predictions.value = list.mapNotNull { entry ->
                        repo.prediction(entry.ticker, "1w")?.let { pred -> entry.ticker to pred }
                    }.toMap()
                } catch (e: Exception) {
                    _errorMessage.value = "Failed to load watchlist data: ${e.message}"
                }
            }
        }
    }
}

data class RankRow(
    val ticker: String,
    val direction: String,  // "UP" / "DOWN"
    val probUp: Double,      // calibrated P(up)
)

data class RankState(
    val enabled: Boolean = false,
    val isScanning: Boolean = false,
    val scanned: Int = 0,
    val total: Int = 0,
    val rows: List<RankRow> = emptyList(),
)
