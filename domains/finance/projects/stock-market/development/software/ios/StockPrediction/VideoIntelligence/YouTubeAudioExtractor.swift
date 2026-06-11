import Foundation

// MARK: - Errors

enum YouTubeError: Error, LocalizedError {
    case invalidURL
    case pageLoadFailed(String)
    case audioStreamNotFound
    case downloadFailed(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid YouTube URL."
        case .pageLoadFailed(let msg):
            return "Failed to load YouTube page: \(msg)"
        case .audioStreamNotFound:
            return "No audio stream found in this video."
        case .downloadFailed(let msg):
            return "Audio download failed: \(msg)"
        }
    }
}

// MARK: - VideoMetadata

struct VideoMetadata: Codable {
    let videoId: String
    let title: String
    let channelName: String
    let channelId: String
    let publishedAt: String
    let durationSec: Int
    let viewCount: Int
    let thumbnail: String
}

// MARK: - YouTubeAudioExtractor

final class YouTubeAudioExtractor {
    static let shared = YouTubeAudioExtractor()
    private init() {}

    // MARK: - Public API

    /// Extract video metadata without downloading audio.
    func fetchMetadata(url: String) async throws -> VideoMetadata {
        let videoId = try extractVideoId(from: url)
        let (playerResponse, _) = try await fetchPlayerResponse(videoId: videoId)
        return try parseMetadata(from: playerResponse, videoId: videoId)
    }

    /// Extract the best audio stream URL from a YouTube watch page.
    func extractAudioStreamURL(videoURL: String) async throws -> (streamURL: URL, mimeType: String) {
        let videoId = try extractVideoId(from: videoURL)
        let (playerResponse, _) = try await fetchPlayerResponse(videoId: videoId)
        return try bestAudioFormat(from: playerResponse)
    }

    /// Download audio from `streamURL` to a temp file, reporting progress (0..1).
    func downloadAudio(from streamURL: URL, progress: @escaping (Double) -> Void) async throws -> URL {
        let tmpDir = FileManager.default.temporaryDirectory
        let tmpFile = tmpDir.appendingPathComponent(UUID().uuidString + ".webm")

        var request = URLRequest(url: streamURL)
        request.timeoutInterval = 3600

        let (asyncBytes, response) = try await URLSession.shared.bytes(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw YouTubeError.downloadFailed("HTTP \((response as? HTTPURLResponse)?.statusCode ?? -1)")
        }

        let contentLength = httpResponse.expectedContentLength > 0
            ? Int(httpResponse.expectedContentLength)
            : 0

        FileManager.default.createFile(atPath: tmpFile.path, contents: nil)
        let handle = try FileHandle(forWritingTo: tmpFile)
        var buffer = Data(capacity: 512 * 1024)
        var written = 0

        for try await byte in asyncBytes {
            buffer.append(byte)
            if buffer.count >= 512 * 1024 {
                handle.write(buffer)
                written += buffer.count
                if contentLength > 0 {
                    progress(min(Double(written) / Double(contentLength), 0.99))
                }
                buffer.removeAll(keepingCapacity: true)
            }
        }
        if !buffer.isEmpty {
            handle.write(buffer)
            written += buffer.count
        }
        try handle.close()
        progress(1.0)
        return tmpFile
    }

    /// Full pipeline: fetch YouTube page, extract audio stream, download to temp file.
    /// Progress callback receives (0..1, statusMessage).
    func prepareAudio(
        youtubeURL: String,
        progress: @escaping (Double, String) -> Void
    ) async throws -> (audioURL: URL, metadata: VideoMetadata) {
        progress(0.0, "Fetching video info…")
        let videoId = try extractVideoId(from: youtubeURL)
        let (playerResponse, _) = try await fetchPlayerResponse(videoId: videoId)

        progress(0.05, "Parsing metadata…")
        let metadata = try parseMetadata(from: playerResponse, videoId: videoId)

        progress(0.1, "Locating audio stream…")
        let (streamURL, _) = try bestAudioFormat(from: playerResponse)

        progress(0.15, "Downloading audio…")
        let audioURL = try await downloadAudio(from: streamURL) { p in
            progress(0.15 + p * 0.80, "Downloading audio… \(Int(p * 100))%")
        }
        progress(1.0, "Download complete")
        return (audioURL, metadata)
    }

    // MARK: - Private Helpers

    private func extractVideoId(from urlString: String) throws -> String {
        guard let url = URL(string: urlString) else { throw YouTubeError.invalidURL }

        // youtu.be/<id>
        if url.host == "youtu.be" {
            let id = url.pathComponents.dropFirst().first ?? ""
            if !id.isEmpty { return id }
        }

        // youtube.com/watch?v=<id>  or  youtube.com/shorts/<id>
        if let host = url.host, host.contains("youtube.com") {
            if let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
               let v = components.queryItems?.first(where: { $0.name == "v" })?.value,
               !v.isEmpty {
                return v
            }
            // /shorts/<id>  or  /embed/<id>
            let parts = url.pathComponents
            if parts.count >= 2 && (parts[1] == "shorts" || parts[1] == "embed"), parts.count >= 3 {
                return parts[2]
            }
        }
        throw YouTubeError.invalidURL
    }

    private func fetchPlayerResponse(videoId: String) async throws -> ([String: Any], String) {
        // Approach 1: parse embedded ytInitialPlayerResponse from the watch page
        let watchURLStr = "https://www.youtube.com/watch?v=\(videoId)"
        guard let watchURL = URL(string: watchURLStr) else { throw YouTubeError.invalidURL }

        var request = URLRequest(url: watchURL)
        request.setValue(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            + "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
            forHTTPHeaderField: "User-Agent"
        )
        request.setValue("en-US,en;q=0.9", forHTTPHeaderField: "Accept-Language")
        request.timeoutInterval = 30

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResp = response as? HTTPURLResponse, httpResp.statusCode == 200 else {
            throw YouTubeError.pageLoadFailed("HTTP \((response as? HTTPURLResponse)?.statusCode ?? -1)")
        }
        guard let html = String(data: data, encoding: .utf8) else {
            throw YouTubeError.pageLoadFailed("Could not decode page HTML")
        }

        // Extract JSON from: var ytInitialPlayerResponse = {...};
        guard let jsonStr = extractJSONObject(from: html, marker: "ytInitialPlayerResponse = "),
              let jsonData = jsonStr.data(using: .utf8),
              let parsed = try? JSONSerialization.jsonObject(with: jsonData) as? [String: Any] else {
            throw YouTubeError.pageLoadFailed("ytInitialPlayerResponse not found in page")
        }

        return (parsed, html)
    }

    /// Naive but reliable: find the marker, then extract the matching {...} block.
    private func extractJSONObject(from html: String, marker: String) -> String? {
        guard let markerRange = html.range(of: marker) else { return nil }
        let afterMarker = html[markerRange.upperBound...]
        guard let firstBrace = afterMarker.firstIndex(of: "{") else { return nil }
        var depth = 0
        var inString = false
        var escaped = false
        var idx = firstBrace
        while idx < afterMarker.endIndex {
            let ch = afterMarker[idx]
            if escaped { escaped = false }
            else if ch == "\\" && inString { escaped = true }
            else if ch == "\"" { inString.toggle() }
            else if !inString {
                if ch == "{" { depth += 1 }
                else if ch == "}" {
                    depth -= 1
                    if depth == 0 {
                        return String(afterMarker[firstBrace...idx])
                    }
                }
            }
            idx = afterMarker.index(after: idx)
        }
        return nil
    }

    private func parseMetadata(from player: [String: Any], videoId: String) throws -> VideoMetadata {
        let videoDetails = player["videoDetails"] as? [String: Any] ?? [:]
        let title = videoDetails["title"] as? String ?? "Unknown Title"
        let channelName = videoDetails["author"] as? String ?? "Unknown Channel"
        let channelId = videoDetails["channelId"] as? String ?? ""
        let durationSec = Int(videoDetails["lengthSeconds"] as? String ?? "0") ?? 0
        let viewCount = Int(videoDetails["viewCount"] as? String ?? "0") ?? 0

        // Thumbnail
        let thumbnails = ((videoDetails["thumbnail"] as? [String: Any])?["thumbnails"] as? [[String: Any]]) ?? []
        let thumbnail = thumbnails.last?["url"] as? String ?? ""

        // Published date from microformat
        let microformat = (player["microformat"] as? [String: Any])?["playerMicroformatRenderer"] as? [String: Any]
        let publishedAt = microformat?["publishDate"] as? String ?? ""

        return VideoMetadata(
            videoId: videoId,
            title: title,
            channelName: channelName,
            channelId: channelId,
            publishedAt: publishedAt,
            durationSec: durationSec,
            viewCount: viewCount,
            thumbnail: thumbnail
        )
    }

    private func bestAudioFormat(from player: [String: Any]) throws -> (URL, String) {
        guard let streamingData = player["streamingData"] as? [String: Any],
              let adaptiveFormats = streamingData["adaptiveFormats"] as? [[String: Any]] else {
            throw YouTubeError.audioStreamNotFound
        }

        // Filter to audio-only formats
        let audioFormats = adaptiveFormats.filter { fmt in
            let mime = (fmt["mimeType"] as? String ?? "").lowercased()
            return mime.contains("audio/")
        }
        guard !audioFormats.isEmpty else { throw YouTubeError.audioStreamNotFound }

        // Prefer opus/webm for size, then any audio; sort by bitrate descending
        let sorted = audioFormats.sorted { a, b in
            let aBitrate = a["averageBitrate"] as? Int ?? a["bitrate"] as? Int ?? 0
            let bBitrate = b["averageBitrate"] as? Int ?? b["bitrate"] as? Int ?? 0
            let aOpus = ((a["mimeType"] as? String) ?? "").contains("opus") ? 1 : 0
            let bOpus = ((b["mimeType"] as? String) ?? "").contains("opus") ? 1 : 0
            if aOpus != bOpus { return aOpus > bOpus }
            return aBitrate > bBitrate
        }

        guard let best = sorted.first,
              let urlString = best["url"] as? String,
              let streamURL = URL(string: urlString) else {
            throw YouTubeError.audioStreamNotFound
        }

        let mimeType = best["mimeType"] as? String ?? "audio/webm"
        return (streamURL, mimeType)
    }
}
