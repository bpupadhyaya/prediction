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
    val horizon: String = "1w"
)

@HiltViewModel
class StockDetailViewModel @Inject constructor(
    private val repo: StockRepository,
    private val engine: PredictionEngine
) : ViewModel() {

    private val _uiState = MutableStateFlow(StockDetailUiState())
    val uiState: StateFlow<StockDetailUiState> = _uiState

    fun load(ticker: String) {
        viewModelScope.launch {
            val price = repo.latestPrice(ticker)?.adjClose
            val pred = loadOrComputePrediction(ticker, _uiState.value.horizon)
            val watchlisted = repo.isWatchlisted(ticker)
            _uiState.value = StockDetailUiState(ticker, price, pred, watchlisted)
        }
    }

    fun onHorizonChange(horizon: String) {
        val ticker = _uiState.value.ticker
        viewModelScope.launch {
            val pred = loadOrComputePrediction(ticker, horizon)
            _uiState.value = _uiState.value.copy(horizon = horizon, prediction = pred)
        }
    }

    fun toggleWatchlist() {
        val ticker = _uiState.value.ticker
        viewModelScope.launch {
            if (_uiState.value.isWatchlisted) {
                repo.removeFromWatchlist(ticker)
            } else {
                repo.addToWatchlist(ticker)
            }
            _uiState.value = _uiState.value.copy(isWatchlisted = !_uiState.value.isWatchlisted)
        }
    }

    private suspend fun loadOrComputePrediction(ticker: String, horizon: String): PredictionEntity? {
        val cached = repo.prediction(ticker, horizon)
        if (cached != null) return cached
        val prices = repo.prices(ticker, 120)
        return engine.predict(ticker, horizon, prices)
    }
}
