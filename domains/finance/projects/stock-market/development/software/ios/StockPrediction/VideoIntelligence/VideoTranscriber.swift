import Foundation
import Speech
import AVFoundation

// MARK: - Errors

enum TranscriptionError: Error, LocalizedError {
    case permissionDenied
    case noSpeechRecognizer
    case transcriptionFailed(String)

    var errorDescription: String? {
        switch self {
        case .permissionDenied:
            return "Speech recognition permission was denied. Please enable it in Settings."
        case .noSpeechRecognizer:
            return "Speech recognizer is not available on this device or locale."
        case .transcriptionFailed(let msg):
            return "Transcription failed: \(msg)"
        }
    }
}

// MARK: - TranscriptionResult

struct TranscriptionResult: Codable {
    let fullText: String
    let chunks: [TranscriptChunk]
    let wordCount: Int
    let language: String
    let modelUsed: String
}

struct TranscriptChunk: Codable {
    let start: Double
    let end: Double
    let text: String
}

// MARK: - VideoTranscriber

// Info.plist keys required:
//   NSSpeechRecognitionUsageDescription — "Used to transcribe YouTube video audio for market signal extraction."
//   NSMicrophoneUsageDescription — "Used to capture audio for live speech recognition."

@MainActor
final class VideoTranscriber: ObservableObject {
    static let shared = VideoTranscriber()

    @Published var isTranscribing = false
    @Published var progress: Double = 0
    @Published var statusMessage = ""

    private let chunkDuration: TimeInterval = 55   // seconds per chunk (safely under 60s SFSpeech limit)
    private init() {}

    // MARK: - Permission

    /// Request speech recognition permission. Returns true if granted.
    func requestPermission() async -> Bool {
        let current = SFSpeechRecognizer.authorizationStatus()
        if current == .authorized { return true }
        if current == .denied || current == .restricted { return false }

        return await withCheckedContinuation { cont in
            SFSpeechRecognizer.requestAuthorization { status in
                cont.resume(returning: status == .authorized)
            }
        }
    }

    // MARK: - Main Transcribe

    /// Transcribe the audio file at `audioURL`, splitting into chunks for long files.
    /// `onProgress` receives (0..1, statusMessage).
    func transcribe(
        audioURL: URL,
        onProgress: @escaping (Double, String) -> Void
    ) async throws -> TranscriptionResult {
        let granted = await requestPermission()
        guard granted else { throw TranscriptionError.permissionDenied }

        guard let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US")),
              recognizer.isAvailable else {
            throw TranscriptionError.noSpeechRecognizer
        }

        isTranscribing = true
        progress = 0
        statusMessage = "Preparing audio…"
        defer {
            isTranscribing = false
            progress = 0
            statusMessage = ""
        }

        // Measure total duration
        let asset = AVURLAsset(url: audioURL)
        let totalDuration: TimeInterval
        do {
            let cmDuration = try await asset.load(.duration)
            totalDuration = CMTimeGetSeconds(cmDuration)
        } catch {
            throw TranscriptionError.transcriptionFailed("Could not read audio duration: \(error.localizedDescription)")
        }

        guard totalDuration > 0 else {
            throw TranscriptionError.transcriptionFailed("Audio file appears to be empty (duration = 0).")
        }

        // Build chunk time ranges
        var chunks: [TranscriptChunk] = []
        var cursor: TimeInterval = 0
        var chunkIndex = 0
        let totalChunks = Int(ceil(totalDuration / chunkDuration))

        while cursor < totalDuration {
            let segStart = cursor
            let segDuration = min(chunkDuration, totalDuration - cursor)
            let segEnd = segStart + segDuration
            chunkIndex += 1

            let progressValue = Double(chunkIndex - 1) / Double(totalChunks)
            let msg = "Transcribing segment \(chunkIndex)/\(totalChunks)…"
            onProgress(progressValue, msg)
            await MainActor.run {
                self.progress = progressValue
                self.statusMessage = msg
            }

            // Export this segment to a temp file
            let segURL = try await exportSegment(
                asset: asset,
                start: segStart,
                duration: segDuration,
                index: chunkIndex
            )
            defer { try? FileManager.default.removeItem(at: segURL) }

            let text = try await transcribeSegment(recognizer: recognizer, audioURL: segURL)
            if !text.isEmpty {
                chunks.append(TranscriptChunk(start: segStart, end: segEnd, text: text))
            }

            cursor += chunkDuration
        }

        onProgress(1.0, "Transcription complete")
        await MainActor.run {
            self.progress = 1.0
            self.statusMessage = "Done"
        }

        let fullText = chunks.map(\.text).joined(separator: " ")
        let wordCount = fullText.split(separator: " ").count

        return TranscriptionResult(
            fullText: fullText,
            chunks: chunks,
            wordCount: wordCount,
            language: "en-US",
            modelUsed: "SFSpeechRecognizer (on-device)"
        )
    }

    // MARK: - Export Segment

    /// Export a time range from `asset` to a temp .m4a file for SFSpeechRecognizer.
    private func exportSegment(
        asset: AVURLAsset,
        start: TimeInterval,
        duration: TimeInterval,
        index: Int
    ) async throws -> URL {
        let tmpDir = FileManager.default.temporaryDirectory
        let segURL = tmpDir.appendingPathComponent("seg_\(index)_\(UUID().uuidString).m4a")

        guard let exportSession = AVAssetExportSession(asset: asset, presetName: AVAssetExportPresetAppleM4A) else {
            throw TranscriptionError.transcriptionFailed("Could not create AVAssetExportSession")
        }

        exportSession.timeRange = CMTimeRange(
            start: CMTime(seconds: start, preferredTimescale: 600),
            duration: CMTime(seconds: duration, preferredTimescale: 600)
        )

        if #available(iOS 18.0, *) {
            do {
                try await exportSession.export(to: segURL, as: .m4a)
            } catch {
                throw TranscriptionError.transcriptionFailed("Export failed for segment \(index): \(error.localizedDescription)")
            }
        } else {
            exportSession.outputURL = segURL
            exportSession.outputFileType = .m4a
            await exportSession.export()
            switch exportSession.status {
            case .completed: break
            case .failed:
                let reason = exportSession.error?.localizedDescription ?? "unknown"
                throw TranscriptionError.transcriptionFailed("Export failed for segment \(index): \(reason)")
            case .cancelled:
                throw TranscriptionError.transcriptionFailed("Export cancelled for segment \(index)")
            default:
                throw TranscriptionError.transcriptionFailed("Export ended with status \(exportSession.status.rawValue)")
            }
        }

        return segURL
    }

    // MARK: - Transcribe One Segment

    /// Transcribe a single audio file using SFSpeechRecognizer.
    private func transcribeSegment(recognizer: SFSpeechRecognizer, audioURL: URL) async throws -> String {
        return try await withCheckedThrowingContinuation { cont in
            let request = SFSpeechURLRecognitionRequest(url: audioURL)
            request.shouldReportPartialResults = false
            request.requiresOnDeviceRecognition = true
            request.taskHint = .dictation

            recognizer.recognitionTask(with: request) { result, error in
                if let error = error {
                    // Treat no-speech as empty string, not a fatal error
                    let nsError = error as NSError
                    if nsError.domain == "kAFAssistantErrorDomain" && nsError.code == 1110 {
                        cont.resume(returning: "")
                    } else {
                        cont.resume(throwing: TranscriptionError.transcriptionFailed(error.localizedDescription))
                    }
                    return
                }
                if let result = result, result.isFinal {
                    cont.resume(returning: result.bestTranscription.formattedString)
                }
            }
        }
    }
}
