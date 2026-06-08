import SwiftUI

@MainActor
final class AppStore: ObservableObject {
    @Published var topPredictions: [Prediction] = []
    @Published var watchlist: [WatchlistEntry] = []
    @Published var portfolio: [PortfolioHolding] = []
    @Published var syncState: SyncState = .idle

    enum SyncState: Equatable {
        case idle
        case syncing
        case done(String)     // tag name
        case failed(String)   // error message
    }

    private let db = DatabaseManager.shared
    private let engine = PredictionEngine.shared

    func initialise() async {
        loadLocal()
    }

    func loadLocal() {
        watchlist = (try? db.watchlist()) ?? []
        portfolio = (try? db.portfolio()) ?? []
        topPredictions = (try? db.allPredictions()) ?? []
    }

    func search(query: String) -> [Stock] {
        (try? db.searchStocks(query: query)) ?? []
    }

    func prediction(for ticker: String, horizon: String = "1w") -> Prediction? {
        try? engine.predict(ticker: ticker, horizon: horizon)
    }

    func prices(for ticker: String, days: Int = 90) -> [PriceBar] {
        (try? db.prices(ticker: ticker, days: days)) ?? []
    }

    func latestPrice(for ticker: String) -> Double? {
        (try? db.latestPrice(ticker: ticker))?.adjClose
    }

    func isWatchlisted(_ ticker: String) -> Bool {
        (try? db.isWatchlisted(ticker: ticker)) ?? false
    }

    func toggleWatchlist(_ ticker: String) {
        if isWatchlisted(ticker) {
            try? db.removeFromWatchlist(ticker: ticker)
        } else {
            try? db.addToWatchlist(ticker: ticker)
        }
        watchlist = (try? db.watchlist()) ?? []
    }

    func addHolding(ticker: String, shares: Double, costBasis: Double) {
        let h = PortfolioHolding(ticker: ticker.uppercased(), shares: shares,
                                 costBasis: costBasis, addedAt: Date())
        try? db.upsertHolding(h)
        portfolio = (try? db.portfolio()) ?? []
    }

    func removeHolding(_ ticker: String) {
        try? db.removeHolding(ticker: ticker)
        portfolio = (try? db.portfolio()) ?? []
    }

    func triggerSync() {
        guard syncState != .syncing else { return }
        syncState = .syncing
        Task {
            do {
                let result = try await SyncManager.shared.sync { _, _, _ in }
                syncState = .done(result)
                loadLocal()
            } catch {
                syncState = .failed(error.localizedDescription)
            }
        }
    }
}
