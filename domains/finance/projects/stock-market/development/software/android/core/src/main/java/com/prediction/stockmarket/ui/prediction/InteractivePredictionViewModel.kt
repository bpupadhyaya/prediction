package com.prediction.stockmarket.ui.prediction

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.prediction.stockmarket.data.repository.StockRepository
import com.prediction.stockmarket.prediction.LLMInferenceEngine
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

/**
 * ViewModel for the Interactive Prediction screen.
 *
 * Manages a set of user-defined signals (name, domain, direction, weight),
 * computes a probability estimate from those signals using the same formula
 * as the web app, and streams LLM research responses via [LLMInferenceEngine].
 */
@HiltViewModel
class InteractivePredictionViewModel @Inject constructor(
    private val llmEngine: LLMInferenceEngine,
    private val repository: StockRepository
) : ViewModel() {

    // -------------------------------------------------------------------------
    // Domain model
    // -------------------------------------------------------------------------

    data class Signal(
        val id: String = UUID.randomUUID().toString(),
        val name: String,
        val domain: String,        // e.g. "Macro", "Technical", …
        val direction: String,     // "up" | "down" | "neutral"
        val weight: Int            // 0-100
    )

    data class UiState(
        val ticker: String = "",
        val signals: List<Signal> = emptyList(),
        val probUp: Double = 0.5,
        val confidence: Double = 0.0,
        val direction: String = "neutral",   // "up" | "down" | "neutral"
        val llmResponse: String = "",
        val isStreaming: Boolean = false,
        val isModelReady: Boolean = false,
        val sessionSaved: Boolean = false,
        val errorMessage: String? = null
    )

    // -------------------------------------------------------------------------
    // State
    // -------------------------------------------------------------------------

    private val _state = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = _state.asStateFlow()

    // -------------------------------------------------------------------------
    // Public API
    // -------------------------------------------------------------------------

    fun setTicker(ticker: String) {
        _state.value = _state.value.copy(
            ticker = ticker,
            isModelReady = llmEngine.isReady
        )
    }

    fun refreshModelStatus() {
        _state.value = _state.value.copy(isModelReady = llmEngine.isReady)
    }

    fun addSignal(signal: Signal) {
        val updated = _state.value.signals + signal
        _state.value = _state.value.copy(signals = updated)
        recompute(updated)
    }

    fun updateSignal(signal: Signal) {
        val updated = _state.value.signals.map { if (it.id == signal.id) signal else it }
        _state.value = _state.value.copy(signals = updated)
        recompute(updated)
    }

    fun removeSignal(id: String) {
        val updated = _state.value.signals.filter { it.id != id }
        _state.value = _state.value.copy(signals = updated)
        recompute(updated)
    }

    /**
     * Trigger LLM inference for [question].
     * Streams tokens directly into [UiState.llmResponse].
     */
    fun askLLM(question: String) {
        if (!llmEngine.isReady) {
            _state.value = _state.value.copy(
                errorMessage = "No model loaded. Download and activate a model in the Models tab."
            )
            return
        }

        val ticker = _state.value.ticker
        val systemPrompt = buildSystemPrompt(ticker)

        viewModelScope.launch(Dispatchers.IO) {
            _state.value = _state.value.copy(
                isStreaming = true,
                llmResponse = "",
                errorMessage = null
            )

            val builder = StringBuilder()
            llmEngine.chat(systemPrompt, question).collect { token ->
                builder.append(token)
                _state.value = _state.value.copy(llmResponse = builder.toString())
            }

            _state.value = _state.value.copy(isStreaming = false)
        }
    }

    /**
     * Recompute the prediction from the current signal list.
     * Also callable explicitly from the UI if needed.
     */
    fun computePrediction() {
        recompute(_state.value.signals)
    }

    /**
     * "Save" the current session.  For now clears the saved flag after a beat
     * and shows a success acknowledgement.
     */
    fun saveSession() {
        _state.value = _state.value.copy(sessionSaved = true, errorMessage = null)
        // Reset the flag so repeated saves work
        viewModelScope.launch {
            kotlinx.coroutines.delay(2000)
            _state.value = _state.value.copy(sessionSaved = false)
        }
    }

    fun clearError() {
        _state.value = _state.value.copy(errorMessage = null)
    }

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    /**
     * Prediction formula (mirrors the web app):
     *   dirValue: up = 1, down = -1, neutral = 0
     *   normalizedScore = Σ(weight × dirValue) / Σ(weight)
     *   probUp           = (normalizedScore + 1) / 2
     *   confidence       = |normalizedScore|
     *   direction        = "up" if probUp > 0.52, "down" if probUp < 0.48, else "neutral"
     */
    private fun recompute(signals: List<Signal>) {
        if (signals.isEmpty()) {
            _state.value = _state.value.copy(
                probUp = 0.5,
                confidence = 0.0,
                direction = "neutral"
            )
            return
        }

        var weightedSum = 0.0
        var totalWeight = 0.0

        for (s in signals) {
            val dirValue = when (s.direction) {
                "up"   -> 1.0
                "down" -> -1.0
                else   -> 0.0
            }
            weightedSum += s.weight * dirValue
            totalWeight += s.weight
        }

        val normalizedScore = if (totalWeight > 0) weightedSum / totalWeight else 0.0
        val probUp = (normalizedScore + 1.0) / 2.0
        val confidence = Math.abs(normalizedScore)
        val direction = when {
            probUp > 0.52 -> "up"
            probUp < 0.48 -> "down"
            else          -> "neutral"
        }

        _state.value = _state.value.copy(
            probUp = probUp,
            confidence = confidence,
            direction = direction
        )
    }

    private fun buildSystemPrompt(ticker: String): String {
        val signals = _state.value.signals
        val signalSummary = if (signals.isEmpty()) {
            "No signals have been entered yet."
        } else {
            signals.joinToString("\n") { s ->
                "• ${s.name} (${s.domain}): ${s.direction.uppercase()}, weight ${s.weight}"
            }
        }
        val direction = _state.value.direction.uppercase()
        val prob = "%.1f%%".format(_state.value.probUp * 100)
        val conf = "%.1f%%".format(_state.value.confidence * 100)

        return """
            You are an expert stock market analyst assistant helping a user analyze $ticker.

            Current interactive prediction summary:
            - Composite direction: $direction
            - Prob(UP): $prob
            - Confidence: $conf

            Active signals:
            $signalSummary

            Provide concise, evidence-based analysis. Do not give buy/sell recommendations.
            Focus on explaining what the signals mean and what the user should watch for.
        """.trimIndent()
    }
}
