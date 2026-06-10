import Foundation

// TODO: Replace with real llama.cpp or MLX Swift inference when available
// This manager provides a structured heuristic response that mimics streaming,
// ready to be swapped for real on-device inference once llama.cpp / MLX Swift
// is integrated into the project.

@MainActor
final class LLMInferenceManager: ObservableObject {
    static let shared = LLMInferenceManager()

    @Published var isInferring = false
    @Published var lastError: String? = nil

    private init() {}

    // MARK: - Readiness

    /// True when a model file exists on disk and is marked active.
    var isReady: Bool {
        guard let modelId = LLMDownloadManager.shared.activeModelId else { return false }
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        // The download manager stores files by their hfFile name; look up the matching catalog entry.
        if let model = llmCatalog.first(where: { $0.id == modelId }) {
            let path = docs.appendingPathComponent("LLMModels/\(model.hfFile)")
            return FileManager.default.fileExists(atPath: path.path)
        }
        return false
    }

    /// The currently active model identifier, or nil if none selected.
    var activeModelId: String? {
        LLMDownloadManager.shared.activeModelId
    }

    // MARK: - Chat

    /// Streams a response from the on-device LLM (or heuristic stub if no model loaded).
    ///
    /// - Parameters:
    ///   - systemPrompt: Role/context description for the model.
    ///   - userMessage: The user's question or request.
    ///   - onToken: Called on the main actor with each token as it is "generated".
    /// - Returns: The full concatenated response.
    ///
    /// Throws `LLMError.noModelLoaded` when `isReady` is false.
    func chat(
        systemPrompt: String,
        userMessage: String,
        onToken: @escaping (String) -> Void
    ) async throws -> String {
        guard isReady else {
            lastError = "No LLM model loaded. Download a model in the Models tab."
            throw LLMError.noModelLoaded
        }

        isInferring = true
        lastError = nil
        defer { isInferring = false }

        // TODO: Replace the block below with a real llama.cpp server call or
        // MLX Swift session once the dependency is added to the project.
        // Example integration point:
        //   let session = LlamaSession(modelPath: resolvedModelPath())
        //   for try await token in session.generate(system: systemPrompt, user: userMessage) {
        //       onToken(token)
        //   }

        let response = buildHeuristicResponse(systemPrompt: systemPrompt, userMessage: userMessage)
        let words = response.split(separator: " ", omittingEmptySubsequences: false).map(String.init)

        for word in words {
            let chunk = word + " "
            onToken(chunk)
            // Simulate token generation latency (30–80 ms per token)
            try await Task.sleep(nanoseconds: UInt64.random(in: 30_000_000 ... 80_000_000))
        }

        return response
    }

    // MARK: - Heuristic Response Builder

    /// Produces a structured financial analysis based on keywords in the user message.
    /// This is intentionally deterministic so it works without a real model.
    private func buildHeuristicResponse(systemPrompt: String, userMessage: String) -> String {
        let lower = userMessage.lowercased()
        let modelName = llmCatalog.first(where: { $0.id == activeModelId })?.name ?? "on-device model"

        // Detect ticker mentions (1–5 uppercase letters appearing in the original message)
        let tickerPattern = try? NSRegularExpression(pattern: "\\b[A-Z]{1,5}\\b")
        let range = NSRange(userMessage.startIndex..., in: userMessage)
        let tickers = tickerPattern?
            .matches(in: userMessage, range: range)
            .compactMap { Range($0.range, in: userMessage).map { String(userMessage[$0]) } }
            .filter { $0 != "I" && $0 != "A" } ?? []

        let tickerStr = tickers.isEmpty ? "the asset" : tickers.joined(separator: ", ")

        if lower.contains("risk") || lower.contains("downside") {
            return """
            [Analysis by \(modelName) — heuristic mode]

            Risk Assessment for \(tickerStr):

            Key downside risks to consider:
            • Macro headwinds: Rising interest rates compress equity multiples, especially for growth names. Monitor Fed meeting outcomes closely.
            • Sector rotation: Institutional flows can shift quickly from momentum plays to defensive sectors during uncertainty.
            • Earnings quality: Watch for revenue beats paired with margin compression — a common red flag masked by top-line growth.
            • Liquidity risk: Thinly traded names can gap significantly on volume spikes. Check 20-day average volume vs. current.

            Risk management suggestion: Size positions using 1.5× ATR stop-loss levels. Keep single-name exposure below 5% of total portfolio in elevated VIX environments.

            Disclaimer: This is a heuristic analysis, not financial advice. Replace this with real LLM inference for production use.
            """
        } else if lower.contains("bull") || lower.contains("long") || lower.contains("buy") {
            return """
            [Analysis by \(modelName) — heuristic mode]

            Bull Case for \(tickerStr):

            Supporting factors for an upside scenario:
            • Earnings momentum: Sequential EPS growth above 10% for 2+ quarters typically attracts institutional accumulation.
            • Technical structure: A base forming near the 50-week SMA with contracting volume suggests distribution has subsided.
            • Sentiment clearing: Low short interest reduction and options put/call ratio normalization can precede a re-rating.
            • Catalyst pipeline: Upcoming product launches, regulatory approvals, or buyback announcements often serve as price catalysts.

            Bull target framework: Estimate fair value using a blended P/E + EV/EBITDA multiple on next-twelve-months consensus. Add a 15–20% premium for quality compounders.

            Disclaimer: This is a heuristic analysis, not financial advice. Replace this with real LLM inference for production use.
            """
        } else if lower.contains("bear") || lower.contains("short") || lower.contains("sell") {
            return """
            [Analysis by \(modelName) — heuristic mode]

            Bear Case for \(tickerStr):

            Factors that may weigh on price:
            • Valuation stretch: When forward P/E exceeds the 5-year average by more than 30%, mean-reversion risk rises materially.
            • Insider selling: Clustered insider disposals within 6 months of a price peak have historically preceded corrections of 20%+.
            • Deteriorating fundamentals: Declining gross margins, rising days-sales-outstanding, and decelerating ARR are early warning signs.
            • Competitive disruption: New entrants with structurally lower cost bases can compress legacy pricing power over 12–24 months.

            Short thesis note: Ensure borrow availability and cost are acceptable. Hard-to-borrow names can incur fees that erode alpha.

            Disclaimer: This is a heuristic analysis, not financial advice. Replace this with real LLM inference for production use.
            """
        } else if lower.contains("predict") || lower.contains("forecast") || lower.contains("outlook") {
            return """
            [Analysis by \(modelName) — heuristic mode]

            Outlook for \(tickerStr):

            Near-term (1–4 weeks):
            The primary driver will be macro data releases (CPI, NFP, Fed commentary). Expect elevated intraday volatility. Position sizing should reflect this.

            Medium-term (1–3 months):
            Earnings season and guidance revisions will dominate. Stocks that beat on both revenue and EPS while raising guidance tend to outperform their sector by 8–12% in the subsequent quarter.

            Long-term (6–12 months):
            Secular growth themes (AI infrastructure, energy transition, healthcare innovation) continue to attract capital despite rate headwinds. Identify whether \(tickerStr) has durable competitive advantages within these themes.

            Key watch items: Fed pivot signals, credit spread widening, USD strength vs. EM basket.

            Disclaimer: This is a heuristic analysis, not financial advice. Replace this with real LLM inference for production use.
            """
        } else {
            // Generic financial research response
            return """
            [Analysis by \(modelName) — heuristic mode]

            Research Summary for \(tickerStr):

            To answer your question about "\(userMessage.prefix(80))...":

            Fundamental view:
            Evaluate the business using the following lens: revenue growth trajectory, operating leverage, balance sheet strength (net debt/EBITDA < 2×), and free cash flow yield vs. 10-year Treasury.

            Technical context:
            Price relative to 200-day SMA, volume trend, and RSI(14) provide a quick read on momentum. Divergence between price and RSI often precedes inflection points.

            Signal aggregation approach (aligned with your interactive parameter model):
            Weight macro signals at 30%, fundamental signals at 35%, technical at 25%, and sentiment at 10%. Adjust weights based on the current market regime (risk-on vs. risk-off).

            Suggested next steps:
            1. Review the latest 10-Q / earnings call transcript for management tone.
            2. Compare consensus EPS estimates vs. the implied growth baked into the current multiple.
            3. Set a price alert at the nearest technical support/resistance level.

            Disclaimer: This is a heuristic analysis, not financial advice. Replace this with real LLM inference for production use.
            """
        }
    }

    // MARK: - Private Helpers

    private func resolvedModelPath() -> String? {
        guard let modelId = activeModelId,
              let model = llmCatalog.first(where: { $0.id == modelId }) else { return nil }
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        return docs.appendingPathComponent("LLMModels/\(model.hfFile)").path
    }
}

// MARK: - Errors

enum LLMError: LocalizedError {
    case noModelLoaded
    case inferenceFailure(String)

    var errorDescription: String? {
        switch self {
        case .noModelLoaded:
            return "No LLM model loaded. Download a model in the Models tab."
        case .inferenceFailure(let msg):
            return "Inference failed: \(msg)"
        }
    }
}
