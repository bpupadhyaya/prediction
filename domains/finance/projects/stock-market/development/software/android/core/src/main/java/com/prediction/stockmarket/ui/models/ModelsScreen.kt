package com.prediction.stockmarket.ui.models

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Memory
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ModelsScreen(
    padding: PaddingValues,
    viewModel: ModelsViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()

    Column(modifier = Modifier.fillMaxSize().padding(padding)) {
        TopAppBar(
            title = { Text("LLM Models") },
            colors = TopAppBarDefaults.mediumTopAppBarColors()
        )

        LazyColumn(
            contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Hardware info card
            item {
                HardwareInfoCard(state)
            }

            // Active model banner
            state.activeModelId?.let { activeId ->
                val activeModel = LLM_CATALOG.find { it.id == activeId }
                if (activeModel != null) {
                    item {
                        ActiveModelBanner(activeModel)
                    }
                }
            }

            // Models directory path
            item {
                Text(
                    text = "Models directory: ${state.modelsDir}",
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = FontFamily.Monospace,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(vertical = 4.dp)
                )
            }

            // Model cards
            items(LLM_CATALOG, key = { it.id }) { model ->
                val isDownloaded = viewModel.isDownloaded(model)
                val diskSizeGB = viewModel.diskSizeGB(model)
                val downloadStatus = state.downloadStatus[model.id]
                val downloadProgress = state.downloadProgress[model.id] ?: 0f
                val isActive = state.activeModelId == model.id
                val compatibility = model.compatibility(state.totalRamGB)

                ModelCard(
                    model = model,
                    isDownloaded = isDownloaded,
                    diskSizeGB = diskSizeGB,
                    downloadStatus = downloadStatus,
                    downloadProgress = downloadProgress,
                    isActive = isActive,
                    compatibility = compatibility,
                    onDownload = { viewModel.download(model) },
                    onActivate = { viewModel.activate(model) },
                    onDeactivate = { viewModel.deactivate() },
                    onDelete = { viewModel.deleteModel(model) }
                )
            }

            item { Spacer(Modifier.height(8.dp)) }
        }
    }
}

@Composable
private fun HardwareInfoCard(state: ModelUiState) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Icon(
                    Icons.Default.Memory,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary
                )
                Text(
                    "Device Hardware",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold
                )
            }
            Spacer(Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                InfoChip(label = "RAM", value = "%.1f GB".format(state.totalRamGB))
                InfoChip(label = "CPU", value = "${state.cpuCount} cores")
                if (state.isArmDevice) {
                    SuggestionChip(
                        onClick = {},
                        label = { Text("ARM", style = MaterialTheme.typography.labelSmall) }
                    )
                }
            }
        }
    }
}

@Composable
private fun InfoChip(label: String, value: String) {
    Surface(
        shape = RoundedCornerShape(8.dp),
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 1.dp
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(label, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(value, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Medium)
        }
    }
}

@Composable
private fun ActiveModelBanner(model: LLMModel) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                "Active:",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onPrimaryContainer
            )
            Text(
                model.name,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.onPrimaryContainer
            )
            Spacer(Modifier.weight(1f))
            Text(
                model.quantization,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
            )
        }
    }
}

@Composable
private fun ModelCard(
    model: LLMModel,
    isDownloaded: Boolean,
    diskSizeGB: Double?,
    downloadStatus: String?,
    downloadProgress: Float,
    isActive: Boolean,
    compatibility: ModelCompatibility,
    onDownload: () -> Unit,
    onActivate: () -> Unit,
    onDeactivate: () -> Unit,
    onDelete: () -> Unit
) {
    val isDownloading = downloadStatus == "downloading"
    val hasError = downloadStatus == "error"

    Card(
        modifier = Modifier
            .fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {

            // Header row: name + tags + compatibility badge
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.Top
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        model.name,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold
                    )
                    Spacer(Modifier.height(4.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                        model.tags.forEach { tag ->
                            TagBadge(tag)
                        }
                    }
                }
                CompatibilityBadge(compatibility)
            }

            Spacer(Modifier.height(8.dp))

            // Metadata row
            Row(
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                MetaItem("Params", "%.0fB".format(model.paramsB))
                MetaItem("Quant", model.quantization)
                MetaItem("Size", "%.1f GB".format(model.sizeGB))
                MetaItem("Min RAM", "%.0f GB".format(model.ramMinGB))
            }

            Spacer(Modifier.height(8.dp))

            // Description
            Text(
                model.description,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            // Download progress
            if (isDownloading) {
                Spacer(Modifier.height(8.dp))
                LinearProgressIndicator(
                    progress = { downloadProgress },
                    modifier = Modifier.fillMaxWidth()
                )
                Text(
                    "%.0f%%".format(downloadProgress * 100),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(top = 2.dp)
                )
            }

            // Error state
            if (hasError) {
                Spacer(Modifier.height(4.dp))
                Text(
                    "Download failed — tap Download to retry",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.error
                )
            }

            // File path if downloaded
            if (isDownloaded && diskSizeGB != null) {
                Spacer(Modifier.height(4.dp))
                Text(
                    "On disk: %.2f GB".format(diskSizeGB),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    fontFamily = FontFamily.Monospace
                )
            }

            Spacer(Modifier.height(12.dp))
            HorizontalDivider(thickness = 0.5.dp)
            Spacer(Modifier.height(12.dp))

            // Action buttons
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                when {
                    isDownloading -> {
                        Button(
                            onClick = {},
                            enabled = false,
                            shape = RoundedCornerShape(12.dp)
                        ) {
                            Text("Downloading…")
                        }
                    }
                    !isDownloaded -> {
                        Button(
                            onClick = onDownload,
                            shape = RoundedCornerShape(12.dp)
                        ) {
                            Text("Download %.1f GB".format(model.sizeGB))
                        }
                    }
                    isActive -> {
                        OutlinedButton(
                            onClick = onDeactivate,
                            shape = RoundedCornerShape(12.dp)
                        ) {
                            Text("Deactivate")
                        }
                        OutlinedButton(
                            onClick = onDelete,
                            shape = RoundedCornerShape(12.dp),
                            colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.error)
                        ) {
                            Text("Clear from Disk")
                        }
                    }
                    else -> {
                        Button(
                            onClick = onActivate,
                            shape = RoundedCornerShape(12.dp)
                        ) {
                            Text("Activate")
                        }
                        OutlinedButton(
                            onClick = onDelete,
                            shape = RoundedCornerShape(12.dp),
                            colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.error)
                        ) {
                            Text("Clear")
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun TagBadge(tag: String) {
    Surface(
        shape = RoundedCornerShape(4.dp),
        color = MaterialTheme.colorScheme.secondaryContainer
    ) {
        Text(
            tag,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSecondaryContainer,
            fontWeight = FontWeight.Medium,
            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
        )
    }
}

@Composable
private fun CompatibilityBadge(compatibility: ModelCompatibility) {
    val (bg, fg) = when (compatibility) {
        ModelCompatibility.COMPATIBLE   -> Pair(Color(0xFF4CAF50).copy(alpha = 0.15f), Color(0xFF2E7D32))
        ModelCompatibility.MARGINAL     -> Pair(Color(0xFFFF9800).copy(alpha = 0.15f), Color(0xFFE65100))
        ModelCompatibility.INSUFFICIENT -> Pair(MaterialTheme.colorScheme.errorContainer, MaterialTheme.colorScheme.onErrorContainer)
    }
    Surface(
        shape = RoundedCornerShape(6.dp),
        color = bg
    ) {
        Text(
            compatibility.label,
            style = MaterialTheme.typography.labelSmall,
            color = fg,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
        )
    }
}

@Composable
private fun MetaItem(label: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(label, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(value, style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Medium)
    }
}
