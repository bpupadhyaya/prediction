package com.prediction.stockmarket.ui.videointelligence

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.prediction.stockmarket.videointelligence.*
import com.prediction.stockmarket.data.database.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.launch
import javax.inject.Inject

data class VideoIntelligenceUiState(
    val urlInput: String = "",
    val isProcessing: Boolean = false,
    val processingMessage: String = "",
    val processingProgress: Float = 0f,
    val recentVideos: List<VideoSourceEntity> = emptyList(),
    val signals: List<VideoSignalEntity> = emptyList(),
    val trackedChannels: List<ChannelTrackEntity> = emptyList(),
    val selectedTimeRangeDays: Int = 7,
    val tickerFilter: String = "",
    val errorMessage: String? = null,
    val jobs: Map<String, ProcessingJob> = emptyMap(),
    /** Whisper model download progress keyed by modelId */
    val whisperDownloadProgress: Map<String, Float> = emptyMap(),
    val whisperDownloadStatus: Map<String, String> = emptyMap()
)

@HiltViewModel
class VideoIntelligenceViewModel @Inject constructor(
    private val manager: VideoIntelligenceManager
) : ViewModel() {

    private val _uiState = MutableStateFlow(VideoIntelligenceUiState())
    val uiState: StateFlow<VideoIntelligenceUiState> = _uiState.asStateFlow()

    init {
        // Observe processing jobs from the manager
        manager.jobs
            .onEach { jobs ->
                _uiState.value = _uiState.value.copy(jobs = jobs)
                val activeJob = jobs.values.firstOrNull {
                    it.status in listOf(
                        JobStatus.QUEUED, JobStatus.DOWNLOADING,
                        JobStatus.TRANSCRIBING, JobStatus.EXTRACTING
                    )
                }
                if (activeJob != null) {
                    _uiState.value = _uiState.value.copy(
                        isProcessing = true,
                        processingProgress = activeJob.progress,
                        processingMessage = activeJob.statusMessage
                    )
                } else {
                    val hasRecentDone = jobs.values.any { it.status == JobStatus.DONE }
                    if (hasRecentDone && _uiState.value.isProcessing) {
                        _uiState.value = _uiState.value.copy(isProcessing = false)
                        loadData()
                    } else {
                        _uiState.value = _uiState.value.copy(isProcessing = false)
                    }
                }
            }
            .launchIn(viewModelScope)

        loadData()
    }

    // -------------------------------------------------------------------------
    // User actions
    // -------------------------------------------------------------------------

    fun onUrlInputChange(url: String) {
        _uiState.value = _uiState.value.copy(urlInput = url, errorMessage = null)
    }

    fun onUrlSubmit(url: String) {
        val trimmed = url.trim()
        if (trimmed.isBlank()) {
            _uiState.value = _uiState.value.copy(errorMessage = "Please enter a YouTube URL")
            return
        }
        if (!trimmed.contains("youtube.com/") && !trimmed.contains("youtu.be/")) {
            _uiState.value = _uiState.value.copy(errorMessage = "Invalid YouTube URL")
            return
        }

        _uiState.value = _uiState.value.copy(
            urlInput = trimmed,
            isProcessing = true,
            processingProgress = 0f,
            processingMessage = "Starting…",
            errorMessage = null
        )
        manager.processUrl(trimmed)
    }

    fun onTimeRangeChange(days: Int) {
        _uiState.value = _uiState.value.copy(selectedTimeRangeDays = days)
        loadSignals(days, _uiState.value.tickerFilter)
    }

    fun onTickerFilterChange(ticker: String) {
        _uiState.value = _uiState.value.copy(tickerFilter = ticker)
        loadSignals(_uiState.value.selectedTimeRangeDays, ticker)
    }

    fun onApplySignal(signal: VideoSignalEntity) {
        viewModelScope.launch {
            try {
                manager.applySignal(signal)
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    errorMessage = "Failed to apply signal: ${e.message}"
                )
            }
        }
    }

    fun onTrackChannel(channelId: String, name: String, speaker: String) {
        viewModelScope.launch {
            try {
                manager.trackChannel(channelId, name, speaker)
                refreshTrackedChannels()
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    errorMessage = "Failed to track channel: ${e.message}"
                )
            }
        }
    }

    fun onRemoveChannel(channelId: String) {
        viewModelScope.launch {
            try {
                manager.removeTrackedChannel(channelId)
                refreshTrackedChannels()
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    errorMessage = "Failed to remove channel: ${e.message}"
                )
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(errorMessage = null)
    }

    fun loadData() {
        viewModelScope.launch {
            try {
                val videos = manager.getRecentVideos(20)
                _uiState.value = _uiState.value.copy(recentVideos = videos)
            } catch (_: Exception) {}
        }
        loadSignals(_uiState.value.selectedTimeRangeDays, _uiState.value.tickerFilter)
        refreshTrackedChannels()
    }

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    private fun loadSignals(days: Int, ticker: String) {
        viewModelScope.launch {
            try {
                val signals = manager.querySignals(
                    ticker = ticker.takeIf { it.isNotBlank() },
                    days = days
                )
                _uiState.value = _uiState.value.copy(signals = signals)
            } catch (_: Exception) {}
        }
    }

    private fun refreshTrackedChannels() {
        viewModelScope.launch {
            try {
                val channels = manager.getTrackedChannels()
                _uiState.value = _uiState.value.copy(trackedChannels = channels)
            } catch (_: Exception) {}
        }
    }
}
