package com.prediction.stockmarket.ui.home

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavController
import com.prediction.stockmarket.data.database.PredictionEntity
import kotlin.math.abs

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    navController: NavController,
    padding: PaddingValues,
    viewModel: HomeViewModel = hiltViewModel()
) {
    val predictions by viewModel.predictions.collectAsState()
    var selectedHorizon by remember { mutableStateOf("1w") }

    Column(modifier = Modifier.fillMaxSize().padding(padding)) {
        TopAppBar(title = { Text("Market") })

        SingleChoiceSegmentedButtonRow(modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)) {
            listOf("1d", "1w", "1m").forEachIndexed { i, h ->
                SegmentedButton(
                    selected = selectedHorizon == h,
                    onClick = { selectedHorizon = h; viewModel.loadPredictions(h) },
                    shape = SegmentedButtonDefaults.itemShape(i, 3),
                    label = { Text(h.uppercase()) }
                )
            }
        }

        if (predictions.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("No predictions yet — sync data first", style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        } else {
            LazyColumn(contentPadding = PaddingValues(vertical = 8.dp)) {
                items(predictions, key = { it.ticker }) { pred ->
                    PredictionListItem(pred) { navController.navigate("stock/${pred.ticker}") }
                }
            }
        }
    }
}

@Composable
private fun PredictionListItem(pred: PredictionEntity, onClick: () -> Unit) {
    val isUp = pred.direction == "UP"
    val dirColor = if (isUp) Color(0xFF4CAF50) else Color(0xFFFF5252)

    ListItem(
        modifier = Modifier.clickable(onClick = onClick),
        headlineContent = { Text(pred.ticker, style = MaterialTheme.typography.titleMedium) },
        supportingContent = {
            Text("%.0f%% confidence · Model: %.0f%%".format(
                pred.probability * 100, pred.modelAccuracy * 100),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant)
        },
        trailingContent = {
            Text(pred.direction, style = MaterialTheme.typography.titleSmall, color = dirColor)
        }
    )
    HorizontalDivider(thickness = 0.5.dp, color = MaterialTheme.colorScheme.surfaceVariant)
}
