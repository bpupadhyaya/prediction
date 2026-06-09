import SwiftUI

struct ContentView: View {
    @EnvironmentObject var store: AppStore

    init() { applyPredictionTabBarAppearance() }

    var body: some View {
        TabView {
            NavigationStack { HomeView() }
                .tabItem { Label("Market", systemImage: "chart.line.uptrend.xyaxis") }

            NavigationStack { SearchView() }
                .tabItem { Label("Lookup", systemImage: "magnifyingglass") }

            NavigationStack { PortfolioView() }
                .tabItem { Label("Portfolio", systemImage: "briefcase") }

            NavigationStack { WatchlistView() }
                .tabItem { Label("Watchlist", systemImage: "star") }

            NavigationStack { SyncView() }
                .tabItem { Label("Sync", systemImage: "arrow.triangle.2.circlepath") }

            NavigationStack { ModelsView() }
                .tabItem { Label("Models", systemImage: "wrench.and.screwdriver") }
        }
        .tint(.white)
    }
}
