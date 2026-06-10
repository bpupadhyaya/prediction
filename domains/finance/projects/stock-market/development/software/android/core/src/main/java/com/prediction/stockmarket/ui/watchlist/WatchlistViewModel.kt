package com.prediction.stockmarket.ui.watchlist

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.prediction.stockmarket.data.database.PredictionEntity
import com.prediction.stockmarket.data.database.WatchlistEntity
import com.prediction.stockmarket.data.repository.StockRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class WatchlistViewModel @Inject constructor(
    private val repo: StockRepository
) : ViewModel() {

    val watchlist: StateFlow<List<WatchlistEntity>> =
        repo.watchlistFlow().stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    private val _prices = MutableStateFlow<Map<String, Double>>(emptyMap())
    val prices: StateFlow<Map<String, Double>> = _prices

    private val _predictions = MutableStateFlow<Map<String, PredictionEntity>>(emptyMap())
    val predictions: StateFlow<Map<String, PredictionEntity>> = _predictions

    private val _errorMessage = MutableStateFlow<String?>(null)
    val errorMessage: StateFlow<String?> = _errorMessage

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
