import SwiftUI

struct ContentView: View {
    @EnvironmentObject var store: AppStore
    @State private var selectedTab = 0
    @State private var activeModuleId: String?

    init() { applyPredictionTabBarAppearance() }

    var body: some View {
        ZStack {
            TabView(selection: $selectedTab) {
                NavigationStack {
                    StockPredictionHomeView(onModuleTap: handleModuleTap)
                }
                .tabItem { Label("Home", systemImage: "house.fill") }
                .tag(0)

                NavigationStack { HomeView().environmentObject(store) }
                    .tabItem { Label("Market", systemImage: "chart.line.uptrend.xyaxis") }
                    .tag(1)

                NavigationStack { SearchView().environmentObject(store) }
                    .tabItem { Label("Lookup", systemImage: "magnifyingglass") }
                    .tag(2)

                NavigationStack { PortfolioView().environmentObject(store) }
                    .tabItem { Label("Portfolio", systemImage: "briefcase") }
                    .tag(3)

                NavigationStack { WatchlistView().environmentObject(store) }
                    .tabItem { Label("Watchlist", systemImage: "star") }
                    .tag(4)

                NavigationStack { VideoIntelligenceView() }
                    .tabItem { Label("Intelligence", systemImage: "video.badge.waveform") }
                    .tag(5)
            }
            .tint(.white)
            .toolbarBackground(Color(red: 0.051, green: 0.122, blue: 0.212), for: .tabBar)
            .toolbarBackground(.visible, for: .tabBar)

            if let moduleId = activeModuleId {
                Group {
                    if ["crypto", "earnings", "sectors", "global"].contains(moduleId) {
                        MarketModuleView(moduleId: moduleId, onBack: {
                            withAnimation(.easeInOut(duration: 0.3)) { activeModuleId = nil }
                        })
                    } else {
                        StockModulePlaceholderOverlay(moduleId: moduleId, onBack: {
                            withAnimation(.easeInOut(duration: 0.3)) { activeModuleId = nil }
                        })
                    }
                }
                .transition(.move(edge: .trailing).combined(with: .opacity))
                .ignoresSafeArea()
            }
        }
        .animation(.easeInOut(duration: 0.3), value: activeModuleId)
    }

    private func handleModuleTap(_ moduleId: String) {
        if marketModuleIds.contains(moduleId) {
            withAnimation(.easeInOut(duration: 0.25)) { selectedTab = 1 }
        } else {
            withAnimation(.easeInOut(duration: 0.3)) { activeModuleId = moduleId }
        }
    }
}

private struct StockModulePlaceholderOverlay: View {
    let moduleId: String
    let onBack: () -> Void

    private var module: StockModule? { stockModules.first { $0.id == moduleId } }

    var body: some View {
        ZStack(alignment: .topLeading) {
            Color(red: 0.043, green: 0.118, blue: 0.212).ignoresSafeArea()

            VStack(spacing: 24) {
                Spacer().frame(height: 100)

                if let mod = module {
                    ZStack {
                        Circle()
                            .fill(mod.gradient)
                            .frame(width: 80, height: 80)
                        Image(systemName: mod.icon)
                            .font(.system(size: 36))
                            .foregroundStyle(mod.iconColor)
                    }

                    Text(mod.title)
                        .font(.title.bold())
                        .foregroundStyle(.white)

                    Text(mod.subtitle)
                        .font(.body)
                        .foregroundStyle(.white.opacity(0.7))
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 32)
                }

                Text("Coming Soon")
                    .font(.headline)
                    .foregroundStyle(.white.opacity(0.5))
                    .padding(.top, 8)

                Spacer()
            }
            .frame(maxWidth: .infinity)

            Button(action: onBack) {
                HStack(spacing: 4) {
                    Image(systemName: "chevron.left")
                    Text("Home")
                }
                .font(.system(size: 15, weight: .medium))
                .foregroundStyle(.white)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(.ultraThinMaterial)
                .clipShape(Capsule())
                .shadow(color: .black.opacity(0.15), radius: 4, y: 2)
            }
            .padding(.top, 56)
            .padding(.leading, 16)
        }
    }
}
