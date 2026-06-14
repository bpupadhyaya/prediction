package com.prediction.stockmarket.ui.trackrecord

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.prediction.stockmarket.data.database.TrackedPredictionEntity
import java.text.SimpleDateFormat
import java.util.Locale

private val HORIZONS = listOf("1d", "1w", "1m")
private val ACCENT = Color(0xFF3B82F6)
private val UP_GREEN = Color(0xFF4CAF50)
private val DOWN_RED = Color(0xFFFF5252)
private val dateFmt = SimpleDateFormat("MMM d, yyyy", Locale.US)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TrackRecordScreen(
    onBack: () -> Unit,
    viewModel: TrackRecordViewModel = hiltViewModel()
) {
    val ui by viewModel.uiState.collectAsState()
    var showClearConfirm by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) { viewModel.load() }

    val record = ui.record
    val scored = record.filter { it.resolved && it.direction != "NEUTRAL" && it.correct != null }
    val hits = scored.count { it.correct == true }
    val hitRate = if (scored.isNotEmpty()) hits.toDouble() / scored.size * 100 else null
    val pending = record.count { !it.resolved }

    if (showClearConfirm) {
        AlertDialog(
            onDismissRequest = { showClearConfirm = false },
            title = { Text("Clear track record?") },
            text = { Text("Clear your entire prediction track record? This cannot be undone.") },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.clear(); showClearConfirm = false
                }) { Text("Clear", color = DOWN_RED) }
            },
            dismissButton = {
                TextButton(onClick = { showClearConfirm = false }) { Text("Cancel") }
            }
        )
    }

    Scaffold(
        containerColor = Color(0xFF0B1526),
        topBar = {
            TopAppBar(
                title = { Text("Track Record") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    if (record.isNotEmpty()) {
                        TextButton(onClick = { showClearConfirm = true }) {
                            Text("Clear", color = Color.White.copy(alpha = 0.8f))
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color(0xFF0D1F36),
                    titleContentColor = Color.White,
                    navigationIconContentColor = Color.White
                )
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Text(
                "Every prediction you view is logged on-device and scored against the real price once its horizon elapses — your model's honest, personal hit rate. Nothing leaves your phone.",
                style = MaterialTheme.typography.bodySmall,
                color = Color.White.copy(alpha = 0.65f)
            )

            ui.resolvingMessage?.let {
                Text(it, style = MaterialTheme.typography.bodySmall, color = ACCENT)
            }

            if (ui.loaded && record.isEmpty()) {
                EmptyState()
            } else if (record.isNotEmpty()) {
                SummaryCard(hitRate, hits, scored.size, pending) { h ->
                    val s = scored.filter { it.horizon == h }
                    val r = if (s.isNotEmpty()) s.count { it.correct == true }.toDouble() / s.size * 100 else null
                    s.size to r
                }
                PredictionList(record.sortedByDescending { it.predictedAt })
            }
        }
    }
}

@Composable
private fun EmptyState() {
    Surface(
        shape = RoundedCornerShape(12.dp),
        color = Color(0xFF11233D)
    ) {
        Text(
            "No predictions logged yet. Open a ticker and view its prediction (any horizon) and it will appear here; come back after the horizon (1d / 1w / 1m) to see whether it was right.",
            modifier = Modifier.padding(16.dp),
            style = MaterialTheme.typography.bodyMedium,
            color = Color.White.copy(alpha = 0.7f)
        )
    }
}

@Composable
private fun SummaryCard(
    hitRate: Double?,
    hits: Int,
    scoredCount: Int,
    pending: Int,
    horizonStat: (String) -> Pair<Int, Double?>,
) {
    Surface(shape = RoundedCornerShape(12.dp), color = Color(0xFF11233D)) {
        Column(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Row(verticalAlignment = Alignment.Top) {
                Column {
                    Text(
                        hitRate?.let { "%.0f%%".format(it) } ?: "—",
                        style = MaterialTheme.typography.displaySmall.copy(fontWeight = FontWeight.Black),
                        color = ACCENT
                    )
                    Text(
                        if (scoredCount == 0) "hit rate" else "hit rate · $hits/$scoredCount scored",
                        style = MaterialTheme.typography.bodySmall,
                        color = Color.White.copy(alpha = 0.6f)
                    )
                }
                Spacer(Modifier.weight(1f))
                if (pending > 0) {
                    Text(
                        "$pending still maturing",
                        style = MaterialTheme.typography.bodySmall,
                        color = Color.White.copy(alpha = 0.6f)
                    )
                }
            }

            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                HORIZONS.forEach { h ->
                    val (n, rate) = horizonStat(h)
                    Column(
                        modifier = Modifier.weight(1f),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(h.uppercase(), style = MaterialTheme.typography.labelSmall, color = Color.White.copy(alpha = 0.6f))
                        Text(
                            rate?.let { "%.0f%%".format(it) } ?: "—",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                        Text("$n scored", style = MaterialTheme.typography.labelSmall, color = Color.White.copy(alpha = 0.5f))
                    }
                }
            }
        }
    }
}

@Composable
private fun PredictionList(items: List<TrackedPredictionEntity>) {
    Surface(shape = RoundedCornerShape(12.dp), color = Color(0xFF11233D)) {
        Column(modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp)) {
            items.forEachIndexed { i, p ->
                PredictionRow(p)
                if (i != items.lastIndex) {
                    HorizontalDivider(color = Color.White.copy(alpha = 0.08f))
                }
            }
        }
    }
}

@Composable
private fun PredictionRow(p: TrackedPredictionEntity) {
    val dirLabel = when (p.direction) {
        "UP" -> "Bullish"; "DOWN" -> "Bearish"; else -> "Neutral"
    }
    val dirColor = when (p.direction) {
        "UP" -> UP_GREEN; "DOWN" -> DOWN_RED; else -> Color.White.copy(alpha = 0.6f)
    }
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text(p.ticker, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold, color = Color.White)
        Surface(shape = RoundedCornerShape(4.dp), color = Color.White.copy(alpha = 0.08f)) {
            Text(
                p.horizon,
                modifier = Modifier.padding(horizontal = 5.dp, vertical = 1.dp),
                style = MaterialTheme.typography.labelSmall,
                color = Color.White.copy(alpha = 0.65f)
            )
        }
        Text(
            "$dirLabel ${"%.0f%%".format(p.probability * 100)}",
            style = MaterialTheme.typography.bodySmall,
            color = dirColor
        )
        Spacer(Modifier.weight(1f))
        Outcome(p)
    }
}

@Composable
private fun Outcome(p: TrackedPredictionEntity) {
    if (p.resolved && p.direction != "NEUTRAL") {
        val ok = p.correct == true
        val color = if (ok) UP_GREEN else DOWN_RED
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(3.dp)) {
            Icon(
                if (ok) Icons.Default.Check else Icons.Default.Close,
                contentDescription = if (ok) "correct" else "incorrect",
                tint = color,
                modifier = Modifier.size(16.dp)
            )
            p.actualReturnPct?.let {
                Text(
                    "${if (it >= 0) "+" else ""}${"%.1f".format(it)}%",
                    style = MaterialTheme.typography.bodySmall,
                    fontWeight = FontWeight.Bold,
                    color = color
                )
            }
        }
    } else if (p.resolved) {
        Text(
            p.actualReturnPct?.let { "${if (it >= 0) "+" else ""}${"%.1f".format(it)}%" } ?: "—",
            style = MaterialTheme.typography.bodySmall,
            color = Color.White.copy(alpha = 0.6f)
        )
    } else {
        Text(
            "matures ${dateFmt.format(p.maturesAt)}",
            style = MaterialTheme.typography.labelSmall,
            color = Color.White.copy(alpha = 0.55f)
        )
    }
}
