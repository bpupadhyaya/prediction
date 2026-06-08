package com.prediction.stockmarket.ui.prediction

import androidx.compose.ui.graphics.Color

object PredictionColors {
    // Home — deep cosmic blue representing the future/unknown
    val homeBg        = Color(0xFF0B1526)
    val headerBg      = Color(0xFF0E1E38)
    val accent        = Color(0xFF3B82F6)   // electric blue
    val accentGold    = Color(0xFFFFB800)   // gold
    val accentPurple  = Color(0xFF6B4FD8)   // indigo/purple
    val textPrimary   = Color.White
    val textSecondary = Color(0xFFA8B8CC)
    val textMuted     = Color(0xFF667080)

    // Light theme for inner pages (domains/settings style)
    val pageBg        = Color(0xFFF2F2F7)
    val cardBg        = Color.White
    val textDark      = Color(0xFF1C1C1E)
    val textDarkMuted = Color(0xFF8A8A8E)
}

data class PredictionModule(
    val id: String,
    val title: String,
    val subtitle: String,
    val iconName: String,
    val gradientColors: List<Color>,
    val iconColor: Color,
    val isAvailable: Boolean
)

val predictionModules = listOf(
    PredictionModule(
        "stock_market", "Stock Market", "AI-powered price predictions", "trending_up",
        listOf(Color(0xFF0C3B6E), Color(0xFF0369A1), Color(0xFF0EA5E9)), Color(0xFF7DD3FC), true
    ),
    PredictionModule(
        "sports", "Sports", "Game outcomes & player stats", "sports_soccer",
        listOf(Color(0xFF14532D), Color(0xFF15803D), Color(0xFF22C55E)), Color(0xFF86EFAC), false
    ),
    PredictionModule(
        "weather", "Weather", "Extended forecasts with AI", "wb_cloudy",
        listOf(Color(0xFF7C1D12), Color(0xFFC2410C), Color(0xFFF97316)), Color(0xFFFED7AA), false
    ),
    PredictionModule(
        "elections", "Elections", "Political outcome forecasts", "how_to_vote",
        listOf(Color(0xFF2E1065), Color(0xFF6D28D9), Color(0xFFA855F7)), Color(0xFFD8B4FE), false
    ),
    PredictionModule(
        "crypto", "Crypto", "Cryptocurrency price signals", "currency_bitcoin",
        listOf(Color(0xFF0A3F54), Color(0xFF0B6677), Color(0xFF0E8E8E)), Color(0xFF66DDDD), false
    ),
    PredictionModule(
        "real_estate", "Real Estate", "Property value trends", "home",
        listOf(Color(0xFF0F473E), Color(0xFF156B3D), Color(0xFF1E9B5D)), Color(0xFF86E3AC), false
    ),
    PredictionModule(
        "health", "Health Trends", "Disease & outbreak forecasts", "favorite",
        listOf(Color(0xFF662B42), Color(0xFF9E2D56), Color(0xFFD14F7D)), Color(0xFFF5B2CC), false
    ),
    PredictionModule(
        "economy", "Economy", "Macro indicators & forecasts", "bar_chart",
        listOf(Color(0xFF29105E), Color(0xFF4F289F), Color(0xFF7A4FD0)), Color(0xFFBFB8F6), false
    ),
)
