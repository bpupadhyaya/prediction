package com.prediction.stockmarket.ui.stock

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.outlined.StarOutline
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavController
import com.prediction.stockmarket.data.database.PredictionEntity

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun StockDetailScreen(
    ticker: String,
    navController: NavController,
    viewModel: StockDetailViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    LaunchedEffect(ticker) { viewModel.load(ticker) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(ticker) },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.toggleWatchlist() }) {
                        Icon(
                            if (uiState.isWatchlisted) Icons.Default.Star else Icons.Outlined.StarOutline,
                            contentDescription = "Watchlist",
                            tint = if (uiState.isWatchlisted) Color(0xFFFFC107) else LocalContentColor.current
                        )
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            uiState.latestPrice?.let { price ->
                Text("$%.2f".format(price), style = MaterialTheme.typography.displaySmall)
            }

            uiState.prediction?.let { pred ->
                PredictionCard(pred, viewModel::onHorizonChange)
            }

            Text(
                "This is a probabilistic prediction, not financial advice.",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
private fun PredictionCard(pred: PredictionEntity, onHorizonChange: (String) -> Unit) {
    val isUp = pred.direction == "UP"
    val dirColor = if (isUp) Color(0xFF4CAF50) else Color(0xFFFF5252)

    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("Prediction", style = MaterialTheme.typography.titleMedium)

            SingleChoiceSegmentedButtonRow {
                listOf("1d", "1w", "1m").forEachIndexed { i, h ->
                    SegmentedButton(
                        selected = pred.horizon == h,
                        onClick = { onHorizonChange(h) },
                        shape = SegmentedButtonDefaults.itemShape(i, 3),
                        label = { Text(h) }
                    )
                }
            }

            Row(horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                StatCell("Direction", pred.direction, dirColor)
                StatCell("Confidence", "%.0f%%".format(pred.probability * 100))
                StatCell("Model Acc.", "%.0f%%".format(pred.modelAccuracy * 100))
            }
        }
    }
}

@Composable
private fun StatCell(label: String, value: String, valueColor: Color = MaterialTheme.colorScheme.onSurface) {
    Column(horizontalAlignment = Alignment.Start) {
        Text(value, style = MaterialTheme.typography.titleLarge, color = valueColor)
        Text(label, style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}
