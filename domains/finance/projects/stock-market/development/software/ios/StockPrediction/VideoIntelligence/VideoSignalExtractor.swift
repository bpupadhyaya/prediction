import Foundation

// MARK: - VideoSignalExtractor

final class VideoSignalExtractor {
    static let shared = VideoSignalExtractor()
    private init() {}

    // MARK: - Public API

    /// Use the on-device LLM to extract market signals from a transcript.
    /// Returns an array of `VideoSignalRecord` (without join-helper fields).
    func extractSignals(
        transcript: String,
        title: String,
        channel: String,
        videoId: String
    ) async throws -> [VideoSignalRecord] {
        guard LLMInferenceManager.shared.isReady else {
            throw LLMError.noModelLoaded
        }

        let truncated = String(transcript.prefix(8000))

        let systemPrompt = """
You are a financial intelligence AI. Extract market signals from the video transcript below.
Return ONLY a JSON array — no markdown, no explanation. Each element must follow this exact schema:
{
  "ticker": "<stock symbol or null if unknown>",
  "parameterName": "<specific factor, e.g. Revenue Growth, Fed Rate, Chip Demand>",
  "domain": "<one of: earnings, macro, technical, sentiment, regulatory, supply_chain, geopolitical, other>",
  "direction": "<up or down>",
  "weight": <integer 1-100>,
  "confidence": <float 0.0-1.0>,
  "keyQuote": "<verbatim short quote from transcript supporting this signal, max 200 chars>"
}
Rules:
- weight reflects importance (100 = critical market mover)
- confidence reflects your certainty that this is a real signal
- direction is "up" if bullish for the ticker/market, "down" if bearish
- Extract up to 10 signals; skip filler commentary
- If no clear signals exist, return []
"""

        let userMessage = """
Video: \(title)
Channel: \(channel)

Transcript:
\(truncated)
"""

        var fullResponse = ""
        _ = try await LLMInferenceManager.shared.chat(
            systemPrompt: systemPrompt,
            userMessage: userMessage,
            onToken: { token in fullResponse += token }
        )

        return parseSignals(from: fullResponse, videoId: videoId)
    }

    // MARK: - Private Parsing

    private func parseSignals(from rawResponse: String, videoId: String) -> [VideoSignalRecord] {
        // Strip any markdown code fences
        let cleaned = rawResponse
            .replacingOccurrences(of: "```json", with: "")
            .replacingOccurrences(of: "```", with: "")
            .trimmingCharacters(in: .whitespacesAndNewlines)

        // Find the JSON array boundaries
        guard let startIdx = cleaned.firstIndex(of: "["),
              let endIdx = cleaned.lastIndex(of: "]") else {
            return []
        }

        let jsonStr = String(cleaned[startIdx...endIdx])
        guard let data = jsonStr.data(using: .utf8),
              let array = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]] else {
            return []
        }

        let now = Date()
        return array.compactMap { dict -> VideoSignalRecord? in
            guard
                let parameterName = dict["parameterName"] as? String,
                let domain = dict["domain"] as? String,
                let direction = dict["direction"] as? String,
                let weight = dict["weight"] as? Int,
                let confidence = dict["confidence"] as? Double
            else { return nil }

            let ticker = dict["ticker"] as? String
            let keyQuote = dict["keyQuote"] as? String ?? ""

            // Validate direction
            let dir = direction.lowercased()
            guard dir == "up" || dir == "down" else { return nil }

            return VideoSignalRecord(
                id: UUID().uuidString,
                videoId: videoId,
                ticker: (ticker?.isEmpty == true || ticker == "null") ? nil : ticker,
                parameterName: parameterName,
                domain: domain,
                direction: dir,
                weight: max(1, min(100, weight)),
                confidence: max(0.0, min(1.0, confidence)),
                keyQuote: keyQuote,
                extractedAt: now,
                videoTitle: nil,
                channelName: nil,
                publishedAt: nil
            )
        }
    }
}
