package com.prediction.stockmarket.ui.sync

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.CloudDownload
import androidx.compose.material.icons.filled.Error
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.Sync
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.prediction.stockmarket.data.sync.MarketDataSourceType

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SyncScreen(
    padding: PaddingValues,
    viewModel: SyncViewModel = hiltViewModel()
) {
    val syncState by viewModel.syncState.collectAsState()
    val selectedSource by viewModel.selectedSource.collectAsState()
    val syncProgress by viewModel.syncProgress.collectAsState()
    val currentTicker by viewModel.currentTicker.collectAsState()

    var apiKeyText by remember(selectedSource) {
        mutableStateOf(viewModel.getApiKey(selectedSource))
    }
    var sourceDropdownExpanded by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(padding)
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp)
    ) {
        // Header
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Icon(
                Icons.Default.Sync,
                contentDescription = null,
                modifier = Modifier.size(32.dp),
                tint = MaterialTheme.colorScheme.primary
            )
            Text("Market Data", style = MaterialTheme.typography.headlineSmall)
        }

        // Data Source section
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Text(
                    "Data Source",
                    style = MaterialTheme.typography.titleMedium
                )

                // Source dropdown
                ExposedDropdownMenuBox(
                    expanded = sourceDropdownExpanded,
                    onExpandedChange = { sourceDropdownExpanded = it }
                ) {
                    OutlinedTextField(
                        value = selectedSource.displayName,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Source") },
                        trailingIcon = {
                            ExposedDropdownMenuDefaults.TrailingIcon(expanded = sourceDropdownExpanded)
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .menuAnchor()
                    )
                    ExposedDropdownMenu(
                        expanded = sourceDropdownExpanded,
                        onDismissRequest = { sourceDropdownExpanded = false }
                    ) {
                        MarketDataSourceType.values().forEach { source ->
                            DropdownMenuItem(
                                text = { Text(source.displayName) },
                                onClick = {
                                    viewModel.setSource(source)
                                    sourceDropdownExpanded = false
                                }
                            )
                        }
                    }
                }

                // Description of selected source
                Text(
                    text = selectedSource.description,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )

                // API key field if needed
                if (selectedSource.requiresKey) {
                    OutlinedTextField(
                        value = apiKeyText,
                        onValueChange = {
                            apiKeyText = it
                            viewModel.setApiKey(selectedSource, it)
                        },
                        label = { Text("API Key") },
                        placeholder = { Text("Enter your API key") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
        }

        // Sync progress / status
        SyncStateSection(
            syncState = syncState,
            syncProgress = syncProgress,
            currentTicker = currentTicker
        )

        // Sync button
        Button(
            onClick = { viewModel.sync() },
            enabled = syncState !is SyncUiState.Syncing,
            modifier = Modifier.fillMaxWidth()
        ) {
            Icon(
                Icons.Default.CloudDownload,
                contentDescription = null,
                modifier = Modifier.padding(end = 8.dp)
            )
            Text("Sync Now", style = MaterialTheme.typography.titleMedium)
        }

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            "All data is stored locally on your device. No account required.",
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth()
        )
    }
}

@Composable
private fun SyncStateSection(
    syncState: SyncUiState,
    syncProgress: Pair<Int, Int>,
    currentTicker: String
) {
    when (syncState) {
        is SyncUiState.Idle -> Text(
            "Tap Sync Now to fetch the latest market data and run on-device predictions.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        is SyncUiState.Syncing -> {
            val (done, total) = syncProgress
            val progress = if (total > 0) done.toFloat() / total.toFloat() else 0f

            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
                    Text(
                        text = if (currentTicker.isNotEmpty() && total > 0)
                            "Syncing $currentTicker... ($done/$total)"
                        else
                            "Preparing sync...",
                        style = MaterialTheme.typography.bodyMedium
                    )
                }

                if (total > 0) {
                    LinearProgressIndicator(
                        progress = { progress },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
        }

        is SyncUiState.Done -> Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Icon(
                Icons.Default.CheckCircle,
                contentDescription = null,
                tint = Color(0xFF4CAF50)
            )
            Text(
                syncState.tagName,
                style = MaterialTheme.typography.bodyMedium,
                color = Color(0xFF4CAF50)
            )
        }

        is SyncUiState.Error -> Column(horizontalAlignment = Alignment.Start) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Icon(
                    Icons.Default.Error,
                    contentDescription = null,
                    tint = Color(0xFFFF5252)
                )
                Text(
                    "Sync failed",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color(0xFFFF5252)
                )
            }
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                syncState.message,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
