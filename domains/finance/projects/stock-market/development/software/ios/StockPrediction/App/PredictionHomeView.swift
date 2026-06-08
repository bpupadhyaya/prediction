import SwiftUI

struct PredictionHomeView: View {
    @State private var activeModule: String? = nil
    private let columns = [GridItem(.flexible()), GridItem(.flexible())]

    var body: some View {
        ZStack {
            PredictionTheme.homeBg.ignoresSafeArea()

            if activeModule == "stock_market" {
                // Stock Market module — full screen with back nav
                StockMarketModuleView(onBack: { activeModule = nil })
                    .transition(.move(edge: .trailing).combined(with: .opacity))
            } else {
                homeGrid
                    .transition(.move(edge: .leading).combined(with: .opacity))
            }
        }
        .animation(.easeInOut(duration: 0.3), value: activeModule)
    }

    private var homeGrid: some View {
        ScrollView {
            VStack(spacing: 0) {
                heroHeader

                LazyVGrid(columns: columns, spacing: 14) {
                    ForEach(predictionModules) { module in
                        PredictionModuleCard(module: module) {
                            if module.isAvailable {
                                activeModule = module.id
                            }
                        }
                    }
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 32)
            }
        }
    }

    private var heroHeader: some View {
        VStack(spacing: 6) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Prediction")
                        .font(.system(size: 28, weight: .bold))
                        .foregroundStyle(PredictionTheme.textPrimary)
                    Text("AI-powered forecasts across every domain")
                        .font(.system(size: 13, weight: .regular))
                        .foregroundStyle(PredictionTheme.textSecondary)
                }
                Spacer()
                // Zoe teaser orb
                ZStack {
                    Circle()
                        .fill(PredictionTheme.accentPurple.opacity(0.25))
                        .frame(width: 52, height: 52)
                    Circle()
                        .fill(PredictionTheme.accentPurple.opacity(0.15))
                        .frame(width: 52, height: 52)
                        .scaleEffect(1.3)
                    Image(systemName: "sparkles")
                        .font(.system(size: 22, weight: .light))
                        .foregroundStyle(PredictionTheme.accentPurple)
                }
            }
            .padding(.horizontal, 20)
            .padding(.top, 60)
            .padding(.bottom, 8)

            // "Powered by Zoe" tag
            HStack {
                HStack(spacing: 5) {
                    Image(systemName: "cpu")
                        .font(.system(size: 10))
                    Text("Powered by Zoe AI · All predictions run on-device")
                        .font(.system(size: 11, weight: .medium))
                }
                .foregroundStyle(PredictionTheme.accent)
                .padding(.horizontal, 10)
                .padding(.vertical, 5)
                .background(PredictionTheme.accent.opacity(0.12))
                .clipShape(Capsule())
                Spacer()
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 20)
        }
    }
}

// MARK: - Module Card

struct PredictionModuleCard: View {
    let module: PredictionModule
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    ZStack {
                        RoundedRectangle(cornerRadius: 10)
                            .fill(Color.white.opacity(0.20))
                            .frame(width: 42, height: 42)
                        Image(systemName: module.icon)
                            .font(.system(size: 20))
                            .foregroundStyle(module.iconColor)
                    }
                    Spacer()
                    if !module.isAvailable {
                        Image(systemName: "lock.fill")
                            .font(.system(size: 13))
                            .foregroundStyle(Color.white.opacity(0.35))
                    }
                }

                Text(module.title)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundStyle(.white)
                    .lineLimit(1)

                Text(module.subtitle)
                    .font(.system(size: 11))
                    .foregroundStyle(.white.opacity(0.55))
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
