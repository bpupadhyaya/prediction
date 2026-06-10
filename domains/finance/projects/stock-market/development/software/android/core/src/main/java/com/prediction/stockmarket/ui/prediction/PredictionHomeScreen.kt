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
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private fun iconForModule(iconName: String): ImageVector = when (iconName) {
    "trending_up"      -> Icons.Default.TrendingUp
    "sports_soccer"    -> Icons.Default.SportsBaseball
    "wb_cloudy"        -> Icons.Default.WbCloudy
    "how_to_vote"      -> Icons.Default.HowToVote
    "currency_bitcoin" -> Icons.Default.CurrencyBitcoin
    "home"             -> Icons.Default.Home
    "favorite"         -> Icons.Default.Favorite
    "bar_chart"        -> Icons.Default.BarChart
    else               -> Icons.Default.Circle
}

// Gradient: deep indigo → royal blue → electric blue (topLeft→bottomRight)
// Mirrors iOS: Color(0x161E50) → Color(0x273688) → Color(0x3B82F6)
private val heroBrush = Brush.linearGradient(
    colors = listOf(
        Color(0xFF161E50),
        Color(0xFF273688),
        Color(0xFF3B82F6),
    ),
    start = Offset(0f, 0f),
    end = Offset(Float.POSITIVE_INFINITY, Float.POSITIVE_INFINITY)
)

@Composable
fun PredictionHomeScreen(onModuleSelect: (String) -> Unit) {
    // Mirrors lifeos HomeView: VStack(spacing:0) { HeroHeader + ScrollView }
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(PredictionColors.homeBg)
    ) {
        PredictionHeroHeader()

        LazyVerticalGrid(
            columns = GridCells.Fixed(2),
            contentPadding = PaddingValues(
                start = 16.dp,
                end = 16.dp,
                top = 12.dp,
                bottom = 24.dp
            ),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            modifier = Modifier.fillMaxSize()
        ) {
            items(predictionModules) { module ->
                PredictionModuleCard(
                    module = module,
                    onClick = { if (module.isAvailable) onModuleSelect(module.id) }
                )
            }
        }
    }
}

// Mirrors lifeos HeroHeader(isHomePage: true):
//   Box(gradient background, extends behind status bar)
//   └─ Column(statusBarsPadding + top:36 + bottom:18, horizontalCenter)
//        ├─ Title  — headlineMedium.bold  white        (= iOS .title.bold())
//        ├─ 4dp spacer
//        ├─ Subtitle — bodyMedium  white/0.8           (= iOS .subheadline)
//        ├─ 10dp spacer
//        └─ Zoe badge — white/0.15 capsule
@Composable
private fun PredictionHeroHeader() {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(heroBrush)
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
                text = "Prediction",
                style = MaterialTheme.typography.headlineMedium.copy(fontWeight = FontWeight.Bold),
                color = Color.White,
                textAlign = TextAlign.Center
            )

            Spacer(Modifier.height(4.dp))

            Text(
                text = "AI-powered forecasts across every domain",
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White.copy(alpha = 0.8f),
                textAlign = TextAlign.Center
            )

            Spacer(Modifier.height(10.dp))

            // Zoe AI badge — white/0.15 capsule, centered
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
                        contentDescription = "Powered by Zoe AI",
                        tint = Color.White.copy(alpha = 0.9f),
                        modifier = Modifier.size(12.dp)
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
private fun PredictionModuleCard(module: PredictionModule, onClick: () -> Unit) {
    val gradient = Brush.linearGradient(
        colors = module.gradientColors,
        start = Offset(0f, 0f),
        end = Offset(Float.POSITIVE_INFINITY, Float.POSITIVE_INFINITY)
    )

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(140.dp)
            .alpha(if (module.isAvailable) 1f else 0.7f)
            .clip(RoundedCornerShape(18.dp))
            .background(gradient)
            .clickable(enabled = module.isAvailable, onClick = onClick)
            .padding(14.dp)
            .semantics { contentDescription = "${module.title}: ${module.subtitle}" }
    ) {
        if (!module.isAvailable) {
            Icon(
                imageVector = Icons.Default.Lock,
                contentDescription = "Coming soon",
                tint = Color.White.copy(alpha = 0.60f),
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .size(16.dp)
            )
        }

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
                    imageVector = iconForModule(module.iconName),
                    contentDescription = null,
                    tint = module.iconColor,
                    modifier = Modifier.size(22.dp)
                )
            }

            Column {
                Text(
                    text = module.title,
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                Spacer(Modifier.height(2.dp))
                Text(
                    text = module.subtitle,
                    style = MaterialTheme.typography.bodySmall,
                    color = Color.White.copy(alpha = 0.70f),
                    lineHeight = 15.sp,
                    maxLines = 2
                )
            }
        }
    }
}
