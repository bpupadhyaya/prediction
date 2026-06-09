import SwiftUI

struct PredictionMainTabView: View {
    @State private var selectedTab = 0
    @State private var activeModule: String? = nil

    init() { applyPredictionTabBarAppearance() }

    var body: some View {
        ZStack {
            TabView(selection: $selectedTab) {
                NavigationStack {
                    PredictionHomeView(onModuleTap: { mod in
                        withAnimation(.easeInOut(duration: 0.3)) { activeModule = mod }
                    })
                }
                .tabItem { Label("Home", systemImage: "square.grid.2x2.fill") }
                .tag(0)

                NavigationStack {
                    PredictionPlaceholderView(title: "Search", icon: "magnifyingglass")
                }
                .tabItem { Label("Search", systemImage: "magnifyingglass") }
                .tag(1)

                NavigationStack {
                    PredictionPlaceholderView(title: "Settings", icon: "gearshape.fill")
                }
                .tabItem { Label("Settings", systemImage: "gearshape.fill") }
                .tag(2)
            }
            .tint(.white)

            if activeModule == "stock_market" {
                StockMarketModuleView(onBack: {
                    withAnimation(.easeInOut(duration: 0.3)) { activeModule = nil }
                })
                .transition(.move(edge: .trailing).combined(with: .opacity))
                .ignoresSafeArea()
            }
        }
        .animation(.easeInOut(duration: 0.3), value: activeModule)
    }
}

private struct PredictionPlaceholderView: View {
    let title: String
    let icon: String

    var body: some View {
        ZStack {
            PredictionTheme.homeBg.ignoresSafeArea()
            VStack(spacing: 14) {
                Image(systemName: icon)
                    .font(.system(size: 44))
                    .foregroundStyle(PredictionTheme.accent)
                Text(title)
                    .font(.title2.bold())
                    .foregroundStyle(PredictionTheme.textPrimary)
                Text("Coming soon")
                    .font(.subheadline)
                    .foregroundStyle(PredictionTheme.textSecondary)
            }
        }
        .toolbar(.hidden, for: .navigationBar)
    }
}
