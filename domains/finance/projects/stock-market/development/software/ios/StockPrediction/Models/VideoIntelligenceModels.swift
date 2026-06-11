import Foundation
import GRDB

// MARK: - VideoSourceRecord

struct VideoSourceRecord: Codable, FetchableRecord, PersistableRecord {
    static let databaseTableName = "video_sources"

    var id: String
    var url: String
    var videoId: String
    var title: String
    var channelName: String
    var channelId: String
    var speakerName: String
    var publishedAt: String
    var durationSec: Int
    var viewCount: Int
    var status: String          // pending / transcribing / extracting / done / error
    var errorMsg: String?
    var transcriptModel: String?
    var fullText: String?
    var createdAt: Date
}

// MARK: - VideoSignalRecord

struct VideoSignalRecord: Identifiable {
    static let databaseTableName = "video_signals"

    var id: String
    var videoId: String
    var ticker: String?
    var parameterName: String
    var domain: String
    var direction: String       // "up" or "down"
    var weight: Int
    var confidence: Double
    var keyQuote: String
    var extractedAt: Date

    // Join helpers — not database columns, populated manually after fetch
    var videoTitle: String?
    var channelName: String?
    var publishedAt: String?
}

// MARK: VideoSignalRecord + GRDB

extension VideoSignalRecord: FetchableRecord {
    init(row: Row) {
        id            = row["id"]
        videoId       = row["videoId"]
        ticker        = row["ticker"]
        parameterName = row["parameterName"]
        domain        = row["domain"]
        direction     = row["direction"]
        weight        = row["weight"]
        confidence    = row["confidence"]
        keyQuote      = row["keyQuote"] ?? ""
        extractedAt   = row["extractedAt"]
        videoTitle    = nil
        channelName   = nil
        publishedAt   = nil
    }
}

extension VideoSignalRecord: PersistableRecord {
    func encode(to container: inout PersistenceContainer) {
        container["id"]            = id
        container["videoId"]       = videoId
        container["ticker"]        = ticker
        container["parameterName"] = parameterName
        container["domain"]        = domain
        container["direction"]     = direction
        container["weight"]        = weight
        container["confidence"]    = confidence
        container["keyQuote"]      = keyQuote
        container["extractedAt"]   = extractedAt
        // Join helpers deliberately excluded
    }
}

// Codable conformance for the manager / extractor (JSON serialisation, not GRDB)
extension VideoSignalRecord: Codable {
    enum CodingKeys: String, CodingKey {
        case id, videoId, ticker, parameterName, domain, direction, weight, confidence, keyQuote, extractedAt
        case videoTitle, channelName, publishedAt
    }
}

// MARK: - ChannelTrackRecord

struct ChannelTrackRecord: Codable, FetchableRecord, PersistableRecord, Identifiable {
    static let databaseTableName = "channel_tracks"

    var id: String { channelId }
    var channelId: String
    var channelName: String
    var speakerName: String
    var autoProcess: Bool
    var timeRangeYears: Int
    var createdAt: Date
}
