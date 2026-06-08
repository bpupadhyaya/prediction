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
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.prediction.stockmarket.ui.AppNavigation
import com.prediction.stockmarket.ui.prediction.PredictionHomeScreen
import com.prediction.stockmarket.ui.theme.StockPredictionTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            var activeModule by remember { mutableStateOf<String?>(null) }

            when (activeModule) {
                "stock_market" -> StockMarketModule(onBack = { activeModule = null })
                else -> PredictionHomeScreen(onModuleSelect = { activeModule = it })
            }
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
