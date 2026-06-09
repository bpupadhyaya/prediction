import SwiftUI
import UIKit

// MARK: - Prediction App Theme (home screen)
struct PredictionTheme {
    // Deep cosmic-blue home background — represents looking into the future
    static let homeBg         = Color(red: 0.043, green: 0.082, blue: 0.149)   // #0B1526
    static let headerBg       = Color(red: 0.055, green: 0.118, blue: 0.220)   // #0E1E38
    static let heroBg         = LinearGradient(
        colors: [Color(red: 0.043, green: 0.082, blue: 0.149),
                 Color(red: 0.078, green: 0.145, blue: 0.255)],
        startPoint: .topLeading, endPoint: .bottomTrailing
    )

    // Accent — electric indigo, represents AI prediction
    static let accent         = Color(red: 0.231, green: 0.510, blue: 0.965)   // #3B82F6
    static let accentGold     = Color(red: 1.000, green: 0.722, blue: 0.000)   // #FFB800
    static let accentPurple   = Color(red: 0.420, green: 0.310, blue: 0.847)   // #6B4FD8

    // Text on dark
    static let textPrimary    = Color.white
    static let textSecondary  = Color.white.opacity(0.65)
    static let textMuted      = Color.white.opacity(0.40)

    // Domains / Settings pages — light, same as zoel-ai
    static let pageBg         = Color(red: 0.949, green: 0.949, blue: 0.969)   // #F2F2F7
    static let cardBg         = Color.white
    static let textDark       = Color(red: 0.110, green: 0.110, blue: 0.118)   // #1C1C1E
    static let textDarkMuted  = Color(red: 0.541, green: 0.541, blue: 0.557)   // #8A8A8E
}

// MARK: - Tab bar appearance (shared by all Prediction app tab views)
func applyPredictionTabBarAppearance() {
    let appearance = UITabBarAppearance()
    appearance.configureWithDefaultBackground()
    let unsel = UIColor.white.withAlphaComponent(0.45)
    appearance.stackedLayoutAppearance.normal.iconColor = unsel
    appearance.stackedLayoutAppearance.normal.titleTextAttributes = [.foregroundColor: unsel]
    appearance.stackedLayoutAppearance.selected.iconColor = .white
    appearance.stackedLayoutAppearance.selected.titleTextAttributes = [.foregroundColor: UIColor.white]
    UITabBar.appearance().standardAppearance = appearance
    UITabBar.appearance().scrollEdgeAppearance = appearance
}

// MARK: - Prediction Module definitions
struct PredictionModule: Identifiable {
    let id: String
    let title: String
    let subtitle: String
    let icon: String
    let gradient: LinearGradient
    let iconColor: Color
    let isAvailable: Bool
}

let predictionModules: [PredictionModule] = [
    PredictionModule(
        id: "stock_market",
        title: "Stock Market",
        subtitle: "AI-powered price predictions",
        icon: "chart.line.uptrend.xyaxis",
        gradient: LinearGradient(
            colors: [Color(red: 0.047, green: 0.231, blue: 0.431),   // #0C3B6E
                     Color(red: 0.102, green: 0.412, blue: 0.635),   // #1A69A2
                     Color(red: 0.055, green: 0.647, blue: 0.914)],  // #0EA5E9
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red: 0.490, green: 0.827, blue: 0.973),     // #7DD3F8
        isAvailable: true
    ),
    PredictionModule(
        id: "sports",
        title: "Sports",
        subtitle: "Game outcomes & player stats",
        icon: "sportscourt",
        gradient: LinearGradient(
            colors: [Color(red: 0.078, green: 0.243, blue: 0.149),   // #143E26
                     Color(red: 0.106, green: 0.478, blue: 0.239),   // #1B7A3D
                     Color(red: 0.133, green: 0.773, blue: 0.369)],  // #22C55E
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red: 0.525, green: 0.937, blue: 0.675),     // #86EFAC
        isAvailable: true
    ),
    PredictionModule(
        id: "weather",
        title: "Weather",
        subtitle: "Extended forecasts with AI",
        icon: "cloud.sun",
        gradient: LinearGradient(
            colors: [Color(red: 0.486, green: 0.114, blue: 0.071),   // #7C1D12
                     Color(red: 0.761, green: 0.255, blue: 0.047),   // #C2410C
                     Color(red: 0.976, green: 0.451, blue: 0.086)],  // #F97316
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red: 0.996, green: 0.843, blue: 0.667),     // #FED7AA
        isAvailable: true
    ),
    PredictionModule(
        id: "elections",
        title: "Elections",
        subtitle: "Political outcome forecasts",
        icon: "building.columns",
        gradient: LinearGradient(
            colors: [Color(red: 0.157, green: 0.051, blue: 0.353),   // #280D5A
                     Color(red: 0.310, green: 0.106, blue: 0.620),   // #4F1B9E
                     Color(red: 0.608, green: 0.302, blue: 0.906)],  // #9B4DE7
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red: 0.804, green: 0.659, blue: 1.000),     // #CDA8FF
        isAvailable: true
    ),
    PredictionModule(
        id: "crypto",
        title: "Crypto",
        subtitle: "Cryptocurrency price signals",
        icon: "bitcoinsign.circle",
        gradient: LinearGradient(
            colors: [Color(red: 0.024, green: 0.235, blue: 0.294),   // #063C4B
                     Color(red: 0.039, green: 0.416, blue: 0.514),   // #0A6A83
                     Color(red: 0.063, green: 0.675, blue: 0.788)],  // #10ACC9
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red: 0.404, green: 0.875, blue: 0.941),     // #67DFF0
        isAvailable: true
    ),
    PredictionModule(
        id: "real_estate",
        title: "Real Estate",
        subtitle: "Property value trends",
        icon: "house",
        gradient: LinearGradient(
            colors: [Color(red: 0.059, green: 0.278, blue: 0.220),   // #0F4738
                     Color(red: 0.082, green: 0.475, blue: 0.369),   // #15795E
                     Color(red: 0.063, green: 0.725, blue: 0.506)],  // #10B981
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red: 0.431, green: 0.906, blue: 0.718),     // #6EE7B7
        isAvailable: true
    ),
    PredictionModule(
        id: "health",
        title: "Health Trends",
        subtitle: "Disease & outbreak forecasts",
        icon: "heart.text.square",
        gradient: LinearGradient(
            colors: [Color(red: 0.333, green: 0.039, blue: 0.188),   // #550A30
                     Color(red: 0.608, green: 0.106, blue: 0.337),   // #9B1B56
                     Color(red: 0.925, green: 0.282, blue: 0.600)],  // #EC4899
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red: 0.976, green: 0.659, blue: 0.831),     // #F9A8D4
        isAvailable: true
    ),
    PredictionModule(
        id: "economy",
        title: "Economy",
        subtitle: "Macro indicators & GDP forecasts",
        icon: "chart.bar",
        gradient: LinearGradient(
            colors: [Color(red: 0.055, green: 0.125, blue: 0.251),   // #0E2040
                     Color(red: 0.102, green: 0.239, blue: 0.451),   // #1A3D73
                     Color(red: 0.157, green: 0.408, blue: 0.745)],  // #2868BE
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red: 0.576, green: 0.765, blue: 0.941),     // #93C3F0
        isAvailable: true
    ),
]
