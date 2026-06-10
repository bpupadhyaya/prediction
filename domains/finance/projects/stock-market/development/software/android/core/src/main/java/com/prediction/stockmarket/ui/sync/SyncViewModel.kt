package com.prediction.stockmarket.ui.sync

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.prediction.stockmarket.data.sync.MarketDataSourceManager
import com.prediction.stockmarket.data.sync.MarketDataSourceType
import com.prediction.stockmarket.data.sync.SyncManager
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class SyncUiState {
    object Idle : SyncUiState()
    object Syncing : SyncUiState()
    data class Done(val tagName: String) : SyncUiState()
    data class Error(val message: String) : SyncUiState()
}

@HiltViewModel
class SyncViewModel @Inject constructor(
    private val syncManager: SyncManager,
    private val sourceManager: MarketDataSourceManager
) : ViewModel() {

    private val _syncState = MutableStateFlow<SyncUiState>(SyncUiState.Idle)
    val syncState: StateFlow<SyncUiState> = _syncState

    private val _selectedSource = MutableStateFlow(sourceManager.activeSource)
    val selectedSource: StateFlow<MarketDataSourceType> = _selectedSource

    private val _syncProgress = MutableStateFlow(Pair(0, 0))
    val syncProgress: StateFlow<Pair<Int, Int>> = _syncProgress

    private val _currentTicker = MutableStateFlow("")
    val currentTicker: StateFlow<String> = _currentTicker

    fun setSource(source: MarketDataSourceType) {
        sourceManager.activeSource = source
        _selectedSource.value = source
    }

    fun setApiKey(source: MarketDataSourceType, key: String) {
        sourceManager.setApiKey(source, key)
    }

    fun getApiKey(source: MarketDataSourceType): String =
        sourceManager.getApiKey(source)

    fun sync() {
        if (_syncState.value is SyncUiState.Syncing) return
        viewModelScope.launch {
            _syncState.value = SyncUiState.Syncing
            _syncProgress.value = Pair(0, 0)
            _currentTicker.value = ""

            try {
                val result = syncManager.sync { done, total, ticker ->
                    _syncProgress.value = Pair(done, total)
                    _currentTicker.value = ticker
                }

                _syncState.value = when (result) {
                    is SyncManager.SyncResult.Success -> SyncUiState.Done(result.tagName)
                    is SyncManager.SyncResult.Error   -> SyncUiState.Error(result.message)
                }
            } catch (e: Exception) {
                _syncState.value = SyncUiState.Error(e.message ?: "Unknown error")
            }
        }
    }
}
