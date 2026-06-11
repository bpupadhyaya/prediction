package com.prediction.stockmarket.videointelligence

import com.prediction.stockmarket.data.database.*

import android.util.Log
import com.prediction.stockmarket.prediction.LLMInferenceEngine
import kotlinx.coroutines.flow.toList
import org.json.JSONArray
import org.json.JSONException
import java.util.Date
import java.util.UUID

private const val TAG = "VideoSignalExtractor"

class VideoSignalExtractor(private val llmEngine: LLMInferenceEngine) {

    /**
     * Extracts market signals from a video transcript using the on-device LLM.
     *
     * Sends the transcript + metadata to the LLM with a structured system prompt
     * asking for a JSON array of signals. Parses and returns [VideoSignalEntity] list.
     */
    suspend fun extractSignals(
        transcript: String,
        title: String,
        channel: String,
        videoId: String
    ): List<VideoSignalEntity> {
        if (!llmEngine.isReady) {
            Log.w(TAG, "LLM not ready — cannot extract signals")
            return emptyList()
        }

        val systemPrompt = buildSystemPrompt()
        val userMessage = buildUserMessage(transcript, title, channel)

        val tokens = llmEngine.chat(systemPrompt, userMessage).toList()
        val rawResponse = tokens.joinToString("")

        return parseSignals(rawResponse, videoId)
    }

    // -------------------------------------------------------------------------
    // Prompt construction
    // -------------------------------------------------------------------------

    private fun buildSystemPrompt(): String = """
You are a financial market intelligence analyst. Your task is to extract actionable market signals
from video transcripts of financial commentary, earnings calls, analyst discussions, and expert interviews.

Extract signals ONLY when there is a clear, specific statement about a market direction, stock,
sector, or economic indicator. Do not invent or hallucinate signals.

Output a JSON array (and nothing else — no markdown fences, no preamble) with this exact schema:
[
  {
    "ticker": "AAPL or null if no specific ticker",
    "domain": "one of: equity, crypto, macro, sector, commodity, forex, rates, sentiment",
    "parameter_name": "short name of the market parameter (e.g., 'revenue_growth', 'fed_rate', 'bitcoin_price')",
    "direction": "up or down",
    "weight": 75,
    "confidence": 0.82,
    "key_quote": "direct quote from transcript supporting this signal"
  }
]

Rules:
- weight is 0–100 representing signal strength/importance
- confidence is 0.0–1.0 representing how certain the speaker sounds
- If no actionable signals found, return an empty array: []
- Maximum 10 signals per transcript
- key_quote must be a verbatim excerpt (≤ 200 chars) from the transcript
""".trimIndent()

    private fun buildUserMessage(transcript: String, title: String, channel: String): String {
        // Truncate transcript to avoid token overflow (approx 3000 chars)
        val truncatedTranscript = if (transcript.length > 3000) {
            transcript.take(3000) + "… [transcript truncated]"
        } else {
            transcript
        }

        return """
Video: "$title"
Channel: $channel

Transcript:
$truncatedTranscript

Extract market signals from this transcript. Return JSON array only.
""".trimIndent()
    }

    // -------------------------------------------------------------------------
    // Response parsing
    // -------------------------------------------------------------------------

    private fun parseSignals(rawResponse: String, videoId: String): List<VideoSignalEntity> {
        val jsonStr = extractJsonArray(rawResponse)
        if (jsonStr.isNullOrBlank()) {
            Log.w(TAG, "No JSON array found in LLM response for video $videoId")
            return emptyList()
        }

        return try {
            val array = JSONArray(jsonStr)
            val signals = mutableListOf<VideoSignalEntity>()
            val now = Date()

            for (i in 0 until array.length()) {
                val obj = array.getJSONObject(i)
                try {
                    val direction = obj.optString("direction", "").lowercase()
                    if (direction !in listOf("up", "down")) {
                        Log.w(TAG, "Skipping signal with invalid direction: $direction")
                        continue
                    }

                    val weight = obj.optInt("weight", 50).coerceIn(0, 100)
                    val confidence = obj.optDouble("confidence", 0.5).coerceIn(0.0, 1.0)
                    val ticker = obj.optString("ticker", "").takeIf { it.isNotBlank() && it != "null" }
                    val domain = obj.optString("domain", "equity").lowercase()
                    val paramName = obj.optString("parameter_name", "unknown")
                    val keyQuote = obj.optString("key_quote", "").take(500)

                    if (paramName.isBlank() || keyQuote.isBlank()) continue

                    signals.add(
                        VideoSignalEntity(
                            id = UUID.randomUUID().toString(),
                            videoId = videoId,
                            ticker = ticker,
                            parameterName = paramName,
                            domain = domain,
                            direction = direction,
                            weight = weight,
                            confidence = confidence,
                            keyQuote = keyQuote,
                            extractedAt = now
                        )
                    )
                } catch (e: JSONException) {
                    Log.w(TAG, "Skipping malformed signal at index $i: ${e.message}")
                }
            }

            Log.i(TAG, "Extracted ${signals.size} signals from video $videoId")
            signals
        } catch (e: JSONException) {
            Log.e(TAG, "Failed to parse signals JSON: ${e.message}\nRaw: ${jsonStr.take(200)}")
            emptyList()
        }
    }

    /**
     * Extracts the first JSON array `[...]` found in [text].
     * Handles cases where the LLM wraps the array in markdown code fences or adds preamble text.
     */
    private fun extractJsonArray(text: String): String? {
        // Strip markdown code fences if present
        val cleaned = text
            .replace(Regex("```json\\s*"), "")
            .replace(Regex("```\\s*"), "")
            .trim()

        val startIdx = cleaned.indexOf('[')
        if (startIdx == -1) return null

        var depth = 0
        var inString = false
        var escape = false

        for (i in startIdx until cleaned.length) {
            val ch = cleaned[i]
            when {
                escape -> escape = false
                ch == '\\' && inString -> escape = true
                ch == '"' -> inString = !inString
                !inString && ch == '[' -> depth++
                !inString && ch == ']' -> {
                    depth--
                    if (depth == 0) return cleaned.substring(startIdx, i + 1)
                }
            }
        }
        return null
    }
}
