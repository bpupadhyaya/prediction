package com.prediction.stockmarket.ui.modules

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ChevronLeft
import androidx.compose.material.icons.filled.Stars
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp

// Pre-IPO module
//
// Tapping the "Pre-IPO" home card opens this screen. There is no live IPO feed,
// so this surfaces a small CURATED list of well-known late-stage private
// companies. Illustrative only — not offerings or advice. Mirrors the chrome/
// styling of MarketModuleScreen.

data class PreIPOCandidate(
    val name: String,
    val sector: String,
    val whyWatch: String,
    val status: String,
)

val PRE_IPO_CANDIDATES = listOf(
    PreIPOCandidate("SpaceX", "Aerospace", "Starlink revenue scaling fast; Starship cadence rising.", "Late-stage private"),
    PreIPOCandidate("OpenAI", "AI / LLM", "Maker of ChatGPT — defining the generative-AI platform race.", "Rumored 2025-26"),
    PreIPOCandidate("Anthropic", "AI / LLM", "Claude models; an AI-safety-focused frontier lab with rapid growth.", "Late-stage private"),
    PreIPOCandidate("Stripe", "Fintech", "Global payments rails for the internet; perennial IPO candidate.", "Late-stage private"),
    PreIPOCandidate("Databricks", "Data / AI", "Unified data + AI lakehouse; large enterprise revenue base.", "Rumored 2025-26"),
    PreIPOCandidate("Canva", "Design / SaaS", "Mass-market visual design tool with strong global adoption.", "Late-stage private"),
    PreIPOCandidate("Discord", "Social", "Communities and gaming communication at massive daily scale.", "Late-stage private"),
    PreIPOCandidate("Epic Games", "Gaming", "Fortnite + Unreal Engine; a key platform across games and 3D.", "Late-stage private"),
    PreIPOCandidate("Chime", "Neobank", "Mobile-first US consumer banking with a large user base.", "Rumored 2025-26"),
    PreIPOCandidate("Plaid", "Fintech", "Bank-data connectivity layer behind much of US fintech.", "Late-stage private"),
)

private val PRE_IPO_GRAD = listOf(Color(0xFF664800), Color(0xFF9E7306), Color(0xFFE6B819))
private val PRE_IPO_ICON = Color(0xFFFFE699)

@Composable
fun PreIPOModuleScreen(onBack: () -> Unit) {
    val gradient = Brush.linearGradient(
        colors = PRE_IPO_GRAD,
        start = Offset(0f, 0f),
        end = Offset(Float.POSITIVE_INFINITY, Float.POSITIVE_INFINITY),
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0B1526))
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .statusBarsPadding()
                .padding(horizontal = 8.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            TextButton(onClick = onBack) {
                Icon(Icons.Default.ChevronLeft, contentDescription = "Go back", tint = Color.White)
                Text("Home", color = Color.White, fontWeight = FontWeight.Medium)
            }
        }

        Row(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                modifier = Modifier.size(44.dp).clip(CircleShape).background(gradient),
                contentAlignment = Alignment.Center,
            ) {
                Icon(Icons.Default.Stars, contentDescription = "Pre-IPO", tint = PRE_IPO_ICON, modifier = Modifier.size(24.dp))
            }
            Spacer(Modifier.width(12.dp))
            Column {
                Text("Pre-IPO", style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold), color = Color.White)
                Text("Notable late-stage private companies", style = MaterialTheme.typography.bodySmall, color = Color.White.copy(alpha = 0.6f))
            }
        }
        Spacer(Modifier.height(8.dp))

        LazyColumn(contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)) {
            items(PRE_IPO_CANDIDATES) { company ->
                CandidateCard(company)
            }
            item {
                Text(
                    "Illustrative watchlist of well-known private companies — not an offering, recommendation, or financial advice. Timing and status are speculative.",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color.White.copy(alpha = 0.35f),
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth().padding(vertical = 14.dp, horizontal = 8.dp),
                )
            }
        }
    }
}

@Composable
private fun CandidateCard(company: PreIPOCandidate) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF13243F)),
        shape = RoundedCornerShape(14.dp),
    ) {
        Column(modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(company.name, style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.SemiBold), color = Color.White)
                Spacer(Modifier.width(8.dp))
                Text(company.sector, style = MaterialTheme.typography.labelSmall, color = Color(0xFF93C3F0))
                Spacer(Modifier.weight(1f))
                StatusChip(company.status)
            }
            Spacer(Modifier.height(4.dp))
            Text(company.whyWatch, style = MaterialTheme.typography.bodySmall, color = Color.White.copy(alpha = 0.6f))
        }
    }
}

@Composable
private fun StatusChip(status: String) {
    val rumored = status.lowercase().contains("rumored")
    val bg = if (rumored) Color(0xFF14532D) else Color(0xFF1E293B)
    val fg = if (rumored) Color(0xFF4ADE80) else Color.White.copy(alpha = 0.55f)
    Surface(shape = RoundedCornerShape(50.dp), color = bg) {
        Text(
            status,
            style = MaterialTheme.typography.labelSmall.copy(fontWeight = FontWeight.Bold),
            color = fg,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
        )
    }
}
