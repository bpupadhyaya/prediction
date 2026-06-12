package com.prediction.stockmarket.prediction

import android.content.Context
import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import com.prediction.stockmarket.data.database.PriceBarEntity
import com.prediction.stockmarket.data.database.PredictionEntity
import dagger.hilt.android.qualifiers.ApplicationContext
import java.nio.FloatBuffer
import java.util.Date
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.abs
import kotlin.math.sqrt

@Singleton
class PredictionEngine @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val env = OrtEnvironment.getEnvironment()
    private var session: OrtSession? = null

    init {
        try {
            val modelBytes = context.assets.open("stock_predictor.onnx").readBytes()
            session = env.createSession(modelBytes, OrtSession.SessionOptions())
        } catch (_: Exception) {
            // Model not yet available; predictions fall back to DB cache
        }
    }

    fun predict(ticker: String, horizon: String, prices: List<PriceBarEntity>): PredictionEntity? {
        val features = buildFeatures(prices) ?: return null
        val prob = runInference(features) ?: return null
        val direction = if (prob >= 0.5f) "UP" else "DOWN"
        val closes = prices.map { it.adjClose.toFloat() }
        val vol = if (closes.size >= 21)
            stdDev((0 until 20).map { i -> closes[i] / closes[i + 1] - 1f })
        else 0f

        return PredictionEntity(
            ticker = ticker,
            horizon = horizon,
            direction = direction,
            probability = prob.toDouble(),
            expectedReturnLow = if (prob >= 0.5f) -0.02 else -0.05,
            expectedReturnHigh = if (prob >= 0.5f) 0.05 else 0.02,
            volatility = vol.toDouble(),
            modelAccuracy = 0.54,
            generatedAt = Date()
        )
    }

    // Feature semantics MUST match the training pipeline (desktop trainer.py) and
    // the exporter's MOBILE_FEATURES order exactly. Prices are newest-first.
    // 16 features — works for ANY instrument with >= 253 daily bars (stocks on any
    // exchange, crypto pairs, ETFs, indices) since all inputs are OHLCV-derived.
    private fun buildFeatures(prices: List<PriceBarEntity>): FloatArray? {
        if (prices.size < 253) return null
        val closes = prices.map { it.adjClose.toFloat() }
        val volumes = prices.map { it.volume.toFloat() }
        val c0 = closes[0]

        fun ret(n: Int) = (c0 - closes[n]) / closes[n]
        fun maDev(n: Int) = closes.take(n).average().toFloat() / c0 - 1f
        fun volStd(n: Int) = sampleStd((0 until n).map { i -> closes[i] / closes[i + 1] - 1f })

        val avgVol = volumes.take(20).average().toFloat()
        val volRatio = if (avgVol > 0) volumes[0] / avgVol else 1f
        val dollarVol = (0 until 20).map { i -> closes[i] * volumes[i] }
        val avgDollarVol = dollarVol.average().toFloat()
        val dollarTurnover = if (avgDollarVol > 0) dollarVol[0] / avgDollarVol else 1f
        val rsi = computeRSI(closes.take(15))
        val high52w = closes.take(252).max()
        val high52wRatio = if (high52w > 0) c0 / high52w else 1f

        return floatArrayOf(
            ret(1), ret(5), ret(20), ret(60), ret(126), ret(252),
            maDev(5), maDev(20), maDev(50), maDev(200),
            volStd(20), volStd(60),
            volRatio, dollarTurnover,
            rsi, high52wRatio,
        )
    }

    /** Sample standard deviation (ddof=1) — matches pandas rolling().std(). */
    private fun sampleStd(values: List<Float>): Float {
        if (values.size < 2) return 0f
        val mean = values.average().toFloat()
        val variance = values.sumOf { ((it - mean) * (it - mean)).toDouble() } / (values.size - 1)
        return kotlin.math.sqrt(variance).toFloat()
    }

    private fun runInference(features: FloatArray): Float? {
        val sess = session ?: return null
        return try {
            val buf = FloatBuffer.wrap(features)
            val shape = longArrayOf(1, features.size.toLong())
            val tensor = OnnxTensor.createTensor(env, buf, shape)
            val result = sess.run(mapOf("input" to tensor))
            val probs = (result[0].value as Array<*>)[0] as FloatArray
            probs[1]  // probability of class 1 (UP)
        } catch (_: Exception) { null }
    }

    private fun stdDev(values: List<Float>): Float {
        if (values.size < 2) return 0f
        val mean = values.average().toFloat()
        val variance = values.sumOf { ((it - mean) * (it - mean)).toDouble() }.toFloat() / values.size
        return sqrt(variance)
    }

    private fun computeRSI(closes: List<Float>, period: Int = 14): Float {
        if (closes.size <= period) return 50f
        var gains = 0f; var losses = 0f
        for (i in 0 until period) {
            val change = closes[i] - closes[i + 1]
            if (change > 0) gains += change else losses -= change
        }
        val avgGain = gains / period
        val avgLoss = losses / period
        if (avgLoss == 0f) return 100f
        val rs = avgGain / avgLoss
        return 100f - (100f / (1f + rs))
    }
}
