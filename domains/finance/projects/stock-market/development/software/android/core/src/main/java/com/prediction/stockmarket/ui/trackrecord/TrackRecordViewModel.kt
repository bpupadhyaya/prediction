package com.prediction.stockmarket.ui.trackrecord

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.prediction.stockmarket.data.database.TrackedPredictionEntity
import com.prediction.stockmarket.data.repository.StockRepository
import com.prediction.stockmarket.data.sync.YahooFinanceFetcher
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.Date
import javax.inject.Inject

data class TrackRecordUiState(
    val record: List<TrackedPredictionEntity> = emptyList(),
    val loaded: Boolean = false,
    val resolvingMessage: String? = null,
)

@HiltViewModel
class TrackRecordViewModel @Inject constructor(
    private val repo: StockRepository,
    private val yahooFetcher: YahooFinanceFetcher,
) : ViewModel() {

    private val _uiState = MutableStateFlow(TrackRecordUiState())
    val uiState: StateFlow<TrackRecordUiState> = _uiState

    fun load() {
        viewModelScope.launch {
            val record = repo.trackedPredictions()
            _uiState.value = _uiState.value.copy(record = record, loaded = true)
            resolveMatured()
        }
    }

    fun clear() {
        viewModelScope.launch {
            repo.clearTrackedPredictions()
            _uiState.value = _uiState.value.copy(record = emptyList())
        }
    }

    /** Score every matured-but-unresolved prediction by re-fetching the current price. */
    private suspend fun resolveMatured() {
        val now = Date()
        val due = _uiState.value.record.filter { !it.resolved && it.maturesAt <= now }
        if (due.isEmpty()) return
        _uiState.value = _uiState.value.copy(
            resolvingMessage = "Scoring ${due.size} matured prediction${if (due.size > 1) "s" else ""}…"
        )
        for (p in due) {
            try {
                val current = withContext(Dispatchers.IO) {
                    val bars = try { yahooFetcher.fetchPriceBars(p.ticker, range = "1mo") } catch (_: Exception) { emptyList() }
                    bars.maxByOrNull { it.date }?.close
                }
                if (current == null || !current.isFinite() || current <= 0.0) continue
                val ret = (current - p.priceAtPrediction) / p.priceAtPrediction * 100.0
                val correct = when (p.direction) {
                    "UP" -> ret > 0
                    "DOWN" -> ret < 0
                    else -> kotlin.math.abs(ret) < 0.5
                }
                repo.saveTrackedPrediction(
                    p.copy(
                        actualPrice = current,
                        actualReturnPct = ret,
                        correct = correct,
                        resolved = true,
                        resolvedAt = Date()
                    )
                )
            } catch (_: Exception) {
                // keep pending — retry on next open
            }
        }
        _uiState.value = _uiState.value.copy(
            record = repo.trackedPredictions(),
            resolvingMessage = null
        )
    }
}
