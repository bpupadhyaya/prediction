import SwiftUI

struct StockPredictionHomeView: View {
    let onModuleTap: (String) -> Void
    private let columns = [GridItem(.flexible()), GridItem(.flexible())]

    var body: some View {
        VStack(spacing: 0) {
            heroHeader
            ScrollView {
                LazyVGrid(columns: columns, spacing: 16) {
                    ForEach(stockModules) { module in
                        StockModuleCard(module: module) {
                            onModuleTap(module.id)
                        }
                    }
                }
                .padding(.horizontal, 16)
                .padding(.top, 16)
                .padding(.bottom, 32)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(PredictionTheme.homeBg.ignoresSafeArea())
        .ignoresSafeArea(edges: .top)
        .toolbar(.hidden, for: .navigationBar)
    }

    private var heroHeader: some View {
        ZStack {
            VStack(spacing: 4) {
                Text("Stock Prediction")
                    .font(.title.bold())
                    .foregroundStyle(.white)
                Text("AI-powered stock market forecasts")
                    .font(.subheadline)
                    .foregroundStyle(.white.opacity(0.8))
                HStack(spacing: 5) {
                    Image(systemName: "sparkles")
                        .font(.system(size: 10))
                    Text("Powered by Zoe AI · All predictions run on-device")
                        .font(.system(size: 11, weight: .medium))
                }
                .foregroundStyle(.white.opacity(0.9))
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(.white.opacity(0.15))
                .clipShape(Capsule())
                .padding(.top, 8)
            }
            .frame(maxWidth: .infinity)
        }
        .padding(.top, 36)
        .padding(.bottom, 16)
        .background(
            LinearGradient(
                colors: [
                    Color(red: 0.047, green: 0.231, blue: 0.431),
                    Color(red: 0.102, green: 0.412, blue: 0.635),
                    Color(red: 0.055, green: 0.647, blue: 0.914),
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .ignoresSafeArea(edges: .top)
    }
}

struct StockModuleCard: View {
    let module: StockModule
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
                }

                Text(module.title)
                    .font(.headline)
                    .foregroundStyle(.white)
                    .lineLimit(1)

                Text(module.subtitle)
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.55))
                    .lineLimit(2)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(16)
            .frame(maxWidth: .infinity, minHeight: 140, alignment: .topLeading)
            .background(module.gradient)
            .clipShape(RoundedRectangle(cornerRadius: 18))
        }
        .buttonStyle(.plain)
        .sensoryFeedback(.impact(flexibility: .soft), trigger: false)
    }
}
