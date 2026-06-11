package com.prediction.stockmarket.ui.videointelligence

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.prediction.stockmarket.videointelligence.*
import java.text.SimpleDateFormat
import java.util.*

// Domain color palette
private val DOMAIN_COLORS = mapOf(
    "equity"    to Color(0xFF1565C0),
    "crypto"    to Color(0xFFE65100),
    "macro"     to Color(0xFF4A148C),
    "sector"    to Color(0xFF1B5E20),
    "commodity" to Color(0xFF827717),
    "forex"     to Color(0xFF006064),
    "rates"     to Color(0xFF880E4F),
    "sentiment" to Color(0xFF37474F),
)

private val TIME_RANGE_OPTIONS = listOf(
    1 to "24h",
    7 to "1w",
    30 to "1m",
    90 to "3m",
    180 to "6m",
    365 to "1y",
    365 * 5 to "5y",
    365 * 10 to "10y",
    365 * 20 to "20y",
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VideoIntelligenceScreen(
    viewModel: VideoIntelligenceViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    var showTrackedSpeakers by remember { mutableStateOf(false) }
    var addChannelDialog by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0B1526))
    ) {
        // Top bar
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    Brush.linearGradient(
                        colors = listOf(Color(0xFF0D1F36), Color(0xFF142B47)),
                        start = Offset(0f, 0f),
                        end = Offset(Float.POSITIVE_INFINITY, 0f)
                    )
                )
                .statusBarsPadding()
                .padding(horizontal = 16.dp, vertical = 12.dp)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    Icons.Default.VideoLibrary,
                    contentDescription = null,
                    tint = Color(0xFF4FC3F7),
                    modifier = Modifier.size(24.dp)
                )
                Spacer(Modifier.width(10.dp))
                Column {
                    Text(
                        "Video Intelligence",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                    Text(
                        "YouTube → Transcribe → Market Signals",
                        style = MaterialTheme.typography.labelSmall,
                        color = Color.White.copy(alpha = 0.6f)
                    )
                }
            }
        }

        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(bottom = 80.dp)
        ) {
            // URL input card
            item {
                UrlInputCard(
                    urlInput = uiState.urlInput,
                    isProcessing = uiState.isProcessing,
                    progress = uiState.processingProgress,
                    statusMessage = uiState.processingMessage,
                    errorMessage = uiState.errorMessage,
                    onUrlChange = { viewModel.onUrlInputChange(it) },
                    onSubmit = { viewModel.onUrlSubmit(uiState.urlInput) }
                )
            }

            // Time range chips
            item {
                TimeRangeChips(
                    selected = uiState.selectedTimeRangeDays,
                    onSelect = { viewModel.onTimeRangeChange(it) }
                )
            }

            // Ticker filter
            item {
                TickerFilterRow(
                    ticker = uiState.tickerFilter,
                    onChange = { viewModel.onTickerFilterChange(it) }
                )
            }

            // Tracked speakers section
            item {
                TrackedSpeakersSection(
                    channels = uiState.trackedChannels,
                    expanded = showTrackedSpeakers,
                    onToggle = { showTrackedSpeakers = !showTrackedSpeakers },
                    onAddChannel = { addChannelDialog = true },
                    onRemove = { viewModel.onRemoveChannel(it) }
                )
            }

            // Whisper model hint
            item {
                WhisperModelHintCard()
            }

            // Signals section header
            item {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        "Market Signals",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.SemiBold,
                        color = Color.White
                    )
                    Spacer(Modifier.width(8.dp))
                    if (uiState.signals.isNotEmpty()) {
                        Surface(
                            shape = RoundedCornerShape(12.dp),
                            color = Color(0xFF1A3D73)
                        ) {
                            Text(
                                "${uiState.signals.size}",
                                style = MaterialTheme.typography.labelSmall,
                                color = Color(0xFF90CAF9),
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp)
                            )
                        }
                    }
                }
            }

            // Signal cards or empty state
            if (uiState.signals.isEmpty()) {
                item {
                    EmptySignalsCard()
                }
            } else {
                items(uiState.signals, key = { it.id }) { signal ->
                    SignalCard(
                        signal = signal,
                        videoSource = uiState.recentVideos.firstOrNull { it.id == signal.videoId },
                        onApply = { viewModel.onApplySignal(signal) }
                    )
                }
            }
        }
    }

    // Add channel dialog
    if (addChannelDialog) {
        AddChannelDialog(
            onDismiss = { addChannelDialog = false },
            onAdd = { channelId, name, speaker ->
                viewModel.onTrackChannel(channelId, name, speaker)
                addChannelDialog = false
            }
        )
    }
}

// ─── URL Input Card ───────────────────────────────────────────────────────────

@Composable
private fun UrlInputCard(
    urlInput: String,
    isProcessing: Boolean,
    progress: Float,
    statusMessage: String,
    errorMessage: String?,
    onUrlChange: (String) -> Unit,
    onSubmit: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 12.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0D1F36)),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                "Analyze YouTube Video",
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.SemiBold,
                color = Color.White
            )
            Spacer(Modifier.height(10.dp))

            OutlinedTextField(
                value = urlInput,
                onValueChange = onUrlChange,
                modifier = Modifier.fillMaxWidth(),
                placeholder = {
                    Text(
                        "https://youtube.com/watch?v=...",
                        color = Color.White.copy(alpha = 0.4f),
                        style = MaterialTheme.typography.bodyMedium
                    )
                },
                leadingIcon = {
                    Icon(Icons.Default.Link, contentDescription = null, tint = Color(0xFF4FC3F7))
                },
                singleLine = true,
                enabled = !isProcessing,
                isError = errorMessage != null,
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    focusedBorderColor = Color(0xFF4FC3F7),
                    unfocusedBorderColor = Color.White.copy(alpha = 0.3f),
                    errorBorderColor = Color(0xFFFF5252),
                    cursorColor = Color(0xFF4FC3F7)
                ),
                shape = RoundedCornerShape(12.dp)
            )

            if (errorMessage != null) {
                Text(
                    errorMessage,
                    style = MaterialTheme.typography.labelSmall,
                    color = Color(0xFFFF5252),
                    modifier = Modifier.padding(top = 4.dp, start = 4.dp)
                )
            }

            Spacer(Modifier.height(12.dp))

            Button(
                onClick = onSubmit,
                enabled = !isProcessing && urlInput.isNotBlank(),
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color.Transparent,
                    disabledContainerColor = Color(0xFF1A3D73).copy(alpha = 0.5f)
                ),
                contentPadding = PaddingValues(0.dp)
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .then(
                            if (!isProcessing && urlInput.isNotBlank()) {
                                Modifier.background(
                                    Brush.horizontalGradient(
                                        listOf(Color(0xFF0EA5E9), Color(0xFF6366F1))
                                    ),
                                    RoundedCornerShape(12.dp)
                                )
                            } else {
                                Modifier.background(Color(0xFF1A3D73), RoundedCornerShape(12.dp))
                            }
                        )
                        .padding(vertical = 12.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        if (isProcessing) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(16.dp),
                                color = Color.White,
                                strokeWidth = 2.dp
                            )
                            Spacer(Modifier.width(8.dp))
                        } else {
                            Icon(
                                Icons.Default.PlayArrow,
                                contentDescription = null,
                                tint = Color.White,
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(Modifier.width(6.dp))
                        }
                        Text(
                            if (isProcessing) "Processing…" else "Analyze",
                            color = Color.White,
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                }
            }

            // Processing status indicator
            AnimatedVisibility(
                visible = isProcessing,
                enter = expandVertically(),
                exit = shrinkVertically()
            ) {
                Column(modifier = Modifier.padding(top = 12.dp)) {
                    LinearProgressIndicator(
                        progress = { progress },
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(4.dp)),
                        color = Color(0xFF4FC3F7),
                        trackColor = Color(0xFF1A3D73)
                    )
                    Spacer(Modifier.height(6.dp))
                    Text(
                        statusMessage,
                        style = MaterialTheme.typography.labelSmall,
                        color = Color.White.copy(alpha = 0.7f)
                    )
                }
            }
        }
    }
}

// ─── Time Range Chips ─────────────────────────────────────────────────────────

@Composable
private fun TimeRangeChips(
    selected: Int,
    onSelect: (Int) -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .horizontalScroll(rememberScrollState())
            .padding(horizontal = 12.dp, vertical = 4.dp),
        horizontalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        TIME_RANGE_OPTIONS.forEach { (days, label) ->
            val isSelected = days == selected
            FilterChip(
                selected = isSelected,
                onClick = { onSelect(days) },
                label = {
                    Text(
                        label,
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal
                    )
                },
                colors = FilterChipDefaults.filterChipColors(
                    selectedContainerColor = Color(0xFF1565C0),
                    selectedLabelColor = Color.White,
                    containerColor = Color(0xFF0D1F36),
                    labelColor = Color.White.copy(alpha = 0.7f)
                ),
                border = FilterChipDefaults.filterChipBorder(
                    enabled = true,
                    selected = isSelected,
                    borderColor = Color.White.copy(alpha = 0.2f),
                    selectedBorderColor = Color(0xFF4FC3F7)
                )
            )
        }
    }
}

// ─── Ticker Filter ────────────────────────────────────────────────────────────

@Composable
private fun TickerFilterRow(
    ticker: String,
    onChange: (String) -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        OutlinedTextField(
            value = ticker,
            onValueChange = { onChange(it.uppercase().take(10)) },
            modifier = Modifier.width(140.dp),
            placeholder = {
                Text("Filter ticker…", color = Color.White.copy(alpha = 0.4f), style = MaterialTheme.typography.bodySmall)
            },
            leadingIcon = {
                Icon(Icons.Default.Search, contentDescription = null, tint = Color(0xFF4FC3F7), modifier = Modifier.size(18.dp))
            },
            singleLine = true,
            colors = OutlinedTextFieldDefaults.colors(
                focusedTextColor = Color.White,
                unfocusedTextColor = Color.White,
                focusedBorderColor = Color(0xFF4FC3F7),
                unfocusedBorderColor = Color.White.copy(alpha = 0.2f),
                cursorColor = Color(0xFF4FC3F7)
            ),
            shape = RoundedCornerShape(10.dp),
            textStyle = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Medium)
        )
        if (ticker.isNotBlank()) {
            Spacer(Modifier.width(8.dp))
            TextButton(onClick = { onChange("") }) {
                Text("Clear", color = Color(0xFF4FC3F7), style = MaterialTheme.typography.labelSmall)
            }
        }
    }
}

// ─── Tracked Speakers Section ─────────────────────────────────────────────────

@Composable
private fun TrackedSpeakersSection(
    channels: List<ChannelTrackEntity>,
    expanded: Boolean,
    onToggle: () -> Unit,
    onAddChannel: () -> Unit,
    onRemove: (String) -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 6.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0D1F36)),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column {
            // Header row
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    Icons.Default.People,
                    contentDescription = null,
                    tint = Color(0xFF4FC3F7),
                    modifier = Modifier.size(18.dp)
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    "Tracked Speakers",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold,
                    color = Color.White,
                    modifier = Modifier.weight(1f)
                )
                if (channels.isNotEmpty()) {
                    Surface(
                        shape = RoundedCornerShape(10.dp),
                        color = Color(0xFF1A3D73)
                    ) {
                        Text(
                            "${channels.size}",
                            style = MaterialTheme.typography.labelSmall,
                            color = Color(0xFF90CAF9),
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                    Spacer(Modifier.width(8.dp))
                }
                IconButton(onClick = onAddChannel, modifier = Modifier.size(32.dp)) {
                    Icon(Icons.Default.Add, contentDescription = "Add speaker", tint = Color(0xFF4FC3F7), modifier = Modifier.size(18.dp))
                }
                IconButton(onClick = onToggle, modifier = Modifier.size(32.dp)) {
                    Icon(
                        if (expanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                        contentDescription = if (expanded) "Collapse" else "Expand",
                        tint = Color.White.copy(alpha = 0.6f),
                        modifier = Modifier.size(18.dp)
                    )
                }
            }

            AnimatedVisibility(
                visible = expanded,
                enter = expandVertically(),
                exit = shrinkVertically()
            ) {
                Column(modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp)) {
                    // Pre-seeded influential speakers hint
                    if (channels.isEmpty()) {
                        Text(
                            "No speakers tracked yet. Tap + to add, or start with influential speakers below.",
                            style = MaterialTheme.typography.bodySmall,
                            color = Color.White.copy(alpha = 0.6f),
                            modifier = Modifier.padding(horizontal = 4.dp, vertical = 4.dp)
                        )
                    } else {
                        channels.forEach { ch ->
                            SpeakerChip(
                                name = ch.speakerName.ifBlank { ch.channelName },
                                onRemove = { onRemove(ch.channelId) }
                            )
                        }
                    }

                    Spacer(Modifier.height(8.dp))

                    // Pre-seeded speakers quick-add row
                    Text(
                        "Quick add influential speakers:",
                        style = MaterialTheme.typography.labelSmall,
                        color = Color.White.copy(alpha = 0.5f),
                        modifier = Modifier.padding(bottom = 6.dp)
                    )
                    Row(
                        modifier = Modifier.horizontalScroll(rememberScrollState()),
                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        INFLUENTIAL_SPEAKERS.forEach { (channelId, name) ->
                            val alreadyTracked = channels.any { it.channelId == channelId }
                            if (!alreadyTracked) {
                                AssistChip(
                                    onClick = { /* handled via dialog in parent */ },
                                    label = {
                                        Text(
                                            name,
                                            style = MaterialTheme.typography.labelSmall
                                        )
                                    },
                                    colors = AssistChipDefaults.assistChipColors(
                                        containerColor = Color(0xFF1A3D73),
                                        labelColor = Color(0xFF90CAF9)
                                    ),
                                    border = AssistChipDefaults.assistChipBorder(
                                        enabled = true,
                                        borderColor = Color(0xFF4FC3F7).copy(alpha = 0.3f)
                                    )
                                )
                            }
                        }
                    }
                    Spacer(Modifier.height(8.dp))
                }
            }
        }
    }
}

@Composable
private fun SpeakerChip(name: String, onRemove: () -> Unit) {
    Row(
        modifier = Modifier.padding(vertical = 3.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Surface(
            shape = RoundedCornerShape(20.dp),
            color = Color(0xFF142B47)
        ) {
            Row(
                modifier = Modifier.padding(start = 10.dp, end = 4.dp, top = 4.dp, bottom = 4.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(Icons.Default.Person, contentDescription = null, tint = Color(0xFF4FC3F7), modifier = Modifier.size(14.dp))
                Spacer(Modifier.width(6.dp))
                Text(name, style = MaterialTheme.typography.labelSmall, color = Color.White)
                Spacer(Modifier.width(4.dp))
                IconButton(onClick = onRemove, modifier = Modifier.size(18.dp)) {
                    Icon(Icons.Default.Close, contentDescription = "Remove", tint = Color.White.copy(alpha = 0.6f), modifier = Modifier.size(12.dp))
                }
            }
        }
    }
}

// ─── Whisper Model Hint Card ──────────────────────────────────────────────────

@Composable
private fun WhisperModelHintCard() {
    // NOTE: To enable ONNX Whisper transcription, download a Whisper model from the
    // Models tab (if/when Whisper model download is added there).
    // Current transcription falls back to Android's SpeechRecognizer when no model is downloaded.
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 4.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0D2A1A)),
        shape = RoundedCornerShape(10.dp)
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(Icons.Default.Info, contentDescription = null, tint = Color(0xFF4CAF50), modifier = Modifier.size(16.dp))
            Spacer(Modifier.width(8.dp))
            Text(
                "Transcription: using on-device speech recognition. " +
                    "Download a Whisper ONNX model for improved accuracy.",
                style = MaterialTheme.typography.labelSmall,
                color = Color(0xFFA5D6A7)
            )
        }
    }
}

// ─── Empty State ──────────────────────────────────────────────────────────────

@Composable
private fun EmptySignalsCard() {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0D1F36)),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(32.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                Icons.Default.VideoLibrary,
                contentDescription = null,
                tint = Color.White.copy(alpha = 0.25f),
                modifier = Modifier.size(56.dp)
            )
            Spacer(Modifier.height(16.dp))
            Text(
                "No signals yet",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold,
                color = Color.White.copy(alpha = 0.7f)
            )
            Spacer(Modifier.height(8.dp))
            Text(
                "Paste a YouTube URL above to extract market signals from financial commentary, " +
                    "earnings calls, or analyst interviews. The LLM will identify tickers, " +
                    "directions, and confidence scores.",
                style = MaterialTheme.typography.bodySmall,
                color = Color.White.copy(alpha = 0.45f),
                textAlign = androidx.compose.ui.text.style.TextAlign.Center
            )
            Spacer(Modifier.height(16.dp))
            Text(
                "Try: CNBC earnings calls, Fed press conferences, analyst interviews",
                style = MaterialTheme.typography.labelSmall,
                color = Color(0xFF4FC3F7).copy(alpha = 0.7f),
                textAlign = androidx.compose.ui.text.style.TextAlign.Center
            )
        }
    }
}

// ─── Signal Card ──────────────────────────────────────────────────────────────

@Composable
private fun SignalCard(
    signal: VideoSignalEntity,
    videoSource: VideoSourceEntity?,
    onApply: () -> Unit
) {
    val isUp = signal.direction == "up"
    val directionColor = if (isUp) Color(0xFF4CAF50) else Color(0xFFFF5252)
    val domainColor = DOMAIN_COLORS[signal.domain] ?: Color(0xFF1565C0)

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 5.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0D1F36)),
        elevation = CardDefaults.cardElevation(defaultElevation = 3.dp),
        shape = RoundedCornerShape(14.dp)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {

            // Top row: direction badge + ticker + domain
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Direction badge
                Surface(
                    shape = RoundedCornerShape(6.dp),
                    color = directionColor.copy(alpha = 0.18f)
                ) {
                    Text(
                        if (isUp) "UP" else "DOWN",
                        style = MaterialTheme.typography.labelMedium,
                        fontWeight = FontWeight.ExtraBold,
                        color = directionColor,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
                    )
                }

                Spacer(Modifier.width(8.dp))

                // Ticker chip
                if (signal.ticker != null) {
                    Surface(
                        shape = RoundedCornerShape(6.dp),
                        color = Color(0xFF142B47)
                    ) {
                        Text(
                            signal.ticker,
                            style = MaterialTheme.typography.labelMedium,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF90CAF9),
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
                        )
                    }
                    Spacer(Modifier.width(6.dp))
                }

                // Domain badge
                Surface(
                    shape = RoundedCornerShape(6.dp),
                    color = domainColor.copy(alpha = 0.18f)
                ) {
                    Text(
                        signal.domain.uppercase(),
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.SemiBold,
                        color = domainColor.copy(alpha = 0.9f).copy(red = (domainColor.red + 0.3f).coerceAtMost(1f)),
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }

                Spacer(Modifier.weight(1f))

                // Confidence badge
                Text(
                    "%.0f%%".format(signal.confidence * 100),
                    style = MaterialTheme.typography.labelSmall,
                    color = Color.White.copy(alpha = 0.5f)
                )
            }

            Spacer(Modifier.height(10.dp))

            // Parameter name
            Text(
                signal.parameterName.replace("_", " ").replaceFirstChar { it.uppercase() },
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.SemiBold,
                color = Color.White
            )

            Spacer(Modifier.height(6.dp))

            // Weight bar
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    "Signal strength",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color.White.copy(alpha = 0.5f),
                    modifier = Modifier.width(96.dp)
                )
                LinearProgressIndicator(
                    progress = { signal.weight / 100f },
                    modifier = Modifier
                        .weight(1f)
                        .height(4.dp)
                        .clip(RoundedCornerShape(2.dp)),
                    color = directionColor,
                    trackColor = Color.White.copy(alpha = 0.1f)
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    "${signal.weight}",
                    style = MaterialTheme.typography.labelSmall,
                    color = directionColor,
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(Modifier.height(10.dp))

            // Key quote
            Surface(
                shape = RoundedCornerShape(8.dp),
                color = Color.White.copy(alpha = 0.05f)
            ) {
                Row(modifier = Modifier.padding(10.dp)) {
                    Text(
                        "\"",
                        style = MaterialTheme.typography.titleMedium,
                        color = Color(0xFF4FC3F7).copy(alpha = 0.6f),
                        fontWeight = FontWeight.Black
                    )
                    Spacer(Modifier.width(4.dp))
                    Text(
                        signal.keyQuote,
                        style = MaterialTheme.typography.bodySmall,
                        color = Color.White.copy(alpha = 0.75f),
                        maxLines = 3,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.weight(1f)
                    )
                }
            }

            Spacer(Modifier.height(10.dp))

            // Video source info + apply button
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    if (videoSource != null) {
                        Text(
                            videoSource.title.take(50),
                            style = MaterialTheme.typography.labelSmall,
                            color = Color.White.copy(alpha = 0.55f),
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                        Text(
                            "${videoSource.channelName} · ${timeAgo(signal.extractedAt)}",
                            style = MaterialTheme.typography.labelSmall,
                            color = Color.White.copy(alpha = 0.35f)
                        )
                    } else {
                        Text(
                            timeAgo(signal.extractedAt),
                            style = MaterialTheme.typography.labelSmall,
                            color = Color.White.copy(alpha = 0.35f)
                        )
                    }
                }

                Button(
                    onClick = onApply,
                    shape = RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (isUp) Color(0xFF1B5E20) else Color(0xFF7F0000)
                    ),
                    contentPadding = PaddingValues(horizontal = 14.dp, vertical = 6.dp),
                    modifier = Modifier.height(32.dp)
                ) {
                    Text(
                        "Apply",
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.SemiBold,
                        color = Color.White
                    )
                }
            }
        }
    }
}

// ─── Add Channel Dialog ───────────────────────────────────────────────────────

@Composable
private fun AddChannelDialog(
    onDismiss: () -> Unit,
    onAdd: (channelId: String, name: String, speaker: String) -> Unit
) {
    var channelId by remember { mutableStateOf("") }
    var channelName by remember { mutableStateOf("") }
    var speakerName by remember { mutableStateOf("") }
    var showPreSeeded by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = Color(0xFF0D1F36),
        title = {
            Text("Track Speaker / Channel", color = Color.White, fontWeight = FontWeight.Bold)
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text(
                    "Enter a YouTube channel ID to track — signals from their videos will appear here.",
                    style = MaterialTheme.typography.bodySmall,
                    color = Color.White.copy(alpha = 0.6f)
                )

                OutlinedTextField(
                    value = speakerName,
                    onValueChange = { speakerName = it },
                    label = { Text("Speaker Name", color = Color.White.copy(alpha = 0.6f)) },
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedBorderColor = Color(0xFF4FC3F7),
                        unfocusedBorderColor = Color.White.copy(alpha = 0.3f),
                        cursorColor = Color(0xFF4FC3F7)
                    ),
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = channelName,
                    onValueChange = { channelName = it },
                    label = { Text("Channel Name", color = Color.White.copy(alpha = 0.6f)) },
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedBorderColor = Color(0xFF4FC3F7),
                        unfocusedBorderColor = Color.White.copy(alpha = 0.3f),
                        cursorColor = Color(0xFF4FC3F7)
                    ),
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = channelId,
                    onValueChange = { channelId = it },
                    label = { Text("YouTube Channel ID", color = Color.White.copy(alpha = 0.6f)) },
                    placeholder = { Text("UCxxxxxxxxxxxxxxxx…", color = Color.White.copy(alpha = 0.3f)) },
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedBorderColor = Color(0xFF4FC3F7),
                        unfocusedBorderColor = Color.White.copy(alpha = 0.3f),
                        cursorColor = Color(0xFF4FC3F7)
                    ),
                    modifier = Modifier.fillMaxWidth()
                )

                // Pre-seeded speakers quick select
                TextButton(onClick = { showPreSeeded = !showPreSeeded }) {
                    Text(
                        if (showPreSeeded) "Hide influential speakers" else "Select from influential speakers",
                        style = MaterialTheme.typography.labelSmall,
                        color = Color(0xFF4FC3F7)
                    )
                }
                if (showPreSeeded) {
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        INFLUENTIAL_SPEAKERS.forEach { (id, name) ->
                            TextButton(
                                onClick = {
                                    channelId = id
                                    speakerName = name
                                    channelName = name
                                },
                                modifier = Modifier.fillMaxWidth(),
                                contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
                            ) {
                                Text(
                                    name,
                                    style = MaterialTheme.typography.bodySmall,
                                    color = Color(0xFF90CAF9),
                                    modifier = Modifier.fillMaxWidth()
                                )
                            }
                        }
                    }
                }
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    if (channelId.isNotBlank()) {
                        onAdd(
                            channelId.trim(),
                            channelName.trim().ifBlank { speakerName.trim() },
                            speakerName.trim().ifBlank { channelName.trim() }
                        )
                    }
                },
                enabled = channelId.isNotBlank(),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF1565C0))
            ) {
                Text("Track", color = Color.White)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel", color = Color.White.copy(alpha = 0.7f))
            }
        }
    )
}

// ─── Utilities ────────────────────────────────────────────────────────────────

private fun timeAgo(date: Date): String {
    val now = System.currentTimeMillis()
    val diffMs = now - date.time
    val diffMins = diffMs / 60_000
    val diffHrs = diffMins / 60
    val diffDays = diffHrs / 24
    return when {
        diffMins < 2  -> "just now"
        diffMins < 60 -> "${diffMins}m ago"
        diffHrs < 24  -> "${diffHrs}h ago"
        diffDays < 30 -> "${diffDays}d ago"
        else -> SimpleDateFormat("MMM d", Locale.US).format(date)
    }
}
