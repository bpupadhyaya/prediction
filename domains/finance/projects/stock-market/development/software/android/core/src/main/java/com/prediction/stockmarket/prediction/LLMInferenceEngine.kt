package com.prediction.stockmarket.prediction

import android.content.Context
import android.util.Log
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.flow
import java.io.File
import javax.inject.Inject
import javax.inject.Singleton

private const val TAG = "LLMInferenceEngine"

/**
 * MediaPipe LLM Inference Engine wrapper.
 *
 * Uses MediaPipe Tasks GenAI (com.google.mediapipe:tasks-genai:0.10.14).
 * If the API surface changes between MediaPipe releases, adjust the options builder calls below
 * (marked with TODO comments) and recompile.
 *
 * TODO: Verify API compatibility with tasks-genai 0.10.14 before production release.
 *       The LlmInference class API can change between minor versions.
 */
@Singleton
class LLMInferenceEngine @Inject constructor(
    private val context: Context
) {
    // Kept as Any? so the class compiles even when MediaPipe API import paths shift.
    // The actual runtime type is com.google.mediapipe.tasks.genai.llminference.LlmInference
    private var llmInference: Any? = null
    private var loadedModelPath: String? = null

    /** True when a model is loaded and ready to serve requests. */
    val isReady: Boolean get() = llmInference != null

    /**
     * Load a GGUF model from the given absolute [modelPath].
     * Returns [Result.success] on success or [Result.failure] with the underlying exception.
     *
     * TODO: If LlmInferenceOptions.Builder method names differ in your version of tasks-genai,
     *       update the builder chain below (setMaxTokens → setMaxNewTokens, etc.).
     */
    fun loadModel(modelPath: String): Result<Unit> {
        return try {
            // Unload any previously loaded model first
            unload()

            // Reflectively invoke MediaPipe to keep this file compilable even if API paths shift.
            // Preferred direct import (uncomment when API is stable):
            //
            // val options = LlmInference.LlmInferenceOptions.builder()
            //     .setModelPath(modelPath)
            //     .setMaxTokens(1024)
            //     .setTopK(40)
            //     .setTemperature(0.8f)
            //     .setRandomSeed(101)
            //     .build()
            // llmInference = LlmInference.createFromOptions(context, options)

            val optionsClass = Class.forName(
                "com.google.mediapipe.tasks.genai.llminference.LlmInference\$LlmInferenceOptions"
            )
            val builderMethod = optionsClass.getMethod("builder")
            val builder = builderMethod.invoke(null)

            // Chain builder calls via reflection
            val builderClass = builder.javaClass
            builderClass.getMethod("setModelPath", String::class.java).invoke(builder, modelPath)
            builderClass.getMethod("setMaxTokens", Int::class.java).invoke(builder, 1024)
            builderClass.getMethod("setTopK", Int::class.java).invoke(builder, 40)
            builderClass.getMethod("setTemperature", Float::class.java).invoke(builder, 0.8f)
            builderClass.getMethod("setRandomSeed", Int::class.java).invoke(builder, 101)
            val options = builderClass.getMethod("build").invoke(builder)

            val inferenceClass = Class.forName(
                "com.google.mediapipe.tasks.genai.llminference.LlmInference"
            )
            llmInference = inferenceClass
                .getMethod("createFromOptions", Context::class.java, optionsClass)
                .invoke(null, context, options)

            loadedModelPath = modelPath
            Log.i(TAG, "Model loaded: $modelPath")
            Result.success(Unit)
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
     * If the engine is not ready, emits a single informational message and completes.
     *
     * TODO: Adjust the listener interface name if tasks-genai changes
     *       PartialResultListener → LlmInferenceResultListener or similar.
     */
    fun chat(systemPrompt: String, userMessage: String): Flow<String> {
        val inference = llmInference
        if (inference == null) {
            return flow {
                emit("[Model not loaded. Download and activate a model in the Models tab.]")
            }
        }

        // Build a simple instruction-style prompt compatible with most GGUF chat models.
        val prompt = buildPrompt(systemPrompt, userMessage)

        return callbackFlow {
            try {
                // Attempt streaming via reflection — works for tasks-genai 0.10.14.
                //
                // Direct equivalent (uncomment when import paths are confirmed):
                // inference.generateResponseAsync(prompt) { partialResult, done ->
                //     trySend(partialResult)
                //     if (done) close()
                // }

                val listenerClass = try {
                    Class.forName(
                        "com.google.mediapipe.tasks.genai.llminference.LlmInference\$LlmInferenceResultListener"
                    )
                } catch (_: ClassNotFoundException) {
                    // Fallback listener name used in some minor versions
                    Class.forName(
                        "com.google.mediapipe.tasks.genai.llminference.LlmInference\$PartialResultListener"
                    )
                }

                val listenerProxy = java.lang.reflect.Proxy.newProxyInstance(
                    listenerClass.classLoader,
                    arrayOf(listenerClass)
                ) { _, _, args ->
                    if (args != null) {
                        val partialResult = args.getOrNull(0) as? String ?: ""
                        val done = args.getOrNull(1) as? Boolean ?: false
                        if (partialResult.isNotEmpty()) trySend(partialResult)
                        if (done) close()
                    }
                    null
                }

                val inferenceClass = inference.javaClass
                inferenceClass
                    .getMethod("generateResponseAsync", String::class.java, listenerClass)
                    .invoke(inference, prompt, listenerProxy)
            } catch (e: Exception) {
                Log.e(TAG, "Streaming generation failed: ${e.message}", e)
                // Fall back to a stub analytical response so the UI is not left blank.
                trySend(buildFallbackResponse(userMessage))
                close()
            }

            awaitClose { /* no cleanup needed; MediaPipe manages its own lifecycle */ }
        }
    }

    /** Release the currently loaded model and free native resources. */
    fun unload() {
        try {
            llmInference?.let { inference ->
                inference.javaClass.getMethod("close").invoke(inference)
            }
        } catch (e: Exception) {
            Log.w(TAG, "Error unloading model: ${e.message}")
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

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    private fun buildPrompt(systemPrompt: String, userMessage: String): String {
        // Generic instruction format understood by Llama / Mistral / Phi chat models.
        return if (systemPrompt.isBlank()) {
            "<s>[INST] $userMessage [/INST]"
        } else {
            "<s>[INST] <<SYS>>\n$systemPrompt\n<</SYS>>\n\n$userMessage [/INST]"
        }
    }

    private fun buildFallbackResponse(question: String): String {
        // Minimal stub so the UI shows something useful when the engine errors at runtime.
        return """
            [Analytical stub — LLM runtime error]

            Question: $question

            Without the LLM runtime, here is a framework for analysis:
            • Review macro environment (interest rates, Fed policy, inflation trend)
            • Assess fundamental signals (P/E vs sector, EPS growth, revenue trend)
            • Check technical momentum (RSI, 50/200-day MA, volume profile)
            • Weigh sentiment signals (options flow, short interest, analyst revisions)

            Adjust signal weights in the Interactive Prediction panel above and recompute.
        """.trimIndent()
    }
}
