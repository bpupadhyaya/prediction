package com.prediction.stockmarket.prediction

import android.content.Context
import org.json.JSONObject
import kotlin.math.exp

/**
 * Bundled model metadata loaded once from assets/mobile_model_meta.json.
 *
 * Provides honest out-of-sample accuracy, probability calibration, and feature
 * baselines used by the perturbation-based explainer. Everything degrades
 * gracefully (sensible defaults / identity calibration) if the file or a key
 * is missing, so prediction never hard-fails on metadata.
 */
object ModelMeta {

    /** Feature names in MOBILE_FEATURES order (matches buildFeatures). */
    val featureNames: List<String> = listOf(
        "return_1d", "return_5d", "return_20d", "return_60d", "return_126d", "return_252d",
        "ma_5", "ma_20", "ma_50", "ma_200",
        "volatility_20", "volatility_60",
        "volume_ratio", "dollar_volume_turnover",
        "rsi", "high_52w_ratio",
    )

    /** Human-readable labels, keyed by feature name. */
    val featureLabels: Map<String, String> = mapOf(
        "return_1d" to "1-day momentum",
        "return_5d" to "1-week momentum",
        "return_20d" to "1-month momentum",
        "return_60d" to "3-month momentum",
        "return_126d" to "6-month momentum",
        "return_252d" to "12-month momentum",
        "ma_5" to "Price vs 5-day avg",
        "ma_20" to "Price vs 20-day avg",
        "ma_50" to "Price vs 50-day avg",
        "ma_200" to "Price vs 200-day avg",
        "volatility_20" to "20-day volatility",
        "volatility_60" to "60-day volatility",
        "volume_ratio" to "Volume vs average",
        "dollar_volume_turnover" to "Dollar-volume turnover",
        "rsi" to "RSI (momentum)",
        "high_52w_ratio" to "Proximity to 52-week high",
    )

    private data class Calibration(val w: Double, val b: Double)

    private var loaded = false
    private val accuracies = mutableMapOf<String, Double>()
    private val calibrations = mutableMapOf<String, Calibration>()
    private val baselines = mutableMapOf<String, Float>()
    private val testUpRates = mutableMapOf<String, Double>()
    private val brierRaw = mutableMapOf<String, Double>()
    private val brierCalibrated = mutableMapOf<String, Double>()
    private val nTests = mutableMapOf<String, Int>()

    /** Maps a UI horizon string to the metadata horizon key. Mirrors engine asset mapping. */
    private fun metaKey(horizon: String): String = when {
        horizon.startsWith("1d", ignoreCase = true) -> "1d"
        horizon.startsWith("1m", ignoreCase = true) ||
        horizon.startsWith("3m", ignoreCase = true) -> "1m"
        else -> "1w"
    }

    @Synchronized
    fun ensureLoaded(context: Context) {
        if (loaded) return
        loaded = true
        try {
            val raw = context.assets.open("mobile_model_meta.json")
                .bufferedReader().use { it.readText() }
            val root = JSONObject(raw)

            root.optJSONObject("baselines")?.let { b ->
                for (name in featureNames) {
                    if (b.has(name)) baselines[name] = b.getDouble(name).toFloat()
                }
            }

            root.optJSONObject("horizons")?.let { hz ->
                val keys = hz.keys()
                while (keys.hasNext()) {
                    val key = keys.next()
                    val h = hz.getJSONObject(key)
                    accuracies[key] = h.optDouble("backtest_accuracy", Double.NaN)
                    if (h.has("test_up_rate")) testUpRates[key] = h.getDouble("test_up_rate")
                    if (h.has("brier_raw")) brierRaw[key] = h.getDouble("brier_raw")
                    if (h.has("brier_calibrated")) brierCalibrated[key] = h.getDouble("brier_calibrated")
                    if (h.has("n_test")) nTests[key] = h.getInt("n_test")
                    h.optJSONObject("calibration")?.let { c ->
                        calibrations[key] = Calibration(
                            w = c.optDouble("w", 1.0),
                            b = c.optDouble("b", 0.0),
                        )
                    }
                }
            }
        } catch (_: Exception) {
            // Leave maps empty — callers fall back to defaults.
        }
    }

    /** Out-of-sample directional accuracy for a horizon; safe default if missing. */
    fun accuracy(horizon: String): Double {
        val v = accuracies[metaKey(horizon)]
        return if (v == null || v.isNaN()) 0.54 else v
    }

    /** Calibrated P(up) = sigmoid(w * rawProbUp + b). Identity fallback if missing. */
    fun calibrate(rawProbUp: Float, horizon: String): Float {
        val c = calibrations[metaKey(horizon)] ?: return rawProbUp
        val z = c.w * rawProbUp + c.b
        return (1.0 / (1.0 + exp(-z))).toFloat()
    }

    /** Mean (training) value of a feature, used as the perturbation baseline. */
    fun baseline(feature: String): Float = baselines[feature] ?: 0f

    fun label(feature: String): String = featureLabels[feature] ?: feature

    /** Naive "always up" base rate on the hold-out for a horizon; null if absent. */
    fun testUpRate(horizon: String): Double? = testUpRates[metaKey(horizon)]

    /** Brier score before calibration for a horizon; null if absent. */
    fun brierRaw(horizon: String): Double? = brierRaw[metaKey(horizon)]

    /** Brier score after Platt calibration for a horizon; null if absent. */
    fun brierCalibrated(horizon: String): Double? = brierCalibrated[metaKey(horizon)]

    /** Hold-out sample count for a horizon; null if absent. */
    fun nTest(horizon: String): Int? = nTests[metaKey(horizon)]

    /** Whether usable horizon metadata was loaded. */
    fun isLoaded(): Boolean = accuracies.isNotEmpty()
}
