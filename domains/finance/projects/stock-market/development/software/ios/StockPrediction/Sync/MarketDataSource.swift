import Foundation

// MARK: - Data source catalog

enum MarketDataSourceType: String, CaseIterable, Codable {
    case yahooFinance  = "Yahoo Finance"
    case alphaVantage  = "Alpha Vantage"
    case twelveData    = "Twelve Data"
    case polygonIO     = "Polygon.io"
    case stooq         = "Stooq"

    var requiresAPIKey: Bool {
        switch self {
        case .yahooFinance, .stooq: return false
        default: return true
        }
    }

    var keyHint: String {
        switch self {
        case .alphaVantage: return "Get free key at alphavantage.co (25 calls/day)"
        case .twelveData:   return "Get free key at twelvedata.com (800 calls/day)"
        case .polygonIO:    return "Get free key at polygon.io (5 calls/min)"
        default: return ""
        }
    }

    var description: String {
        switch self {
        case .yahooFinance: return "Default · No API key required · Reliable"
        case .alphaVantage: return "Free 25 calls/day · Full adjusted history"
        case .twelveData:   return "Free 800 calls/day · Fast & accurate"
        case .polygonIO:    return "Free 5 calls/min · Professional grade"
        case .stooq:        return "No key required · CSV-based · International"
        }
    }
}

// MARK: - Settings persistence

struct MarketDataSettings {
    static let defaults = UserDefaults.standard
    static let sourceKey = "market_data_source"
    static let keyPrefix = "market_api_key_"

    static var activeSource: MarketDataSourceType {
        get {
            let raw = defaults.string(forKey: sourceKey) ?? MarketDataSourceType.yahooFinance.rawValue
            return MarketDataSourceType(rawValue: raw) ?? .yahooFinance
        }
        set { defaults.set(newValue.rawValue, forKey: sourceKey) }
    }

    static func apiKey(for source: MarketDataSourceType) -> String {
        defaults.string(forKey: keyPrefix + source.rawValue) ?? ""
    }

    static func setAPIKey(_ key: String, for source: MarketDataSourceType) {
        defaults.set(key, forKey: keyPrefix + source.rawValue)
    }
}

// MARK: - Yahoo Finance fetcher (default, no key required)

struct YahooFinanceFetcher {
    static func fetchPriceBars(ticker: String) async throws -> [PriceBar] {
        let urlStr = "https://query1.finance.yahoo.com/v8/finance/chart/\(ticker)?interval=1d&range=5y"
        guard let url = URL(string: urlStr) else { throw URLError(.badURL) }
        var req = URLRequest(url: url, timeoutInterval: 30)
        req.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15", forHTTPHeaderField: "User-Agent")
        req.setValue("application/json", forHTTPHeaderField: "Accept")
        let (data, response) = try await URLSession.shared.data(for: req)
        guard (response as? HTTPURLResponse)?.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }
        return try parseChart(data, ticker: ticker)
    }

    private static func parseChart(_ data: Data, ticker: String) throws -> [PriceBar] {
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let chart = json["chart"] as? [String: Any],
              let results = chart["result"] as? [[String: Any]],
              let result = results.first,
              let timestamps = result["timestamp"] as? [Double],
              let indicators = result["indicators"] as? [String: Any],
              let quoteArr = indicators["quote"] as? [[String: Any]],
              let quote = quoteArr.first
        else { throw URLError(.cannotParseResponse) }

        let adjcloseArr = (indicators["adjclose"] as? [[String: Any]])?.first
        let adjcloses = adjcloseArr?["adjclose"] as? [Double?] ?? []

        let opens   = quote["open"]   as? [Double?] ?? []
        let highs   = quote["high"]   as? [Double?] ?? []
        let lows    = quote["low"]    as? [Double?] ?? []
        let closes  = quote["close"]  as? [Double?] ?? []
        let volumes = quote["volume"] as? [Double?] ?? []

        var bars: [PriceBar] = []
        for i in 0..<min(timestamps.count, opens.count) {
            guard let o = opens[i], let h = highs[i], let l = lows[i],
                  let c = closes[i], let v = volumes[i]
            else { continue }
            let adj = i < adjcloses.count ? (adjcloses[i] ?? c) : c
            bars.append(PriceBar(
                ticker: ticker.uppercased(),
                date: Date(timeIntervalSince1970: timestamps[i]),
                open: o, high: h, low: l, close: c,
                adjClose: adj, volume: Int64(v)
            ))
        }
        return bars
    }

    static func fetchQuote(ticker: String) async throws -> Stock? {
        let urlStr = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=\(ticker)"
        guard let url = URL(string: urlStr) else { return nil }
        var req = URLRequest(url: url, timeoutInterval: 20)
        req.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", forHTTPHeaderField: "User-Agent")
        req.setValue("application/json", forHTTPHeaderField: "Accept")
        let (data, _) = try await URLSession.shared.data(for: req)
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let qr = json["quoteResponse"] as? [String: Any],
              let results = qr["result"] as? [[String: Any]],
              let q = results.first else { return nil }
        return Stock(
            ticker: (q["symbol"] as? String)?.uppercased() ?? ticker.uppercased(),
            name: q["longName"] as? String ?? q["shortName"] as? String ?? ticker.uppercased(),
            sector: q["sector"] as? String,
            industry: q["industry"] as? String,
            marketCap: q["marketCap"] as? Double,
            updatedAt: Date()
        )
    }
}

// MARK: - Stooq fetcher (no key, CSV)

struct StooqFetcher {
    static func fetchPriceBars(ticker: String) async throws -> [PriceBar] {
        let urlStr = "https://stooq.com/q/d/l/?s=\(ticker.lowercased()).us&i=d"
        guard let url = URL(string: urlStr) else { throw URLError(.badURL) }
        var req = URLRequest(url: url, timeoutInterval: 30)
        req.setValue("Mozilla/5.0", forHTTPHeaderField: "User-Agent")
        let (data, _) = try await URLSession.shared.data(for: req)
        guard let csv = String(data: data, encoding: .utf8) else { throw URLError(.cannotParseResponse) }
        return parseCSV(csv, ticker: ticker)
    }

    private static func parseCSV(_ csv: String, ticker: String) -> [PriceBar] {
        let df = DateFormatter(); df.dateFormat = "yyyy-MM-dd"
        let lines = csv.components(separatedBy: "\n").dropFirst() // skip header
        return lines.compactMap { line -> PriceBar? in
            let cols = line.trimmingCharacters(in: .whitespaces).components(separatedBy: ",")
            guard cols.count >= 5, let date = df.date(from: cols[0]),
                  let o = Double(cols[1]), let h = Double(cols[2]),
                  let l = Double(cols[3]), let c = Double(cols[4])
            else { return nil }
            let vol = cols.count > 5 ? Int64(cols[5]) ?? 0 : 0
            return PriceBar(ticker: ticker.uppercased(), date: date, open: o, high: h, low: l, close: c, adjClose: c, volume: vol)
        }
    }
}
