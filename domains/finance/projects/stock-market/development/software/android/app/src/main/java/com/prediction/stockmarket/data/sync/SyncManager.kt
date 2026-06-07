package com.prediction.stockmarket.data.sync

import android.content.Context
import com.google.gson.Gson
import com.google.gson.annotations.SerializedName
import com.prediction.stockmarket.data.database.*
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.util.zip.GZIPInputStream
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SyncManager @Inject constructor(
    @ApplicationContext private val context: Context,
    private val stockDao: StockDao,
    private val priceDao: PriceDao,
    private val predictionDao: PredictionDao,
    private val client: OkHttpClient,
    private val gson: Gson
) {
    private val releaseUrl = "https://api.github.com/repos/bpupadhyaya/prediction/releases/latest"

    data class ReleaseAsset(
        @SerializedName("name") val name: String,
        @SerializedName("browser_download_url") val downloadUrl: String
    )

    data class Release(
        @SerializedName("tag_name") val tagName: String,
        @SerializedName("assets") val assets: List<ReleaseAsset>
    )

    sealed class SyncResult {
        data class Success(val tagName: String) : SyncResult()
        data class Error(val message: String) : SyncResult()
    }

    suspend fun sync(): SyncResult = withContext(Dispatchers.IO) {
        try {
            val release = fetchRelease()
            val asset = release.assets.firstOrNull { it.name.endsWith(".sqlite.gz") }
                ?: return@withContext SyncResult.Error("No snapshot asset found")

            val compressed = download(asset.downloadUrl)
            val tmpFile = File(context.cacheDir, "snapshot.sqlite")
            decompressToFile(compressed, tmpFile)

            importFromSnapshot(tmpFile)
            tmpFile.delete()

            SyncResult.Success(release.tagName)
        } catch (e: Exception) {
            SyncResult.Error(e.message ?: "Unknown error")
        }
    }

    private fun fetchRelease(): Release {
        val req = Request.Builder()
            .url(releaseUrl)
            .header("Accept", "application/vnd.github+json")
            .build()
        val body = client.newCall(req).execute().use { it.body!!.string() }
        return gson.fromJson(body, Release::class.java)
    }

    private fun download(url: String): ByteArray {
        val req = Request.Builder().url(url).build()
        return client.newCall(req).execute().use { it.body!!.bytes() }
    }

    private fun decompressToFile(data: ByteArray, dest: File) {
        GZIPInputStream(data.inputStream()).use { gz ->
            dest.outputStream().use { out -> gz.copyTo(out) }
        }
    }

    private suspend fun importFromSnapshot(file: File) = withContext(Dispatchers.IO) {
        val snapDb = android.database.sqlite.SQLiteDatabase.openDatabase(
            file.absolutePath, null, android.database.sqlite.SQLiteDatabase.OPEN_READONLY
        )

        // Import stocks
        val stocks = mutableListOf<StockEntity>()
        snapDb.rawQuery("SELECT ticker, name, sector, industry, market_cap FROM stocks", null).use { c ->
            while (c.moveToNext()) {
                stocks.add(
                    StockEntity(
                        ticker = c.getString(0),
                        name = c.getString(1),
                        sector = c.getString(2),
                        industry = c.getString(3),
                        marketCap = if (c.isNull(4)) null else c.getDouble(4)
                    )
                )
            }
        }
        if (stocks.isNotEmpty()) stockDao.upsertAll(stocks)

        // Import prices
        val prices = mutableListOf<PriceBarEntity>()
        snapDb.rawQuery(
            "SELECT ticker, date, open, high, low, close, adj_close, volume FROM prices", null
        ).use { c ->
            while (c.moveToNext()) {
                prices.add(
                    PriceBarEntity(
                        ticker = c.getString(0),
                        date = java.util.Date(
                            c.getString(1).let {
                                try {
                                    java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.US)
                                        .parse(it)?.time ?: 0L
                                } catch (_: Exception) { 0L }
                            }
                        ),
                        open = c.getDouble(2),
                        high = c.getDouble(3),
                        low = c.getDouble(4),
                        close = c.getDouble(5),
                        adjClose = c.getDouble(6),
                        volume = c.getLong(7)
                    )
                )
                if (prices.size >= 500) {
                    priceDao.upsertAll(prices)
                    prices.clear()
                }
            }
        }
        if (prices.isNotEmpty()) priceDao.upsertAll(prices)

        // Import predictions
        val preds = mutableListOf<PredictionEntity>()
        snapDb.rawQuery(
            "SELECT ticker, horizon, direction, probability, expected_return_low, expected_return_high, volatility, model_accuracy FROM predictions",
            null
        ).use { c ->
            while (c.moveToNext()) {
                preds.add(
                    PredictionEntity(
                        ticker = c.getString(0),
                        horizon = c.getString(1),
                        direction = c.getString(2).uppercase(),
                        probability = c.getDouble(3),
                        expectedReturnLow = c.getDouble(4),
                        expectedReturnHigh = c.getDouble(5),
                        volatility = c.getDouble(6),
                        modelAccuracy = c.getDouble(7),
                        generatedAt = java.util.Date()
                    )
                )
            }
        }
        if (preds.isNotEmpty()) predictionDao.upsertAll(preds)

        snapDb.close()
    }
}
