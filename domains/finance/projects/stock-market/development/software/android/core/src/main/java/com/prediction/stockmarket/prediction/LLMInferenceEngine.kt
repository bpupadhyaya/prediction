package com.prediction.stockmarket.prediction

import android.content.Context
import android.util.Log
import com.google.mediapipe.tasks.genai.llminference.LlmInference
import com.google.mediapipe.tasks.genai.llminference.LlmInference.LlmInferenceOptions
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.flowOn
import org.json.JSONObject
import java.io.File
import javax.inject.Inject
import javax.inject.Singleton

private const val TAG = "LLMInferenceEngine"

@Singleton
class LLMInferenceEngine @Inject constructor(
    private val context: Context
) {
    private var llmInference: LlmInference? = null
    private var loadedModelPath: String? = null

    // MediaPipe 0.10.x streams partial results to the options-level result listener,
    // not a per-call callback. The active chat() flow registers its forwarder here.
    @Volatile private var responseCallback: ((String, Boolean) -> Unit)? = null

    /** True when a model is loaded and ready to serve requests. */
    val isReady: Boolean get() = llmInference != null

    /**
     * Load a GGUF model from the given absolute [modelPath].
     * Returns [Result.success] on success or [Result.failure] with the underlying exception.
     *
     * If the model format is incompatible (e.g. UnsupportedOperationException for certain GGUF
     * variants), the error is captured and returned as a failure so callers can fall back gracefully.
     */
    fun loadModel(modelPath: String): Result<Unit> {
        return try {
            unload()
            val options = LlmInferenceOptions.builder()
                .setModelPath(modelPath)
                .setMaxTokens(1024)
                .setTopK(40)
                .setTemperature(0.8f)
                .setRandomSeed(101)
                .setResultListener { partial, done -> responseCallback?.invoke(partial ?: "", done) }
                .build()
            llmInference = LlmInference.createFromOptions(context, options)
            loadedModelPath = modelPath
            Log.i(TAG, "Model loaded from $modelPath")
            Result.success(Unit)
        } catch (e: UnsupportedOperationException) {
            Log.e(TAG, "Model format incompatible (GGUF variant not supported): ${e.message}")
            llmInference = null
            loadedModelPath = null
            Result.failure(e)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to load model: ${e.message}", e)
            llmInference = null
            loadedModelPath = null
            Result.failure(e)
        }
    }

    /**
     * Stream a chat response token-by-token using MediaPipe's async generation API.
     *
     * Emits partial tokens as they arrive; the flow completes when generation finishes.
     * If the engine is not ready, emits a single informational error message and completes.
     */
    fun chat(systemPrompt: String, userMessage: String): Flow<String> = callbackFlow {
        val inference = llmInference
        if (inference == null) {
            trySend("[Error: No model loaded. Download and activate a model in the Models tab.]")
            close()
            return@callbackFlow
        }

        val prompt = buildPrompt(systemPrompt, userMessage)

        responseCallback = { partialResult, done ->
            if (partialResult.isNotEmpty()) {
                trySend(partialResult)
            }
            if (done) close()
        }
        try {
            inference.generateResponseAsync(prompt)
        } catch (e: Exception) {
            Log.e(TAG, "Inference error: ${e.message}", e)
            trySend("\n[Inference error: ${e.message}]")
            close(e)
        }

        awaitClose { responseCallback = null }
    }.flowOn(Dispatchers.IO)

    /** Release the currently loaded model and free native resources. */
    fun unload() {
        try {
            llmInference?.close()
        } catch (e: Exception) {
            Log.w(TAG, "Error closing model: ${e.message}")
        } finally {
            llmInference = null
            loadedModelPath = null
        }
    }

    /**
     * Returns the absolute path of [modelId].gguf inside filesDir/llm_models,
     * or null if the file has not been downloaded yet.
     */
    fun getModelPath(modelId: String): String? {
        val f = File(context.filesDir, "llm_models/$modelId.gguf")
        return if (f.exists()) f.absolutePath else null
    }

    /**
     * Attempt to auto-load the model identified by [activeModelId].
     * Returns true if the model was successfully loaded, false otherwise.
     */
    suspend fun tryAutoLoad(activeModelId: String?): Boolean {
        if (activeModelId == null) return false
        val path = getModelPath(activeModelId) ?: return false
        return loadModel(path).isSuccess
    }

    /**
     * Reads the active model ID from the llm_config.json file stored in filesDir.
     * Returns null if no active model has been configured or the file is missing/corrupt.
     */
    fun readActiveModelId(): String? {
        return try {
            val configFile = File(context.filesDir, "llm_config.json")
            JSONObject(configFile.readText()).optString("active_model_id").takeIf { it.isNotEmpty() }
        } catch (_: Exception) {
            null
        }
    }

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    private fun buildPrompt(system: String, user: String): String =
        "<|system|>\n$system\n<|user|>\n$user\n<|assistant|>\n"
}
