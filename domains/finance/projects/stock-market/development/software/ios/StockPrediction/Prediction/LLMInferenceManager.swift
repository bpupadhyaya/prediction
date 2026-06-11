import Foundation

// MARK: - Errors

enum LLMError: Error, LocalizedError {
    case noModelLoaded
    case modelLoadFailed(String)
    case inferenceError(String)
    case unavailable

    var errorDescription: String? {
        switch self {
        case .noModelLoaded:
            return "No LLM model loaded. Download a model in the Models tab."
        case .modelLoadFailed(let msg):
            return "Failed to load model: \(msg)"
        case .inferenceError(let msg):
            return "Inference error: \(msg)"
        case .unavailable:
            return "On-device LLM is not available in this build."
        }
    }
}

// MARK: - LLMInferenceManager
//
// NOTE: The on-device LLM (llama.cpp) integration is temporarily stubbed out.
// The `llama.cpp` Swift package no longer resolves via SwiftPM, which broke the
// whole iOS build. The LLM is an OPTIONAL layer — core predictions run on the
// bundled ONNX model, and all callers (VideoSignalExtractor, InteractiveParameterView)
// already guard on `isReady`, so they degrade gracefully when it is unavailable.
//
// To restore: re-add a working llama.cpp SwiftPM dependency (or an xcframework)
// and reinstate the inference implementation (see git history of this file).
@MainActor
final class LLMInferenceManager: ObservableObject {
    static let shared = LLMInferenceManager()

    @Published var isInferring = false
    @Published var lastError: String? = nil

    private var currentModelPath: String? = nil

    private init() {}

    // MARK: - Readiness

    /// Always false while the on-device LLM is stubbed out.
    var isReady: Bool { false }

    /// The currently active model identifier, or nil if none selected.
    var activeModelId: String? { LLMDownloadManager.shared.activeModelId }

    // MARK: - Model Lifecycle

    func loadModel(path: String) throws {
        throw LLMError.unavailable
    }

    func unloadModel() {
        currentModelPath = nil
    }

    // MARK: - Inference

    /// Stubbed — throws `LLMError.unavailable`. Callers guard on `isReady` first,
    /// so this path is not hit in normal use.
    func chat(
        systemPrompt: String,
        userMessage: String,
        onToken: @escaping (String) -> Void
    ) async throws -> String {
        throw LLMError.unavailable
    }
}
