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
        val vol = stdDev(prices.take(20).map { it.adjClose.toFloat() })

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

    private fun buildFeatures(prices: List<PriceBarEntity>): FloatArray? {
        if (prices.size < 50) return null
        val closes = prices.map { it.adjClose.toFloat() }
        val volumes = prices.map { it.volume.toFloat() }

        val ret1 = (closes[0] - closes[1]) / closes[1]
        val ret5 = (closes[0] - closes[5]) / closes[5]
        val ret20 = (closes[0] - closes[20]) / closes[20]
        val ma5 = closes.take(5).average().toFloat()
        val ma20 = closes.take(20).average().toFloat()
        val ma50 = closes.take(50).average().toFloat()
        val vol20 = stdDev(closes.take(20))
        val avgVol = volumes.take(20).average().toFloat()
        val volRatio = if (avgVol > 0) volumes[0] / avgVol else 1f
        val rsi = computeRSI(closes.take(15))

        return floatArrayOf(ret1, ret5, ret20, closes[0] / ma5, closes[0] / ma20,
            closes[0] / ma50, vol20, volRatio, rsi)
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
