package com.prediction.stockmarket.ui.stock

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.prediction.stockmarket.data.database.StockEntity
import com.prediction.stockmarket.data.repository.StockRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SearchViewModel @Inject constructor(
    private val repo: StockRepository,
    private val yahooFetcher: com.prediction.stockmarket.data.sync.YahooFinanceFetcher,
) : ViewModel() {

    private val _results = MutableStateFlow<List<StockEntity>>(emptyList())
    val results: StateFlow<List<StockEntity>> = _results

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading

    private val _errorMessage = MutableStateFlow<String?>(null)
    val errorMessage: StateFlow<String?> = _errorMessage

    private var searchJob: Job? = null

    fun search(query: String) {
        searchJob?.cancel()
        if (query.isBlank()) {
            _results.value = emptyList()
            _isLoading.value = false
            return
        }
        searchJob = viewModelScope.launch {
            delay(200)  // debounce
            _isLoading.value = true
            _errorMessage.value = null
            try {
                // Local synced universe answers instantly…
                val local = repo.search(query)
                _results.value = local
                // …then merge global Yahoo results (any exchange, crypto, ETF, index)
                val remote = kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
                    yahooFetcher.searchSymbols(query)
                }
                val seen = local.map { it.ticker }.toSet()
                _results.value = local + remote.filter { it.ticker !in seen }
            } catch (e: Exception) {
                _errorMessage.value = "Search failed: ${e.message}"
                _results.value = emptyList()
            } finally {
                _isLoading.value = false
            }
        }
    }
}
