package com.prediction.stockmarket.ui.modules

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.prediction.stockmarket.data.sync.YahooFinanceFetcher
import com.prediction.stockmarket.prediction.PredictionEngine
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import javax.inject.Inject
import kotlin.math.abs
import kotlin.math.min

// ─── Instrument universes ─────────────────────────────────────────────────────

internal data class Instrument(val symbol: String, val label: String, val sublabel: String = "")

private val CRYPTO_UNIVERSE = listOf(
    Instrument("BTC-USD", "Bitcoin"), Instrument("ETH-USD", "Ethereum"),
    Instrument("SOL-USD", "Solana"), Instrument("BNB-USD", "BNB"),
    Instrument("XRP-USD", "XRP"), Instrument("ADA-USD", "Cardano"),
    Instrument("DOGE-USD", "Dogecoin"), Instrument("AVAX-USD", "Avalanche"),
    Instrument("DOT-USD", "Polkadot"), Instrument("LINK-USD", "Chainlink"),
    Instrument("LTC-USD", "Litecoin"), Instrument("BCH-USD", "Bitcoin Cash"),
    Instrument("TRX-USD", "TRON"), Instrument("XLM-USD", "Stellar"),
    Instrument("XMR-USD", "Monero"), Instrument("ETC-USD", "Ethereum Classic"),
    Instrument("FIL-USD", "Filecoin"), Instrument("ATOM-USD", "Cosmos"),
    Instrument("UNI7083-USD", "Uniswap"), Instrument("AAVE-USD", "Aave"),
    Instrument("ALGO-USD", "Algorand"), Instrument("VET-USD", "VeChain"),
    Instrument("HBAR-USD", "Hedera"), Instrument("NEAR-USD", "NEAR"),
)

private val SECTOR_UNIVERSE = listOf(
    Instrument("XLK", "Technology"), Instrument("XLF", "Financials"),
    Instrument("XLE", "Energy"), Instrument("XLV", "Health Care"),
    Instrument("XLI", "Industrials"), Instrument("XLY", "Cons. Discretionary"),
    Instrument("XLP", "Cons. Staples"), Instrument("XLU", "Utilities"),
    Instrument("XLRE", "Real Estate"), Instrument("XLB", "Materials"),
    Instrument("XLC", "Communications"), Instrument("SPY", "S&P 500 (bench)"),
)

private val GLOBAL_UNIVERSE = listOf(
    Instrument("^GSPC", "S&P 500", "United States"), Instrument("^IXIC", "Nasdaq", "United States"),
    Instrument("^DJI", "Dow Jones", "United States"), Instrument("^GSPTSE", "TSX", "Canada"),
    Instrument("^BVSP", "Bovespa", "Brazil"), Instrument("^FTSE", "FTSE 100", "United Kingdom"),
    Instrument("^GDAXI", "DAX", "Germany"), Instrument("^FCHI", "CAC 40", "France"),
    Instrument("^STOXX50E", "Euro Stoxx 50", "Eurozone"), Instrument("^N225", "Nikkei 225", "Japan"),
    Instrument("^HSI", "Hang Seng", "Hong Kong"), Instrument("000001.SS", "Shanghai", "China"),
    Instrument("^KS11", "KOSPI", "South Korea"), Instrument("^BSESN", "Sensex", "India"),
    Instrument("^NSEI", "NIFTY 50", "India"), Instrument("^AXJO", "ASX 200", "Australia"),
    Instrument("^TWII", "TAIEX", "Taiwan"), Instrument("^STI", "Straits Times", "Singapore"),
    Instrument("^JKSE", "IDX Composite", "Indonesia"), Instrument("^KLSE", "KLCI", "Malaysia"),
    Instrument("^MXX", "IPC", "Mexico"), Instrument("^TA125.TA", "TA-125", "Israel"),
)

// Earnings watch universe — mega caps + high-interest names (merged with watchlist at load)
private val EARNINGS_UNIVERSE = listOf(
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "AMD", "NFLX",
    "JPM", "V", "WMT", "COST", "ORCL", "CRM", "ADBE", "INTC", "QCOM", "TXN",
    "HOOD", "PLTR", "COIN", "UBER", "SOFI", "RDDT",
)

// ─── Row model + UI state ─────────────────────────────────────────────────────

data class ModuleRow(
    val symbol: String,
    val name: String,
    val sublabel: String,
    val price: Double,
    val changePct1d: Double,
    val ret1w: Double,
    val direction: String?,        // "UP" / "DOWN" / null when model unavailable
    val probability: Double?,
    val earningsDate: Date? = null,
)

data class ModuleUiState(
    val isLoading: Boolean = true,
    val rows: List<ModuleRow> = emptyList(),
    val error: String? = null,
)

// ─── ViewModel ────────────────────────────────────────────────────────────────

@HiltViewModel
class MarketModuleViewModel @Inject constructor(
    private val fetcher: YahooFinanceFetcher,
    private val engine: PredictionEngine,
    private val watchlistDao: com.prediction.stockmarket.data.database.WatchlistDao,
) : ViewModel() {

    private val _uiState = MutableStateFlow(ModuleUiState())
    val uiState: StateFlow<ModuleUiState> = _uiState.asStateFlow()

    private var loadedModule: String? = null

    fun load(moduleId: String, force: Boolean = false) {
        if (!force && loadedModule == moduleId && _uiState.value.rows.isNotEmpty()) return
        loadedModule = moduleId
        _uiState.value = ModuleUiState(isLoading = true)
        viewModelScope.launch {
            try {
                val rows = withContext(Dispatchers.IO) {
                    when (moduleId) {
                        "crypto"  -> loadInstruments(CRYPTO_UNIVERSE)
                        "sectors" -> loadInstruments(SECTOR_UNIVERSE)
                        "global"  -> loadInstruments(GLOBAL_UNIVERSE)
                        "earnings" -> loadEarnings()
                        else      -> emptyList()
                    }
                }
                _uiState.value = ModuleUiState(
                    isLoading = false,
                    rows = rows,
                    error = if (rows.isEmpty()) "No data available — check your connection and retry." else null,
                )
            } catch (e: Exception) {
                _uiState.value = ModuleUiState(isLoading = false, error = e.message ?: "Load failed")
            }
        }
    }

    private suspend fun loadInstruments(universe: List<Instrument>): List<ModuleRow> =
        withContext(Dispatchers.IO) {
            universe.map { inst ->
                async {
                    try {
                        val bars = fetcher.fetchPriceBars(inst.symbol, range = "2y")
                        if (bars.size < 253) return@async null
                        val chrono = bars.sortedBy { it.date }
                        val last = chrono.last()
                        val prev = chrono[chrono.size - 2]
                        val wk = chrono[chrono.size - 6]
                        val pred = engine.predict(inst.symbol, "1W", chrono.sortedByDescending { it.date })
                        ModuleRow(
                            symbol = inst.symbol,
                            name = inst.label,
                            sublabel = inst.sublabel,
                            price = last.close,
                            changePct1d = (last.close - prev.close) / prev.close * 100,
                            ret1w = (last.close - wk.close) / wk.close * 100,
                            direction = pred?.direction,
                            probability = pred?.probability,
                        )
                    } catch (_: Exception) { null }
                }
            }.awaitAll().filterNotNull()
        }

    private suspend fun loadEarnings(): List<ModuleRow> = withContext(Dispatchers.IO) {
        val watch = try { watchlistDao.getAll().map { it.ticker } } catch (_: Exception) { emptyList() }
        val symbols = (watch + EARNINGS_UNIVERSE).distinct()
        val nowSec = System.currentTimeMillis() / 1000
        val horizonSec = nowSec + 60L * 60 * 24 * 45   // next 45 days

        val upcoming = fetcher.fetchQuoteLites(symbols)
            .filter { it.earningsTimestamp != null && it.earningsTimestamp in nowSec..horizonSec }
            .sortedBy { it.earningsTimestamp }
            .take(15)

        upcoming.map { q ->
            async {
                val pred = try {
                    val bars = fetcher.fetchPriceBars(q.symbol, range = "2y")
                    if (bars.size >= 253) engine.predict(q.symbol, "1W", bars.sortedByDescending { it.date }) else null
                } catch (_: Exception) { null }
                ModuleRow(
                    symbol = q.symbol,
                    name = q.name,
                    sublabel = "",
                    price = q.price,
                    changePct1d = q.changePct,
                    ret1w = 0.0,
                    direction = pred?.direction,
                    probability = pred?.probability,
                    earningsDate = Date(q.earningsTimestamp!! * 1000),
                )
            }
        }.awaitAll()
    }
}

// ─── Radar (scan & rank by model conviction) ──────────────────────────────────
//
// Fetches a whole instrument universe (crypto, sector ETFs, or global indices),
// runs the on-device 1-week model on each instrument, and ranks the results by
// calibrated P(up) descending (most bullish → most bearish). Per-instrument
// fetch failures are skipped so one bad symbol never stops the scan. Reuses
// YahooFinanceFetcher + PredictionEngine — no new data layer, no changes to the
// engine. Parameterized by universe + title so it serves every scannable module.

data class RadarRow(
    val symbol: String,
    val name: String,
    val direction: String,   // "UP" / "DOWN"
    val probUp: Double,       // calibrated P(up)
)

data class RadarUiState(
    val isScanning: Boolean = false,
    val scanned: Int = 0,
    val total: Int = 0,
    val rows: List<RadarRow> = emptyList(),
    val started: Boolean = false,
)

@HiltViewModel
class RadarViewModel @Inject constructor(
    private val fetcher: YahooFinanceFetcher,
    private val engine: PredictionEngine,
) : ViewModel() {

    private val _uiState = MutableStateFlow(RadarUiState())
    val uiState: StateFlow<RadarUiState> = _uiState.asStateFlow()

    // Universe is injected once by the overlay (the only runtime input) so the
    // identical scan/rank logic is reused across crypto, sectors, and global.
    private var universe: List<Instrument> = emptyList()

    internal fun startIfNeeded(universe: List<Instrument>) {
        if (_uiState.value.started) return
        this.universe = universe
        scan()
    }

    fun scan() {
        val universe = this.universe
        _uiState.value = RadarUiState(
            isScanning = true, scanned = 0, total = universe.size,
            rows = emptyList(), started = true,
        )
        viewModelScope.launch {
            val collected = java.util.Collections.synchronizedList(mutableListOf<RadarRow>())
            withContext(Dispatchers.IO) {
                universe.map { inst ->
                    async {
                        val row = try {
                            val bars = fetcher.fetchPriceBars(inst.symbol, range = "2y")
                            if (bars.size < 253) null
                            else {
                                val pred = engine.predict(inst.symbol, "1W", bars.sortedByDescending { it.date })
                                if (pred?.direction == null) null
                                else RadarRow(inst.symbol, inst.label, pred.direction, pred.probability)
                            }
                        } catch (_: Exception) {
                            // Per-instrument failures are skipped so one bad symbol never stops the scan.
                            null
                        }
                        // Update progress + ranked list progressively as results stream in.
                        if (row != null) collected.add(row)
                        val ranked = synchronized(collected) { collected.sortedByDescending { it.probUp } }
                        val cur = _uiState.value
                        _uiState.value = cur.copy(scanned = cur.scanned + 1, rows = ranked)
                    }
                }.awaitAll()
            }
            _uiState.value = _uiState.value.copy(isScanning = false)
        }
    }
}

@Composable
internal fun RadarOverlay(
    title: String,
    universe: List<Instrument>,
    onClose: () -> Unit,
    onOpenTicker: (String) -> Unit,
    viewModel: RadarViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsState()
    LaunchedEffect(Unit) { viewModel.startIfNeeded(universe) }

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
            TextButton(onClick = onClose) {
                Icon(Icons.Default.ChevronLeft, contentDescription = "Close", tint = Color.White)
                Text("Back", color = Color.White, fontWeight = FontWeight.Medium)
            }
            Spacer(Modifier.weight(1f))
        }

        Row(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                modifier = Modifier.size(44.dp).clip(CircleShape)
                    .background(Brush.linearGradient(listOf(Color(0xFF063C4B), Color(0xFF10ACC9)))),
                contentAlignment = Alignment.Center,
            ) {
                Icon(Icons.Default.Radar, contentDescription = "Radar", tint = Color(0xFF67DFF0), modifier = Modifier.size(24.dp))
            }
            Spacer(Modifier.width(12.dp))
            Column {
                Text(title, style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold), color = Color.White)
                Text(
                    if (state.isScanning) "1-week outlook · ranked by P(up) · ${state.scanned}/${state.total}"
                    else "1-week outlook · ranked by P(up)",
                    style = MaterialTheme.typography.bodySmall,
                    color = Color.White.copy(alpha = 0.6f),
                )
            }
        }
        Spacer(Modifier.height(8.dp))

        if (state.isScanning && state.rows.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    CircularProgressIndicator(color = Color(0xFF67DFF0))
                    Spacer(Modifier.height(12.dp))
                    Text("Scanning ${state.scanned}/${state.total}…", color = Color.White.copy(alpha = 0.6f), style = MaterialTheme.typography.bodySmall)
                }
            }
        } else {
            LazyColumn(contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)) {
                itemsIndexed(state.rows, key = { _, r -> r.symbol }) { idx, row ->
                    RadarCard(rank = idx + 1, row = row, onClick = { onOpenTicker(row.symbol) })
                }
                item {
                    Text(
                        "Same on-device model, calibrated — ranks the strongest 1-week bullish → bearish read. Probabilistic — not financial advice.",
                        style = MaterialTheme.typography.labelSmall,
                        color = Color.White.copy(alpha = 0.35f),
                        textAlign = TextAlign.Center,
                        modifier = Modifier.fillMaxWidth().padding(vertical = 14.dp),
                    )
                }
            }
        }
    }
}

@Composable
private fun RadarCard(rank: Int, row: RadarRow, onClick: () -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp)
            .clickable(onClick = onClick),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF13243F)),
        shape = RoundedCornerShape(14.dp),
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                "$rank",
                style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.Bold),
                color = Color.White.copy(alpha = 0.55f),
                modifier = Modifier.width(26.dp),
                textAlign = TextAlign.Center,
            )
            Spacer(Modifier.width(10.dp))
            Column(Modifier.weight(1f)) {
                Text(row.name, style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.SemiBold), color = Color.White)
                Text(row.symbol, style = MaterialTheme.typography.labelSmall, color = Color.White.copy(alpha = 0.5f))
            }
            RadarBadge(row.direction, row.probUp)
        }
    }
}

@Composable
private fun RadarBadge(direction: String, probUp: Double) {
    val (label, bg, fg) = if (direction.uppercase() == "UP")
        Triple("▲ Bullish ${(probUp * 100).toInt()}%", Color(0xFF14532D), Color(0xFF4ADE80))
    else
        Triple("▼ Bearish ${((1.0 - probUp) * 100).toInt()}%", Color(0xFF601A1A), Color(0xFFF87171))
    Surface(shape = RoundedCornerShape(8.dp), color = bg) {
        Text(
            label,
            style = MaterialTheme.typography.labelMedium.copy(fontWeight = FontWeight.Bold),
            color = fg,
            modifier = Modifier.padding(horizontal = 9.dp, vertical = 5.dp),
        )
    }
}

// ─── Screen ───────────────────────────────────────────────────────────────────

private data class ModuleChrome(
    val title: String,
    val subtitle: String,
    val icon: ImageVector,
    val gradColors: List<Color>,
    val iconColor: Color,
)

private fun chromeFor(moduleId: String): ModuleChrome = when (moduleId) {
    "crypto"   -> ModuleChrome("Crypto", "BTC, ETH & altcoin price signals", Icons.Default.CurrencyBitcoin, listOf(Color(0xFF063C4B), Color(0xFF0A6A83), Color(0xFF10ACC9)), Color(0xFF67DFF0))
    "earnings" -> ModuleChrome("Earnings", "Upcoming reports & AI direction", Icons.Default.CalendarMonth, listOf(Color(0xFF0F4738), Color(0xFF157A5E), Color(0xFF10B981)), Color(0xFF6EE7B7))
    "sectors"  -> ModuleChrome("Sectors", "Sector rotation & performance map", Icons.Default.GridView, listOf(Color(0xFF0E2040), Color(0xFF1A3D73), Color(0xFF2868BE)), Color(0xFF93C3F0))
    "global"   -> ModuleChrome("Global Markets", "International index forecasts", Icons.Default.Public, listOf(Color(0xFF143E26), Color(0xFF1B7A3D), Color(0xFF22C55E)), Color(0xFF86EFAC))
    else       -> ModuleChrome(moduleId, "", Icons.Default.TrendingUp, listOf(Color(0xFF0C3B6E), Color(0xFF1A69A2), Color(0xFF0EA5E9)), Color(0xFF7DD3F8))
}

@Composable
fun MarketModuleScreen(
    moduleId: String,
    onBack: () -> Unit,
    onOpenTicker: (String) -> Unit,
    viewModel: MarketModuleViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsState()
    LaunchedEffect(moduleId) { viewModel.load(moduleId) }

    var showRadar by remember { mutableStateOf(false) }

    val chrome = chromeFor(moduleId)
    val gradient = Brush.linearGradient(
        colors = chrome.gradColors,
        start = Offset(0f, 0f),
        end = Offset(Float.POSITIVE_INFINITY, Float.POSITIVE_INFINITY),
    )
    // Index symbols (with ^ / .SS) have no detail screen — only plain tickers navigate.
    val rowsTappable = moduleId != "global"

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0B1526))
    ) {
        // Header
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
            Spacer(Modifier.weight(1f))
            TextButton(onClick = { viewModel.load(moduleId, force = true) }) {
                Icon(Icons.Default.Refresh, contentDescription = "Refresh", tint = Color.White.copy(alpha = 0.7f), modifier = Modifier.size(18.dp))
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
                Icon(chrome.icon, contentDescription = chrome.title, tint = chrome.iconColor, modifier = Modifier.size(24.dp))
            }
            Spacer(Modifier.width(12.dp))
            Column {
                Text(chrome.title, style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold), color = Color.White)
                Text(chrome.subtitle, style = MaterialTheme.typography.bodySmall, color = Color.White.copy(alpha = 0.6f))
            }
        }
        Spacer(Modifier.height(8.dp))

        when {
            state.isLoading -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    CircularProgressIndicator(color = chrome.iconColor)
                    Spacer(Modifier.height(12.dp))
                    Text("Fetching market data…", color = Color.White.copy(alpha = 0.6f), style = MaterialTheme.typography.bodySmall)
                }
            }
            state.error != null && state.rows.isEmpty() -> Box(Modifier.fillMaxSize().padding(32.dp), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(state.error ?: "", color = Color.White.copy(alpha = 0.7f), textAlign = TextAlign.Center)
                    Spacer(Modifier.height(12.dp))
                    Button(onClick = { viewModel.load(moduleId, force = true) }) { Text("Retry") }
                }
            }
            moduleId == "sectors" -> SectorContent(state.rows, onOpenTicker, onScanRadar = { showRadar = true })
            else -> LazyColumn(contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)) {
                if (radarFor(moduleId) != null) {
                    item { ScanRadarButton(onClick = { showRadar = true }) }
                }
                items(state.rows, key = { it.symbol }) { row ->
                    InstrumentCard(
                        row = row,
                        showEarnings = moduleId == "earnings",
                        onClick = if (rowsTappable) ({ onOpenTicker(row.symbol) }) else null,
                    )
                }
                item { DisclaimerFooter() }
            }
        }
    }

    if (showRadar) {
        val radar = radarFor(moduleId)
        if (radar != null) {
            RadarOverlay(
                title = radar.first,
                universe = radar.second,
                onClose = { showRadar = false },
                onOpenTicker = { t -> showRadar = false; onOpenTicker(t) },
            )
        }
    }
}

// Modules that support a live "scan & rank" radar, with their title + universe.
// Excludes S&P 500 / Nasdaq 100 / Hot Stocks / Earnings — universes too large or
// DB-backed to scan live.
private fun radarFor(moduleId: String): Pair<String, List<Instrument>>? = when (moduleId) {
    "crypto"  -> "Crypto Radar" to CRYPTO_UNIVERSE
    "sectors" -> "Sector Radar" to SECTOR_UNIVERSE
    "global"  -> "Global Radar" to GLOBAL_UNIVERSE
    else      -> null
}

@Composable
private fun ScanRadarButton(onClick: () -> Unit) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp)
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(14.dp),
        color = Color.Transparent,
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(14.dp))
                .background(Brush.horizontalGradient(listOf(Color(0xFF063C4B), Color(0xFF0A6A83))))
                .padding(horizontal = 14.dp, vertical = 13.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(Icons.Default.Radar, contentDescription = null, tint = Color.White, modifier = Modifier.size(20.dp))
            Spacer(Modifier.width(8.dp))
            Text(
                "Scan all — rank by conviction",
                style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.SemiBold),
                color = Color.White,
            )
            Spacer(Modifier.weight(1f))
            Icon(Icons.Default.ChevronRight, contentDescription = null, tint = Color.White.copy(alpha = 0.5f), modifier = Modifier.size(18.dp))
        }
    }
}

// ─── Sector heat map + list ──────────────────────────────────────────────────

@Composable
private fun SectorContent(rows: List<ModuleRow>, onOpenTicker: (String) -> Unit, onScanRadar: () -> Unit) {
    LazyColumn(contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)) {
        item { ScanRadarButton(onClick = onScanRadar) }
        item { Spacer(Modifier.height(8.dp)) }
        item {
            Text(
                "Conviction heat-map · model P(up) over 1 week",
                style = MaterialTheme.typography.labelMedium,
                color = Color.White.copy(alpha = 0.6f),
                modifier = Modifier.padding(start = 4.dp, bottom = 6.dp),
            )
            // Fixed-height grid: 12 tiles / 2 columns = 6 rows of 72dp + spacing
            LazyVerticalGrid(
                columns = GridCells.Fixed(2),
                modifier = Modifier.fillMaxWidth().height(498.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                userScrollEnabled = false,
            ) {
                items(rows, key = { it.symbol }) { row ->
                    val tileColor = convictionColor(row.probability)
                    Column(
                        modifier = Modifier
                            .height(72.dp)
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(10.dp))
                            .background(tileColor)
                            .clickable { onOpenTicker(row.symbol) }
                            .padding(10.dp),
                        verticalArrangement = Arrangement.Center,
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(row.symbol, style = MaterialTheme.typography.labelMedium.copy(fontWeight = FontWeight.Bold), color = Color.White)
                            Spacer(Modifier.weight(1f))
                            Text(convictionLabel(row.probability), style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.Bold), color = Color.White)
                        }
                        Text(row.name, style = MaterialTheme.typography.labelSmall, color = Color.White.copy(alpha = 0.85f), maxLines = 1)
                        Text(formatPct(row.changePct1d) + " today", style = MaterialTheme.typography.labelSmall, color = Color.White.copy(alpha = 0.7f))
                    }
                }
            }
            Spacer(Modifier.height(14.dp))
            Text(
                "Forecasts",
                style = MaterialTheme.typography.labelMedium,
                color = Color.White.copy(alpha = 0.6f),
                modifier = Modifier.padding(start = 4.dp, bottom = 4.dp),
            )
        }
        items(rows, key = { "list-${it.symbol}" }) { row ->
            InstrumentCard(row = row, showEarnings = false, onClick = { onOpenTicker(row.symbol) })
        }
        item { DisclaimerFooter() }
    }
}

// ─── Instrument card ──────────────────────────────────────────────────────────

@Composable
private fun InstrumentCard(row: ModuleRow, showEarnings: Boolean, onClick: (() -> Unit)?) {
    val dayColor = if (row.changePct1d >= 0) Color(0xFF4ADE80) else Color(0xFFF87171)
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp)
            .then(if (onClick != null) Modifier.clickable(onClick = onClick) else Modifier),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF13243F)),
        shape = RoundedCornerShape(14.dp),
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(row.name, style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.SemiBold), color = Color.White)
                    if (row.sublabel.isNotEmpty()) {
                        Spacer(Modifier.width(6.dp))
                        Text(row.sublabel, style = MaterialTheme.typography.labelSmall, color = Color.White.copy(alpha = 0.45f))
                    }
                }
                Spacer(Modifier.height(2.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(row.symbol, style = MaterialTheme.typography.labelSmall, color = Color.White.copy(alpha = 0.5f))
                    if (showEarnings && row.earningsDate != null) {
                        Spacer(Modifier.width(8.dp))
                        Surface(shape = RoundedCornerShape(6.dp), color = Color(0xFF1A3D73)) {
                            Text(
                                "Earnings ${SimpleDateFormat("EEE, MMM d", Locale.US).format(row.earningsDate)}",
                                style = MaterialTheme.typography.labelSmall,
                                color = Color(0xFF93C3F0),
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                            )
                        }
                    }
                }
            }
            Column(horizontalAlignment = Alignment.End) {
                Text(formatPrice(row.price), style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.SemiBold), color = Color.White)
                Text(formatPct(row.changePct1d) + " today", style = MaterialTheme.typography.labelSmall, color = dayColor)
            }
            Spacer(Modifier.width(10.dp))
            DirectionChip(row.direction, row.probability)
        }
    }
}

@Composable
private fun DirectionChip(direction: String?, probability: Double?) {
    val (label, bg, fg) = when (direction?.uppercase()) {
        "UP"   -> Triple("▲ ${pctLabel(probability)}", Color(0xFF14532D), Color(0xFF4ADE80))
        "DOWN" -> Triple("▼ ${pctLabel(probability, invert = true)}", Color(0xFF601A1A), Color(0xFFF87171))
        else   -> Triple("—", Color(0xFF1E293B), Color.White.copy(alpha = 0.4f))
    }
    Surface(shape = RoundedCornerShape(8.dp), color = bg) {
        Text(
            label,
            style = MaterialTheme.typography.labelMedium.copy(fontWeight = FontWeight.Bold),
            color = fg,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 5.dp),
        )
    }
}

@Composable
private fun DisclaimerFooter() {
    Text(
        "1-week direction from the on-device model. Probabilistic — not financial advice.",
        style = MaterialTheme.typography.labelSmall,
        color = Color.White.copy(alpha = 0.35f),
        textAlign = TextAlign.Center,
        modifier = Modifier.fillMaxWidth().padding(vertical = 14.dp),
    )
}

// ─── Conviction heat-map helpers ──────────────────────────────────────────────
//
// Maps the model's calibrated P(up) (0..1) to a tile color. 50% is neutral; the
// further from 50%, the stronger the green (bullish) or red (bearish). Tiles stay
// on the dark theme via a dark base blended with the conviction color by alpha.

private fun convictionColor(probability: Double?): Color {
    // No model read → neutral slate tile.
    if (probability == null) return Color(0xFF1E293B)
    val t = (((probability * 100.0) - 50.0) / 50.0).coerceIn(-1.0, 1.0) // signed [-1,1]
    val intensity = min(1.0, abs(t) * 2.2).toFloat()
    val conviction = if (t >= 0) Color(0xFF16A34A) else Color(0xFFDC2626)
    // Blend over a dark base so faint convictions are still readable in dark theme.
    val base = Color(0xFF13243F)
    return Color(
        red = base.red + (conviction.red - base.red) * intensity,
        green = base.green + (conviction.green - base.green) * intensity,
        blue = base.blue + (conviction.blue - base.blue) * intensity,
    )
}

private fun convictionLabel(probability: Double?): String {
    if (probability == null) return "—"
    return "${(probability * 100).toInt()}%"
}

// ─── Formatting helpers ───────────────────────────────────────────────────────

private fun pctLabel(probability: Double?, invert: Boolean = false): String {
    if (probability == null) return ""
    val p = if (invert) 1.0 - probability else probability
    return "${(p * 100).toInt()}%"
}

private fun formatPct(v: Double): String = String.format(Locale.US, "%+.2f%%", v)

private fun formatPrice(v: Double): String = when {
    v.isNaN() -> "—"
    v >= 1000 -> String.format(Locale.US, "%,.0f", v)
    v >= 1    -> String.format(Locale.US, "%,.2f", v)
    else      -> String.format(Locale.US, "%.4f", v)
}
