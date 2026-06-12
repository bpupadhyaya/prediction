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

    /// Global symbol search via Yahoo's search API — finds ANY instrument on ANY
    /// exchange: equities worldwide (7203.T, SAP.DE, RELIANCE.NS, ...), crypto
    /// pairs, ETFs, indices. Makes the "predict any stock or crypto, local or
    /// global" mission reachable from the Lookup tab.
    static func searchSymbols(query: String, limit: Int = 20) async -> [Stock] {
        let trimmed = query.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty,
              let q = trimmed.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed),
              let url = URL(string: "https://query1.finance.yahoo.com/v1/finance/search?q=\(q)&quotesCount=\(limit)&newsCount=0&listsCount=0")
        else { return [] }
        var req = URLRequest(url: url, timeoutInterval: 15)
        req.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", forHTTPHeaderField: "User-Agent")
        req.setValue("application/json", forHTTPHeaderField: "Accept")
        guard let (data, _) = try? await URLSession.shared.data(for: req),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let quotes = json["quotes"] as? [[String: Any]] else { return [] }
        return quotes.compactMap { item in
            guard let symbol = item["symbol"] as? String, !symbol.isEmpty else { return nil }
            let name = (item["shortname"] as? String)
                ?? (item["longname"] as? String) ?? symbol
            let type = item["quoteType"] as? String ?? ""
            let exchange = (item["exchDisp"] as? String) ?? (item["exchange"] as? String) ?? ""
            let tag = [type, exchange].filter { !$0.isEmpty }.joined(separator: " · ")
            return Stock(
                ticker: symbol,
                name: name,
                sector: tag.isEmpty ? nil : tag,
                industry: nil,
                marketCap: nil,
                updatedAt: Date()
            )
        }
    }

    /// Lightweight batch quote — name, price, day change, next earnings timestamp.
    struct QuoteLite {
        let symbol: String
        let name: String
        let price: Double
        let changePct: Double
        let earningsTimestamp: Int64?   // unix seconds, nil if none reported
    }

    // Yahoo's v7 quote API is crumb-gated: hitting fc.yahoo.com seeds a session
    // cookie (URLSession's shared cookie storage keeps it), then v1/test/getcrumb
    // yields the crumb token that must accompany every v7 request.
    private static var yahooCrumb: String?

    private static func ensureCrumb(force: Bool = false) async -> String? {
        if !force, let crumb = yahooCrumb { return crumb }
        let ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"
        if let seedURL = URL(string: "https://fc.yahoo.com") {
            var seed = URLRequest(url: seedURL, timeoutInterval: 15)
            seed.setValue(ua, forHTTPHeaderField: "User-Agent")
            _ = try? await URLSession.shared.data(for: seed)   // sets cookie; response body irrelevant
        }
        guard let crumbURL = URL(string: "https://query1.finance.yahoo.com/v1/test/getcrumb") else { return nil }
        var req = URLRequest(url: crumbURL, timeoutInterval: 15)
        req.setValue(ua, forHTTPHeaderField: "User-Agent")
        guard let (data, _) = try? await URLSession.shared.data(for: req),
              let crumb = String(data: data, encoding: .utf8)?
                  .trimmingCharacters(in: .whitespacesAndNewlines),
              !crumb.isEmpty, !crumb.lowercased().contains("too many") else { return nil }
        yahooCrumb = crumb
        return crumb
    }

    static func fetchQuoteLites(symbols: [String]) async throws -> [QuoteLite] {
        guard !symbols.isEmpty else { return [] }
        let joined = symbols.joined(separator: ",")

        var results: [[String: Any]] = []
        for attempt in 0..<2 {
            guard let crumb = await ensureCrumb(force: attempt > 0),
                  let crumbEnc = crumb.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed),
                  let url = URL(string: "https://query1.finance.yahoo.com/v7/finance/quote?symbols=\(joined)&crumb=\(crumbEnc)")
            else { return [] }
            var req = URLRequest(url: url, timeoutInterval: 20)
            req.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", forHTTPHeaderField: "User-Agent")
            req.setValue("application/json", forHTTPHeaderField: "Accept")
            guard let (data, response) = try? await URLSession.shared.data(for: req) else { return [] }
            if (response as? HTTPURLResponse)?.statusCode == 401, attempt == 0 { continue }
            guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let qr = json["quoteResponse"] as? [String: Any],
                  let r = qr["result"] as? [[String: Any]] else { return [] }
            results = r
            break
        }
        return results.compactMap { q in
            guard let symbol = q["symbol"] as? String else { return nil }
            return QuoteLite(
                symbol: symbol,
                name: q["shortName"] as? String ?? q["longName"] as? String ?? symbol,
                price: q["regularMarketPrice"] as? Double ?? .nan,
                changePct: q["regularMarketChangePercent"] as? Double ?? 0,
                earningsTimestamp: (q["earningsTimestamp"] as? NSNumber)?.int64Value
            )
        }
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
