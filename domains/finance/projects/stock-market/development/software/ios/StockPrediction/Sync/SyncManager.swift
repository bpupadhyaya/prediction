import Foundation

actor SyncManager {
    static let shared = SyncManager()

    // Tickers synced in "Quick Sync" (always included)
    private let hotTickers = [
        "NVDA","AAPL","MSFT","META","GOOGL","AMZN","TSLA","AMD","NFLX",
        "HOOD","PLTR","ARM","SMCI","COIN","MSTR","UBER","LYFT","SOFI",
        "RBLX","SNAP","RIVN","SOUN","AI","IONQ","QUBT","RDDT","ACHR","JOBY",
    ]

    // Top 50 S&P 500 by market cap (hardcoded for reliability)
    private let sp500Top50 = [
        "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK-B","AVGO","JPM",
        "LLY","V","XOM","UNH","MA","JNJ","HD","PG","COST","MRK",
        "ABBV","BAC","WMT","CVX","NFLX","KO","AMD","PEP","TMO","ORCL",
        "CSCO","CRM","ABT","ACN","MCD","ADBE","TXN","PM","DHR","VZ",
        "CAT","WFC","INTU","SPGI","NOW","NEE","AXP","UPS","MS","DE",
    ]

    enum SyncError: LocalizedError {
        case noData(String)
        case networkError(String)

        var errorDescription: String? {
            switch self {
            case .noData(let t):       return "No data returned for \(t)"
            case .networkError(let m): return "Network error: \(m)"
            }
        }
    }

    // Progress callback: (tickersDone, totalTickers, currentTicker)
    func sync(fullSP500: Bool = false, onProgress: @escaping (Int, Int, String) -> Void) async throws -> String {
        var tickers: [String]
        if fullSP500 {
            tickers = Array(Set(hotTickers + sp500Top50)).sorted()
        } else {
            tickers = Array(Set(hotTickers + sp500Top50)).sorted()
        }
        let total = tickers.count
        var done = 0

        for ticker in tickers {
            onProgress(done, total, ticker)
            do {
                let bars = try await fetchBars(ticker: ticker)
                if !bars.isEmpty {
                    try DatabaseManager.shared.upsertPrices(bars)
                }
                // Also fetch/update stock info for first-time tickers
                if let stock = try? await YahooFinanceFetcher.fetchQuote(ticker: ticker) {
                    try? DatabaseManager.shared.upsertStocks([stock])
                }
                // Run prediction and cache
                if let pred = try? PredictionEngine.shared.predict(ticker: ticker, horizon: "1w") {
                    try? DatabaseManager.shared.upsertPrediction(pred)
                }
            } catch {
                // Skip failed tickers — don't abort the whole sync
            }
            done += 1
            // Rate limit: 0.3s between calls to avoid 429
            try? await Task.sleep(nanoseconds: 300_000_000)
        }
        onProgress(total, total, "")
        return "Synced \(done) tickers"
    }

    private func fetchBars(ticker: String) async throws -> [PriceBar] {
        switch MarketDataSettings.activeSource {
        case .yahooFinance:
            return try await YahooFinanceFetcher.fetchPriceBars(ticker: ticker)
        case .stooq:
            return try await StooqFetcher.fetchPriceBars(ticker: ticker)
        case .alphaVantage, .twelveData, .polygonIO:
            // Fallback to Yahoo if no API key configured
            let key = MarketDataSettings.apiKey(for: MarketDataSettings.activeSource)
            if key.isEmpty { return try await YahooFinanceFetcher.fetchPriceBars(ticker: ticker) }
            // TODO: implement keyed sources — fall back to Yahoo for now
            return try await YahooFinanceFetcher.fetchPriceBars(ticker: ticker)
        }
    }
}
