package com.prediction.stockmarket.ui.stock

// Contextual speaker suggestions
//
// Maps a ticker (and, where useful, sector keywords) to the most relevant of the
// pre-seeded YVIS speakers to follow for that stock. Used to render a subtle
// "Track for this stock: <name>" hint on the stock detail screen.
// Single source of truth — names match the seeded speakers in VideoIntelligenceManager.

object SpeakerSuggestions {

    private val byTicker: Map<String, List<String>> = mapOf(
        "TSLA" to listOf("Elon Musk", "Cathie Wood"),
        "MSTR" to listOf("Michael Saylor"),
        "BTC-USD" to listOf("Michael Saylor"),
        "ETH-USD" to listOf("Michael Saylor"),
        "COIN" to listOf("Michael Saylor", "Cathie Wood"),
        "NVDA" to listOf("Jensen Huang"),
        "AAPL" to listOf("Tim Cook"),
        "ROKU" to listOf("Cathie Wood"),
        "RBLX" to listOf("Cathie Wood"),
        "HOOD" to listOf("Cathie Wood"),
        "SQ" to listOf("Cathie Wood"),
        "PATH" to listOf("Cathie Wood"),
        "BRK-B" to listOf("Warren Buffett"),
        "BRK-A" to listOf("Warren Buffett"),
    )

    private val bySectorKeyword: List<Pair<String, List<String>>> = listOf(
        "ev" to listOf("Elon Musk"),
        "auto" to listOf("Elon Musk"),
        "crypto" to listOf("Michael Saylor"),
        "blockchain" to listOf("Michael Saylor"),
        "semiconductor" to listOf("Jensen Huang"),
        "semis" to listOf("Jensen Huang"),
        "artificial intelligence" to listOf("Jensen Huang"),
        "technology" to listOf("Jensen Huang"),
        "innovation" to listOf("Cathie Wood"),
        "disruptive" to listOf("Cathie Wood"),
        "financial" to listOf("Warren Buffett"),
        "bank" to listOf("Jerome Powell", "Warren Buffett"),
    )

    /**
     * Suggested speaker names for the given ticker / optional sector, most
     * relevant first. Empty when nothing relevant is found.
     */
    fun speakers(ticker: String, sector: String? = null): List<String> {
        val key = ticker.uppercase()
        byTicker[key]?.let { return it }

        // Crypto pairs not individually listed → Saylor.
        if (key.endsWith("-USD")) return listOf("Michael Saylor")

        if (!sector.isNullOrEmpty()) {
            val lower = sector.lowercase()
            for ((keyword, speakers) in bySectorKeyword) {
                if (lower.contains(keyword)) return speakers
            }
        }
        return emptyList()
    }
}
