package com.prediction.stockmarket.ui.stock

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavController
import com.prediction.stockmarket.data.database.StockEntity

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SearchScreen(
    navController: NavController,
    padding: PaddingValues,
    viewModel: SearchViewModel = hiltViewModel()
) {
    var query by remember { mutableStateOf("") }
    val results by viewModel.results.collectAsState()

    Column(modifier = Modifier.fillMaxSize().padding(padding)) {
        SearchBar(
            query = query,
            onQueryChange = { query = it; viewModel.search(it) },
            onSearch = { viewModel.search(it) },
            active = false,
            onActiveChange = {},
            placeholder = { Text("Ticker or company name") },
            modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp)
        ) {}

        LazyColumn {
            items(results, key = { it.ticker }) { stock ->
                StockListItem(stock) { navController.navigate("stock/${stock.ticker}") }
                HorizontalDivider(thickness = 0.5.dp, color = MaterialTheme.colorScheme.surfaceVariant)
            }
        }
    }
}

@Composable
private fun StockListItem(stock: StockEntity, onClick: () -> Unit) {
    ListItem(
        modifier = Modifier.clickable(onClick = onClick),
        headlineContent = { Text(stock.ticker, style = MaterialTheme.typography.titleMedium) },
        supportingContent = {
            Text(buildString {
                append(stock.name)
                stock.sector?.let { append(" · $it") }
            }, style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 1)
        },
        trailingContent = {
            stock.marketCap?.let {
                Text(formatCap(it), style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    )
}

private fun formatCap(cap: Double) = when {
    cap >= 1e12 -> "$%.1fT".format(cap / 1e12)
    cap >= 1e9 -> "$%.1fB".format(cap / 1e9)
    cap >= 1e6 -> "$%.1fM".format(cap / 1e6)
    else -> "$%.0f".format(cap)
}
