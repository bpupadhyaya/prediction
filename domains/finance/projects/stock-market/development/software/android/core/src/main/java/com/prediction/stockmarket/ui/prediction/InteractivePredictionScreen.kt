package com.prediction.stockmarket.ui.prediction

import androidx.compose.foundation.BorderStroke
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
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.prediction.stockmarket.data.StockParameter

// ─────────────────────────────────────────────────────────────────────────────
// Domain color helpers
// ─────────────────────────────────────────────────────────────────────────────

private fun domainAccentColor(domain: String): Color = when (domain) {
    "macro"        -> Color(0xFF0EA5E9)
    "fundamental"  -> Color(0xFF10B981)
    "cross_asset"  -> Color(0xFFE6B819)
    "technical"    -> Color(0xFF9B4DE7)
    "sentiment"    -> Color(0xFFF97316)
    "geopolitical" -> Color(0xFFEF4444)
    else           -> Color(0xFF64748B)
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

    LaunchedEffect(ticker) {
        if (ticker.isNotBlank()) {
            viewModel.loadParameters(ticker)
            viewModel.refreshModelStatus()
        }
    }

    Scaffold(
        containerColor = Color(0xFF0B1526),
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = if (ticker.isNotBlank()) "$ticker — Interactive Predict" else "Interactive Prediction",
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
                    TextButton(onClick = { viewModel.reset() }) {
                        Text("Reset", color = Color(0xFF94A3B8))
                    }
                    TextButton(onClick = { viewModel.saveSession() }) {
                        Text("Save", color = Color(0xFF0EA5E9), fontWeight = FontWeight.Bold)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFF0D1F36))
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Sticky score header
            ScoreHeaderCard(state = state)

            // Save confirmation message
            if (state.saveMessage.isNotEmpty()) {
                Text(
                    text = state.saveMessage,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
                    color = Color(0xFF4ADE80),
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Medium
                )
            }

            // Error message
            if (state.errorMessage != null) {
                Text(
                    text = state.errorMessage ?: "",
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
                    color = Color(0xFFF87171),
                    fontSize = 13.sp
                )
            }

            // Scrollable parameter groups + LLM section
            if (state.parameters.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator(color = Color(0xFF0EA5E9))
                }
            } else {
                val grouped = state.parameters.groupBy { it.domain }
                val domainOrder = listOf(
                    "macro", "fundamental", "cross_asset", "technical", "sentiment", "geopolitical"
                )

                LazyColumn(
                    modifier = Modifier
                        .weight(1f)
                        .padding(horizontal = 12.dp),
                    contentPadding = PaddingValues(bottom = 32.dp, top = 8.dp)
                ) {
                    for (domain in domainOrder) {
                        val params = grouped[domain] ?: continue

                        item(key = "header-$domain") {
                            DomainGroupHeader(params = params, states = state.states)
                        }

                        items(params, key = { it.name }) { param ->
                            val paramState = state.states[param.name] ?: InteractivePredictionViewModel.ParamState()
                            val isExpanded = state.expandedParams.contains(param.name)
                            ParameterRowItem(
                                param = param,
                                paramState = paramState,
                                isExpanded = isExpanded,
                                onExpand = { viewModel.toggleExpand(param.name) },
                                onDirection = { dir -> viewModel.setDirection(param.name, dir) },
                                onWeight = { w -> viewModel.setWeight(param.name, w) }
                            )
                            HorizontalDivider(
                                color = MaterialTheme.colorScheme.outline.copy(alpha = 0.2f),
                                thickness = 0.5.dp
                            )
                        }

                        item(key = "spacer-$domain") {
                            Spacer(Modifier.height(12.dp))
                        }
                    }

                    // LLM research section at bottom
                    item(key = "llm-section") {
                        LLMResearchSection(state = state, viewModel = viewModel)
                    }
                    item(key = "bottom-spacer") {
                        Spacer(Modifier.height(32.dp))
                    }
                }
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Score header card (sticky)
// ─────────────────────────────────────────────────────────────────────────────

@Composable
private fun ScoreHeaderCard(state: InteractivePredictionViewModel.UiState) {
    val (bgColor, dirLabel) = when (state.direction) {
        "up"   -> Color(0xFF0F4738) to "▲ UP"
        "down" -> Color(0xFF4A1010) to "▼ DOWN"
        else   -> Color(0xFF1E293B) to "— NEUTRAL"
    }
    val dirTextColor = when (state.direction) {
        "up"   -> Color(0xFF4ADE80)
        "down" -> Color(0xFFF87171)
        else   -> Color(0xFF94A3B8)
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 12.dp, vertical = 8.dp),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0D1F36))
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
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
                    .padding(horizontal = 14.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    dirLabel,
                    color = dirTextColor,
                    fontWeight = FontWeight.Bold,
                    style = MaterialTheme.typography.bodyLarge
                )
                Text(
                    "${state.paramsSet} params set",
                    color = dirTextColor.copy(alpha = 0.7f),
                    style = MaterialTheme.typography.labelSmall
                )
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(24.dp)
            ) {
                ScoreStatCell(
                    label = "Prob(UP)",
                    value = "%.1f%%".format(state.probUp * 100),
                    valueColor = Color(0xFF7DD3F8)
                )
                ScoreStatCell(
                    label = "Confidence",
                    value = "%.1f%%".format(state.confidence * 100),
                    valueColor = Color(0xFFCDA8FF)
                )
            }
        }
    }
}

@Composable
private fun ScoreStatCell(label: String, value: String, valueColor: Color) {
    Column {
        Text(value, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, color = valueColor)
        Text(label, style = MaterialTheme.typography.labelSmall, color = Color.White.copy(alpha = 0.5f))
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Domain group header
// ─────────────────────────────────────────────────────────────────────────────

@Composable
private fun DomainGroupHeader(
    params: List<StockParameter>,
    states: Map<String, InteractivePredictionViewModel.ParamState>
) {
    val netScore = params.sumOf { p ->
        val s = states[p.name] ?: return@sumOf 0.0
        if (s.direction == "neutral") 0.0
        else s.weight.toDouble() * (if (s.direction == "up") 1.0 else -1.0)
    }
    val netLabel = when {
        netScore > 0 -> "▲ net bullish"
        netScore < 0 -> "▼ net bearish"
        else         -> "— neutral"
    }
    val netColor = when {
        netScore > 0 -> Color(0xFF34D399)
        netScore < 0 -> Color(0xFFF87171)
        else         -> Color(0xFF94A3B8)
    }
    val accentColor = if (params.isNotEmpty()) domainAccentColor(params[0].domain) else Color.Gray

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color(0xFF0E1E38))
            .padding(horizontal = 12.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .width(3.dp)
                .height(16.dp)
                .background(accentColor, RoundedCornerShape(2.dp))
        )
        Spacer(Modifier.width(8.dp))
        Text(
            text = if (params.isNotEmpty()) params[0].domainLabel else "",
            style = MaterialTheme.typography.labelMedium,
            color = Color.White,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.weight(1f)
        )
        Text(
            "${params.size} params",
            style = MaterialTheme.typography.labelSmall,
            color = Color(0xFF64748B),
            modifier = Modifier.padding(end = 8.dp)
        )
        Text(
            netLabel,
            style = MaterialTheme.typography.labelSmall,
            color = netColor,
            fontWeight = FontWeight.Bold
        )
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Parameter row item
// ─────────────────────────────────────────────────────────────────────────────

@Composable
private fun ParameterRowItem(
    param: StockParameter,
    paramState: InteractivePredictionViewModel.ParamState,
    isExpanded: Boolean,
    onExpand: () -> Unit,
    onDirection: (String) -> Unit,
    onWeight: (Int) -> Unit
) {
    val upActive = paramState.direction == "up"
    val downActive = paramState.direction == "down"
    val isSet = paramState.direction != "neutral"

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .alpha(if (isSet) 1f else 0.65f)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 5.dp, horizontal = 4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Expand chevron
            IconButton(
                onClick = onExpand,
                modifier = Modifier.size(28.dp)
            ) {
                Icon(
                    imageVector = if (isExpanded) Icons.Default.ExpandLess else Icons.Default.ChevronRight,
                    contentDescription = if (isExpanded) "Collapse ${param.label}" else "Expand ${param.label}",
                    modifier = Modifier.size(14.dp),
                    tint = Color(0xFF64748B)
                )
            }

            // Parameter name + label
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    param.name,
                    fontFamily = FontFamily.Monospace,
                    fontSize = 11.sp,
                    color = Color.White,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                Text(
                    param.label,
                    fontSize = 10.sp,
                    color = Color(0xFF94A3B8),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }

            // Weight slider + value
            Slider(
                value = paramState.weight.toFloat(),
                onValueChange = { onWeight(it.toInt()) },
                valueRange = 0f..100f,
                modifier = Modifier
                    .width(80.dp)
                    .semantics { contentDescription = "Weight: ${paramState.weight}" },
                colors = SliderDefaults.colors(
                    thumbColor = Color(0xFF4F8EF7),
                    activeTrackColor = Color(0xFF4F8EF7),
                    inactiveTrackColor = Color(0xFF1E3A5F)
                )
            )
            Text(
                "${paramState.weight}",
                fontFamily = FontFamily.Monospace,
                fontSize = 11.sp,
                color = Color(0xFF4F8EF7),
                modifier = Modifier.width(28.dp),
                fontWeight = FontWeight.SemiBold
            )

            Spacer(Modifier.width(4.dp))

            // Direction buttons
            Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                OutlinedButton(
                    onClick = { onDirection(if (upActive) "neutral" else "up") },
                    modifier = Modifier
                        .height(28.dp)
                        .semantics { contentDescription = "Set up direction for ${param.label}" },
                    border = BorderStroke(1.dp, if (upActive) Color(0xFF34D399) else Color(0xFF334155)),
                    shape = RoundedCornerShape(8.dp),
                    contentPadding = PaddingValues(horizontal = 8.dp),
                    colors = ButtonDefaults.outlinedButtonColors(
                        containerColor = if (upActive) Color(0xFF0F4738) else Color.Transparent
                    )
                ) {
                    Text("▲", color = if (upActive) Color(0xFF34D399) else Color(0xFF64748B), fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
                OutlinedButton(
                    onClick = { onDirection(if (downActive) "neutral" else "down") },
                    modifier = Modifier
                        .height(28.dp)
                        .semantics { contentDescription = "Set down direction for ${param.label}" },
                    border = BorderStroke(1.dp, if (downActive) Color(0xFFF87171) else Color(0xFF334155)),
                    shape = RoundedCornerShape(8.dp),
                    contentPadding = PaddingValues(horizontal = 8.dp),
                    colors = ButtonDefaults.outlinedButtonColors(
                        containerColor = if (downActive) Color(0xFF4A1010) else Color.Transparent
                    )
                ) {
                    Text("▼", color = if (downActive) Color(0xFFF87171) else Color(0xFF64748B), fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
            }
        }

        // Expanded definition panel — two columns side by side using Row + Box divider
        if (isExpanded) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color(0xFF0B1526))
                    .padding(vertical = 8.dp)
            ) {
                Column(
                    modifier = Modifier
                        .weight(1f)
                        .padding(horizontal = 10.dp)
                ) {
                    Text(
                        "IN PLAIN ENGLISH",
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF34D399),
                        letterSpacing = 1.sp
                    )
                    Spacer(Modifier.height(4.dp))
                    Text(
                        param.layman,
                        fontSize = 11.sp,
                        lineHeight = 16.sp,
                        color = Color.White.copy(alpha = 0.85f)
                    )
                }
                // Vertical divider via Box
                Box(
                    modifier = Modifier
                        .width(1.dp)
                        .fillMaxHeight()
                        .background(Color(0xFF334155))
                )
                Column(
                    modifier = Modifier
                        .weight(1f)
                        .padding(horizontal = 10.dp)
                ) {
                    Text(
                        "TECHNICAL",
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF4F8EF7),
                        letterSpacing = 1.sp
                    )
                    Spacer(Modifier.height(4.dp))
                    Text(
                        param.technical,
                        fontSize = 11.sp,
                        lineHeight = 16.sp,
                        color = Color.White.copy(alpha = 0.85f)
                    )
                }
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// LLM Research section (at bottom of list)
// ─────────────────────────────────────────────────────────────────────────────

@Composable
private fun LLMResearchSection(
    state: InteractivePredictionViewModel.UiState,
    viewModel: InteractivePredictionViewModel
) {
    var questionText by remember { mutableStateOf("") }

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
                Icon(
                    Icons.Default.AutoAwesome,
                    contentDescription = null,
                    tint = Color(0xFFCDA8FF),
                    modifier = Modifier.size(16.dp)
                )
                Text(
                    "AI Research",
                    color = Color.White,
                    fontWeight = FontWeight.SemiBold,
                    style = MaterialTheme.typography.titleSmall
                )
            }

            if (!state.isModelReady) {
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
                            color = Color.White.copy(alpha = 0.85f),
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                }
            } else {
                OutlinedTextField(
                    value = questionText,
                    onValueChange = { questionText = it },
                    modifier = Modifier.fillMaxWidth(),
                    placeholder = {
                        Text(
                            "Ask about this stock, parameters, or market context…",
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
                    onClick = {
                        val q = questionText.trim()
                        if (q.isNotBlank()) {
                            viewModel.askLLM(q)
                            questionText = ""
                        }
                    },
                    enabled = questionText.isNotBlank() && !state.isStreaming,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF0EA5E9),
                        disabledContainerColor = Color(0xFF0EA5E9).copy(alpha = 0.35f)
                    )
                ) {
                    if (state.isStreaming) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(16.dp),
                            strokeWidth = 2.dp,
                            color = Color.White
                        )
                        Spacer(Modifier.width(8.dp))
                        Text("Generating…", color = Color.White)
                    } else {
                        Icon(
                            Icons.Default.Send,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(16.dp)
                        )
                        Spacer(Modifier.width(8.dp))
                        Text("Ask AI", color = Color.White, fontWeight = FontWeight.SemiBold)
                    }
                }

                if (state.llmResponse.isNotBlank() || state.isStreaming) {
                    Surface(
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(min = 80.dp, max = 300.dp),
                        shape = RoundedCornerShape(10.dp),
                        color = Color(0xFF0B1526)
                    ) {
                        Column(
                            modifier = Modifier
                                .verticalScroll(rememberScrollState())
                                .padding(12.dp)
                        ) {
                            Text(
                                text = state.llmResponse.ifBlank { "…" },
                                color = Color.White.copy(alpha = 0.85f),
                                style = MaterialTheme.typography.bodySmall,
                                lineHeight = 20.sp
                            )
                            if (state.isStreaming) {
                                Text("▍", color = Color(0xFF0EA5E9))
                            }
                        }
                    }
                }
            }
        }
    }
}
