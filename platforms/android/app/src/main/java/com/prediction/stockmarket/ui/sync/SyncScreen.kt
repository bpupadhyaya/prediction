package com.prediction.stockmarket.ui.sync

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CloudDownload
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Error
import androidx.compose.material.icons.filled.Sync
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SyncScreen(
    padding: PaddingValues,
    viewModel: SyncViewModel = hiltViewModel()
) {
    val syncState by viewModel.syncState.collectAsState()

    Column(
        modifier = Modifier.fillMaxSize().padding(padding).padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(24.dp, Alignment.CenterVertically)
    ) {
        Icon(Icons.Default.Sync, contentDescription = null,
            modifier = Modifier.size(80.dp),
            tint = MaterialTheme.colorScheme.primary)

        Text("Data Sync", style = MaterialTheme.typography.headlineMedium)

        Text(
            "Download the latest market data and predictions from GitHub Releases. Works over WiFi or cellular.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )

        SyncStateIndicator(syncState)

        Button(
            onClick = { viewModel.sync() },
            enabled = syncState !is SyncUiState.Syncing,
            modifier = Modifier.fillMaxWidth()
        ) {
            Icon(Icons.Default.CloudDownload, contentDescription = null,
                modifier = Modifier.padding(end = 8.dp))
            Text("Sync Now", style = MaterialTheme.typography.titleMedium)
        }

        Spacer(modifier = Modifier.weight(1f))

        Text(
            "All data is stored locally on your device. No account required.",
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )
    }
}

@Composable
private fun SyncStateIndicator(state: SyncUiState) {
    when (state) {
        is SyncUiState.Idle -> Text("Tap Sync to fetch fresh data",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant)

        is SyncUiState.Syncing -> Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            CircularProgressIndicator(modifier = Modifier.size(24.dp))
            Text("Syncing…", style = MaterialTheme.typography.bodyMedium)
        }

        is SyncUiState.Done -> Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Icon(Icons.Default.CheckCircle, contentDescription = null, tint = Color(0xFF4CAF50))
            Text("Updated to ${state.tagName}", style = MaterialTheme.typography.bodyMedium)
        }

        is SyncUiState.Error -> Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Icon(Icons.Default.Error, contentDescription = null, tint = Color(0xFFFF5252))
                Text("Sync failed", style = MaterialTheme.typography.bodyMedium, color = Color(0xFFFF5252))
            }
            Text(state.message, style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center)
        }
    }
}
