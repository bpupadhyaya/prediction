package com.prediction.stockmarket.ui.watchlist

import androidx.compose.animation.animateItemPlacement
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.StarOutline
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavController
import com.prediction.stockmarket.data.database.WatchlistEntity

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WatchlistScreen(
    navController: NavController,
    padding: PaddingValues,
    viewModel: WatchlistViewModel = hiltViewModel()
) {
    val watchlist by viewModel.watchlist.collectAsState()
    val prices by viewModel.prices.collectAsState()
    val predictions by viewModel.predictions.collectAsState()

    Column(modifier = Modifier.fillMaxSize().padding(padding)) {
        TopAppBar(
            title = { Text("Watchlist") },
            colors = TopAppBarDefaults.mediumTopAppBarColors()
        )

        if (watchlist.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.StarOutline,
                        contentDescription = null,
                        modifier = Modifier.size(48.dp),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        "Star a stock to add it here",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        } else {
            LazyColumn {
                items(watchlist, key = { it.ticker }) { entry ->
                    WatchlistListItem(
                        ticker = entry.ticker,
                        price = prices[entry.ticker],
                        direction = predictions[entry.ticker]?.direction,
                        probability = predictions[entry.ticker]?.probability,
                        onClick = {
                            if (entry.ticker.isNotBlank()) {
                                navController.navigate("stock/${entry.ticker}")
                            }
                        }
                    )
                    HorizontalDivider(thickness = 0.5.dp, color = MaterialTheme.colorScheme.surfaceVariant)
                }
            }
        }
    }
}

@Composable
private fun WatchlistListItem(
    ticker: String,
    price: Double?,
    direction: String?,
    probability: Double?,
    onClick: () -> Unit
) {
    val isUp = direction == "UP"
    val dirColor = if (isUp) Color(0xFF4CAF50) else Color(0xFFFF5252)

    ListItem(
        modifier = Modifier
            .fillMaxWidth()
            .animateItemPlacement()
            .clickable(onClick = onClick),
        headlineContent = {
            Text(ticker, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
        },
        supportingContent = {
            if (probability != null && direction != null) {
                Text(
                    "%.0f%% %s".format(probability * 100, direction),
                    style = MaterialTheme.typography.bodySmall,
                    fontWeight = FontWeight.Medium,
                    color = dirColor
                )
            }
        },
        trailingContent = {
            price?.let {
                Text(
                    "$%.2f".format(it),
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold
                )
            }
        }
    )
}
