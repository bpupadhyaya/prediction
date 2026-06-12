package com.prediction.stockmarket.data.sync

import android.content.SharedPreferences
import com.prediction.stockmarket.data.database.PriceBarEntity
import com.prediction.stockmarket.data.database.StockEntity
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.*
import javax.inject.Inject
import javax.inject.Singleton

enum class MarketDataSourceType(
    val displayName: String,
    val requiresKey: Boolean,
    val description: String
) {
    YAHOO_FINANCE("Yahoo Finance", false, "Default · No API key required · Reliable"),
    ALPHA_VANTAGE("Alpha Vantage", true, "Free 25 calls/day · Get key at alphavantage.co"),
    TWELVE_DATA("Twelve Data", true, "Free 800 calls/day · Get key at twelvedata.com"),
    POLYGON_IO("Polygon.io", true, "Free 5 calls/min · Get key at polygon.io"),
    STOOQ("Stooq", false, "No key required · CSV-based · International"),
}

@Singleton
class MarketDataSourceManager @Inject constructor(
    private val prefs: SharedPreferences
) {
    var activeSource: MarketDataSourceType
        get() = MarketDataSourceType.values().firstOrNull {
            it.name == prefs.getString("market_data_source", null)
        } ?: MarketDataSourceType.YAHOO_FINANCE
        set(v) { prefs.edit().putString("market_data_source", v.name).apply() }

    fun getApiKey(source: MarketDataSourceType): String =
        prefs.getString("api_key_${source.name}", "") ?: ""

    fun setApiKey(source: MarketDataSourceType, key: String) =
        prefs.edit().putString("api_key_${source.name}", key).apply()
}

// MARK: - Yahoo Finance fetcher

class YahooFinanceFetcher @Inject constructor(private val client: OkHttpClient) {

    fun fetchPriceBars(ticker: String, range: String = "5y"): List<PriceBarEntity> {
        val url = "https://query1.finance.yahoo.com/v8/finance/chart/$ticker?interval=1d&range=$range"
        val req = Request.Builder().url(url)
            .header("User-Agent", "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36")
            .header("Accept", "application/json")
            .build()
        val body = client.newCall(req).execute().use { it.body?.string() ?: "" }
        return parseChartJson(body, ticker)
    }

    /**
     * Global symbol search via Yahoo's search API — finds ANY instrument on ANY
     * exchange: equities worldwide (7203.T, SAP.DE, RELIANCE.NS, ...), crypto
     * pairs, ETFs, indices, futures. This is what makes the app's "predict any
     * stock or crypto, local or global" mission reachable from the Lookup tab.
     */
    fun searchSymbols(query: String, limit: Int = 20): List<StockEntity> {
        if (query.isBlank()) return emptyList()
        return try {
            val q = java.net.URLEncoder.encode(query.trim(), "UTF-8")
            val url = "https://query1.finance.yahoo.com/v1/finance/search" +
                "?q=$q&quotesCount=$limit&newsCount=0&listsCount=0"
            val req = Request.Builder().url(url)
                .header("User-Agent", "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36")
                .header("Accept", "application/json")
                .build()
            val body = client.newCall(req).execute().use { it.body?.string() ?: "" }
            val quotes = JSONObject(body).optJSONArray("quotes") ?: return emptyList()
            (0 until quotes.length()).mapNotNull { i ->
                val item = quotes.optJSONObject(i) ?: return@mapNotNull null
                val symbol = item.optString("symbol")
                if (symbol.isEmpty()) return@mapNotNull null
                val name = item.optString("shortname")
                    .ifEmpty { item.optString("longname") }
                    .ifEmpty { symbol }
                val type = item.optString("quoteType")        // EQUITY, CRYPTOCURRENCY, ETF, INDEX…
                val exchange = item.optString("exchDisp").ifEmpty { item.optString("exchange") }
                StockEntity(
                    ticker = symbol,
                    name = name,
                    sector = listOf(type, exchange).filter { it.isNotEmpty() }.joinToString(" · "),
                    industry = null,
                    marketCap = null,
                )
            }
        } catch (_: Exception) { emptyList() }
    }

    /** Lightweight batch quote — name, price, day change, next earnings timestamp. */
    data class QuoteLite(
        val symbol: String,
        val name: String,
        val price: Double,
        val changePct: Double,
        val earningsTimestamp: Long?,   // unix seconds, null if none reported
    )

    fun fetchQuoteLites(symbols: List<String>): List<QuoteLite> {
        if (symbols.isEmpty()) return emptyList()
        return try {
            val joined = symbols.joinToString(",")
            val url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=$joined"
            val req = Request.Builder().url(url)
                .header("User-Agent", "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36")
                .header("Accept", "application/json")
                .build()
            val body = client.newCall(req).execute().use { it.body?.string() ?: "" }
            val result = JSONObject(body).getJSONObject("quoteResponse").getJSONArray("result")
            (0 until result.length()).mapNotNull { i ->
                val q = result.getJSONObject(i)
                QuoteLite(
                    symbol = q.optString("symbol") ?: return@mapNotNull null,
                    name = q.optString("shortName").ifEmpty { q.optString("longName", q.optString("symbol")) },
                    price = q.optDouble("regularMarketPrice", Double.NaN),
                    changePct = q.optDouble("regularMarketChangePercent", 0.0),
                    earningsTimestamp = if (q.has("earningsTimestamp")) q.getLong("earningsTimestamp") else null,
                )
            }
        } catch (_: Exception) { emptyList() }
    }

    fun fetchQuote(ticker: String): StockEntity? {
        return try {
            val url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=$ticker"
            val req = Request.Builder().url(url)
                .header("User-Agent", "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36")
                .header("Accept", "application/json")
                .build()
            val body = client.newCall(req).execute().use { it.body?.string() ?: "" }
            val json = JSONObject(body)
            val result = json.getJSONObject("quoteResponse").getJSONArray("result")
            if (result.length() == 0) return null
            val q = result.getJSONObject(0)
            StockEntity(
                ticker = q.optString("symbol", ticker).uppercase(),
                name = q.optString("longName").ifEmpty { q.optString("shortName", ticker.uppercase()) },
                sector = q.optString("sector").ifEmpty { null },
                industry = q.optString("industry").ifEmpty { null },
                marketCap = if (q.has("marketCap")) q.getDouble("marketCap") else null
            )
        } catch (_: Exception) { null }
    }

    private fun parseChartJson(body: String, ticker: String): List<PriceBarEntity> {
        return try {
            val chart = JSONObject(body).getJSONObject("chart")
            val result = chart.getJSONArray("result").getJSONObject(0)
            val timestamps = result.getJSONArray("timestamp")
            val indicators = result.getJSONObject("indicators")
            val quote = indicators.getJSONArray("quote").getJSONObject(0)
            val adjcloseArr = indicators.optJSONArray("adjclose")
            val adjcloseData = adjcloseArr?.optJSONObject(0)?.optJSONArray("adjclose")

            val opens   = quote.getJSONArray("open")
            val highs   = quote.getJSONArray("high")
            val lows    = quote.getJSONArray("low")
            val closes  = quote.getJSONArray("close")
            val volumes = quote.getJSONArray("volume")

            (0 until timestamps.length()).mapNotNull { i ->
                if (opens.isNull(i) || closes.isNull(i)) return@mapNotNull null
                val close = closes.getDouble(i)
                val adjClose = adjcloseData?.let {
                    if (i < it.length() && !it.isNull(i)) it.getDouble(i) else close
                } ?: close
                PriceBarEntity(
                    ticker = ticker.uppercase(),
                    date = Date(timestamps.getLong(i) * 1000L),
                    open = opens.getDouble(i),
                    high = highs.getDouble(i),
                    low = lows.getDouble(i),
                    close = close,
                    adjClose = adjClose,
                    volume = if (volumes.isNull(i)) 0L else volumes.getLong(i)
                )
            }
        } catch (_: Exception) { emptyList() }
    }
}

// MARK: - Stooq fetcher (CSV, no key)

class StooqFetcher @Inject constructor(private val client: OkHttpClient) {

    fun fetchPriceBars(ticker: String): List<PriceBarEntity> {
        val url = "https://stooq.com/q/d/l/?s=${ticker.lowercase()}.us&i=d"
        val req = Request.Builder().url(url).header("User-Agent", "Mozilla/5.0").build()
        val csv = client.newCall(req).execute().use { it.body?.string() ?: "" }
        val df = SimpleDateFormat("yyyy-MM-dd", Locale.US)
        return csv.lines().drop(1).mapNotNull { line ->
            val cols = line.trim().split(",")
            if (cols.size < 5) return@mapNotNull null
            try {
                PriceBarEntity(
                    ticker = ticker.uppercase(),
                    date = df.parse(cols[0]) ?: return@mapNotNull null,
                    open = cols[1].toDouble(),
                    high = cols[2].toDouble(),
                    low = cols[3].toDouble(),
                    close = cols[4].toDouble(),
                    adjClose = cols[4].toDouble(),
                    volume = if (cols.size > 5) cols[5].toLongOrNull() ?: 0L else 0L
                )
            } catch (_: Exception) { null }
        }
    }
}
