import Foundation
import Combine

struct LLMModel: Identifiable {
    let id: String
    let name: String
    let paramsB: Double
    let sizeGB: Double
    let ramMinGB: Double
    let quantization: String
    let description: String
    let tags: [String]
    let hfRepo: String
    let hfFile: String

    var downloadURL: URL {
        URL(string: "https://huggingface.co/\(hfRepo)/resolve/main/\(hfFile)")!
    }

    func compatibility(totalRAMGB: Double) -> ModelCompatibility {
        if totalRAMGB >= ramMinGB * 1.25 { return .compatible }
        if totalRAMGB >= ramMinGB * 0.75 { return .marginal }
        return .insufficient
    }
}

enum ModelCompatibility: String {
    case compatible = "✓ Compatible"
    case marginal = "⚠ Marginal"
    case insufficient = "✗ Needs more RAM"
}

let llmCatalog: [LLMModel] = [
    LLMModel(id: "llama3.2-1b-q4", name: "Llama 3.2 1B", paramsB: 1, sizeGB: 0.8, ramMinGB: 4, quantization: "Q4_K_M",
             description: "Smallest — fast on any device, basic reasoning",
             tags: ["Fast", "Low RAM"],
             hfRepo: "bartowski/Llama-3.2-1B-Instruct-GGUF",
             hfFile: "Llama-3.2-1B-Instruct-Q4_K_M.gguf"),
    LLMModel(id: "llama3.2-3b-q4", name: "Llama 3.2 3B", paramsB: 3, sizeGB: 2.0, ramMinGB: 8, quantization: "Q4_K_M",
             description: "Good balance of speed and quality",
             tags: ["Recommended"],
             hfRepo: "bartowski/Llama-3.2-3B-Instruct-GGUF",
             hfFile: "Llama-3.2-3B-Instruct-Q4_K_M.gguf"),
    LLMModel(id: "phi3.5-mini-q4", name: "Phi-3.5 Mini", paramsB: 3.8, sizeGB: 2.4, ramMinGB: 8, quantization: "Q4_K_M",
             description: "Microsoft small model, strong reasoning for its size",
             tags: ["Efficient"],
             hfRepo: "bartowski/Phi-3.5-mini-instruct-GGUF",
             hfFile: "Phi-3.5-mini-instruct-Q4_K_M.gguf"),
    LLMModel(id: "mistral-7b-q4", name: "Mistral 7B", paramsB: 7, sizeGB: 4.4, ramMinGB: 16, quantization: "Q4_K_M",
             description: "Strong instruction-following, good financial reasoning",
             tags: ["Popular"],
             hfRepo: "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
             hfFile: "mistral-7b-instruct-v0.2.Q4_K_M.gguf"),
    LLMModel(id: "llama3.1-8b-q4", name: "Llama 3.1 8B", paramsB: 8, sizeGB: 4.9, ramMinGB: 16, quantization: "Q4_K_M",
             description: "Meta flagship small model, excellent quality",
             tags: ["Popular"],
             hfRepo: "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
             hfFile: "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"),
    LLMModel(id: "gemma2-9b-q4", name: "Gemma 2 9B", paramsB: 9, sizeGB: 5.8, ramMinGB: 16, quantization: "Q4_K_M",
             description: "Google model, strong analytical reasoning",
             tags: ["Google"],
             hfRepo: "bartowski/gemma-2-9b-it-GGUF",
             hfFile: "gemma-2-9b-it-Q4_K_M.gguf"),
    LLMModel(id: "llama3.1-70b-q4", name: "Llama 3.1 70B", paramsB: 70, sizeGB: 42.5, ramMinGB: 64, quantization: "Q4_K_M",
             description: "Most capable — requires a powerful machine with 64 GB+ RAM",
             tags: ["Most Capable"],
             hfRepo: "bartowski/Meta-Llama-3.1-70B-Instruct-GGUF",
             hfFile: "Meta-Llama-3.1-70B-Instruct-Q4_K_M.gguf"),
]

// MARK: - LLMDownloadManager

@MainActor
final class LLMDownloadManager: ObservableObject {
    static let shared = LLMDownloadManager()

    @Published var downloadProgress: [String: Double] = [:]   // model id → 0..1
    @Published var downloadStatus: [String: String] = [:]     // model id → "downloading" | "done" | "error"
    @Published var activeModelId: String? = nil

    private let modelsDir: URL
    private let configURL: URL

    private init() {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        modelsDir = docs.appendingPathComponent("LLMModels")
        configURL = docs.appendingPathComponent("llm_config.json")
        try? FileManager.default.createDirectory(at: modelsDir, withIntermediateDirectories: true)
        loadConfig()
    }

    var totalRAMGB: Double {
        Double(ProcessInfo.processInfo.physicalMemory) / (1024 * 1024 * 1024)
    }

    func modelPath(for model: LLMModel) -> URL {
        modelsDir.appendingPathComponent(model.hfFile)
    }

    func isDownloaded(_ model: LLMModel) -> Bool {
        FileManager.default.fileExists(atPath: modelPath(for: model).path)
    }

    func diskSizeGB(_ model: LLMModel) -> Double? {
        guard let attrs = try? FileManager.default.attributesOfItem(atPath: modelPath(for: model).path),
              let size = attrs[.size] as? Int64 else { return nil }
        return Double(size) / (1024 * 1024 * 1024)
    }

    func download(_ model: LLMModel) {
        guard downloadStatus[model.id] != "downloading" else { return }
        downloadStatus[model.id] = "downloading"
        downloadProgress[model.id] = 0.0
        Task {
            do {
                try await streamDownload(model: model)
                downloadStatus[model.id] = "done"
            } catch {
                downloadStatus[model.id] = "error"
            }
        }
    }

    func deleteModel(_ model: LLMModel) {
        try? FileManager.default.removeItem(at: modelPath(for: model))
        downloadStatus.removeValue(forKey: model.id)
        downloadProgress.removeValue(forKey: model.id)
        if activeModelId == model.id {
            activeModelId = nil
            saveConfig()
        }
    }

    func activate(_ model: LLMModel) {
        activeModelId = model.id
        saveConfig()
    }

    func deactivate() {
        activeModelId = nil
        saveConfig()
    }

    private func streamDownload(model: LLMModel) async throws {
        let dest = modelPath(for: model)
        let tmp = dest.appendingPathExtension("tmp")
        var req = URLRequest(url: model.downloadURL)
        req.timeoutInterval = 3600
        let (asyncBytes, response) = try await URLSession.shared.bytes(for: req)
        let total = (response as? HTTPURLResponse).flatMap { Int($0.expectedContentLength) } ?? 0
        var written = 0
        FileManager.default.createFile(atPath: tmp.path, contents: nil)
        let handle = try FileHandle(forWritingTo: tmp)
        var buf = Data(capacity: 1024 * 1024)
        for try await byte in asyncBytes {
            buf.append(byte)
            if buf.count >= 1024 * 1024 {
                handle.write(buf)
                written += buf.count
                if total > 0 { downloadProgress[model.id] = Double(written) / Double(total) }
                buf.removeAll(keepingCapacity: true)
            }
        }
        if !buf.isEmpty { handle.write(buf); written += buf.count }
        try handle.close()
        try FileManager.default.moveItem(at: tmp, to: dest)
        downloadProgress[model.id] = 1.0
    }

    private func loadConfig() {
        guard let data = try? Data(contentsOf: configURL),
              let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return }
        activeModelId = dict["active_model_id"] as? String
    }

    private func saveConfig() {
        let dict: [String: Any?] = ["active_model_id": activeModelId]
        if let data = try? JSONSerialization.data(withJSONObject: dict.compactMapValues { $0 }) {
            try? data.write(to: configURL)
        }
    }
}
