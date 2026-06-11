package com.prediction.stockmarket.videointelligence

import android.content.Context
import android.util.Log
import com.prediction.stockmarket.data.database.AppDatabase
import com.prediction.stockmarket.prediction.LLMInferenceEngine
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.Date
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

private const val TAG = "VideoIntelligenceManager"

data class ProcessingJob(
    val videoId: String,
    val url: String,
    var status: JobStatus,
    var progress: Float,
    var statusMessage: String,
    val startedAt: Long = System.currentTimeMillis()
)

enum class JobStatus { QUEUED, DOWNLOADING, TRANSCRIBING, EXTRACTING, DONE, FAILED }

/**
 * Pre-seeded list of influential financial speakers with their YouTube channel IDs.
 * Users can add/remove from this list in the app.
 */
val INFLUENTIAL_SPEAKERS = listOf(
    "UCEb7pOMZ5h3MdqN7fYPD5mw" to "Elon Musk",
    "UCIRYBXDze5krPDzAEOxFGVA" to "Warren Buffett",
    "UCTk_-XgFDfSf6EGpJQJhRdA" to "Jerome Powell",
    "UCeeFfhMcJa1kjtfZAGskOCA" to "Jensen Huang",
    "UCE_M8A5yxnLfW0KghEeajjw" to "Tim Cook",
    "UCimKczFRuRUKPPHarX6v_jQ" to "Cathie Wood",
    "UCFiJ9iqkIEYQlFa_WJyRGqQ" to "Jim Cramer",
    "UCVHVFAm24e5i3kEi0IG3ItQ" to "Michael Saylor",
)

@Singleton
class VideoIntelligenceManager @Inject constructor(
    private val context: Context,
    private val database: AppDatabase,
    private val okHttpClient: okhttp3.OkHttpClient,
    private val llmEngine: LLMInferenceEngine
) {
    private val audioExtractor = YouTubeAudioExtractor(okHttpClient)
    private val transcriber = VideoTranscriber(context)
    private val signalExtractor = VideoSignalExtractor(llmEngine)

    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    private val _jobs = MutableStateFlow<Map<String, ProcessingJob>>(emptyMap())
    val jobs: StateFlow<Map<String, ProcessingJob>> = _jobs.asStateFlow()

    // -------------------------------------------------------------------------
    // URL processing pipeline
    // -------------------------------------------------------------------------

    /**
     * Kicks off the full YVIS pipeline for a YouTube URL:
     * 1. Download audio
     * 2. Transcribe
     * 3. Extract market signals
     * 4. Persist to Room
     */
    fun processUrl(url: String) {
        val videoId = audioExtractor.extractVideoId(url) ?: run {
            Log.w(TAG, "Cannot extract video ID from URL: $url")
            return
        }

        if (_jobs.value.containsKey(videoId)) {
            val existing = _jobs.value[videoId]
            if (existing?.status in listOf(JobStatus.QUEUED, JobStatus.DOWNLOADING, JobStatus.TRANSCRIBING, JobStatus.EXTRACTING)) {
                Log.i(TAG, "Job for $videoId already in progress — skipping")
                return
            }
        }

        val job = ProcessingJob(
            videoId = videoId,
            url = url,
            status = JobStatus.QUEUED,
            progress = 0f,
            statusMessage = "Queued"
        )
        updateJob(videoId, job)

        scope.launch {
            runPipeline(url, videoId)
        }
    }

    private suspend fun runPipeline(url: String, videoId: String) {
        val cacheDir = context.cacheDir

        try {
            // Phase 1: Download audio
            updateJob(videoId) { it.copy(status = JobStatus.DOWNLOADING, statusMessage = "Fetching video…") }

            val (audioFile, metadata) = audioExtractor.prepareAudio(url, cacheDir) { progress, msg ->
                updateJob(videoId) { j ->
                    j.copy(progress = progress * 0.4f, statusMessage = msg)
                }
            }

            // Persist initial VideoSource record
            val sourceId = UUID.randomUUID().toString()
            database.videoSourceDao().upsert(
                VideoSourceEntity(
                    id = sourceId,
                    url = url,
                    videoId = videoId,
                    title = metadata.title,
                    channelName = metadata.channelName,
                    channelId = metadata.channelId,
                    speakerName = "",
                    publishedAt = metadata.publishedAt,
                    durationSec = metadata.durationSec,
                    viewCount = metadata.viewCount,
                    status = "transcribing",
                    errorMsg = null,
                    transcriptModel = null,
                    fullText = null,
                    createdAt = Date()
                )
            )

            // Phase 2: Transcribe
            updateJob(videoId) { it.copy(status = JobStatus.TRANSCRIBING, progress = 0.4f, statusMessage = "Transcribing audio…") }

            val transcriptionResult = transcriber.transcribe(audioFile) { progress, msg ->
                updateJob(videoId) { j ->
                    j.copy(progress = 0.4f + progress * 0.4f, statusMessage = msg)
                }
            }

            // Update source with transcript
            database.videoSourceDao().updateStatus(
                id = sourceId,
                status = "extracting",
                errorMsg = null,
                fullText = transcriptionResult.fullText
            )

            // Phase 3: Extract signals
            updateJob(videoId) { it.copy(status = JobStatus.EXTRACTING, progress = 0.8f, statusMessage = "Extracting market signals…") }

            val signals = signalExtractor.extractSignals(
                transcript = transcriptionResult.fullText,
                title = metadata.title,
                channel = metadata.channelName,
                videoId = sourceId
            )

            if (signals.isNotEmpty()) {
                database.videoSignalDao().insertAll(signals)
            }

            // Finalize
            database.videoSourceDao().updateStatus(
                id = sourceId,
                status = "done",
                errorMsg = null,
                fullText = transcriptionResult.fullText
            )

            updateJob(videoId) {
                it.copy(
                    status = JobStatus.DONE,
                    progress = 1f,
                    statusMessage = "Done — ${signals.size} signals extracted"
                )
            }

            Log.i(TAG, "Pipeline complete for $videoId: ${signals.size} signals")

            // Clean up cached audio file to free space
            audioFile.delete()

        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            Log.e(TAG, "Pipeline failed for $videoId: ${e.message}", e)
            updateJob(videoId) { it.copy(status = JobStatus.FAILED, statusMessage = "Error: ${e.message}") }
        }
    }

    // -------------------------------------------------------------------------
    // Query methods
    // -------------------------------------------------------------------------

    suspend fun querySignals(ticker: String?, days: Int): List<VideoSignalEntity> {
        val cutoff = Date(System.currentTimeMillis() - days.toLong() * 24 * 60 * 60 * 1000)
        return database.videoSignalDao().querySignals(
            ticker = ticker?.takeIf { it.isNotBlank() },
            cutoff = cutoff
        )
    }

    suspend fun applySignal(signal: VideoSignalEntity) {
        // Mark signal as applied — in a full implementation this would update
        // the PredictionEngine with the extracted weight/direction for the ticker.
        Log.i(TAG, "Applying signal: ticker=${signal.ticker}, dir=${signal.direction}, weight=${signal.weight}")
        // Future: database.predictionDao().adjustWithSignal(signal)
    }

    suspend fun getRecentVideos(limit: Int = 20): List<VideoSourceEntity> =
        database.videoSourceDao().getRecent(limit)

    // -------------------------------------------------------------------------
    // Channel tracking
    // -------------------------------------------------------------------------

    suspend fun trackChannel(channelId: String, name: String, speaker: String) {
        database.channelTrackDao().upsert(
            ChannelTrackEntity(
                channelId = channelId,
                channelName = name,
                speakerName = speaker,
                autoProcess = true,
                timeRangeYears = 1,
                createdAt = Date()
            )
        )
        Log.i(TAG, "Tracking channel: $name ($channelId)")
    }

    suspend fun getTrackedChannels(): List<ChannelTrackEntity> =
        database.channelTrackDao().getAll()

    suspend fun removeTrackedChannel(channelId: String) {
        database.channelTrackDao().remove(channelId)
        Log.i(TAG, "Removed channel tracking: $channelId")
    }

    // -------------------------------------------------------------------------
    // Whisper model info
    // -------------------------------------------------------------------------

    fun getWhisperModels(): List<WhisperModelInfo> = WHISPER_MODELS.map { m ->
        m  // Downloaded status is checked via VideoTranscriber.isModelDownloaded()
    }

    fun isWhisperModelDownloaded(modelId: String): Boolean =
        transcriber.isModelDownloaded(modelId)

    suspend fun downloadWhisperModel(
        modelId: String,
        onProgress: (Float, String) -> Unit
    ) = transcriber.downloadModel(modelId, onProgress)

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    private fun updateJob(videoId: String, update: (ProcessingJob) -> ProcessingJob) {
        val current = _jobs.value.toMutableMap()
        val existing = current[videoId] ?: return
        current[videoId] = update(existing)
        _jobs.value = current
    }

    private fun updateJob(videoId: String, job: ProcessingJob) {
        val current = _jobs.value.toMutableMap()
        current[videoId] = job
        _jobs.value = current
    }
}
