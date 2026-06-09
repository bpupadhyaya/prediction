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
        listOf(Color(0xFF0C3B6E), Color(0xFF1A69A2), Color(0xFF0EA5E9)), Color(0xFF7DD3F8), true
    ),
    PredictionModule(
        "sports", "Sports", "Game outcomes & player stats", "sports_soccer",
        listOf(Color(0xFF143E26), Color(0xFF1B7A3D), Color(0xFF22C55E)), Color(0xFF86EFAC), true
    ),
    PredictionModule(
        "weather", "Weather", "Extended forecasts with AI", "wb_cloudy",
        listOf(Color(0xFF7C1D12), Color(0xFFC2410C), Color(0xFFF97316)), Color(0xFFFED7AA), true
    ),
    PredictionModule(
        "elections", "Elections", "Political outcome forecasts", "how_to_vote",
        listOf(Color(0xFF280D5A), Color(0xFF4F1B9E), Color(0xFF9B4DE7)), Color(0xFFCDA8FF), true
    ),
    PredictionModule(
        "crypto", "Crypto", "Cryptocurrency price signals", "currency_bitcoin",
        listOf(Color(0xFF063C4B), Color(0xFF0A6A83), Color(0xFF10ACC9)), Color(0xFF67DFF0), true
    ),
    PredictionModule(
        "real_estate", "Real Estate", "Property value trends", "home",
        listOf(Color(0xFF0F4738), Color(0xFF15795E), Color(0xFF10B981)), Color(0xFF6EE7B7), true
    ),
    PredictionModule(
        "health", "Health Trends", "Disease & outbreak forecasts", "favorite",
        listOf(Color(0xFF550A30), Color(0xFF9B1B56), Color(0xFFEC4899)), Color(0xFFF9A8D4), true
    ),
    PredictionModule(
        "economy", "Economy", "Macro indicators & forecasts", "bar_chart",
        listOf(Color(0xFF0E2040), Color(0xFF1A3D73), Color(0xFF2868BE)), Color(0xFF93C3F0), true
    ),
)
