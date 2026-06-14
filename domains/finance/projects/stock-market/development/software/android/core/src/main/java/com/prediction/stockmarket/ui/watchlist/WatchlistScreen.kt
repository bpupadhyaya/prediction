package com.prediction.stockmarket.ui.watchlist

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Bolt
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
    val rankState by viewModel.rankState.collectAsState()

    Column(modifier = Modifier.fillMaxSize().padding(padding)) {
        TopAppBar(
            title = { Text("Watchlist") },
            colors = TopAppBarDefaults.mediumTopAppBarColors(),
            actions = {
                if (watchlist.isNotEmpty()) {
                    val active = rankState.enabled
                    TextButton(onClick = { viewModel.toggleRanked() }) {
                        Icon(
                            imageVector = Icons.Default.Bolt,
                            contentDescription = null,
                            modifier = Modifier.size(18.dp),
                            tint = if (active) MaterialTheme.colorScheme.primary
                                   else MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Spacer(Modifier.size(4.dp))
                        Text(
                            if (active) "Default" else "Rank by conviction",
                            color = if (active) MaterialTheme.colorScheme.primary
                                    else MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            },
        )

        if (rankState.isScanning && rankState.rows.isEmpty()) {
            LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
        }
        if (rankState.enabled && rankState.total > 0) {
            Text(
                "1-week outlook · ranked by P(up) · ${rankState.scanned}/${rankState.total}",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 6.dp),
            )
        }

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
        } else if (rankState.enabled) {
            LazyColumn {
                itemsIndexed(rankState.rows) { idx, row ->
                    RankedListItem(
                        rank = idx + 1,
                        ticker = row.ticker,
                        direction = row.direction,
                        probUp = row.probUp,
                        price = prices[row.ticker],
                        onClick = {
                            if (row.ticker.isNotBlank()) navController.navigate("stock/${row.ticker}")
                        },
                    )
                    HorizontalDivider(thickness = 0.5.dp, color = MaterialTheme.colorScheme.surfaceVariant)
                }
                if (!rankState.isScanning && rankState.rows.isEmpty()) {
                    item {
                        Text(
                            "No ranked predictions yet — tickers need at least ~1y of price history.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.padding(16.dp),
                        )
                    }
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

@Composable
private fun RankedListItem(
    rank: Int,
    ticker: String,
    direction: String,
    probUp: Double,
    price: Double?,
    onClick: () -> Unit,
) {
    ListItem(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        leadingContent = {
            Text(
                "$rank",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        },
        headlineContent = {
            Text(ticker, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
        },
        supportingContent = { ConvictionBadge(direction, probUp) },
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

// Matches the Crypto Radar conviction badge styling.
@Composable
private fun ConvictionBadge(direction: String, probUp: Double) {
    val (label, bg, fg) = if (direction.uppercase() == "UP")
        Triple("▲ Bullish ${(probUp * 100).toInt()}%", Color(0xFF14532D), Color(0xFF4ADE80))
    else
        Triple("▼ Bearish ${((1.0 - probUp) * 100).toInt()}%", Color(0xFF601A1A), Color(0xFFF87171))
    Surface(shape = RoundedCornerShape(8.dp), color = bg) {
        Text(
            label,
            style = MaterialTheme.typography.labelMedium.copy(fontWeight = FontWeight.Bold),
            color = fg,
            modifier = Modifier.padding(horizontal = 9.dp, vertical = 5.dp),
        )
    }
}
