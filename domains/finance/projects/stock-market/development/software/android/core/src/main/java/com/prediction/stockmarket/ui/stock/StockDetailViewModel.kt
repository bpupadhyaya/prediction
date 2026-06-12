package com.prediction.stockmarket.ui.stock

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.prediction.stockmarket.data.database.PredictionEntity
import com.prediction.stockmarket.data.repository.StockRepository
import com.prediction.stockmarket.prediction.PredictionEngine
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class StockDetailUiState(
    val ticker: String = "",
    val latestPrice: Double? = null,
    val prediction: PredictionEntity? = null,
    val isWatchlisted: Boolean = false,
    val horizon: String = "1w",
    val isLoading: Boolean = false,
    val errorMessage: String? = null
)

@HiltViewModel
class StockDetailViewModel @Inject constructor(
    private val repo: StockRepository,
    private val engine: PredictionEngine,
    private val yahooFetcher: com.prediction.stockmarket.data.sync.YahooFinanceFetcher,
) : ViewModel() {

    private val _uiState = MutableStateFlow(StockDetailUiState())
    val uiState: StateFlow<StockDetailUiState> = _uiState

    /**
     * Any-symbol support: searched global symbols (7203.T, BTC-USD, SAP.DE...) are
     * not in the synced universe, so the local DB has no bars for them. Fetch ~5y
     * from Yahoo on demand and persist, so the chart, prediction, and watchlist
     * all work for any instrument — local or global.
     */
    private suspend fun ensureTickerData(ticker: String) {
        if (repo.prices(ticker, 600).size >= 253) return
        kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
            val bars = try { yahooFetcher.fetchPriceBars(ticker, range = "5y") } catch (_: Exception) { emptyList() }
            if (bars.isNotEmpty()) {
                repo.upsertPrices(bars)
                yahooFetcher.fetchQuote(ticker)?.let { repo.upsertStock(it) }
            }
        }
    }

    fun load(ticker: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, errorMessage = null)
            try {
                ensureTickerData(ticker)
                val price = repo.latestPrice(ticker)?.adjClose
                val pred = loadOrComputePrediction(ticker, _uiState.value.horizon)
                val watchlisted = repo.isWatchlisted(ticker)
                _uiState.value = StockDetailUiState(
                    ticker = ticker,
                    latestPrice = price,
                    prediction = pred,
                    isWatchlisted = watchlisted,
                    isLoading = false
                )
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    errorMessage = "Failed to load data: ${e.message}"
                )
            }
        }
    }

    fun onHorizonChange(horizon: String) {
        val ticker = _uiState.value.ticker
        if (ticker.isBlank()) return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            try {
                val pred = loadOrComputePrediction(ticker, horizon)
                _uiState.value = _uiState.value.copy(
                    horizon = horizon,
                    prediction = pred,
                    isLoading = false
                )
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    errorMessage = "Failed to load prediction: ${e.message}"
                )
            }
        }
    }

    fun toggleWatchlist() {
        val ticker = _uiState.value.ticker
        if (ticker.isBlank()) return
        viewModelScope.launch {
            try {
                if (_uiState.value.isWatchlisted) {
                    repo.removeFromWatchlist(ticker)
                } else {
                    repo.addToWatchlist(ticker)
                }
                _uiState.value = _uiState.value.copy(isWatchlisted = !_uiState.value.isWatchlisted)
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    errorMessage = "Failed to update watchlist: ${e.message}"
                )
            }
        }
    }

    private suspend fun loadOrComputePrediction(ticker: String, horizon: String): PredictionEntity? {
        val cached = repo.prediction(ticker, horizon)
        if (cached != null) return cached
        val prices = repo.prices(ticker, 600)
        return engine.predict(ticker, horizon, prices)
    }
}
