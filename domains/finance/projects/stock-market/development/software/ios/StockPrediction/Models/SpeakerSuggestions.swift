import Foundation

// MARK: - Contextual speaker suggestions
//
// Maps a ticker (and, where useful, sector keywords) to the most relevant of the
// pre-seeded YVIS speakers to follow for that stock. Used to render a subtle
// "Track for this stock: <name>" hint on the stock detail screen.
// Single source of truth — names match the seeded speakers in VideoIntelligenceView.

enum SpeakerSuggestions {

    /// Speakers most relevant to a specific ticker.
    private static let byTicker: [String: [String]] = [
        "TSLA":    ["Elon Musk", "Cathie Wood"],
        "MSTR":    ["Michael Saylor"],
        "BTC-USD": ["Michael Saylor"],
        "ETH-USD": ["Michael Saylor"],
        "COIN":    ["Michael Saylor", "Cathie Wood"],
        "NVDA":    ["Jensen Huang"],
        "AAPL":    ["Tim Cook"],
        "ROKU":    ["Cathie Wood"],
        "RBLX":    ["Cathie Wood"],
        "HOOD":    ["Cathie Wood"],
        "SQ":      ["Cathie Wood"],
        "PATH":    ["Cathie Wood"],
        "BRK-B":   ["Warren Buffett"],
        "BRK-A":   ["Warren Buffett"],
    ]

    /// Sector / keyword fallbacks when the ticker isn't explicitly mapped.
    private static let bySectorKeyword: [(keyword: String, speakers: [String])] = [
        ("ev",             ["Elon Musk"]),
        ("auto",           ["Elon Musk"]),
        ("crypto",         ["Michael Saylor"]),
        ("blockchain",     ["Michael Saylor"]),
        ("semiconductor",  ["Jensen Huang"]),
        ("semis",          ["Jensen Huang"]),
        ("artificial intelligence", ["Jensen Huang"]),
        ("technology",     ["Jensen Huang"]),
        ("innovation",     ["Cathie Wood"]),
        ("disruptive",     ["Cathie Wood"]),
        ("financial",      ["Warren Buffett"]),
        ("bank",           ["Jerome Powell", "Warren Buffett"]),
    ]

    /// Returns suggested speaker names for the given ticker / optional sector,
    /// most relevant first. Empty when nothing relevant is found.
    static func speakers(forTicker ticker: String, sector: String? = nil) -> [String] {
        let key = ticker.uppercased()
        if let direct = byTicker[key] { return direct }

        // Crypto pairs not individually listed → Saylor.
        if key.hasSuffix("-USD") { return ["Michael Saylor"] }

        if let sector, !sector.isEmpty {
            let lower = sector.lowercased()
            for entry in bySectorKeyword where lower.contains(entry.keyword) {
                return entry.speakers
            }
        }
        return []
    }
}
