package com.prediction.stockmarket.ui.models

data class LLMModel(
    val id: String,
    val name: String,
    val paramsB: Double,
    val sizeGB: Double,
    val ramMinGB: Double,
    val quantization: String,
    val description: String,
    val tags: List<String>,
    val hfRepo: String,
    val hfFile: String
) {
    val downloadUrl: String get() = "https://huggingface.co/$hfRepo/resolve/main/$hfFile"

    fun compatibility(totalRamGB: Double): ModelCompatibility = when {
        totalRamGB >= ramMinGB * 1.25 -> ModelCompatibility.COMPATIBLE
        totalRamGB >= ramMinGB * 0.75 -> ModelCompatibility.MARGINAL
        else -> ModelCompatibility.INSUFFICIENT
    }
}

enum class ModelCompatibility(val label: String) {
    COMPATIBLE("✓ Compatible"),
    MARGINAL("⚠ Marginal"),
    INSUFFICIENT("✗ Needs more RAM")
}

val LLM_CATALOG = listOf(
    LLMModel(
        "llama3.2-1b-q4", "Llama 3.2 1B", 1.0, 0.8, 4.0, "Q4_K_M",
        "Smallest — fast on any device",
        listOf("Fast", "Low RAM"),
        "bartowski/Llama-3.2-1B-Instruct-GGUF",
        "Llama-3.2-1B-Instruct-Q4_K_M.gguf"
    ),
    LLMModel(
        "llama3.2-3b-q4", "Llama 3.2 3B", 3.0, 2.0, 8.0, "Q4_K_M",
        "Good balance of speed and quality",
        listOf("Recommended"),
        "bartowski/Llama-3.2-3B-Instruct-GGUF",
        "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    ),
    LLMModel(
        "phi3.5-mini-q4", "Phi-3.5 Mini", 3.8, 2.4, 8.0, "Q4_K_M",
        "Microsoft model, strong reasoning for its size",
        listOf("Efficient"),
        "bartowski/Phi-3.5-mini-instruct-GGUF",
        "Phi-3.5-mini-instruct-Q4_K_M.gguf"
    ),
    LLMModel(
        "mistral-7b-q4", "Mistral 7B", 7.0, 4.4, 16.0, "Q4_K_M",
        "Strong instruction-following, good financial reasoning",
        listOf("Popular"),
        "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
        "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    ),
    LLMModel(
        "llama3.1-8b-q4", "Llama 3.1 8B", 8.0, 4.9, 16.0, "Q4_K_M",
        "Meta flagship small model, excellent quality",
        listOf("Popular"),
        "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
        "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
    ),
    LLMModel(
        "gemma2-9b-q4", "Gemma 2 9B", 9.0, 5.8, 16.0, "Q4_K_M",
        "Google model, strong analytical reasoning",
        listOf("Google"),
        "bartowski/gemma-2-9b-it-GGUF",
        "gemma-2-9b-it-Q4_K_M.gguf"
    ),
    LLMModel(
        "llama3.1-70b-q4", "Llama 3.1 70B", 70.0, 42.5, 64.0, "Q4_K_M",
        "Most capable — requires 64 GB+ RAM",
        listOf("Most Capable"),
        "bartowski/Meta-Llama-3.1-70B-Instruct-GGUF",
        "Meta-Llama-3.1-70B-Instruct-Q4_K_M.gguf"
    ),
)
