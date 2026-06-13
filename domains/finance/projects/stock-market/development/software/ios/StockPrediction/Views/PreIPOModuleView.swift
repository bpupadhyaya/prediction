import SwiftUI

// MARK: - Pre-IPO module
//
// Tapping the "Pre-IPO" home module opens this detail screen. There is no live
// IPO feed, so this surfaces a small CURATED list of well-known late-stage
// private companies. Illustrative only — not offerings or advice.
// Mirrors the chrome/styling of MarketModuleView.

// MARK: - Curated data

struct PreIPOCandidate: Identifiable {
    let id = UUID()
    let name: String
    let sector: String
    let whyWatch: String
    let status: String
}

let preIPOCandidates: [PreIPOCandidate] = [
    PreIPOCandidate(name: "SpaceX",      sector: "Aerospace",     whyWatch: "Starlink revenue scaling fast; Starship cadence rising.",               status: "Late-stage private"),
    PreIPOCandidate(name: "OpenAI",      sector: "AI / LLM",      whyWatch: "Maker of ChatGPT — defining the generative-AI platform race.",          status: "Rumored 2025-26"),
    PreIPOCandidate(name: "Anthropic",   sector: "AI / LLM",      whyWatch: "Claude models; an AI-safety-focused frontier lab with rapid growth.",   status: "Late-stage private"),
    PreIPOCandidate(name: "Stripe",      sector: "Fintech",       whyWatch: "Global payments rails for the internet; perennial IPO candidate.",       status: "Late-stage private"),
    PreIPOCandidate(name: "Databricks",  sector: "Data / AI",     whyWatch: "Unified data + AI lakehouse; large enterprise revenue base.",            status: "Rumored 2025-26"),
    PreIPOCandidate(name: "Canva",       sector: "Design / SaaS", whyWatch: "Mass-market visual design tool with strong global adoption.",            status: "Late-stage private"),
    PreIPOCandidate(name: "Discord",     sector: "Social",        whyWatch: "Communities and gaming communication at massive daily scale.",          status: "Late-stage private"),
    PreIPOCandidate(name: "Epic Games",  sector: "Gaming",        whyWatch: "Fortnite + Unreal Engine; a key platform across games and 3D.",         status: "Late-stage private"),
    PreIPOCandidate(name: "Chime",       sector: "Neobank",       whyWatch: "Mobile-first US consumer banking with a large user base.",              status: "Rumored 2025-26"),
    PreIPOCandidate(name: "Plaid",       sector: "Fintech",       whyWatch: "Bank-data connectivity layer behind much of US fintech.",               status: "Late-stage private"),
]

// MARK: - View

struct PreIPOModuleView: View {
    let onBack: () -> Void

    private var module: StockModule? { stockModules.first { $0.id == "pre_ipo" } }

    var body: some View {
        ZStack(alignment: .top) {
            Color(red: 0.043, green: 0.118, blue: 0.212).ignoresSafeArea()

            VStack(spacing: 0) {
                header
                content
            }
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Button(action: onBack) {
                    HStack(spacing: 4) {
                        Image(systemName: "chevron.left")
                        Text("Home")
                    }
                    .font(.system(size: 15, weight: .medium))
                    .foregroundStyle(.white)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(.ultraThinMaterial)
                    .clipShape(Capsule())
                }
                Spacer()
            }
            .padding(.horizontal, 16)
            .padding(.top, 8)

            HStack(spacing: 12) {
                if let mod = module {
                    ZStack {
                        Circle().fill(mod.gradient).frame(width: 44, height: 44)
                        Image(systemName: mod.icon)
                            .font(.system(size: 20))
                            .foregroundStyle(mod.iconColor)
                    }
                    VStack(alignment: .leading, spacing: 2) {
                        Text(mod.title).font(.title3.bold()).foregroundStyle(.white)
                        Text("Notable late-stage private companies").font(.caption).foregroundStyle(.white.opacity(0.6))
                    }
                }
                Spacer()
            }
            .padding(.horizontal, 16)
        }
        .padding(.bottom, 8)
    }

    private var content: some View {
        ScrollView {
            LazyVStack(spacing: 8) {
                ForEach(preIPOCandidates) { company in
                    candidateCard(company)
                }
                Text("Illustrative watchlist of well-known private companies — not an offering, recommendation, or financial advice. Timing and status are speculative.")
                    .font(.caption2)
                    .foregroundStyle(.white.opacity(0.35))
                    .multilineTextAlignment(.center)
                    .padding(.vertical, 14)
                    .padding(.horizontal, 8)
            }
            .padding(.horizontal, 12)
        }
    }

    private func candidateCard(_ company: PreIPOCandidate) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 8) {
                Text(company.name)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(.white)
                Text(company.sector)
                    .font(.caption2)
                    .foregroundStyle(Color(red: 0.576, green: 0.765, blue: 0.941))
                Spacer()
                statusChip(company.status)
            }
            Text(company.whyWatch)
                .font(.caption)
                .foregroundStyle(.white.opacity(0.6))
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(red: 0.075, green: 0.141, blue: 0.247))
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }

    private func statusChip(_ status: String) -> some View {
        let isRumored = status.lowercased().contains("rumored")
        let bg = isRumored ? Color(red: 0.078, green: 0.325, blue: 0.176)
                           : Color(red: 0.118, green: 0.161, blue: 0.231)
        let fg = isRumored ? Color(red: 0.29, green: 0.87, blue: 0.50)
                           : Color.white.opacity(0.55)
        return Text(status)
            .font(.caption2.bold())
            .foregroundStyle(fg)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(bg)
            .clipShape(Capsule())
    }
}
