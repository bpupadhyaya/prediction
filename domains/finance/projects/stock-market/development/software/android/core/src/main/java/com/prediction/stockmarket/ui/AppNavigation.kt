package com.prediction.stockmarket.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.navigation.NavType
import androidx.navigation.compose.*
import androidx.navigation.navArgument
import com.prediction.stockmarket.ui.home.HomeScreen
import com.prediction.stockmarket.ui.stock.StockDetailScreen
import com.prediction.stockmarket.ui.portfolio.PortfolioScreen
import com.prediction.stockmarket.ui.watchlist.WatchlistScreen
import com.prediction.stockmarket.ui.prediction.StockPredictionHomeScreen
import com.prediction.stockmarket.ui.prediction.InteractivePredictionScreen
import com.prediction.stockmarket.ui.prediction.marketSectionIds

private data class Tab(val route: String, val label: String, val icon: ImageVector)

private val tabs = listOf(
    Tab("stockhome", "Home",      Icons.Default.Home),
    Tab("market",    "Market",    Icons.Default.TrendingUp),
    Tab("search",    "Lookup",    Icons.Default.Search),
    Tab("portfolio", "Portfolio", Icons.Default.Work),
    Tab("watchlist", "Watchlist", Icons.Default.Star),
)

@Composable
fun AppNavigation() {
    val navController = rememberNavController()
    val backstackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = backstackEntry?.destination?.route

    val topLevelRoutes = tabs.map { it.route }.toSet()
    val showBottomBar = currentRoute in topLevelRoutes

    Scaffold(
        containerColor = Color(0xFF0B1526),
        bottomBar = {
            if (showBottomBar) {
                NavigationBar(
                    containerColor = Color(0xFF0D1F36),
                    windowInsets = WindowInsets(0)
                ) {
                    tabs.forEach { tab ->
                        NavigationBarItem(
                            selected = currentRoute == tab.route,
                            onClick = {
                                navController.navigate(tab.route) {
                                    popUpTo("stockhome") { saveState = true }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            icon = {
                                Icon(
                                    tab.icon,
                                    contentDescription = tab.label
                                )
                            },
                            label = { Text(tab.label) },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = Color.White,
                                selectedTextColor = Color.White,
                                indicatorColor = Color(0xFF142B47),
                                unselectedIconColor = Color.White.copy(alpha = 0.45f),
                                unselectedTextColor = Color.White.copy(alpha = 0.45f)
                            )
                        )
                    }
                }
            }
        }
    ) { padding ->
        NavHost(navController, startDestination = "stockhome") {
            composable("stockhome") {
                StockPredictionHomeScreen { sectionId ->
                    if (sectionId.isNotBlank()) {
                        if (sectionId in marketSectionIds) {
                            navController.navigate("market") {
                                popUpTo("stockhome") { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        } else {
                            navController.navigate("stock_module/$sectionId")
                        }
                    }
                }
            }
            composable("market") { HomeScreen(navController, padding) }
            composable("search") {
                com.prediction.stockmarket.ui.stock.SearchScreen(navController, padding)
            }
            composable("portfolio") { PortfolioScreen(navController, padding) }
            composable("watchlist") { WatchlistScreen(navController, padding) }
            composable(
                "stock/{ticker}",
                arguments = listOf(navArgument("ticker") { type = NavType.StringType })
            ) { backstack ->
                val ticker = backstack.arguments?.getString("ticker").orEmpty()
                if (ticker.isNotBlank()) {
                    StockDetailScreen(
                        ticker = ticker,
                        navController = navController,
                        onInteractivePredict = { t ->
                            if (t.isNotBlank()) navController.navigate("interactive_prediction/$t")
                        }
                    )
                }
            }
            composable(
                "interactive_prediction/{ticker}",
                arguments = listOf(navArgument("ticker") { type = NavType.StringType })
            ) { backStackEntry ->
                val ticker = backStackEntry.arguments?.getString("ticker").orEmpty()
                InteractivePredictionScreen(
                    ticker = ticker,
                    onBack = { navController.popBackStack() }
                )
            }
            composable(
                "stock_module/{moduleId}",
                arguments = listOf(navArgument("moduleId") { type = NavType.StringType })
            ) { backstack ->
                val moduleId = backstack.arguments?.getString("moduleId").orEmpty()
                StockModulePlaceholder(
                    moduleId = moduleId,
                    onBack = { navController.popBackStack() }
                )
            }
        }
    }
}

@Composable
private fun StockModulePlaceholder(moduleId: String, onBack: () -> Unit) {
    val (title, subtitle, icon, gradColors, iconColor) = when (moduleId) {
        "crypto"   -> PlaceholderData("Crypto",         "BTC, ETH & altcoin price signals",     Icons.Default.CurrencyBitcoin, listOf(Color(0xFF063C4B), Color(0xFF0A6A83), Color(0xFF10ACC9)), Color(0xFF67DFF0))
        "earnings" -> PlaceholderData("Earnings",       "Beat or miss AI forecasts",             Icons.Default.CalendarMonth,   listOf(Color(0xFF0F4738), Color(0xFF157A5E), Color(0xFF10B981)), Color(0xFF6EE7B7))
        "sectors"  -> PlaceholderData("Sectors",        "Sector rotation & performance maps",    Icons.Default.GridView,        listOf(Color(0xFF0E2040), Color(0xFF1A3D73), Color(0xFF2868BE)), Color(0xFF93C3F0))
        "global"   -> PlaceholderData("Global Markets", "International index forecasts",         Icons.Default.Public,          listOf(Color(0xFF143E26), Color(0xFF1B7A3D), Color(0xFF22C55E)), Color(0xFF86EFAC))
        else       -> PlaceholderData(moduleId,         "Coming soon",                           Icons.Default.TrendingUp,      listOf(Color(0xFF0C3B6E), Color(0xFF1A69A2), Color(0xFF0EA5E9)), Color(0xFF7DD3F8))
    }

    val gradient = Brush.linearGradient(
        colors = gradColors,
        start = Offset(0f, 0f),
        end = Offset(Float.POSITIVE_INFINITY, Float.POSITIVE_INFINITY)
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0B1526))
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(top = 120.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Top
        ) {
            Box(
                modifier = Modifier
                    .size(80.dp)
                    .clip(CircleShape)
                    .background(gradient),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = title,
                    tint = iconColor,
                    modifier = Modifier.size(38.dp)
                )
            }

            Spacer(Modifier.height(24.dp))

            Text(
                text = title,
                style = MaterialTheme.typography.headlineSmall.copy(fontWeight = FontWeight.Bold),
                color = Color.White,
                textAlign = TextAlign.Center
            )

            Spacer(Modifier.height(8.dp))

            Text(
                text = subtitle,
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White.copy(alpha = 0.7f),
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(horizontal = 32.dp)
            )

            Spacer(Modifier.height(16.dp))

            Text(
                text = "Coming Soon",
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White.copy(alpha = 0.4f)
            )
        }

        TextButton(
            onClick = onBack,
            modifier = Modifier
                .align(Alignment.TopStart)
                .statusBarsPadding()
                .padding(start = 8.dp, top = 8.dp)
                .semantics { contentDescription = "Go back" }
        ) {
            Icon(
                Icons.Default.ChevronLeft,
                contentDescription = null,
                tint = Color.White
            )
            Text("Home", color = Color.White, fontWeight = FontWeight.Medium)
        }
    }
}

private data class PlaceholderData(
    val title: String,
    val subtitle: String,
    val icon: ImageVector,
    val gradColors: List<Color>,
    val iconColor: Color
)
