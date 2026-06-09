package com.prediction.stockmarket.ui.prediction

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private data class StockSection(
    val id: String,
    val title: String,
    val subtitle: String,
    val icon: ImageVector,
    val gradientColors: List<Color>,
    val iconColor: Color
)

private val stockSections = listOf(
    StockSection(
        "sp500", "S&P 500", "Top 500 US company AI forecasts",
        Icons.Default.TrendingUp,
        listOf(Color(0xFF0C3B6E), Color(0xFF1A69A2), Color(0xFF0EA5E9)),
        Color(0xFF7DD3F8)
    ),
    StockSection(
        "nasdaq100", "Nasdaq 100", "Tech giants & growth stock forecasts",
        Icons.Default.ShowChart,
        listOf(Color(0xFF280D5A), Color(0xFF4F1B9E), Color(0xFF9B4DE7)),
        Color(0xFFCDA8FF)
    ),
    StockSection(
        "hot_stocks", "Hot Stocks", "Trending picks & momentum plays",
        Icons.Default.Whatshot,
        listOf(Color(0xFF7C1D12), Color(0xFFC2410C), Color(0xFFF97316)),
        Color(0xFFFED7AA)
    ),
    StockSection(
        "pre_ipo", "Pre-IPO", "Upcoming IPO opportunity radar",
        Icons.Default.Stars,
        listOf(Color(0xFF664800), Color(0xFF9E7306), Color(0xFFE6B819)),
        Color(0xFFFFE699)
    ),
    StockSection(
        "crypto", "Crypto", "BTC, ETH & altcoin price signals",
        Icons.Default.CurrencyBitcoin,
        listOf(Color(0xFF063C4B), Color(0xFF0A6A83), Color(0xFF10ACC9)),
        Color(0xFF67DFF0)
    ),
    StockSection(
        "earnings", "Earnings", "Beat or miss AI forecasts",
        Icons.Default.CalendarMonth,
        listOf(Color(0xFF0F4738), Color(0xFF157A5E), Color(0xFF10B981)),
        Color(0xFF6EE7B7)
    ),
    StockSection(
        "sectors", "Sectors", "Sector rotation & performance maps",
        Icons.Default.GridView,
        listOf(Color(0xFF0E2040), Color(0xFF1A3D73), Color(0xFF2868BE)),
        Color(0xFF93C3F0)
    ),
    StockSection(
        "global", "Global Markets", "International index forecasts",
        Icons.Default.Public,
        listOf(Color(0xFF143E26), Color(0xFF1B7A3D), Color(0xFF22C55E)),
        Color(0xFF86EFAC)
    ),
)

val marketSectionIds = setOf("sp500", "nasdaq100", "hot_stocks", "pre_ipo")

private val stockHeroBrush = Brush.linearGradient(
    colors = listOf(
        Color(0xFF0C3B6E),
        Color(0xFF1A69A2),
        Color(0xFF0EA5E9),
    ),
    start = Offset(0f, 0f),
    end = Offset(Float.POSITIVE_INFINITY, Float.POSITIVE_INFINITY)
)

@Composable
fun StockPredictionHomeScreen(onSectionSelect: (String) -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(PredictionColors.homeBg)
    ) {
        StockHeroHeader()

        LazyVerticalGrid(
            columns = GridCells.Fixed(2),
            contentPadding = PaddingValues(
                start = 16.dp, end = 16.dp, top = 12.dp, bottom = 24.dp
            ),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            modifier = Modifier.fillMaxSize()
        ) {
            items(stockSections) { section ->
                StockSectionCard(section = section, onClick = { onSectionSelect(section.id) })
            }
        }
    }
}

@Composable
private fun StockHeroHeader() {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(stockHeroBrush)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .statusBarsPadding()
                .padding(top = 8.dp, bottom = 12.dp)
                .padding(horizontal = 16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "Stock Prediction",
                style = MaterialTheme.typography.headlineMedium.copy(fontWeight = FontWeight.Bold),
                color = Color.White,
                textAlign = TextAlign.Center
            )

            Spacer(Modifier.height(4.dp))

            Text(
                text = "AI-powered stock market forecasts",
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White.copy(alpha = 0.8f),
                textAlign = TextAlign.Center
            )

            Spacer(Modifier.height(10.dp))

            Surface(
                shape = RoundedCornerShape(50.dp),
                color = Color.White.copy(alpha = 0.15f)
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(5.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.AutoAwesome,
                        contentDescription = null,
                        tint = Color.White.copy(alpha = 0.9f),
                        modifier = Modifier.size(10.dp)
                    )
                    Text(
                        text = "Powered by Zoe AI · All predictions run on-device",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Medium,
                        color = Color.White.copy(alpha = 0.9f)
                    )
                }
            }
        }
    }
}

@Composable
private fun StockSectionCard(section: StockSection, onClick: () -> Unit) {
    val gradient = Brush.linearGradient(
        colors = section.gradientColors,
        start = Offset(0f, 0f),
        end = Offset(Float.POSITIVE_INFINITY, Float.POSITIVE_INFINITY)
    )

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(140.dp)
            .clip(RoundedCornerShape(18.dp))
            .background(gradient)
            .clickable(onClick = onClick)
            .padding(14.dp)
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(RoundedCornerShape(10.dp))
                    .background(Color.White.copy(alpha = 0.20f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = section.icon,
                    contentDescription = section.title,
                    tint = section.iconColor,
                    modifier = Modifier.size(22.dp)
                )
            }

            Column {
                Text(
                    text = section.title,
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                Spacer(Modifier.height(2.dp))
                Text(
                    text = section.subtitle,
                    style = MaterialTheme.typography.bodySmall,
                    color = Color.White.copy(alpha = 0.50f),
                    lineHeight = 15.sp,
                    maxLines = 2
                )
            }
        }
    }
}
