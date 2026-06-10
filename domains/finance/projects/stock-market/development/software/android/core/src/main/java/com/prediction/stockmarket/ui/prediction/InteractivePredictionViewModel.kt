package com.prediction.stockmarket.ui.prediction

import android.content.SharedPreferences
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.prediction.stockmarket.data.ParameterRepository
import com.prediction.stockmarket.data.StockParameter
import com.prediction.stockmarket.prediction.LLMInferenceEngine
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel for the Interactive Prediction screen.
 *
 * Loads all 656 pre-defined parameters from [ParameterRepository], persists per-ticker
 * parameter states to [SharedPreferences], computes a weighted-signal probability
 * estimate, and streams LLM research responses via [LLMInferenceEngine].
 */
@HiltViewModel
class InteractivePredictionViewModel @Inject constructor(
    private val llmEngine: LLMInferenceEngine,
    private val paramRepository: ParameterRepository,
    private val prefs: SharedPreferences,
    private val gson: Gson
) : ViewModel() {

    // -------------------------------------------------------------------------
    // Domain model
    // -------------------------------------------------------------------------

    data class ParamState(
        val weight: Int = 0,
        val direction: String = "neutral"   // "up" | "down" | "neutral"
    )

    data class UiState(
        val ticker: String = "",
        val parameters: List<StockParameter> = emptyList(),
        val states: Map<String, ParamState> = emptyMap(),
        val probUp: Double = 0.5,
        val confidence: Double = 0.0,
        val direction: String = "neutral",  // "up" | "down" | "neutral"
        val paramsSet: Int = 0,
        val expandedParams: Set<String> = emptySet(),
        val llmResponse: String = "",
        val isStreaming: Boolean = false,
        val isModelReady: Boolean = false,
        val saveMessage: String = "",
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

    fun loadParameters(ticker: String) {
        val params = paramRepository.parameters
        val saved = loadSavedStates(ticker)
        val states = saved ?: initStates(params)
        _state.update {
            it.copy(
                ticker = ticker,
                parameters = params,
                states = states,
                isModelReady = llmEngine.isReady
            )
        }
        computePrediction()

        // Auto-load the active LLM model if it is not already loaded
        if (!llmEngine.isReady) {
            viewModelScope.launch(Dispatchers.IO) {
                val activeId = llmEngine.readActiveModelId()
                if (activeId != null) {
                    llmEngine.tryAutoLoad(activeId)
                    _state.update { it.copy(isModelReady = llmEngine.isReady) }
                }
            }
        }
    }

    fun refreshModelStatus() {
        _state.update { it.copy(isModelReady = llmEngine.isReady) }
    }

    fun initStates(params: List<StockParameter> = paramRepository.parameters): Map<String, ParamState> =
        params.associate { it.name to ParamState() }

    fun setDirection(name: String, dir: String) {
        _state.update { s ->
            val newStates = s.states.toMutableMap()
            newStates[name] = (newStates[name] ?: ParamState()).copy(direction = dir)
            s.copy(states = newStates)
        }
        computePrediction()
        saveStates()
    }

    fun setWeight(name: String, weight: Int) {
        _state.update { s ->
            val newStates = s.states.toMutableMap()
            newStates[name] = (newStates[name] ?: ParamState()).copy(weight = weight)
            s.copy(states = newStates)
        }
        computePrediction()
        saveStates()
    }

    fun toggleExpand(name: String) {
        _state.update { s ->
            val exp = s.expandedParams.toMutableSet()
            if (exp.contains(name)) exp.remove(name) else exp.add(name)
            s.copy(expandedParams = exp)
        }
    }

    fun reset() {
        _state.update { it.copy(states = initStates()) }
        computePrediction()
        saveStates()
    }

    /**
     * Trigger LLM inference for [question].
     * Streams tokens directly into [UiState.llmResponse].
     */
    fun askLLM(question: String) {
        if (!llmEngine.isReady) {
            _state.update {
                it.copy(errorMessage = "No model loaded. Download and activate a model in the Models tab.")
            }
            return
        }

        val ticker = _state.value.ticker
        val systemPrompt = buildSystemPrompt(ticker)

        viewModelScope.launch(Dispatchers.IO) {
            _state.update { it.copy(isStreaming = true, llmResponse = "", errorMessage = null) }

            val builder = StringBuilder()
            llmEngine.chat(systemPrompt, question).collect { token ->
                builder.append(token)
                _state.update { it.copy(llmResponse = builder.toString()) }
            }

            _state.update { it.copy(isStreaming = false) }
        }
    }

    /**
     * Save the current session and show a brief confirmation message.
     */
    fun saveSession() {
        saveStates()
        _state.update { it.copy(saveMessage = "Session saved", errorMessage = null) }
        viewModelScope.launch {
            kotlinx.coroutines.delay(2000)
            _state.update { it.copy(saveMessage = "") }
        }
    }

    fun clearError() {
        _state.update { it.copy(errorMessage = null) }
    }

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    /**
     * Prediction formula (mirrors the web app):
     *   dirValue: up = 1, down = -1, neutral = 0
     *   normalizedScore = Σ(weight × dirValue) / Σ(weight)  [only non-neutral params]
     *   probUp           = (normalizedScore + 1) / 2
     *   confidence       = |normalizedScore|
     *   direction        = "up" if probUp > 0.52, "down" if probUp < 0.48, else "neutral"
     */
    private fun computePrediction() {
        val states = _state.value.states
        var totalWeight = 0.0
        var weightedScore = 0.0
        var paramsSet = 0

        for ((_, s) in states) {
            if (s.direction == "neutral") continue
            val dv = if (s.direction == "up") 1.0 else -1.0
            weightedScore += s.weight * dv
            totalWeight += s.weight
            paramsSet++
        }

        val (probUp, confidence, direction) = if (totalWeight == 0.0) {
            Triple(0.5, 0.0, "neutral")
        } else {
            val norm = weightedScore / totalWeight
            val p = (norm + 1.0) / 2.0
            val d = when {
                p > 0.52 -> "up"
                p < 0.48 -> "down"
                else     -> "neutral"
            }
            Triple(p, Math.abs(norm), d)
        }

        _state.update {
            it.copy(
                probUp = probUp,
                confidence = confidence,
                direction = direction,
                paramsSet = paramsSet
            )
        }
    }

    /** Persist current parameter states for [ticker] to SharedPreferences. */
    private fun saveStates() {
        val ticker = _state.value.ticker
        if (ticker.isBlank()) return
        val json = gson.toJson(_state.value.states)
        prefs.edit().putString("ip-$ticker", json).apply()
    }

    /** Load previously persisted parameter states for [ticker], or null if none. */
    @Suppress("UNCHECKED_CAST")
    private fun loadSavedStates(ticker: String): Map<String, ParamState>? {
        val json = prefs.getString("ip-$ticker", null) ?: return null
        return try {
            val type = object : TypeToken<Map<String, ParamState>>() {}.type
            gson.fromJson<Map<String, ParamState>>(json, type)
        } catch (e: Exception) {
            null
        }
    }

    private fun buildSystemPrompt(ticker: String): String {
        val states = _state.value.states
        val activeParams = _state.value.parameters
            .filter { p -> states[p.name]?.direction != "neutral" && states[p.name] != null }
        val signalSummary = if (activeParams.isEmpty()) {
            "No parameters have been set yet."
        } else {
            activeParams.joinToString("\n") { p ->
                val s = states[p.name] ?: ParamState()
                "• ${p.label} (${p.domainLabel}): ${s.direction.uppercase()}, weight ${s.weight}"
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
            - Parameters set: ${_state.value.paramsSet}

            Active parameters:
            $signalSummary

            Provide concise, evidence-based analysis. Do not give buy/sell recommendations.
            Focus on explaining what the signals mean and what the user should watch for.
        """.trimIndent()
    }
}
