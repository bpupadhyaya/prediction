import Foundation
import llama

// MARK: - Errors

enum LLMError: Error, LocalizedError {
    case noModelLoaded
    case modelLoadFailed(String)
    case inferenceError(String)

    var errorDescription: String? {
        switch self {
        case .noModelLoaded:
            return "No LLM model loaded. Download a model in the Models tab."
        case .modelLoadFailed(let msg):
            return "Failed to load model: \(msg)"
        case .inferenceError(let msg):
            return "Inference error: \(msg)"
        }
    }
}

// MARK: - LLMInferenceManager

@MainActor
final class LLMInferenceManager: ObservableObject {
    static let shared = LLMInferenceManager()

    @Published var isInferring = false
    @Published var lastError: String? = nil

    private var llamaModel: OpaquePointer? = nil
    private var llamaContext: OpaquePointer? = nil
    private var currentModelPath: String? = nil

    private init() {
        llama_backend_init()
    }

    deinit {
        // Release model resources on deallocation.
        // This is intentionally not @MainActor — deinit runs when the last
        // reference is released, which may happen off the main actor. The
        // pointer operations are safe regardless of the calling thread.
        if let ctx = llamaContext { llama_free(ctx) }
        if let model = llamaModel { llama_model_free(model) }
        llama_backend_free()
    }

    // MARK: - Readiness

    /// True when the active model file exists on disk and is currently loaded.
    var isReady: Bool {
        guard let modelId = LLMDownloadManager.shared.activeModelId,
              let model = llmCatalog.first(where: { $0.id == modelId }) else { return false }
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let path = docs.appendingPathComponent("LLMModels/\(model.hfFile)").path
        return FileManager.default.fileExists(atPath: path) && llamaModel != nil
    }

    /// The currently active model identifier, or nil if none selected.
    var activeModelId: String? { LLMDownloadManager.shared.activeModelId }

    // MARK: - Model Lifecycle

    /// Load a GGUF model from the given file-system path.
    /// Unloads any previously loaded model first.
    func loadModel(path: String) throws {
        unloadModel()

        var modelParams = llama_model_default_params()
        modelParams.n_gpu_layers = 0  // CPU-only; Metal GPU layers may be enabled in a future pass

        guard let model = llama_model_load_from_file(path, modelParams) else {
            throw LLMError.modelLoadFailed("llama_model_load_from_file returned nil for path: \(path)")
        }

        var ctxParams = llama_context_default_params()
        ctxParams.n_ctx = 2048
        ctxParams.n_batch = 512

        guard let ctx = llama_init_from_model(model, ctxParams) else {
            llama_model_free(model)
            throw LLMError.modelLoadFailed("llama_init_from_model returned nil")
        }

        self.llamaModel = model
        self.llamaContext = ctx
        self.currentModelPath = path
    }

    /// Release model and context from memory.
    func unloadModel() {
        if let ctx = llamaContext { llama_free(ctx) }
        if let model = llamaModel { llama_model_free(model) }
        llamaContext = nil
        llamaModel = nil
        currentModelPath = nil
    }

    // MARK: - Private Helpers

    /// Ensures the active model is loaded; reloads only when the path changes.
    private func ensureModelLoaded() throws {
        guard let modelId = LLMDownloadManager.shared.activeModelId,
              let catalogEntry = llmCatalog.first(where: { $0.id == modelId }) else {
            throw LLMError.noModelLoaded
        }

        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let path = docs.appendingPathComponent("LLMModels/\(catalogEntry.hfFile)").path

        guard FileManager.default.fileExists(atPath: path) else {
            throw LLMError.noModelLoaded
        }

        if currentModelPath != path {
            try loadModel(path: path)
        }
    }

    // MARK: - Inference

    /// Streams a response from the on-device LLM using llama.cpp.
    ///
    /// - Parameters:
    ///   - systemPrompt: Role/context description for the model.
    ///   - userMessage: The user's question or request.
    ///   - onToken: Called on the main actor with each decoded token fragment.
    /// - Returns: The full concatenated response string.
    ///
    /// Throws `LLMError.noModelLoaded` when no model is ready, or
    /// `LLMError.inferenceError` for llama.cpp failures.
    func chat(
        systemPrompt: String,
        userMessage: String,
        onToken: @escaping (String) -> Void
    ) async throws -> String {
        try ensureModelLoaded()

        guard let model = llamaModel, let ctx = llamaContext else {
            throw LLMError.noModelLoaded
        }

        isInferring = true
        lastError = nil
        defer { isInferring = false }

        // Build prompt in ChatML format (compatible with most GGUF instruction models).
        let prompt = "<|system|>\n\(systemPrompt)\n<|user|>\n\(userMessage)\n<|assistant|>\n"

        // Capture raw pointers for use inside the detached task (non-Sendable).
        let modelPtr = model
        let ctxPtr = ctx

        return try await Task.detached(priority: .userInitiated) {
            // Tokenize the full prompt.
            let promptBytes = Array(prompt.utf8)
            let promptLen = Int32(promptBytes.count)
            let maxTokens = promptLen + 4
            var tokens = [llama_token](repeating: 0, count: Int(maxTokens))

            let nTokens = llama_tokenize(
                modelPtr,
                prompt,
                promptLen,
                &tokens,
                maxTokens,
                /*add_special=*/ true,
                /*parse_special=*/ true
            )

            guard nTokens > 0 else {
                throw LLMError.inferenceError("Tokenization produced no tokens")
            }

            // Clear the KV cache and decode the prompt.
            llama_kv_cache_clear(ctxPtr)

            var promptTokens = Array(tokens[0..<Int(nTokens)])
            var batch = llama_batch_get_one(&promptTokens, nTokens, 0, 0)
            guard llama_decode(ctxPtr, batch) == 0 else {
                throw LLMError.inferenceError("llama_decode failed on prompt batch")
            }

            // Build the sampler chain: temperature → top-k → distribution sampler.
            var sparams = llama_sampler_chain_default_params()
            let sampler = llama_sampler_chain_init(sparams)
            llama_sampler_chain_add(sampler, llama_sampler_init_temp(0.8))
            llama_sampler_chain_add(sampler, llama_sampler_init_top_k(40))
            llama_sampler_chain_add(
                sampler,
                llama_sampler_init_dist(UInt32.random(in: 0..<UInt32.max))
            )
            defer { llama_sampler_free(sampler) }

            var fullResponse = ""
            var nPos = nTokens
            let maxNewTokens = 512

            for _ in 0..<maxNewTokens {
                let newToken = llama_sampler_sample(sampler, ctxPtr, -1)
                llama_sampler_accept(sampler, newToken)

                // Stop on end-of-generation token.
                if llama_token_is_eog(modelPtr, newToken) { break }

                // Decode the token id to a UTF-8 string fragment.
                var piece = [CChar](repeating: 0, count: 256)
                let nPiece = llama_token_to_piece(modelPtr, newToken, &piece, 256, 0, true)
                if nPiece > 0 {
                    let fragment = String(cString: piece)
                    if !fragment.isEmpty {
                        fullResponse += fragment
                        let tokenStr = fragment
                        // Deliver token to the caller on the main actor.
                        Task { @MainActor in onToken(tokenStr) }
                    }
                }

                // Feed the generated token back for the next decode step.
                var nextToken = newToken
                batch = llama_batch_get_one(&nextToken, 1, nPos, 0)
                nPos += 1
                if llama_decode(ctxPtr, batch) != 0 { break }
            }

            return fullResponse
        }.value
    }
}
