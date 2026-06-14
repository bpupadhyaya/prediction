package com.prediction.stockmarket.ui.prediction

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.VerifiedUser
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.prediction.stockmarket.prediction.ModelMeta
import kotlin.math.abs

/**
 * Read-only "How accurate is this model?" dialog. Mirrors the web's "Model
 * Transparency" card, surfacing the honest out-of-sample stats already bundled
 * in mobile_model_meta.json (via ModelMeta): directional accuracy, the naive
 * "always up" base rate, the edge over it, and a Brier calibration indicator.
 * No model is run here.
 */
@Composable
fun ModelTransparencyDialog(onDismiss: () -> Unit) {
    val context = LocalContext.current
    // Ensure metadata is loaded, then signal readiness so the body recomposes
    // (ModelMeta is a plain object, not observable, so we drive a State flag).
    val ready by produceState(initialValue = false) {
        ModelMeta.ensureLoaded(context)
        value = ModelMeta.isLoaded()
    }

    val horizons = listOf("1d" to "1 Day", "1w" to "1 Week", "1m" to "1 Month")

    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Surface(
            shape = RoundedCornerShape(20.dp),
            color = Color(0xFF0E1E38),
            modifier = Modifier
                .fillMaxWidth(0.92f)
                .fillMaxHeight(0.85f)
        ) {
            Column(modifier = Modifier.fillMaxSize()) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(start = 20.dp, end = 8.dp, top = 12.dp, bottom = 4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Model Accuracy",
                        style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                        color = PredictionColors.textPrimary,
                        modifier = Modifier.weight(1f)
                    )
                    IconButton(onClick = onDismiss) {
                        Icon(Icons.Default.Close, contentDescription = "Close", tint = PredictionColors.textSecondary)
                    }
                }

                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f)
                        .verticalScroll(rememberScrollState())
                        .padding(horizontal = 20.dp)
                        .padding(bottom = 20.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    Text(
                        text = "How accurate is this model?",
                        style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.Bold),
                        color = PredictionColors.textPrimary
                    )
                    Text(
                        text = "honest, out-of-sample",
                        fontSize = 12.sp,
                        color = PredictionColors.accent
                    )
                    Text(
                        text = "Measured on a time-ordered hold-out the model never trained on " +
                            "(no look-ahead). \"Edge\" is how far it beats the naive \"always up\" " +
                            "guess — the bar a coin-flip on a drifting market would clear.",
                        fontSize = 13.sp,
                        lineHeight = 19.sp,
                        color = PredictionColors.textSecondary
                    )

                    if (ready) {
                        horizons.forEach { (key, label) ->
                            HorizonCard(uiHorizon = key, label = label)
                        }
                        Footnote()
                    } else {
                        Text(
                            text = "Loading model metadata…",
                            fontSize = 13.sp,
                            color = PredictionColors.textSecondary
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun HorizonCard(uiHorizon: String, label: String) {
    val acc = ModelMeta.accuracy(uiHorizon)
    val base = ModelMeta.testUpRate(uiHorizon)
    val brierRaw = ModelMeta.brierRaw(uiHorizon)
    val brierCal = ModelMeta.brierCalibrated(uiHorizon)

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(Color.White.copy(alpha = 0.06f))
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.SemiBold),
            color = PredictionColors.textPrimary
        )

        Row(verticalAlignment = Alignment.CenterVertically) {
            Stat("Accuracy", pct(acc), PredictionColors.accent, Modifier.weight(1f))
            VDivider()
            Stat("Base rate", base?.let { pct(it) } ?: "—", PredictionColors.textPrimary, Modifier.weight(1f))
            VDivider()
            Stat("Edge", edgeText(acc, base), edgeColor(acc, base), Modifier.weight(1f))
        }

        if (brierRaw != null && brierCal != null) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Icon(
                    Icons.Default.VerifiedUser,
                    contentDescription = null,
                    tint = PredictionColors.accent,
                    modifier = Modifier.size(13.dp)
                )
                Text(
                    text = "Calibrated · Brier ${fmt3(brierRaw)} → ${fmt3(brierCal)}",
                    fontSize = 12.sp,
                    color = PredictionColors.textSecondary
                )
            }
        }
    }
}

@Composable
private fun Stat(label: String, value: String, color: Color, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        Text(text = value, fontSize = 17.sp, fontWeight = FontWeight.Bold, color = color)
        Text(text = label, fontSize = 11.sp, color = PredictionColors.textMuted)
    }
}

@Composable
private fun VDivider() {
    Box(
        modifier = Modifier
            .width(1.dp)
            .height(34.dp)
            .background(Color.White.copy(alpha = 0.10f))
    )
}

@Composable
private fun Footnote() {
    val n = ModelMeta.nTest("1w")
    val nText = if (n != null) "Hold-out ≈ ${formatCount(n)} samples per horizon · " else ""
    Text(
        text = nText + "probabilities are Platt-calibrated so the shown % matches real " +
            "frequencies · 16 OHLCV features, on-device. Directional edge is small by nature — " +
            "markets are near-efficient, and honesty about that is the point.",
        fontSize = 11.sp,
        lineHeight = 16.sp,
        color = PredictionColors.textMuted,
        textAlign = TextAlign.Start
    )
}

private fun pct(v: Double): String = "%.1f%%".format(v * 100)

private fun fmt3(v: Double): String = "%.3f".format(v)

private fun edgeText(acc: Double, base: Double?): String {
    if (base == null) return "—"
    val d = acc - base
    val sign = if (d >= 0) "+" else "−"
    return "$sign%.1f pts".format(abs(d) * 100)
}

private fun edgeColor(acc: Double, base: Double?): Color =
    if (base != null && acc - base >= 0) PredictionColors.accent else PredictionColors.textPrimary

private fun formatCount(n: Int): String = "%,d".format(n)
