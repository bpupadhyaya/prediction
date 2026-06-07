import Foundation
import GRDB

actor SyncManager {
    static let shared = SyncManager()

    private let releaseURL = "https://api.github.com/repos/bpupadhyaya/prediction/releases/latest"

    enum SyncError: LocalizedError {
        case noAsset, downloadFailed, importFailed(String)

        var errorDescription: String? {
            switch self {
            case .noAsset: return "No data snapshot found in latest release"
            case .downloadFailed: return "Failed to download snapshot"
            case .importFailed(let msg): return "Import failed: \(msg)"
            }
        }
    }

    private struct Release: Decodable {
        struct Asset: Decodable {
            let name: String
            let browserDownloadUrl: String
        }
        let tagName: String
        let assets: [Asset]
    }

    func sync() async throws -> String {
        let release = try await fetchLatestRelease()
        guard let asset = release.assets.first(where: { $0.name.hasSuffix(".sqlite.gz") }) else {
            throw SyncError.noAsset
        }
        let url = URL(string: asset.browserDownloadUrl)!
        let data = try await download(url: url)
        let decompressed = try decompress(data)
        try await importSnapshot(decompressed)
        return release.tagName
    }

    private func fetchLatestRelease() async throws -> Release {
        var req = URLRequest(url: URL(string: releaseURL)!)
        req.setValue("application/vnd.github+json", forHTTPHeaderField: "Accept")
        let (data, _) = try await URLSession.shared.data(for: req)
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return try decoder.decode(Release.self, from: data)
    }

    private func download(url: URL) async throws -> Data {
        let (data, response) = try await URLSession.shared.data(from: url)
        guard (response as? HTTPURLResponse)?.statusCode == 200 else {
            throw SyncError.downloadFailed
        }
        return data
    }

    private func decompress(_ data: Data) throws -> Data {
        // If not gzip-compressed, return as-is (dev fallback)
        guard data.count > 2, data[0] == 0x1f, data[1] == 0x8b else { return data }
        return try (data as NSData).decompressed(using: .zlib) as Data
    }

    private func importSnapshot(_ sqliteData: Data) async throws {
        let tmp = FileManager.default.temporaryDirectory.appendingPathComponent("snapshot.sqlite")
        try sqliteData.write(to: tmp)
        defer { try? FileManager.default.removeItem(at: tmp) }

        let sourceQueue = try DatabaseQueue(path: tmp.path)
        let stocks = try sourceQueue.read { db in try Stock.fetchAll(db) }
        let prices = try sourceQueue.read { db in try PriceBar.fetchAll(db) }
        let predictions = try sourceQueue.read { db in try Prediction.fetchAll(db) }

        try DatabaseManager.shared.upsertStocks(stocks)
        try DatabaseManager.shared.upsertPrices(prices)
        for p in predictions { try DatabaseManager.shared.upsertPrediction(p) }
    }
}
