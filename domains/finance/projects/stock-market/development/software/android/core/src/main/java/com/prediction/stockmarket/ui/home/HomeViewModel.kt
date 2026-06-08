package com.prediction.stockmarket.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.prediction.stockmarket.data.database.PredictionEntity
import com.prediction.stockmarket.data.repository.StockRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val repo: StockRepository
) : ViewModel() {

    private val _predictions = MutableStateFlow<List<PredictionEntity>>(emptyList())
    val predictions: StateFlow<List<PredictionEntity>> = _predictions

    private val _hotPredictions = MutableStateFlow<Map<String, PredictionEntity?>>(emptyMap())
    val hotPredictions: StateFlow<Map<String, PredictionEntity?>> = _hotPredictions

    init { loadPredictions("1w") }

    fun loadPredictions(horizon: String) {
        viewModelScope.launch {
            repo.predictionsFlow(horizon).collectLatest { _predictions.value = it }
        }
    }

    fun loadHotPredictions(tickers: List<String>) {
        viewModelScope.launch {
            val result = tickers.associateWith { ticker ->
                repo.prediction(ticker, "1w")
            }
            _hotPredictions.value = result
        }
    }
}
