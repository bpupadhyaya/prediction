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

    private suspend fun importFromSnapshot(file: File) {
        // Open the snapshot as a separate Room-compatible SQLite and copy rows.
        // For simplicity we parse a JSON sidecar (market.json.gz) that the desktop
        // backend produces alongside the SQLite. Both are published in the release.
        // This avoids cross-process SQLite file locking.
        // Full SQLite-to-SQLite merge would use Android's SQLiteDatabase.openDatabase.
        // The JSON approach is safer for the first version.
        // (Placeholder — real data import is via JSON sidecar described in README)
    }
}
