package com.prediction.stockmarket.ui.portfolio

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Inbox
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavController
import com.prediction.stockmarket.data.database.PortfolioEntity

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PortfolioScreen(
    navController: NavController,
    padding: PaddingValues,
    viewModel: PortfolioViewModel = hiltViewModel()
) {
    val holdings by viewModel.holdings.collectAsState()
    val prices by viewModel.latestPrices.collectAsState()
    var showAddDialog by remember { mutableStateOf(false) }

    val totalValue = holdings.sumOf { h -> (prices[h.ticker] ?: h.costBasis) * h.shares }
    val totalCost = holdings.sumOf { it.costBasis * it.shares }
    val gain = totalValue - totalCost
    val gainPct = if (totalCost > 0) gain / totalCost * 100 else 0.0

    Column(modifier = Modifier.fillMaxSize().padding(padding)) {
        TopAppBar(
            title = { Text("Portfolio") },
            actions = {
                IconButton(onClick = { showAddDialog = true }) {
                    Icon(Icons.Default.Add, contentDescription = "Add holding")
                }
            },
            colors = TopAppBarDefaults.mediumTopAppBarColors()
        )

        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    "Total Value",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    "$%.2f".format(totalValue),
                    style = MaterialTheme.typography.headlineLarge,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    "%+.2f (%+.1f%%)".format(gain, gainPct),
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Medium,
                    color = if (gain >= 0) Color(0xFF4CAF50) else Color(0xFFFF5252)
                )
            }
        }

        if (holdings.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Inbox,
                        contentDescription = null,
                        modifier = Modifier.size(48.dp),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        "No holdings yet — tap + to add one",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        } else {
            LazyColumn {
                items(holdings, key = { it.ticker }) { holding ->
                    val price = prices[holding.ticker] ?: holding.costBasis
                    HoldingListItem(
                        holding = holding,
                        currentPrice = price,
                        onClick = {
                            if (holding.ticker.isNotBlank()) {
                                navController.navigate("stock/${holding.ticker}")
                            }
                        }
                    )
                }
            }
        }
    }

    if (showAddDialog) {
        AddHoldingDialog(
            onDismiss = { showAddDialog = false },
            onAdd = { ticker, shares, cost ->
                viewModel.addHolding(ticker, shares, cost)
                showAddDialog = false
            }
        )
    }
}

@Composable
private fun HoldingListItem(holding: PortfolioEntity, currentPrice: Double, onClick: () -> Unit) {
    val marketValue = currentPrice * holding.shares
    val gainPct = if (holding.costBasis > 0) {
        (currentPrice - holding.costBasis) / holding.costBasis * 100
    } else 0.0
    val gainColor = if (gainPct >= 0) Color(0xFF4CAF50) else Color(0xFFFF5252)

    ListItem(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        headlineContent = {
            Text(holding.ticker, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
        },
        supportingContent = {
            Text(
                "%.2f shares @ $%.2f".format(holding.shares, holding.costBasis),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        },
        trailingContent = {
            Column(horizontalAlignment = Alignment.End) {
                Text(
                    "$%.2f".format(marketValue),
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    "%+.1f%%".format(gainPct),
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Medium,
                    color = gainColor
                )
            }
        }
    )
    HorizontalDivider(thickness = 0.5.dp, color = MaterialTheme.colorScheme.surfaceVariant)
}

@Composable
private fun AddHoldingDialog(onDismiss: () -> Unit, onAdd: (String, Double, Double) -> Unit) {
    var ticker by remember { mutableStateOf("") }
    var shares by remember { mutableStateOf("") }
    var costBasis by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Holding", fontWeight = FontWeight.SemiBold) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = ticker,
                    onValueChange = { ticker = it.uppercase() },
                    label = { Text("Ticker") },
                    singleLine = true,
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = shares,
                    onValueChange = { shares = it },
                    label = { Text("Shares") },
                    singleLine = true,
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = costBasis,
                    onValueChange = { costBasis = it },
                    label = { Text("Avg cost/share ($)") },
                    singleLine = true,
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    val s = shares.toDoubleOrNull() ?: return@TextButton
                    val c = costBasis.toDoubleOrNull() ?: return@TextButton
                    if (ticker.isNotBlank()) onAdd(ticker, s, c)
                }
            ) { Text("Add") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } }
    )
}
