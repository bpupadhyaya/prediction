import SwiftUI

struct ContentView: View {
    @EnvironmentObject var store: AppStore

    var body: some View {
        TabView {
            HomeView()
                .tabItem { Label("Market", systemImage: "chart.line.uptrend.xyaxis") }

            SearchView()
                .tabItem { Label("Lookup", systemImage: "magnifyingglass") }

            PortfolioView()
                .tabItem { Label("Portfolio", systemImage: "briefcase") }

            WatchlistView()
                .tabItem { Label("Watchlist", systemImage: "star") }

            SyncView()
                .tabItem { Label("Sync", systemImage: "arrow.triangle.2.circlepath") }
        }
        .accentColor(.blue)
    }
}
