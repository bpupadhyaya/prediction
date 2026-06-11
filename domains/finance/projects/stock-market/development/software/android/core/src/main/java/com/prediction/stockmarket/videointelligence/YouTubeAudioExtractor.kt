package com.prediction.stockmarket.videointelligence

// NOTE: The app must declare <uses-permission android:name="android.permission.INTERNET"/>
// in AndroidManifest.xml for all network operations in this file.

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.net.URLDecoder

private const val TAG = "YouTubeAudioExtractor"

data class VideoMetadata(
    val videoId: String,
    val title: String,
    val channelName: String,
    val channelId: String,
    val publishedAt: String,
    val durationSec: Int,
    val viewCount: Long,
    val thumbnail: String
)

class YouTubeAudioExtractor(private val client: OkHttpClient) {

    // -------------------------------------------------------------------------
    // Public API
    // -------------------------------------------------------------------------

    fun extractVideoId(url: String): String? {
        val patterns = listOf(
            Regex("""[?&]v=([a-zA-Z0-9_-]{11})"""),
            Regex("""youtu\.be/([a-zA-Z0-9_-]{11})"""),
            Regex("""youtube\.com/embed/([a-zA-Z0-9_-]{11})"""),
            Regex("""youtube\.com/shorts/([a-zA-Z0-9_-]{11})""")
        )
        for (pattern in patterns) {
            val match = pattern.find(url)
            if (match != null) return match.groupValues[1]
        }
        return null
    }

    suspend fun fetchMetadata(videoUrl: String): VideoMetadata = withContext(Dispatchers.IO) {
        val videoId = extractVideoId(videoUrl)
            ?: throw IllegalArgumentException("Cannot extract video ID from URL: $videoUrl")
        val html = fetchPageHtml("https://www.youtube.com/watch?v=$videoId")
        val playerResponse = extractPlayerResponse(html)
        parseMetadata(videoId, playerResponse)
    }

    suspend fun extractAudioStreamUrl(videoUrl: String): Pair<String, String> =
        withContext(Dispatchers.IO) {
            val videoId = extractVideoId(videoUrl)
                ?: throw IllegalArgumentException("Cannot extract video ID from URL: $videoUrl")
            val html = fetchPageHtml("https://www.youtube.com/watch?v=$videoId")
            val playerResponse = extractPlayerResponse(html)
            findBestAudioStream(playerResponse)
        }

    suspend fun downloadAudio(
        streamUrl: String,
        outputFile: File,
        onProgress: (Float) -> Unit
    ) = withContext(Dispatchers.IO) {
        val request = Request.Builder()
            .url(streamUrl)
            .header("User-Agent", BROWSER_UA)
            .header("Referer", "https://www.youtube.com/")
            .build()

        client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) {
                throw Exception("Audio download failed: HTTP ${response.code}")
            }
            val body = response.body ?: throw Exception("Empty audio response body")
            val totalBytes = body.contentLength()
            var downloaded = 0L

            outputFile.parentFile?.mkdirs()
            val tmp = File(outputFile.parent, "${outputFile.name}.tmp")

            FileOutputStream(tmp).use { out ->
                val buffer = ByteArray(256 * 1024) // 256 KB chunks
                body.byteStream().use { input ->
                    var bytesRead: Int
                    while (input.read(buffer).also { bytesRead = it } != -1) {
                        out.write(buffer, 0, bytesRead)
                        downloaded += bytesRead
                        if (totalBytes > 0) {
                            onProgress(downloaded.toFloat() / totalBytes.toFloat())
                        }
                    }
                }
            }
            tmp.renameTo(outputFile)
            Log.i(TAG, "Audio downloaded: ${outputFile.absolutePath} (${downloaded} bytes)")
        }
    }

    /**
     * Full pipeline: fetch metadata + audio stream, download audio to cache, return
     * the audio file and metadata. Calls [onProgress] with (0..1, statusMessage).
     */
    suspend fun prepareAudio(
        youtubeUrl: String,
        cacheDir: File,
        onProgress: (Float, String) -> Unit
    ): Pair<File, VideoMetadata> = withContext(Dispatchers.IO) {
        onProgress(0.02f, "Fetching video info…")
        val videoId = extractVideoId(youtubeUrl)
            ?: throw IllegalArgumentException("Invalid YouTube URL")

        val html = fetchPageHtml("https://www.youtube.com/watch?v=$videoId")
        onProgress(0.10f, "Parsing video metadata…")

        val playerResponse = extractPlayerResponse(html)
        val metadata = parseMetadata(videoId, playerResponse)
        onProgress(0.20f, "Extracting audio stream…")

        val (streamUrl, _) = findBestAudioStream(playerResponse)
        onProgress(0.25f, "Downloading audio…")

        val audioFile = File(cacheDir, "audio_$videoId.webm")
        if (!audioFile.exists()) {
            downloadAudio(streamUrl, audioFile) { dlProgress ->
                // Map download progress to 25%–90% of overall progress
                onProgress(0.25f + dlProgress * 0.65f, "Downloading audio… %.0f%%".format(dlProgress * 100))
            }
        } else {
            Log.i(TAG, "Using cached audio file for $videoId")
        }
        onProgress(0.90f, "Audio ready")

        Pair(audioFile, metadata)
    }

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    private fun fetchPageHtml(url: String): String {
        val request = Request.Builder()
            .url(url)
            .header("User-Agent", BROWSER_UA)
            .header("Accept-Language", "en-US,en;q=0.9")
            .header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
            .build()

        return client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) throw Exception("HTTP ${response.code} fetching $url")
            response.body?.string() ?: throw Exception("Empty HTML body")
        }
    }

    private fun extractPlayerResponse(html: String): JSONObject {
        // Extract the ytInitialPlayerResponse JSON object from the page HTML
        val pattern = Regex("""ytInitialPlayerResponse\s*=\s*(\{.+?\});\s*(?:var |window\[|</script)""")
        val match = pattern.find(html)
            ?: run {
                // Fallback: try broader match
                val fallback = Regex("""ytInitialPlayerResponse\s*=\s*(\{""")
                val start = fallback.find(html) ?: throw Exception("ytInitialPlayerResponse not found in page")
                val startIdx = start.groups[1]!!.range.first
                // Find matching closing brace
                extractJsonObject(html, startIdx)?.let {
                    return@run object {
                        val groupValues = listOf("", it)
                    }
                } ?: throw Exception("Could not parse ytInitialPlayerResponse JSON")
            }

        return try {
            JSONObject(match.groupValues[1])
        } catch (e: Exception) {
            // Try with the broad extractor
            val fallbackPattern = Regex("""ytInitialPlayerResponse\s*=\s*(\{""")
            val startMatch = fallbackPattern.find(html) ?: throw Exception("ytInitialPlayerResponse parse failed")
            val jsonStr = extractJsonObject(html, startMatch.groups[1]!!.range.first)
                ?: throw Exception("Cannot extract ytInitialPlayerResponse: ${e.message}")
            JSONObject(jsonStr)
        }
    }

    private fun extractJsonObject(source: String, startIdx: Int): String? {
        var depth = 0
        var inString = false
        var escape = false
        var i = startIdx
        while (i < source.length) {
            val ch = source[i]
            when {
                escape -> escape = false
                ch == '\\' && inString -> escape = true
                ch == '"' -> inString = !inString
                !inString && ch == '{' -> depth++
                !inString && ch == '}' -> {
                    depth--
                    if (depth == 0) return source.substring(startIdx, i + 1)
                }
            }
            i++
        }
        return null
    }

    private fun parseMetadata(videoId: String, playerResponse: JSONObject): VideoMetadata {
        val details = playerResponse.optJSONObject("videoDetails") ?: JSONObject()

        val title = details.optString("title", "Unknown Title")
        val channelName = details.optString("author", "Unknown Channel")
        val channelId = details.optString("channelId", "")
        val durationSec = details.optString("lengthSeconds", "0").toIntOrNull() ?: 0
        val viewCount = details.optString("viewCount", "0").toLongOrNull() ?: 0L

        // Thumbnail: pick highest resolution available
        val thumbArray = details
            .optJSONObject("thumbnail")
            ?.optJSONArray("thumbnails")
        val thumbnail = if (thumbArray != null && thumbArray.length() > 0) {
            thumbArray.getJSONObject(thumbArray.length() - 1).optString("url", "")
        } else {
            "https://img.youtube.com/vi/$videoId/hqdefault.jpg"
        }

        // Published date from microformat
        val publishedAt = playerResponse
            .optJSONObject("microformat")
            ?.optJSONObject("playerMicroformatRenderer")
            ?.optString("publishDate", "") ?: ""

        return VideoMetadata(
            videoId = videoId,
            title = title,
            channelName = channelName,
            channelId = channelId,
            publishedAt = publishedAt,
            durationSec = durationSec,
            viewCount = viewCount,
            thumbnail = thumbnail
        )
    }

    private fun findBestAudioStream(playerResponse: JSONObject): Pair<String, String> {
        val streamingData = playerResponse.optJSONObject("streamingData")
            ?: throw Exception("No streamingData in player response")

        val adaptiveFormats: JSONArray = streamingData.optJSONArray("adaptiveFormats")
            ?: throw Exception("No adaptiveFormats found")

        data class AudioFormat(
            val url: String,
            val mimeType: String,
            val bitrate: Int
        )

        val audioFormats = mutableListOf<AudioFormat>()

        for (i in 0 until adaptiveFormats.length()) {
            val fmt = adaptiveFormats.getJSONObject(i)
            val mimeType = fmt.optString("mimeType", "")
            if (!mimeType.startsWith("audio/")) continue

            val bitrate = fmt.optInt("bitrate", 0)
            val url = fmt.optString("url", "")
            if (url.isNotEmpty()) {
                audioFormats.add(AudioFormat(url, mimeType, bitrate))
            } else {
                // Handle cipher/signatureCipher (simplified — URL may require decoding)
                val cipher = fmt.optString("signatureCipher", fmt.optString("cipher", ""))
                if (cipher.isNotEmpty()) {
                    val cipherUrl = parseCipherUrl(cipher)
                    if (cipherUrl.isNotEmpty()) {
                        audioFormats.add(AudioFormat(cipherUrl, mimeType, bitrate))
                    }
                }
            }
        }

        if (audioFormats.isEmpty()) throw Exception("No audio streams found")

        // Prefer webm/opus at highest bitrate, fallback to any audio
        val best = audioFormats
            .sortedByDescending { it.bitrate }
            .firstOrNull() ?: audioFormats.first()

        Log.i(TAG, "Selected audio stream: mimeType=${best.mimeType}, bitrate=${best.bitrate}")
        return Pair(best.url, best.mimeType)
    }

    private fun parseCipherUrl(cipher: String): String {
        return try {
            val params = cipher.split("&").associate { part ->
                val idx = part.indexOf('=')
                if (idx == -1) part to "" else part.substring(0, idx) to URLDecoder.decode(part.substring(idx + 1), "UTF-8")
            }
            params["url"] ?: ""
        } catch (e: Exception) {
            Log.w(TAG, "Failed to parse cipher URL: ${e.message}")
            ""
        }
    }

    companion object {
        private const val BROWSER_UA =
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    }
}
