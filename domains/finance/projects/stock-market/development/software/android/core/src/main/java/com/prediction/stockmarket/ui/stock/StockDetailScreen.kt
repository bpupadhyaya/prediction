package com.prediction.stockmarket.ui.stock

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.outlined.StarOutline
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavController
import com.prediction.stockmarket.data.database.PredictionEntity

private val DIRECTION_HORIZONS = listOf("1d", "1w", "1m")

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun StockDetailScreen(
    ticker: String,
    navController: NavController,
    onInteractivePredict: (String) -> Unit = {},
    viewModel: StockDetailViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    LaunchedEffect(ticker) {
        if (ticker.isNotBlank()) viewModel.load(ticker)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(ticker.ifBlank { "Stock Detail" }) },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.toggleWatchlist() }) {
                        Icon(
                            if (uiState.isWatchlisted) Icons.Default.Star else Icons.Outlined.StarOutline,
                            contentDescription = if (uiState.isWatchlisted) "Remove from watchlist" else "Add to watchlist",
                            tint = if (uiState.isWatchlisted) Color(0xFFFFC107) else LocalContentColor.current
                        )
                    }
                },
                colors = TopAppBarDefaults.mediumTopAppBarColors()
            )
        }
    ) { padding ->
        if (uiState.isLoading) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .verticalScroll(rememberScrollState())
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                uiState.errorMessage?.let { error ->
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)
                    ) {
                        Text(
                            text = error,
                            modifier = Modifier.padding(12.dp),
                            color = MaterialTheme.colorScheme.onErrorContainer,
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                }

                uiState.latestPrice?.let { price ->
                    Text(
                        "$%.2f".format(price),
                        style = MaterialTheme.typography.displaySmall,
                        fontWeight = FontWeight.Bold
                    )
                }

                uiState.prediction?.let { pred ->
                    PredictionCard(pred, viewModel::onHorizonChange)
                }

                // Interactive prediction entry point
                Button(
                    onClick = { onInteractivePredict(ticker) },
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF1A3A5C)
                    )
                ) {
                    Icon(
                        Icons.Default.AutoAwesome,
                        contentDescription = null,
                        tint = Color(0xFF7DD3F8),
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(Modifier.width(8.dp))
                    Text(
                        "Interactive Predict",
                        color = Color(0xFF7DD3F8),
                        fontWeight = FontWeight.SemiBold
                    )
                }

                Text(
                    "This is a probabilistic prediction, not financial advice.",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
@OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)
private fun PredictionCard(pred: PredictionEntity, onHorizonChange: (String) -> Unit) {
    val isUp = pred.direction == "UP"
    val dirColor = if (isUp) Color(0xFF4CAF50) else Color(0xFFFF5252)

    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("Prediction", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)

            SingleChoiceSegmentedButtonRow(modifier = Modifier.fillMaxWidth()) {
                DIRECTION_HORIZONS.forEachIndexed { i, h ->
                    SegmentedButton(
                        selected = pred.horizon == h,
                        onClick = { onHorizonChange(h) },
                        shape = SegmentedButtonDefaults.itemShape(i, DIRECTION_HORIZONS.size),
                        label = { Text(h.uppercase()) }
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
        Text(value, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = valueColor)
        Text(
            label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}
