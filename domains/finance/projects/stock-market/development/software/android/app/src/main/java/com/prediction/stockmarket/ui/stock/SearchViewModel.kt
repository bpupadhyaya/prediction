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
    private val repo: StockRepository
) : ViewModel() {

    private val _results = MutableStateFlow<List<StockEntity>>(emptyList())
    val results: StateFlow<List<StockEntity>> = _results

    private var searchJob: Job? = null

    fun search(query: String) {
        searchJob?.cancel()
        if (query.isBlank()) { _results.value = emptyList(); return }
        searchJob = viewModelScope.launch {
            delay(200)  // debounce
            _results.value = repo.search(query)
        }
    }
}
