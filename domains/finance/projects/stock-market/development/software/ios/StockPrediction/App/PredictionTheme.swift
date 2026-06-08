import SwiftUI

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
            colors: [Color(red: 0.047, green: 0.231, blue: 0.431),
                     Color(red: 0.012, green: 0.412, blue: 0.631),
                     Color(red: 0.055, green: 0.647, blue: 0.914)],
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red: 0.490, green: 0.827, blue: 0.988),
        isAvailable: true
    ),
    PredictionModule(
        id: "sports",
        title: "Sports",
        subtitle: "Game outcomes & player stats",
        icon: "sportscourt",
        gradient: LinearGradient(
            colors: [Color(red: 0.078, green: 0.325, blue: 0.176),
                     Color(red: 0.082, green: 0.502, blue: 0.239),
                     Color(red: 0.133, green: 0.773, blue: 0.369)],
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red: 0.525, green: 0.937, blue: 0.671),
        isAvailable: false
    ),
    PredictionModule(
        id: "weather",
        title: "Weather",
        subtitle: "Extended forecasts with AI",
        icon: "cloud.sun",
        gradient: LinearGradient(
            colors: [Color(red: 0.486, green: 0.114, blue: 0.071),
                     Color(red: 0.761, green: 0.255, blue: 0.047),
                     Color(red: 0.976, green: 0.451, blue: 0.086)],
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red: 0.996, green: 0.843, blue: 0.667),
        isAvailable: false
    ),
    PredictionModule(
        id: "elections",
        title: "Elections",
        subtitle: "Political outcome forecasts",
        icon: "building.columns",
        gradient: LinearGradient(
            colors: [Color(red: 0.180, green: 0.063, blue: 0.396),
                     Color(red: 0.427, green: 0.157, blue: 0.851),
                     Color(red: 0.659, green: 0.333, blue: 0.969)],
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red: 0.847, green: 0.706, blue: 0.996),
        isAvailable: false
    ),
    PredictionModule(
        id: "crypto",
        title: "Crypto",
        subtitle: "Cryptocurrency price signals",
        icon: "bitcoinsign.circle",
        gradient: LinearGradient(
            colors: [Color(red: 0.039, green: 0.247, blue: 0.329),
                     Color(red: 0.043, green: 0.400, blue: 0.467),
                     Color(red: 0.055, green: 0.557, blue: 0.557)],
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red: 0.400, green: 0.867, blue: 0.867),
        isAvailable: false
    ),
    PredictionModule(
        id: "real_estate",
        title: "Real Estate",
        subtitle: "Property value trends",
        icon: "house",
        gradient: LinearGradient(
            colors: [Color(red: 0.059, green: 0.278, blue: 0.157),
                     Color(red: 0.082, green: 0.420, blue: 0.239),
                     Color(red: 0.118, green: 0.608, blue: 0.365)],
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red: 0.525, green: 0.890, blue: 0.671),
        isAvailable: false
    ),
    PredictionModule(
        id: "health",
        title: "Health Trends",
        subtitle: "Disease & outbreak forecasts",
        icon: "heart.text.square",
        gradient: LinearGradient(
            colors: [Color(red: 0.400, green: 0.106, blue: 0.200),
                     Color(red: 0.620, green: 0.176, blue: 0.341),
                     Color(red: 0.820, green: 0.310, blue: 0.490)],
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red: 0.961, green: 0.698, blue: 0.800),
        isAvailable: false
    ),
    PredictionModule(
        id: "economy",
        title: "Economy",
        subtitle: "Macro indicators & GDP forecasts",
        icon: "chart.bar",
        gradient: LinearGradient(
            colors: [Color(red: 0.161, green: 0.063, blue: 0.369),
                     Color(red: 0.310, green: 0.157, blue: 0.624),
                     Color(red: 0.478, green: 0.310, blue: 0.816)],
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red: 0.749, green: 0.722, blue: 0.965),
        isAvailable: false
    ),
]
