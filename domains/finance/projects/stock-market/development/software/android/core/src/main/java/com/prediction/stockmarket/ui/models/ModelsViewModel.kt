package com.prediction.stockmarket.ui.models

import android.app.ActivityManager
import android.app.Application
import android.content.Context
import android.os.Build
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.prediction.stockmarket.prediction.LLMInferenceEngine
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import javax.inject.Inject

data class ModelUiState(
    val totalRamGB: Double = 0.0,
    val cpuCount: Int = Runtime.getRuntime().availableProcessors(),
    val isArmDevice: Boolean = Build.SUPPORTED_ABIS.any { it.contains("arm") },
    val modelsDir: String = "",
    val activeModelId: String? = null,
    val downloadProgress: Map<String, Float> = emptyMap(),
    val downloadStatus: Map<String, String> = emptyMap()  // "downloading" | "done" | "error"
)

@HiltViewModel
class ModelsViewModel @Inject constructor(
    application: Application,
    private val httpClient: OkHttpClient,
    private val llmEngine: LLMInferenceEngine
) : AndroidViewModel(application) {

    private val modelsDir = File(application.filesDir, "llm_models").also { it.mkdirs() }
    private val configFile = File(application.filesDir, "llm_config.json")

    private val _state = MutableStateFlow(ModelUiState())
    val state: StateFlow<ModelUiState> = _state

    init {
        val am = application.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val mi = ActivityManager.MemoryInfo()
        am.getMemoryInfo(mi)
        val ramGB = mi.totalMem.toDouble() / (1024 * 1024 * 1024)
        _state.value = _state.value.copy(
            totalRamGB = ramGB,
            modelsDir = modelsDir.absolutePath,
            activeModelId = loadConfig()
        )
    }

    fun modelFile(model: LLMModel) = File(modelsDir, model.hfFile)
    fun isDownloaded(model: LLMModel) = modelFile(model).exists()
    fun diskSizeGB(model: LLMModel) = if (isDownloaded(model)) modelFile(model).length().toDouble() / (1024 * 1024 * 1024) else null

    fun download(model: LLMModel) {
        if (_state.value.downloadStatus[model.id] == "downloading") return
        setDownloadState(model.id, "downloading", 0f)
        viewModelScope.launch(Dispatchers.IO) {
            try {
                val tmp = File(modelsDir, "${model.hfFile}.tmp")
                val req = Request.Builder().url(model.downloadUrl).build()
                httpClient.newCall(req).execute().use { resp ->
                    val body = resp.body ?: throw Exception("No response body")
                    val total = body.contentLength()
                    var downloaded = 0L
                    FileOutputStream(tmp).use { out ->
                        val buf = ByteArray(1024 * 1024)
                        body.byteStream().use { inp ->
                            var n: Int
                            while (inp.read(buf).also { n = it } != -1) {
                                out.write(buf, 0, n)
                                downloaded += n
                                if (total > 0) {
                                    val prog = downloaded.toFloat() / total
                                    withContext(Dispatchers.Main) { setDownloadState(model.id, "downloading", prog) }
                                }
                            }
                        }
                    }
                }
                tmp.renameTo(modelFile(model))
                withContext(Dispatchers.Main) { setDownloadState(model.id, "done", 1f) }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) { setDownloadState(model.id, "error", 0f) }
            }
        }
    }

    fun deleteModel(model: LLMModel) {
        modelFile(model).delete()
        val newStatus = _state.value.downloadStatus.toMutableMap().also { it.remove(model.id) }
        var newActive = _state.value.activeModelId
        if (newActive == model.id) {
            newActive = null
            saveConfig(null)
            llmEngine.unload()
        }
        _state.value = _state.value.copy(downloadStatus = newStatus, activeModelId = newActive)
    }

    fun activate(model: LLMModel) {
        saveConfig(model.id)
        _state.value = _state.value.copy(activeModelId = model.id)
        val modelPath = modelFile(model).absolutePath
        viewModelScope.launch(Dispatchers.IO) {
            llmEngine.loadModel(modelPath)
        }
    }

    fun deactivate() {
        saveConfig(null)
        _state.value = _state.value.copy(activeModelId = null)
        llmEngine.unload()
    }

    private fun setDownloadState(id: String, status: String, progress: Float) {
        val newStatus = _state.value.downloadStatus.toMutableMap().also { it[id] = status }
        val newProgress = _state.value.downloadProgress.toMutableMap().also { it[id] = progress }
        _state.value = _state.value.copy(downloadStatus = newStatus, downloadProgress = newProgress)
    }

    private fun loadConfig(): String? = try {
        JSONObject(configFile.readText()).optString("active_model_id").takeIf { it.isNotEmpty() }
    } catch (_: Exception) { null }

    private fun saveConfig(activeId: String?) {
        val obj = JSONObject()
        if (activeId != null) obj.put("active_model_id", activeId) else obj.put("active_model_id", JSONObject.NULL)
        configFile.writeText(obj.toString())
    }
}
