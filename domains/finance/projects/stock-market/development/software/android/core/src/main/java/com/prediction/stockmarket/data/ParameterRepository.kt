package com.prediction.stockmarket.data

import android.content.Context
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

data class StockParameter(
    val name: String,
    val domain: String,
    val domainLabel: String,
    val label: String,
    val unit: String,
    val defaultValue: Double,
    val layman: String,
    val technical: String
)

@Singleton
class ParameterRepository @Inject constructor(
    @ApplicationContext private val context: Context,
    private val gson: Gson
) {
    @Suppress("UNCHECKED_CAST")
    val parameters: List<StockParameter> by lazy {
        val json = context.assets.open("parameters.json")
            .bufferedReader().use { it.readText() }
        val type = object : TypeToken<List<StockParameter>>() {}.type
        gson.fromJson<List<StockParameter>>(json, type)
    }

    val domainOrder = listOf(
        "macro", "fundamental", "cross_asset", "technical", "sentiment", "geopolitical"
    )

    fun groupedByDomain(): List<Pair<String, List<StockParameter>>> {
        val grouped = parameters.groupBy { it.domain }
        return domainOrder.mapNotNull { domain ->
            grouped[domain]?.let { domain to it }
        }
    }
}
