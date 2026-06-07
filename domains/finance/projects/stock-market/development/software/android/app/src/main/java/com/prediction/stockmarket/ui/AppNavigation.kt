package com.prediction.stockmarket.ui

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.NavType
import androidx.navigation.compose.*
import androidx.navigation.navArgument
import com.prediction.stockmarket.ui.home.HomeScreen
import com.prediction.stockmarket.ui.stock.StockDetailScreen
import com.prediction.stockmarket.ui.portfolio.PortfolioScreen
import com.prediction.stockmarket.ui.watchlist.WatchlistScreen
import com.prediction.stockmarket.ui.sync.SyncScreen
import com.prediction.stockmarket.ui.models.ModelsScreen

private data class Tab(val route: String, val label: String, val icon: ImageVector)

private val tabs = listOf(
    Tab("home", "Market", Icons.Default.TrendingUp),
    Tab("search", "Lookup", Icons.Default.Search),
    Tab("portfolio", "Portfolio", Icons.Default.Work),
    Tab("watchlist", "Watchlist", Icons.Default.Star),
    Tab("sync", "Sync", Icons.Default.Sync),
    Tab("models", "Models", Icons.Default.Build)
)

@Composable
fun AppNavigation() {
    val navController = rememberNavController()
    val backstackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = backstackEntry?.destination?.route

    Scaffold(
        bottomBar = {
            NavigationBar {
                tabs.forEach { tab ->
                    NavigationBarItem(
                        selected = currentRoute == tab.route,
                        onClick = {
                            navController.navigate(tab.route) {
                                popUpTo(navController.graph.startDestinationId) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(tab.icon, contentDescription = tab.label) },
                        label = { Text(tab.label) }
                    )
                }
            }
        }
    ) { padding ->
        NavHost(navController, startDestination = "home") {
            composable("home") { HomeScreen(navController, padding) }
            composable("search") {
                com.prediction.stockmarket.ui.stock.SearchScreen(navController, padding)
            }
            composable("portfolio") { PortfolioScreen(navController, padding) }
            composable("watchlist") { WatchlistScreen(navController, padding) }
            composable("sync") { SyncScreen(padding) }
            composable("models") { ModelsScreen(padding) }
            composable(
                "stock/{ticker}",
                arguments = listOf(navArgument("ticker") { type = NavType.StringType })
            ) { backstack ->
                StockDetailScreen(
                    ticker = backstack.arguments?.getString("ticker") ?: "",
                    navController = navController
                )
            }
        }
    }
}
