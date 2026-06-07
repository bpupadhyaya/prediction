package com.prediction.stockmarket.ui.portfolio

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.prediction.stockmarket.data.database.PortfolioEntity
import com.prediction.stockmarket.data.repository.StockRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class PortfolioViewModel @Inject constructor(
    private val repo: StockRepository
) : ViewModel() {

    val holdings: StateFlow<List<PortfolioEntity>> =
        repo.portfolioFlow().stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    private val _latestPrices = MutableStateFlow<Map<String, Double>>(emptyMap())
    val latestPrices: StateFlow<Map<String, Double>> = _latestPrices

    init {
        viewModelScope.launch {
            holdings.collectLatest { list ->
                val prices = list.associate { h ->
                    h.ticker to (repo.latestPrice(h.ticker)?.adjClose ?: h.costBasis)
                }
                _latestPrices.value = prices
            }
        }
    }

    fun addHolding(ticker: String, shares: Double, costBasis: Double) {
        viewModelScope.launch { repo.addHolding(ticker, shares, costBasis) }
    }

    fun removeHolding(ticker: String) {
        viewModelScope.launch { repo.removeHolding(ticker) }
    }
}
