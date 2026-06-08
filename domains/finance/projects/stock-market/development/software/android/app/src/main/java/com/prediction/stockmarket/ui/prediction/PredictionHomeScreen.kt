package com.prediction.stockmarket.ui.prediction

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
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

@Composable
fun PredictionHomeScreen(onModuleSelect: (String) -> Unit) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(PredictionColors.homeBg)
    ) {
        LazyVerticalGrid(
            columns = GridCells.Fixed(2),
            contentPadding = PaddingValues(
                start = 16.dp,
                end = 16.dp,
                top = 0.dp,
                bottom = 24.dp
            ),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Hero header — full width span
            item(span = { GridItemSpan(2) }) {
                PredictionHeroHeader()
            }

            // Module cards
            items(predictionModules) { module ->
                PredictionModuleCard(
                    module = module,
                    onClick = { if (module.isAvailable) onModuleSelect(module.id) }
                )
            }
        }
    }
}

@Composable
private fun PredictionHeroHeader() {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(PredictionColors.headerBg)
            .padding(start = 20.dp, end = 20.dp, top = 56.dp, bottom = 20.dp)
    ) {
        // Zoe orb top-right
        Box(
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(top = 0.dp)
                .size(44.dp)
                .clip(CircleShape)
                .background(
                    Brush.radialGradient(
                        listOf(Color(0xFF9B72F5), Color(0xFF6B4FD8))
                    )
                ),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = Icons.Default.AutoAwesome,
                contentDescription = "Zoe AI",
                tint = Color.White,
                modifier = Modifier.size(22.dp)
            )
        }

        Column(
            modifier = Modifier.fillMaxWidth().padding(end = 56.dp)
        ) {
            Text(
                text = "Prediction",
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold,
                color = PredictionColors.textPrimary
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "AI-powered forecasts across every domain",
                fontSize = 13.sp,
                color = PredictionColors.textSecondary,
                lineHeight = 18.sp
            )
            Spacer(modifier = Modifier.height(14.dp))

            // Powered by Zoe pill badge
            Surface(
                shape = RoundedCornerShape(20.dp),
                color = PredictionColors.accent.copy(alpha = 0.18f),
                modifier = Modifier.wrapContentSize()
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 5.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(5.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Bolt,
                        contentDescription = null,
                        tint = PredictionColors.accent,
                        modifier = Modifier.size(12.dp)
                    )
                    Text(
                        text = "Powered by Zoe AI · All predictions run on-device",
                        fontSize = 11.sp,
                        color = PredictionColors.accent,
                        fontWeight = FontWeight.Medium
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
        start = androidx.compose.ui.geometry.Offset(0f, 0f),
        end = androidx.compose.ui.geometry.Offset(Float.POSITIVE_INFINITY, Float.POSITIVE_INFINITY)
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
    ) {
        // Lock icon top-right for unavailable modules
        if (!module.isAvailable) {
            Icon(
                imageVector = Icons.Default.Lock,
                contentDescription = "Coming soon",
                tint = Color.White.copy(alpha = 0.6f),
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .size(16.dp)
            )
        }

        Column(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            // Icon in rounded box
            Box(
                modifier = Modifier
                    .size(36.dp)
                    .clip(RoundedCornerShape(10.dp))
                    .background(Color.White.copy(alpha = 0.15f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = iconForModule(module.iconName),
                    contentDescription = module.title,
                    tint = module.iconColor,
                    modifier = Modifier.size(20.dp)
                )
            }

            // Title + subtitle at bottom
            Column {
                Text(
                    text = module.title,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = module.subtitle,
                    fontSize = 11.sp,
                    color = Color.White.copy(alpha = 0.55f),
                    lineHeight = 14.sp,
                    maxLines = 2
                )
            }
        }
    }
}
