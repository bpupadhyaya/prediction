package com.prediction.stockmarket.ui.prediction

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel

// ─────────────────────────────────────────────────────────────────────────────
// Domain chip colors
// ─────────────────────────────────────────────────────────────────────────────
private val domainOptions = listOf(
    "Macro", "Fundamental", "Technical", "Sentiment", "Cross-Asset", "Geopolitical"
)

private fun domainColor(domain: String): Color = when (domain) {
    "Macro"         -> Color(0xFF0EA5E9)
    "Fundamental"   -> Color(0xFF10B981)
    "Technical"     -> Color(0xFF9B4DE7)
    "Sentiment"     -> Color(0xFFF97316)
    "Cross-Asset"   -> Color(0xFFE6B819)
    "Geopolitical"  -> Color(0xFFEF4444)
    else            -> Color(0xFF64748B)
}

// ─────────────────────────────────────────────────────────────────────────────
// Screen
// ─────────────────────────────────────────────────────────────────────────────

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun InteractivePredictionScreen(
    ticker: String,
    onBack: () -> Unit,
    viewModel: InteractivePredictionViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    var showAddSheet by remember { mutableStateOf(false) }
    var questionText by remember { mutableStateOf("") }

    LaunchedEffect(ticker) {
        viewModel.setTicker(ticker)
        viewModel.refreshModelStatus()
    }

    // Show snackbar when session is saved
    val snackbarHostState = remember { SnackbarHostState() }
    LaunchedEffect(state.sessionSaved) {
        if (state.sessionSaved) snackbarHostState.showSnackbar("Session saved")
    }
    LaunchedEffect(state.errorMessage) {
        state.errorMessage?.let {
            snackbarHostState.showSnackbar(it)
            viewModel.clearError()
        }
    }

    Scaffold(
        containerColor = Color(0xFF0B1526),
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = if (ticker.isNotBlank()) "Predict: $ticker" else "Interactive Prediction",
                        color = Color.White,
                        fontWeight = FontWeight.SemiBold,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back",
                            tint = Color.White
                        )
                    }
                },
                actions = {
                    TextButton(onClick = { viewModel.saveSession() }) {
                        Text("Save", color = Color(0xFF0EA5E9), fontWeight = FontWeight.SemiBold)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color(0xFF0D1F36)
                )
            )
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
            contentPadding = PaddingValues(bottom = 32.dp, top = 12.dp)
        ) {
            // ── 1. Prediction summary card ──────────────────────────────────
            item {
                PredictionSummaryCard(
                    direction = state.direction,
                    probUp = state.probUp,
                    confidence = state.confidence
                )
            }

            // ── 2. Signals header row ───────────────────────────────────────
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        "Signals (${state.signals.size})",
                        color = Color.White,
                        fontWeight = FontWeight.SemiBold,
                        style = MaterialTheme.typography.titleSmall
                    )
                    FilledTonalButton(
                        onClick = { showAddSheet = true },
                        colors = ButtonDefaults.filledTonalButtonColors(
                            containerColor = Color(0xFF142B47)
                        )
                    ) {
                        Icon(
                            Icons.Default.Add,
                            contentDescription = "Add signal",
                            tint = Color(0xFF7DD3F8),
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(Modifier.width(4.dp))
                        Text("Add Signal", color = Color(0xFF7DD3F8), fontSize = 13.sp)
                    }
                }
            }

            // ── 3. Signal cards ─────────────────────────────────────────────
            if (state.signals.isEmpty()) {
                item {
                    EmptySignalsHint()
                }
            } else {
                items(state.signals, key = { it.id }) { signal ->
                    SignalCard(
                        signal = signal,
                        onUpdate = { viewModel.updateSignal(it) },
                        onRemove = { viewModel.removeSignal(signal.id) }
                    )
                }
            }

            // ── 4. LLM Research section ─────────────────────────────────────
            item {
                LLMResearchSection(
                    isModelReady = state.isModelReady,
                    isStreaming = state.isStreaming,
                    llmResponse = state.llmResponse,
                    questionText = questionText,
                    onQuestionChange = { questionText = it },
                    onAskLLM = {
                        if (questionText.isNotBlank()) {
                            viewModel.askLLM(questionText)
                            questionText = ""
                        }
                    }
                )
            }
        }
    }

    // ── Add Signal bottom sheet ─────────────────────────────────────────────
    if (showAddSheet) {
        AddSignalSheet(
            onDismiss = { showAddSheet = false },
            onAdd = { signal ->
                viewModel.addSignal(signal)
                showAddSheet = false
            }
        )
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Prediction summary card
// ─────────────────────────────────────────────────────────────────────────────

@Composable
private fun PredictionSummaryCard(
    direction: String,
    probUp: Double,
    confidence: Double
) {
    val (bgColor, dirLabel, dirIcon) = when (direction) {
        "up"   -> Triple(Color(0xFF0F4738), "▲ UP", Icons.Default.TrendingUp)
        "down" -> Triple(Color(0xFF4A1010), "▼ DOWN", Icons.Default.TrendingDown)
        else   -> Triple(Color(0xFF1E293B), "— NEUTRAL", Icons.Default.HorizontalRule)
    }
    val dirTextColor = when (direction) {
        "up"   -> Color(0xFF4ADE80)
        "down" -> Color(0xFFF87171)
        else   -> Color(0xFF94A3B8)
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0D1F36))
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Text(
                "Composite Prediction",
                style = MaterialTheme.typography.labelMedium,
                color = Color.White.copy(alpha = 0.55f)
            )

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(bgColor, RoundedCornerShape(10.dp))
                    .padding(horizontal = 14.dp, vertical = 10.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Icon(dirIcon, contentDescription = direction, tint = dirTextColor, modifier = Modifier.size(20.dp))
                Text(
                    dirLabel,
                    color = dirTextColor,
                    fontWeight = FontWeight.Bold,
                    style = MaterialTheme.typography.bodyLarge
                )
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(24.dp)
            ) {
                SummaryStatCell(
                    label = "Prob(UP)",
                    value = "%.1f%%".format(probUp * 100),
                    valueColor = Color(0xFF7DD3F8)
                )
                SummaryStatCell(
                    label = "Confidence",
                    value = "%.1f%%".format(confidence * 100),
                    valueColor = Color(0xFFCDA8FF)
                )
            }
        }
    }
}

@Composable
private fun SummaryStatCell(label: String, value: String, valueColor: Color) {
    Column {
        Text(value, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, color = valueColor)
        Text(label, style = MaterialTheme.typography.labelSmall, color = Color.White.copy(alpha = 0.5f))
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Signal card (inline editing)
// ─────────────────────────────────────────────────────────────────────────────

@Composable
private fun SignalCard(
    signal: InteractivePredictionViewModel.Signal,
    onUpdate: (InteractivePredictionViewModel.Signal) -> Unit,
    onRemove: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0D1F36))
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Header row: name + domain chip + delete
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.weight(1f)
                ) {
                    Text(
                        text = signal.name,
                        color = Color.White,
                        fontWeight = FontWeight.Medium,
                        style = MaterialTheme.typography.bodyMedium,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    DomainChip(signal.domain)
                }
                IconButton(onClick = onRemove, modifier = Modifier.size(32.dp)) {
                    Icon(Icons.Default.Delete, contentDescription = "Remove", tint = Color(0xFF94A3B8), modifier = Modifier.size(18.dp))
                }
            }

            // Direction toggle
            Row(
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                listOf("up", "neutral", "down").forEach { dir ->
                    val selected = signal.direction == dir
                    val (bgSel, fgSel, label) = when (dir) {
                        "up"      -> Triple(Color(0xFF166534), Color(0xFF4ADE80), "UP")
                        "down"    -> Triple(Color(0xFF7F1D1D), Color(0xFFF87171), "DOWN")
                        else      -> Triple(Color(0xFF1E293B), Color(0xFF94A3B8), "NEUTRAL")
                    }
                    OutlinedButton(
                        onClick = { onUpdate(signal.copy(direction = dir)) },
                        modifier = Modifier.weight(1f).height(32.dp),
                        shape = RoundedCornerShape(8.dp),
                        contentPadding = PaddingValues(horizontal = 4.dp),
                        colors = ButtonDefaults.outlinedButtonColors(
                            containerColor = if (selected) bgSel else Color.Transparent,
                            contentColor = if (selected) fgSel else Color.White.copy(alpha = 0.4f)
                        ),
                        border = androidx.compose.foundation.BorderStroke(
                            1.dp,
                            if (selected) fgSel.copy(alpha = 0.6f) else Color.White.copy(alpha = 0.15f)
                        )
                    ) {
                        Text(label, fontSize = 11.sp, fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal)
                    }
                }
            }

            // Weight slider
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Text("Weight", style = MaterialTheme.typography.labelSmall, color = Color.White.copy(alpha = 0.55f))
                Slider(
                    value = signal.weight.toFloat(),
                    onValueChange = { onUpdate(signal.copy(weight = it.toInt())) },
                    valueRange = 0f..100f,
                    steps = 0,
                    modifier = Modifier.weight(1f),
                    colors = SliderDefaults.colors(
                        thumbColor = Color(0xFF0EA5E9),
                        activeTrackColor = Color(0xFF0EA5E9),
                        inactiveTrackColor = Color(0xFF1E3A5F)
                    )
                )
                Text(
                    "${signal.weight}",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color(0xFF7DD3F8),
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.width(26.dp)
                )
            }
        }
    }
}

@Composable
private fun DomainChip(domain: String) {
    Surface(
        shape = RoundedCornerShape(50.dp),
        color = domainColor(domain).copy(alpha = 0.18f)
    ) {
        Text(
            text = domain,
            modifier = Modifier.padding(horizontal = 7.dp, vertical = 2.dp),
            style = MaterialTheme.typography.labelSmall,
            color = domainColor(domain),
            fontWeight = FontWeight.Medium
        )
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Empty state hint
// ─────────────────────────────────────────────────────────────────────────────

@Composable
private fun EmptySignalsHint() {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color(0xFF0D1F36), RoundedCornerShape(12.dp))
            .padding(20.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            Icon(Icons.Default.AddChart, contentDescription = null, tint = Color.White.copy(alpha = 0.25f), modifier = Modifier.size(36.dp))
            Text(
                "No signals yet",
                color = Color.White.copy(alpha = 0.4f),
                style = MaterialTheme.typography.bodyMedium
            )
            Text(
                "Tap Add Signal to build your prediction model",
                color = Color.White.copy(alpha = 0.25f),
                style = MaterialTheme.typography.bodySmall
            )
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// LLM Research section
// ─────────────────────────────────────────────────────────────────────────────

@Composable
private fun LLMResearchSection(
    isModelReady: Boolean,
    isStreaming: Boolean,
    llmResponse: String,
    questionText: String,
    onQuestionChange: (String) -> Unit,
    onAskLLM: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0D1F36))
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Icon(Icons.Default.AutoAwesome, contentDescription = null, tint = Color(0xFFCDA8FF), modifier = Modifier.size(16.dp))
                Text(
                    "AI Research",
                    color = Color.White,
                    fontWeight = FontWeight.SemiBold,
                    style = MaterialTheme.typography.titleSmall
                )
            }

            if (!isModelReady) {
                // No model loaded — prompt user to download one
                Surface(
                    shape = RoundedCornerShape(10.dp),
                    color = Color(0xFF1E293B)
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(12.dp),
                        horizontalArrangement = Arrangement.spacedBy(10.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            Icons.Default.Download,
                            contentDescription = null,
                            tint = Color(0xFFF97316),
                            modifier = Modifier.size(20.dp)
                        )
                        Text(
                            "Download a model in the Models tab to enable AI research",
                            color = Color.White.copy(alpha = 0.7f),
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                }
            } else {
                // Question input
                OutlinedTextField(
                    value = questionText,
                    onValueChange = onQuestionChange,
                    modifier = Modifier.fillMaxWidth(),
                    placeholder = {
                        Text(
                            "Ask about this stock, signals, or market context…",
                            color = Color.White.copy(alpha = 0.3f),
                            style = MaterialTheme.typography.bodySmall
                        )
                    },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedContainerColor = Color(0xFF0B1526),
                        unfocusedContainerColor = Color(0xFF0B1526),
                        focusedBorderColor = Color(0xFF0EA5E9),
                        unfocusedBorderColor = Color.White.copy(alpha = 0.15f),
                        cursorColor = Color(0xFF0EA5E9)
                    ),
                    shape = RoundedCornerShape(10.dp),
                    maxLines = 3
                )

                Button(
                    onClick = onAskLLM,
                    enabled = questionText.isNotBlank() && !isStreaming,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF0EA5E9),
                        disabledContainerColor = Color(0xFF0EA5E9).copy(alpha = 0.35f)
                    )
                ) {
                    if (isStreaming) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(16.dp),
                            strokeWidth = 2.dp,
                            color = Color.White
                        )
                        Spacer(Modifier.width(8.dp))
                        Text("Generating…", color = Color.White)
                    } else {
                        Icon(Icons.Default.Send, contentDescription = null, tint = Color.White, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(8.dp))
                        Text("Ask AI", color = Color.White, fontWeight = FontWeight.SemiBold)
                    }
                }

                // Response area
                if (llmResponse.isNotBlank() || isStreaming) {
                    Surface(
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(min = 80.dp, max = 300.dp),
                        shape = RoundedCornerShape(10.dp),
                        color = Color(0xFF0B1526)
                    ) {
                        Column(modifier = Modifier.verticalScroll(rememberScrollState()).padding(12.dp)) {
                            Text(
                                text = llmResponse.ifBlank { "…" },
                                color = Color.White.copy(alpha = 0.85f),
                                style = MaterialTheme.typography.bodySmall,
                                lineHeight = 20.sp
                            )
                            if (isStreaming) {
                                Text("▍", color = Color(0xFF0EA5E9))
                            }
                        }
                    }
                }
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Add Signal bottom sheet
// ─────────────────────────────────────────────────────────────────────────────

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun AddSignalSheet(
    onDismiss: () -> Unit,
    onAdd: (InteractivePredictionViewModel.Signal) -> Unit
) {
    var name by remember { mutableStateOf("") }
    var domain by remember { mutableStateOf(domainOptions[0]) }
    var direction by remember { mutableStateOf("neutral") }
    var weight by remember { mutableStateOf(50) }
    var expandedDomain by remember { mutableStateOf(false) }

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        containerColor = Color(0xFF0D1F36),
        tonalElevation = 0.dp
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp)
                .padding(bottom = 32.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Text(
                "Add Signal",
                color = Color.White,
                fontWeight = FontWeight.Bold,
                style = MaterialTheme.typography.titleMedium
            )

            // Signal name
            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Signal name", color = Color.White.copy(alpha = 0.5f)) },
                placeholder = { Text("e.g. Fed rate cut, RSI divergence", color = Color.White.copy(alpha = 0.3f)) },
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    focusedContainerColor = Color(0xFF0B1526),
                    unfocusedContainerColor = Color(0xFF0B1526),
                    focusedBorderColor = Color(0xFF0EA5E9),
                    unfocusedBorderColor = Color.White.copy(alpha = 0.15f),
                    cursorColor = Color(0xFF0EA5E9)
                ),
                shape = RoundedCornerShape(10.dp),
                singleLine = true
            )

            // Domain dropdown
            ExposedDropdownMenuBox(
                expanded = expandedDomain,
                onExpandedChange = { expandedDomain = it }
            ) {
                OutlinedTextField(
                    value = domain,
                    onValueChange = {},
                    readOnly = true,
                    modifier = Modifier
                        .fillMaxWidth()
                        .menuAnchor(),
                    label = { Text("Domain", color = Color.White.copy(alpha = 0.5f)) },
                    trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expandedDomain) },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedContainerColor = Color(0xFF0B1526),
                        unfocusedContainerColor = Color(0xFF0B1526),
                        focusedBorderColor = Color(0xFF0EA5E9),
                        unfocusedBorderColor = Color.White.copy(alpha = 0.15f)
                    ),
                    shape = RoundedCornerShape(10.dp)
                )
                ExposedDropdownMenu(
                    expanded = expandedDomain,
                    onDismissRequest = { expandedDomain = false },
                    containerColor = Color(0xFF142B47)
                ) {
                    domainOptions.forEach { opt ->
                        DropdownMenuItem(
                            text = { Text(opt, color = Color.White) },
                            onClick = {
                                domain = opt
                                expandedDomain = false
                            }
                        )
                    }
                }
            }

            // Direction selector
            Text("Direction", style = MaterialTheme.typography.labelMedium, color = Color.White.copy(alpha = 0.6f))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                listOf("up", "neutral", "down").forEach { dir ->
                    val selected = direction == dir
                    val (bgSel, fgSel, label) = when (dir) {
                        "up"   -> Triple(Color(0xFF166534), Color(0xFF4ADE80), "UP")
                        "down" -> Triple(Color(0xFF7F1D1D), Color(0xFFF87171), "DOWN")
                        else   -> Triple(Color(0xFF1E293B), Color(0xFF94A3B8), "NEUTRAL")
                    }
                    OutlinedButton(
                        onClick = { direction = dir },
                        modifier = Modifier.weight(1f).height(38.dp),
                        shape = RoundedCornerShape(10.dp),
                        contentPadding = PaddingValues(horizontal = 4.dp),
                        colors = ButtonDefaults.outlinedButtonColors(
                            containerColor = if (selected) bgSel else Color.Transparent,
                            contentColor = if (selected) fgSel else Color.White.copy(alpha = 0.4f)
                        ),
                        border = androidx.compose.foundation.BorderStroke(
                            1.dp,
                            if (selected) fgSel.copy(alpha = 0.6f) else Color.White.copy(alpha = 0.15f)
                        )
                    ) {
                        Text(label, fontSize = 12.sp, fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal)
                    }
                }
            }

            // Weight slider
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Text("Weight", style = MaterialTheme.typography.labelMedium, color = Color.White.copy(alpha = 0.6f))
                Slider(
                    value = weight.toFloat(),
                    onValueChange = { weight = it.toInt() },
                    valueRange = 0f..100f,
                    modifier = Modifier.weight(1f),
                    colors = SliderDefaults.colors(
                        thumbColor = Color(0xFF0EA5E9),
                        activeTrackColor = Color(0xFF0EA5E9),
                        inactiveTrackColor = Color(0xFF1E3A5F)
                    )
                )
                Text(
                    "$weight",
                    color = Color(0xFF7DD3F8),
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.width(30.dp)
                )
            }

            Spacer(Modifier.height(4.dp))

            // Add button
            Button(
                onClick = {
                    if (name.isNotBlank()) {
                        onAdd(
                            InteractivePredictionViewModel.Signal(
                                name = name.trim(),
                                domain = domain,
                                direction = direction,
                                weight = weight
                            )
                        )
                    }
                },
                enabled = name.isNotBlank(),
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF0EA5E9),
                    disabledContainerColor = Color(0xFF0EA5E9).copy(alpha = 0.3f)
                )
            ) {
                Text("Add Signal", fontWeight = FontWeight.SemiBold, color = Color.White)
            }
        }
    }
}
