package com.equalinformation.prediction.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.GridView
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.prediction.stockmarket.ui.AppNavigation
import com.prediction.stockmarket.ui.prediction.PredictionHomeScreen
import com.prediction.stockmarket.ui.theme.StockPredictionTheme
import dagger.hilt.android.AndroidEntryPoint

private val navBg  = Color(0xFF0D1F36)
private val navSel = Color(0xFF142B47)
private val homeBg = Color(0xFF0B1526)
private val accent = Color(0xFF3B82F6)

private data class PredTab(val label: String, val icon: ImageVector)
private val predTabs = listOf(
    PredTab("Home", Icons.Default.GridView),
    PredTab("Search", Icons.Default.Search),
    PredTab("Settings", Icons.Default.Settings)
)

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            var activeModule by remember { mutableStateOf<String?>(null) }

            if (activeModule == "stock_market") {
                StockMarketModule(onBack = { activeModule = null })
            } else {
                PredictionMainScreen(onModuleSelect = { activeModule = it })
            }
        }
    }
}

@Composable
private fun PredictionMainScreen(onModuleSelect: (String) -> Unit) {
    var selectedTab by remember { mutableStateOf(0) }

    StockPredictionTheme {
        Scaffold(
            containerColor = homeBg,
            bottomBar = {
                NavigationBar(
                    containerColor = navBg,
                    windowInsets = WindowInsets(0)
                ) {
                    predTabs.forEachIndexed { index, tab ->
                        NavigationBarItem(
                            selected = selectedTab == index,
                            onClick = { selectedTab = index },
                            icon = { Icon(tab.icon, contentDescription = tab.label) },
                            label = { Text(tab.label) },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = Color.White,
                                selectedTextColor = Color.White,
                                indicatorColor = navSel,
                                unselectedIconColor = Color.White.copy(alpha = 0.45f),
                                unselectedTextColor = Color.White.copy(alpha = 0.45f)
                            )
                        )
                    }
                }
            }
        ) { padding ->
            Box(Modifier.padding(bottom = padding.calculateBottomPadding())) {
                when (selectedTab) {
                    0 -> PredictionHomeScreen(onModuleSelect = onModuleSelect)
                    1 -> PredPlaceholder("Search", Icons.Default.Search)
                    2 -> PredPlaceholder("Settings", Icons.Default.Settings)
                }
            }
        }
    }
}

@Composable
private fun PredPlaceholder(title: String, icon: ImageVector) {
    Box(
        Modifier.fillMaxSize().background(homeBg),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Icon(icon, contentDescription = null, tint = accent, modifier = Modifier.size(48.dp))
            Text(title, color = Color.White, fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Text("Coming soon", color = Color.White.copy(alpha = 0.6f))
        }
    }
}

@Composable
private fun StockMarketModule(onBack: () -> Unit) {
    StockPredictionTheme {
        Box(Modifier.fillMaxSize()) {
            AppNavigation()
            TextButton(
                onClick = onBack,
                modifier = Modifier
                    .align(Alignment.TopStart)
                    .padding(top = 48.dp, start = 8.dp)
                    .background(
                        MaterialTheme.colorScheme.surface.copy(alpha = 0.9f),
                        RoundedCornerShape(20.dp)
                    )
            ) {
                Icon(
                    Icons.AutoMirrored.Filled.ArrowBack,
                    contentDescription = "Back to home",
                    modifier = Modifier.size(16.dp)
                )
                Spacer(Modifier.width(4.dp))
                Text("Home", style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}
