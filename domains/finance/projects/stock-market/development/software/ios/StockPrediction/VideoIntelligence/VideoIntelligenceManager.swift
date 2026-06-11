import Foundation
import GRDB

// MARK: - ProcessingStatus

enum ProcessingStatus: Equatable {
    case queued
    case downloading
    case transcribing
    case extracting
    case done
    case failed(String)

    var displayLabel: String {
        switch self {
        case .queued:       return "Queued"
        case .downloading:  return "Downloading"
        case .transcribing: return "Transcribing"
        case .extracting:   return "Extracting Signals"
        case .done:         return "Done"
        case .failed(let m): return "Failed: \(m)"
        }
    }

    var isFinal: Bool {
        switch self {
        case .done, .failed: return true
        default: return false
        }
    }
}

// MARK: - ProcessingJob

struct ProcessingJob: Identifiable {
    let id: String          // same as videoId
    var videoId: String
    var status: ProcessingStatus
    var progress: Double
    var statusMessage: String
    var startedAt: Date
}

// MARK: - VideoIntelligenceManager

@MainActor
final class VideoIntelligenceManager: ObservableObject {
    static let shared = VideoIntelligenceManager()

    @Published var processingJobs: [String: ProcessingJob] = [:]    // videoId → job
    @Published var recentVideos: [VideoSourceRecord] = []
    @Published var recentSignals: [VideoSignalRecord] = []
    @Published var errorMessage: String? = nil

    private init() {
        Task { await loadRecent() }
    }

    // MARK: - Process YouTube URL

    /// End-to-end pipeline: download audio → transcribe → extract signals → persist.
    func processURL(_ url: String, modelOverride: String? = nil) async {
        let sanitized = url.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !sanitized.isEmpty else {
            errorMessage = "Please enter a YouTube URL."
            return
        }

        // Derive a provisional videoId for the job key before we have metadata
        let provisionalId = UUID().uuidString
        var job = ProcessingJob(
            id: provisionalId,
            videoId: provisionalId,
            status: .queued,
            progress: 0,
            statusMessage: "Starting…",
            startedAt: Date()
        )
        processingJobs[provisionalId] = job

        do {
            // 1. Download audio + fetch metadata
            job.status = .downloading
            job.statusMessage = "Fetching video info…"
            processingJobs[provisionalId] = job

            let (audioURL, metadata) = try await YouTubeAudioExtractor.shared.prepareAudio(
                youtubeURL: sanitized
            ) { progress, msg in
                Task { @MainActor [weak self] in
                    guard let self else { return }
                    var j = self.processingJobs[provisionalId] ?? job
                    j.progress = progress * 0.45
                    j.statusMessage = msg
                    self.processingJobs[provisionalId] = j
                }
            }

            // Persist video source record
            let videoRecord = VideoSourceRecord(
                id: metadata.videoId,
                url: sanitized,
                videoId: metadata.videoId,
                title: metadata.title,
                channelName: metadata.channelName,
                channelId: metadata.channelId,
                speakerName: "",
                publishedAt: metadata.publishedAt,
                durationSec: metadata.durationSec,
                viewCount: metadata.viewCount,
                status: "transcribing",
                errorMsg: nil,
                transcriptModel: nil,
                fullText: nil,
                createdAt: Date()
            )
            try? DatabaseManager.shared.saveVideoSource(videoRecord)

            // Remap job key to real videoId
            processingJobs.removeValue(forKey: provisionalId)
            job = ProcessingJob(
                id: metadata.videoId,
                videoId: metadata.videoId,
                status: .transcribing,
                progress: 0.45,
                statusMessage: "Starting transcription…",
                startedAt: job.startedAt
            )
            processingJobs[metadata.videoId] = job
            let realId = metadata.videoId

            // 2. Transcribe
            job.status = .transcribing
            processingJobs[realId] = job

            let result = try await VideoTranscriber.shared.transcribe(audioURL: audioURL) { progress, msg in
                Task { @MainActor [weak self] in
                    guard let self else { return }
                    var j = self.processingJobs[realId] ?? job
                    j.progress = 0.45 + progress * 0.35
                    j.statusMessage = msg
                    self.processingJobs[realId] = j
                }
            }

            // Clean up audio temp file
            try? FileManager.default.removeItem(at: audioURL)

            // Update DB with transcript
            try? DatabaseManager.shared.updateVideoSourceStatus(
                id: realId,
                status: "extracting",
                errorMsg: nil,
                fullText: result.fullText
            )

            // 3. Extract signals
            job.status = .extracting
            job.progress = 0.80
            job.statusMessage = "Extracting market signals…"
            processingJobs[realId] = job

            let signals = try await VideoSignalExtractor.shared.extractSignals(
                transcript: result.fullText,
                title: metadata.title,
                channel: metadata.channelName,
                videoId: realId
            )

            try? DatabaseManager.shared.saveVideoSignals(signals)

            // Update DB status to done
            try? DatabaseManager.shared.updateVideoSourceStatus(
                id: realId,
                status: "done",
                errorMsg: nil,
                fullText: result.fullText
            )

            // 4. Mark done
            job.status = .done
            job.progress = 1.0
            job.statusMessage = "Done — \(signals.count) signal(s) extracted"
            processingJobs[realId] = job

            await loadRecent()

            // Remove completed job after a short delay
            try? await Task.sleep(nanoseconds: 4_000_000_000)
            processingJobs.removeValue(forKey: realId)

        } catch {
            let errMsg = error.localizedDescription
            job.status = .failed(errMsg)
            job.statusMessage = errMsg
            processingJobs[provisionalId] = job
            errorMessage = errMsg

            // Clean up if we have a real video id
            // (best-effort — we may not have it)
        }
    }

    // MARK: - Load Recent

    func loadRecent() async {
        do {
            recentVideos = try DatabaseManager.shared.getVideoSources(limit: 20)
            recentSignals = try DatabaseManager.shared.getVideoSignals(ticker: nil, days: 30)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Query Signals

    func querySignals(ticker: String?, days: Int) async -> [VideoSignalRecord] {
        do {
            return try DatabaseManager.shared.getVideoSignals(ticker: ticker, days: days)
        } catch {
            errorMessage = error.localizedDescription
            return []
        }
    }

    // MARK: - Apply Signal to Prediction

    /// Saves a video-derived signal record to the local database for use in predictions.
    func applySignalToPrediction(_ signal: VideoSignalRecord) async {
        // Persist the applied signal — future prediction engine will read from video_signals
        // filtered by extractedAt to incorporate it automatically.
        // For now we re-save (upsert-like behaviour) with updated extractedAt to
        // float it to the top of signal priority.
        var updated = signal
        updated.extractedAt = Date()
        do {
            try DatabaseManager.shared.saveVideoSignals([updated])
            await loadRecent()
        } catch {
            errorMessage = "Failed to apply signal: \(error.localizedDescription)"
        }
    }

    // MARK: - Channel Tracking

    func trackChannel(_ channelId: String, name: String, speaker: String) async {
        let record = ChannelTrackRecord(
            channelId: channelId,
            channelName: name,
            speakerName: speaker,
            autoProcess: true,
            timeRangeYears: 5,
            createdAt: Date()
        )
        do {
            try DatabaseManager.shared.saveChannelTrack(record)
        } catch {
            errorMessage = "Failed to save channel: \(error.localizedDescription)"
        }
    }

    func getTrackedChannels() async -> [ChannelTrackRecord] {
        do {
            return try DatabaseManager.shared.getChannelTracks()
        } catch {
            errorMessage = error.localizedDescription
            return []
        }
    }

    func removeTrackedChannel(_ channelId: String) async {
        do {
            try DatabaseManager.shared.removeChannelTrack(channelId: channelId)
        } catch {
            errorMessage = "Failed to remove channel: \(error.localizedDescription)"
        }
    }
}
