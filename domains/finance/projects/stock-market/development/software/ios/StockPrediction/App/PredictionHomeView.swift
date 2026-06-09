import SwiftUI

struct PredictionHomeView: View {
    var onModuleTap: ((String) -> Void)? = nil
    @State private var activeModule: String? = nil
    private let columns = [GridItem(.flexible()), GridItem(.flexible())]

    var body: some View {
        VStack(spacing: 0) {
            heroHeader
            ScrollView {
                LazyVGrid(columns: columns, spacing: 14) {
                    ForEach(predictionModules) { module in
                        PredictionModuleCard(module: module) {
                            if module.isAvailable {
                                if let onModuleTap {
                                    onModuleTap(module.id)
                                } else {
                                    withAnimation(.easeInOut(duration: 0.3)) {
                                        activeModule = module.id
                                    }
                                }
                            }
                        }
                    }
                }
                .padding(.horizontal, 16)
                .padding(.top, 12)
                .padding(.bottom, 32)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(PredictionTheme.homeBg.ignoresSafeArea())
        .ignoresSafeArea(edges: .top)
        .toolbar(.hidden, for: .navigationBar)
        .overlay {
            if onModuleTap == nil, activeModule == "stock_market" {
                StockMarketModuleView(onBack: {
                    withAnimation(.easeInOut(duration: 0.3)) { activeModule = nil }
                })
                .transition(.move(edge: .trailing).combined(with: .opacity))
            }
        }
        .animation(.easeInOut(duration: 0.3), value: activeModule)
    }

    // MARK: - Hero header — same structure as lifeos HeroHeader (isHomePage: true)
    private var heroHeader: some View {
        ZStack {
            VStack(spacing: 4) {
                Text(Bundle.main.infoDictionary?["CFBundleDisplayName"] as? String ?? "Prediction")
                    .font(.title.bold())
                    .foregroundStyle(.white)
                Text("AI-powered forecasts across every domain")
                    .font(.subheadline)
                    .foregroundStyle(.white.opacity(0.8))
                // Zoe badge — tucked into the banner
                HStack(spacing: 5) {
                    Image(systemName: "sparkles")
                        .font(.system(size: 10))
                    Text("Powered by Zoe AI · All predictions run on-device")
                        .font(.system(size: 11, weight: .medium))
                }
                .foregroundStyle(.white.opacity(0.9))
                .padding(.horizontal, 10)
                .padding(.vertical, 5)
                .background(.white.opacity(0.15))
                .clipShape(Capsule())
                .padding(.top, 6)
            }
            .frame(maxWidth: .infinity)
        }
        .padding(.top, 36)
        .padding(.bottom, 18)
        .background(
            LinearGradient(
                colors: [
                    Color(red: 0.086, green: 0.118, blue: 0.314),   // deep indigo
                    Color(red: 0.153, green: 0.212, blue: 0.549),   // royal blue
                    Color(red: 0.231, green: 0.510, blue: 0.965),   // electric blue (accent)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .ignoresSafeArea(edges: .top)
    }
}

// MARK: - Module Card

struct PredictionModuleCard: View {
    let module: PredictionModule
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    ZStack {
                        RoundedRectangle(cornerRadius: 10)
                            .fill(Color.white.opacity(0.20))
                            .frame(width: 40, height: 40)
                        Image(systemName: module.icon)
                            .font(.system(size: 20))
                            .foregroundStyle(module.iconColor)
                    }
                    Spacer()
                    if !module.isAvailable {
                        Image(systemName: "lock.fill")
                            .font(.system(size: 13))
                            .foregroundStyle(Color.white.opacity(0.50))
                    }
                }

                Text(module.title)
                    .font(.headline)
                    .foregroundStyle(.white)
                    .lineLimit(1)

                Text(module.subtitle)
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.50))
                    .lineLimit(2)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(14)
            .frame(maxWidth: .infinity, minHeight: 140, alignment: .topLeading)
            .background(module.gradient)
            .clipShape(RoundedRectangle(cornerRadius: 18))
            .opacity(module.isAvailable ? 1.0 : 0.7)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Stock Market Module wrapper (custom overlay back button, no NavigationStack to avoid TabView conflicts)

struct StockMarketModuleView: View {
    let onBack: () -> Void

    var body: some View {
        ZStack(alignment: .topLeading) {
            ContentView()

            // Floating back button
            Button(action: onBack) {
                HStack(spacing: 4) {
                    Image(systemName: "chevron.left")
                    Text("Home")
                }
                .font(.system(size: 15, weight: .medium))
                .foregroundStyle(.blue)
                .padding(.horizontal, 12)
                .padding(.vertical, 7)
                .background(.ultraThinMaterial)
                .clipShape(Capsule())
                .shadow(color: .black.opacity(0.15), radius: 4, y: 2)
            }
            .padding(.top, 56)
            .padding(.leading, 16)
        }
    }
}
