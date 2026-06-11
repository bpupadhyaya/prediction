package com.prediction.stockmarket.ui.home

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
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
import com.prediction.stockmarket.data.database.PredictionEntity

private val HOT_TICKERS = listOf(
    "NVDA", "AAPL", "MSFT", "META", "GOOGL", "AMZN", "TSLA", "AMD", "NFLX",
    "HOOD", "PLTR", "ARM", "SMCI", "COIN", "MSTR", "UBER", "LYFT", "SOFI",
    "RBLX", "SNAP", "RIVN", "SOUN", "AI", "IONQ", "QUBT", "RDDT", "ACHR", "JOBY"
)

private data class PreIPOCompany(
    val name: String,
    val sector: String,
    val description: String,
    val status: String,
    val estValuation: String
)

private val PRE_IPO = listOf(
    PreIPOCompany("OpenAI", "AI / LLM", "Maker of ChatGPT, GPT-4o, and Sora", "Pre-IPO", "\$157B"),
    PreIPOCompany("Anthropic", "AI / LLM", "AI safety company, maker of Claude", "Pre-IPO", "\$61B"),
    PreIPOCompany("SpaceX", "Aerospace", "Rockets, Starship, Starlink satellite internet", "Pre-IPO", "\$350B"),
    PreIPOCompany("Stripe", "Fintech", "Global payments infrastructure for internet businesses", "Pre-IPO", "\$65B"),
    PreIPOCompany("Databricks", "Data / AI", "Unified data analytics and AI platform", "Pre-IPO", "\$62B"),
    PreIPOCompany("Canva", "Design / SaaS", "Online visual design and content creation platform", "Pre-IPO", "\$26B"),
    PreIPOCompany("Chime", "Neobank", "Mobile-first banking and financial services", "Pre-IPO", "\$25B"),
    PreIPOCompany("Klarna", "Fintech", "Buy now, pay later — filed for US IPO", "Filed IPO", "\$20B"),
    PreIPOCompany("Discord", "Social", "Community and gaming communication platform", "Pre-IPO", "\$15B"),
    PreIPOCompany("Epic Games", "Gaming", "Fortnite, Unreal Engine, Epic Games Store", "Private", "\$32B"),
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    navController: NavController,
    padding: PaddingValues,
    viewModel: HomeViewModel = hiltViewModel()
) {
    val predictions by viewModel.predictions.collectAsState()
    val hotPredictions by viewModel.hotPredictions.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    var selectedHorizon by remember { mutableStateOf("1w") }
    var selectedTab by remember { mutableIntStateOf(0) }
    val tabs = listOf("Top Signals", "Hot Stocks", "Pre-IPO")

    // Load hot predictions when hot stocks tab is first selected
    LaunchedEffect(selectedTab) {
        if (selectedTab == 1 && hotPredictions.isEmpty()) {
            viewModel.loadHotPredictions(HOT_TICKERS)
        }
    }

    Column(modifier = Modifier.fillMaxSize().padding(padding)) {
        TopAppBar(
            title = { Text("Market") },
            colors = TopAppBarDefaults.mediumTopAppBarColors()
        )

        TabRow(selectedTabIndex = selectedTab) {
            tabs.forEachIndexed { index, title ->
                Tab(
                    selected = selectedTab == index,
                    onClick = { selectedTab = index },
                    text = { Text(title, style = MaterialTheme.typography.labelMedium) }
                )
            }
        }

        when (selectedTab) {
            0 -> TopSignalsTab(
                predictions = predictions,
                isLoading = isLoading,
                selectedHorizon = selectedHorizon,
                onHorizonChange = { h ->
                    selectedHorizon = h
                    viewModel.loadPredictions(h)
                },
                onTickerClick = { ticker ->
                    if (ticker.isNotBlank()) navController.navigate("stock/$ticker")
                }
            )
            1 -> HotStocksTab(
                hotPredictions = hotPredictions,
                isLoading = isLoading,
                onTickerClick = { ticker ->
                    if (ticker.isNotBlank()) navController.navigate("stock/$ticker")
                },
                onRefresh = { viewModel.loadHotPredictions(HOT_TICKERS) }
            )
            2 -> PreIPOTab()
        }
    }
}

@OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)
@Composable
private fun TopSignalsTab(
    predictions: List<PredictionEntity>,
    isLoading: Boolean,
    selectedHorizon: String,
    onHorizonChange: (String) -> Unit,
    onTickerClick: (String) -> Unit
) {
    Column(modifier = Modifier.fillMaxSize()) {
        SingleChoiceSegmentedButtonRow(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp)
        ) {
            listOf("1d", "1w", "1m").forEachIndexed { i, h ->
                SegmentedButton(
                    selected = selectedHorizon == h,
                    onClick = { onHorizonChange(h) },
                    shape = SegmentedButtonDefaults.itemShape(i, 3),
                    label = { Text(h.uppercase()) }
                )
            }
        }

        when {
            isLoading -> {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            }
            predictions.isEmpty() -> {
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
                            "No predictions yet — sync data first",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
            else -> {
                LazyColumn(contentPadding = PaddingValues(vertical = 8.dp)) {
                    items(predictions, key = { it.ticker }) { pred ->
                        PredictionListItem(pred) { onTickerClick(pred.ticker) }
                    }
                }
            }
        }
    }
}

@Composable
private fun HotStocksTab(
    hotPredictions: Map<String, PredictionEntity?>,
    isLoading: Boolean,
    onTickerClick: (String) -> Unit,
    onRefresh: () -> Unit
) {
    val withPredictions = HOT_TICKERS.count { hotPredictions[it] != null }
    val notSynced = HOT_TICKERS.count { !hotPredictions.containsKey(it) }

    Column(modifier = Modifier.fillMaxSize()) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                "$withPredictions with predictions · $notSynced not yet synced",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.weight(1f)
            )
            TextButton(onClick = onRefresh) {
                Text("Refresh", style = MaterialTheme.typography.labelSmall)
            }
        }

        when {
            isLoading -> {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            }
            hotPredictions.isEmpty() -> {
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
                            "Tap Refresh to load hot stock data",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
            else -> {
                LazyColumn(contentPadding = PaddingValues(vertical = 4.dp)) {
                    items(HOT_TICKERS) { ticker ->
                        val pred = hotPredictions[ticker]
                        HotTickerCard(
                            ticker = ticker,
                            prediction = pred,
                            onClick = { onTickerClick(ticker) }
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun HotTickerCard(
    ticker: String,
    prediction: PredictionEntity?,
    onClick: () -> Unit
) {
    ListItem(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        headlineContent = {
            Text(ticker, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
        },
        supportingContent = {
            if (prediction != null) {
                Text(
                    "%.0f%% confidence · Model: %.0f%%".format(
                        prediction.probability * 100,
                        prediction.modelAccuracy * 100
                    ),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            } else {
                Text(
                    "Not in local database",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        },
        trailingContent = {
            if (prediction != null) {
                val isUp = prediction.direction == "UP"
                val dirColor = if (isUp) Color(0xFF4CAF50) else Color(0xFFFF5252)
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = dirColor.copy(alpha = 0.15f)
                ) {
                    Text(
                        prediction.direction,
                        style = MaterialTheme.typography.labelMedium,
                        color = dirColor,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                    )
                }
            }
        }
    )
    HorizontalDivider(thickness = 0.5.dp, color = MaterialTheme.colorScheme.surfaceVariant)
}

@Composable
private fun PreIPOTab() {
    LazyVerticalGrid(
        columns = GridCells.Fixed(2),
        contentPadding = PaddingValues(12.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        modifier = Modifier.fillMaxSize()
    ) {
        items(PRE_IPO, key = { it.name }) { company ->
            PreIPOCard(company)
        }
    }
}

@Composable
private fun PreIPOCard(company: PreIPOCompany) {
    val statusColor = when (company.status) {
        "Filed IPO" -> Color(0xFF1976D2)
        "Private"   -> Color(0xFF616161)
        else        -> Color(0xFF7B1FA2)
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Text(
                    company.name,
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.weight(1f)
                )
                Surface(
                    shape = RoundedCornerShape(4.dp),
                    color = statusColor.copy(alpha = 0.15f)
                ) {
                    Text(
                        company.status,
                        style = MaterialTheme.typography.labelSmall,
                        color = statusColor,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 4.dp, vertical = 2.dp)
                    )
                }
            }

            Spacer(Modifier.height(4.dp))
            Text(
                company.sector,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.primary
            )
            Spacer(Modifier.height(4.dp))
            Text(
                company.description,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 3
            )
            Spacer(Modifier.height(8.dp))
            Text(
                company.estValuation,
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurface
            )
        }
    }
}

@Composable
private fun PredictionListItem(pred: PredictionEntity, onClick: () -> Unit) {
    val isUp = pred.direction == "UP"
    val dirColor = if (isUp) Color(0xFF4CAF50) else Color(0xFFFF5252)

    ListItem(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        headlineContent = {
            Text(pred.ticker, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
        },
        supportingContent = {
            Text(
                "%.0f%% confidence · Model: %.0f%%".format(
                    pred.probability * 100, pred.modelAccuracy * 100
                ),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        },
        trailingContent = {
            Text(
                pred.direction,
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold,
                color = dirColor
            )
        }
    )
    HorizontalDivider(thickness = 0.5.dp, color = MaterialTheme.colorScheme.surfaceVariant)
}
