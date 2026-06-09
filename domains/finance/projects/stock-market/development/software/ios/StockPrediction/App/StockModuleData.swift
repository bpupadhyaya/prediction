import SwiftUI

struct StockModule: Identifiable {
    let id: String
    let title: String
    let subtitle: String
    let icon: String
    let gradient: LinearGradient
    let iconColor: Color
}

// IDs that map to existing content in HomeView's Market tab
let marketModuleIds: Set<String> = ["sp500", "nasdaq100", "hot_stocks", "pre_ipo"]

let stockModules: [StockModule] = [
    StockModule(
        id: "sp500", title: "S&P 500",
        subtitle: "Top 500 US company AI forecasts",
        icon: "chart.bar.fill",
        gradient: LinearGradient(
            colors: [Color(red:0.047,green:0.231,blue:0.431), Color(red:0.102,green:0.412,blue:0.635), Color(red:0.055,green:0.647,blue:0.914)],
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red:0.490,green:0.827,blue:0.973)
    ),
    StockModule(
        id: "nasdaq100", title: "Nasdaq 100",
        subtitle: "Tech giants & growth stock forecasts",
        icon: "waveform.path.ecg",
        gradient: LinearGradient(
            colors: [Color(red:0.157,green:0.051,blue:0.353), Color(red:0.310,green:0.106,blue:0.620), Color(red:0.608,green:0.302,blue:0.906)],
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red:0.804,green:0.659,blue:1.000)
    ),
    StockModule(
        id: "hot_stocks", title: "Hot Stocks",
        subtitle: "Trending picks & momentum plays",
        icon: "flame.fill",
        gradient: LinearGradient(
            colors: [Color(red:0.486,green:0.114,blue:0.071), Color(red:0.761,green:0.255,blue:0.047), Color(red:0.976,green:0.451,blue:0.086)],
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red:0.996,green:0.843,blue:0.667)
    ),
    StockModule(
        id: "pre_ipo", title: "Pre-IPO",
        subtitle: "Upcoming IPO opportunity radar",
        icon: "star.circle.fill",
        gradient: LinearGradient(
            colors: [Color(red:0.400,green:0.280,blue:0.020), Color(red:0.620,green:0.450,blue:0.040), Color(red:0.900,green:0.720,blue:0.100)],
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red:1.000,green:0.900,blue:0.600)
    ),
    StockModule(
        id: "crypto", title: "Crypto",
        subtitle: "BTC, ETH & altcoin price signals",
        icon: "bitcoinsign.circle.fill",
        gradient: LinearGradient(
            colors: [Color(red:0.024,green:0.235,blue:0.294), Color(red:0.039,green:0.416,blue:0.514), Color(red:0.063,green:0.675,blue:0.788)],
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red:0.404,green:0.875,blue:0.941)
    ),
    StockModule(
        id: "earnings", title: "Earnings",
        subtitle: "Beat or miss AI forecasts",
        icon: "calendar.badge.clock",
        gradient: LinearGradient(
            colors: [Color(red:0.059,green:0.278,blue:0.220), Color(red:0.082,green:0.475,blue:0.369), Color(red:0.063,green:0.725,blue:0.506)],
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red:0.431,green:0.906,blue:0.718)
    ),
    StockModule(
        id: "sectors", title: "Sectors",
        subtitle: "Sector rotation & performance maps",
        icon: "square.grid.3x3.fill",
        gradient: LinearGradient(
            colors: [Color(red:0.055,green:0.125,blue:0.251), Color(red:0.102,green:0.239,blue:0.451), Color(red:0.157,green:0.408,blue:0.745)],
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red:0.576,green:0.765,blue:0.941)
    ),
    StockModule(
        id: "global", title: "Global Markets",
        subtitle: "International index forecasts",
        icon: "globe.americas.fill",
        gradient: LinearGradient(
            colors: [Color(red:0.078,green:0.243,blue:0.149), Color(red:0.106,green:0.478,blue:0.239), Color(red:0.133,green:0.773,blue:0.369)],
            startPoint: .topLeading, endPoint: .bottomTrailing),
        iconColor: Color(red:0.525,green:0.937,blue:0.675)
    ),
]
