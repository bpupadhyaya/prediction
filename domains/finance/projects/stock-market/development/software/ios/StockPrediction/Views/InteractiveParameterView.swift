import SwiftUI

// MARK: - Hex Color Helper (local extension — avoids polluting global namespace)

private extension Color {
    init(hex: String) {
        var h = hex.trimmingCharacters(in: .alphanumerics.inverted)
        if h.count == 6 { h = "FF" + h }
        var n: UInt64 = 0
        Scanner(string: h).scanHexInt64(&n)
        self.init(
            .sRGB,
            red:     Double((n >> 16) & 0xff) / 255,
            green:   Double((n >>  8) & 0xff) / 255,
            blue:    Double( n        & 0xff) / 255,
            opacity: Double((n >> 24) & 0xff) / 255
        )
    }
}

// MARK: - Colour Constants

private enum IPVColor {
    static let bg          = Color(red: 0.043, green: 0.082, blue: 0.149)   // #0B1526
    static let card        = Color(red: 0.055, green: 0.118, blue: 0.220)   // #0E1E38
    static let header      = Color(red: 0.055, green: 0.118, blue: 0.220)   // #0E1E38
    static let accent      = Color(red: 0.310, green: 0.557, blue: 0.969)   // #4f8ef7
    static let green       = Color(red: 0.204, green: 0.827, blue: 0.600)   // #34d399
    static let red         = Color(red: 0.973, green: 0.443, blue: 0.443)   // #f87171
    static let border      = Color.white.opacity(0.10)
    static let textPri     = Color.white
    static let textSec     = Color.white.opacity(0.60)
    static let textMuted   = Color.white.opacity(0.35)
}

// MARK: - Main View

struct InteractiveParameterView: View {
    let ticker: String

    @StateObject private var store = ParameterStore()
    @State private var expandedParams = Set<String>()
    @State private var saveMessage = ""

    // LLM chat
    @State private var llmQuestion = ""
    @State private var llmResponse = ""
    @State private var isStreaming = false
    @State private var llmError: String?

    var body: some View {
        ZStack {
            IPVColor.bg.ignoresSafeArea()

            NavigationStack {
                VStack(spacing: 0) {
                    // Score header (sticky)
                    scoreHeader

                    // Parameter groups (scrollable)
                    ScrollView {
                        LazyVStack(spacing: 12, pinnedViews: []) {
                            ForEach(store.groupedByDomain(), id: \.domain) { group in
                                DomainGroupView(
                                    group: group,
                                    states: store.states,
                                    expandedParams: $expandedParams,
                                    onDirectionChange: { name, dir in store.setDirection(name, dir) },
                                    onWeightChange: { name, weight in store.setWeight(name, weight) }
                                )
                            }

                            // LLM Research section at bottom
                            llmResearchSection
                                .padding(.horizontal, 16)
                                .padding(.bottom, 32)
                        }
                        .padding(.horizontal, 16)
                    }
                }
                .background(IPVColor.bg)
                .navigationTitle("\(ticker) — Interactive Predict")
                .navigationBarTitleDisplayMode(.inline)
                .toolbarBackground(IPVColor.header, for: .navigationBar)
                .toolbarColorScheme(.dark, for: .navigationBar)
                .toolbar {
                    ToolbarItem(placement: .navigationBarLeading) {
                        Button("Reset") {
                            withAnimation(.easeInOut(duration: 0.2)) {
                                store.initStates()
                                store.saveForTicker(ticker)
                                expandedParams = []
                                saveMessage = "Reset"
                            }
                            DispatchQueue.main.asyncAfter(deadline: .now() + 2.5) {
                                withAnimation { saveMessage = "" }
                            }
                        }
                        .foregroundStyle(IPVColor.textSec)
                    }
                    ToolbarItem(placement: .navigationBarTrailing) {
                        Button("Save") { saveSnapshot() }
                            .foregroundStyle(IPVColor.accent)
                    }
                }
                .onAppear {
                    store.loadForTicker(ticker)
                }
                .overlay(alignment: .bottom) {
                    if !saveMessage.isEmpty {
                        Text(saveMessage)
                            .font(.caption.bold())
                            .foregroundStyle(.white)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 8)
                            .background(IPVColor.accent)
                            .clipShape(Capsule())
                            .padding(.bottom, 16)
                            .transition(.move(edge: .bottom).combined(with: .opacity))
                    }
                }
            }
        }
    }

    // MARK: - Score Header

    private var scoreHeader: some View {
        let r = store.computePrediction()
        let dirColor: Color = r.direction == "up" ? IPVColor.green : r.direction == "down" ? IPVColor.red : .gray
        let dirLabel: String = r.direction == "up" ? "▲ UP" : r.direction == "down" ? "▼ DOWN" : "— NEUTRAL"

        return HStack(spacing: 16) {
            Text(ticker)
                .font(.headline)
                .fontWeight(.bold)
                .foregroundStyle(IPVColor.textPri)

            Text(dirLabel)
                .font(.title3)
                .fontWeight(.heavy)
                .foregroundStyle(dirColor)
                .animation(.easeInOut(duration: 0.2), value: r.direction)

            VStack(alignment: .leading, spacing: 2) {
                Text("Prob(UP): \(String(format: "%.1f", r.probUp * 100))%")
                    .font(.caption)
                    .foregroundStyle(IPVColor.textSec)
                Text("Confidence: \(String(format: "%.1f", r.confidence * 100))%")
                    .font(.caption)
                    .foregroundStyle(IPVColor.textSec)
            }

            Spacer()

            Text("\(r.paramsSet)/656")
                .font(.caption)
                .foregroundStyle(IPVColor.textMuted)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(IPVColor.header)
    }

    // MARK: - LLM Research Section

    private var llmResearchSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 6) {
                Image(systemName: "brain.head.profile")
                    .foregroundStyle(IPVColor.accent)
                Text("AI Research Assistant")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundStyle(IPVColor.textPri)
            }

            if !LLMInferenceManager.shared.isReady {
                noModelBanner
            }

            VStack(spacing: 8) {
                TextField("Ask a question about \(ticker)…", text: $llmQuestion, axis: .vertical)
                    .lineLimit(2...4)
                    .textFieldStyle(.plain)
                    .font(.system(size: 15))
                    .foregroundStyle(IPVColor.textPri)
                    .padding(12)
                    .background(IPVColor.bg)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(IPVColor.border, lineWidth: 1))
                    .disabled(isStreaming)

                Button { askAI() } label: {
                    HStack(spacing: 6) {
                        if isStreaming {
                            ProgressView().tint(.white).scaleEffect(0.8)
                        }
                        Text(isStreaming ? "Generating…" : "Ask AI")
                            .font(.system(size: 15, weight: .semibold))
                    }
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(canAsk ? IPVColor.accent : IPVColor.accent.opacity(0.3))
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                    .animation(.easeInOut(duration: 0.15), value: canAsk)
                }
                .disabled(!canAsk)
            }

            if let err = llmError {
                Text(err)
                    .font(.caption)
                    .foregroundStyle(IPVColor.red)
                    .padding(10)
                    .background(IPVColor.red.opacity(0.10))
                    .clipShape(RoundedRectangle(cornerRadius: 8))
            }

            if !llmResponse.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Image(systemName: "sparkles").foregroundStyle(IPVColor.accent)
                        Text("AI Analysis")
                            .font(.caption.bold())
                            .foregroundStyle(IPVColor.textSec)
                        Spacer()
                        if isStreaming {
                            ProgressView().scaleEffect(0.7).tint(IPVColor.accent)
                        }
                    }
                    ScrollView {
                        Text(llmResponse)
                            .font(.system(size: 14))
                            .foregroundStyle(IPVColor.textPri)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(12)
                    }
                    .frame(maxHeight: 280)
                    .background(IPVColor.bg)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(IPVColor.border, lineWidth: 1))
                }
            }
        }
        .padding(16)
        .background(IPVColor.card)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(IPVColor.border, lineWidth: 1))
    }

    private var noModelBanner: some View {
        HStack(spacing: 10) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(IPVColor.accent)
            VStack(alignment: .leading, spacing: 2) {
                Text("No model loaded")
                    .font(.caption.bold())
                    .foregroundStyle(IPVColor.textPri)
                Text("Download and activate a model in the Models tab to enable AI analysis.")
                    .font(.caption2)
                    .foregroundStyle(IPVColor.textSec)
            }
        }
        .padding(12)
        .background(IPVColor.accent.opacity(0.10))
        .clipShape(RoundedRectangle(cornerRadius: 10))
        .overlay(RoundedRectangle(cornerRadius: 10).stroke(IPVColor.accent.opacity(0.25), lineWidth: 1))
    }

    private var canAsk: Bool {
        !isStreaming && !llmQuestion.trimmingCharacters(in: .whitespaces).isEmpty
    }

    // MARK: - Actions

    private func saveSnapshot() {
        store.saveForTicker(ticker)
        let r = store.computePrediction()
        withAnimation { saveMessage = "Saved — \(r.paramsSet) params set" }
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.5) {
            withAnimation { saveMessage = "" }
        }
    }

    private func askAI() {
        guard canAsk else { return }
        llmError = nil
        llmResponse = ""
        isStreaming = true

        let question = llmQuestion
        let r = store.computePrediction()
        let signalSummary = "Params set: \(r.paramsSet)/656, direction: \(r.direction), Prob(UP): \(String(format: "%.1f", r.probUp * 100))%, Confidence: \(String(format: "%.1f", r.confidence * 100))%"
        let system = "You are a concise financial research assistant specialising in stock market analysis. The user is analysing \(ticker). Current signal summary: \(signalSummary). Provide actionable, structured analysis."

        Task {
            do {
                _ = try await LLMInferenceManager.shared.chat(
                    systemPrompt: system,
                    userMessage: question
                ) { token in
                    Task { @MainActor in self.llmResponse += token }
                }
            } catch {
                await MainActor.run { llmError = error.localizedDescription }
            }
            await MainActor.run { isStreaming = false }
            llmQuestion = ""
        }
    }
}

// MARK: - Domain Group View

private struct DomainGroupView: View {
    let group: (domain: String, label: String, params: [StockParameter])
    let states: [String: ParamState]
    @Binding var expandedParams: Set<String>
    let onDirectionChange: (String, String) -> Void
    let onWeightChange: (String, Int) -> Void

    @State private var isCollapsed = false

    private var netDirection: String {
        let active = group.params.filter { (states[$0.name]?.weight ?? 0) > 0 }
        let upCount = active.filter { states[$0.name]?.direction == "up" }.count
        let downCount = active.filter { states[$0.name]?.direction == "down" }.count
        if upCount > downCount { return "up" }
        if downCount > upCount { return "down" }
        return "neutral"
    }

    private var activeCount: Int {
        group.params.filter { (states[$0.name]?.weight ?? 0) > 0 }.count
    }

    var body: some View {
        VStack(spacing: 0) {
            // Domain header
            Button {
                withAnimation(.spring(response: 0.3)) { isCollapsed.toggle() }
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: isCollapsed ? "chevron.right" : "chevron.down")
                        .font(.caption)
                        .foregroundStyle(IPVColor.textMuted)

                    Text(group.label)
                        .font(.system(size: 13, weight: .bold))
                        .foregroundStyle(IPVColor.textPri)

                    Text("\(group.params.count)")
                        .font(.system(size: 11))
                        .foregroundStyle(IPVColor.textMuted)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(IPVColor.border)
                        .clipShape(Capsule())

                    if activeCount > 0 {
                        Text("\(activeCount) set")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundStyle(IPVColor.accent)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(IPVColor.accent.opacity(0.12))
                            .clipShape(Capsule())
                    }

                    Spacer()

                    // Net direction badge
                    let dirColor: Color = netDirection == "up" ? IPVColor.green
                                       : netDirection == "down" ? IPVColor.red
                                       : .gray.opacity(0.5)
                    let dirLabel: String = netDirection == "up" ? "▲" : netDirection == "down" ? "▼" : "—"
                    Text(dirLabel)
                        .font(.system(size: 13, weight: .heavy))
                        .foregroundStyle(dirColor)
                        .frame(width: 28, height: 24)
                        .background(dirColor.opacity(0.15))
                        .clipShape(RoundedRectangle(cornerRadius: 6))
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 10)
            }
            .buttonStyle(.plain)

            if !isCollapsed {
                Divider().background(IPVColor.border)

                VStack(spacing: 0) {
                    ForEach(group.params) { param in
                        let state = states[param.name] ?? ParamState()
                        let isExpanded = expandedParams.contains(param.name)

                        ParameterRowView(
                            param: param,
                            state: state,
                            isExpanded: isExpanded,
                            onExpand: {
                                withAnimation(.spring(response: 0.3)) {
                                    if isExpanded {
                                        expandedParams.remove(param.name)
                                    } else {
                                        expandedParams.insert(param.name)
                                    }
                                }
                            },
                            onDirection: { dir in onDirectionChange(param.name, dir) },
                            onWeight: { weight in onWeightChange(param.name, weight) }
                        )

                        if param.id != group.params.last?.id {
                            Divider()
                                .background(IPVColor.border)
                                .padding(.leading, 36)
                        }
                    }
                }
            }
        }
        .background(IPVColor.card)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(IPVColor.border, lineWidth: 1))
    }
}

// MARK: - Parameter Row View

private struct ParameterRowView: View {
    let param: StockParameter
    let state: ParamState
    let isExpanded: Bool
    let onExpand: () -> Void
    let onDirection: (String) -> Void
    let onWeight: (Int) -> Void

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 6) {
                // Expand chevron
                Button(action: onExpand) {
                    Image(systemName: isExpanded ? "chevron.down" : "chevron.right")
                        .font(.caption2)
                        .foregroundStyle(IPVColor.textMuted)
                        .frame(width: 20)
                }
                .buttonStyle(.plain)

                // Name + label
                VStack(alignment: .leading, spacing: 1) {
                    Text(param.name)
                        .font(.system(.caption, design: .monospaced))
                        .foregroundStyle(state.direction == "neutral" ? IPVColor.textSec : IPVColor.textPri)
                        .lineLimit(1)
                    Text(param.label)
                        .font(.caption2)
                        .foregroundStyle(IPVColor.textMuted)
                        .lineLimit(1)
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                // Weight slider
                Slider(value: Binding(
                    get: { Double(state.weight) },
                    set: { onWeight(Int($0)) }
                ), in: 0...100, step: 1)
                .frame(width: 70)
                .tint(IPVColor.accent)

                Text("\(state.weight)")
                    .font(.system(.caption, design: .monospaced))
                    .foregroundStyle(IPVColor.accent)
                    .frame(width: 24, alignment: .trailing)

                // Direction buttons
                Button("▲") {
                    onDirection(state.direction == "up" ? "neutral" : "up")
                }
                .buttonStyle(.bordered)
                .tint(state.direction == "up" ? IPVColor.green : Color.secondary)
                .controlSize(.mini)

                Button("▼") {
                    onDirection(state.direction == "down" ? "neutral" : "down")
                }
                .buttonStyle(.bordered)
                .tint(state.direction == "down" ? IPVColor.red : Color.secondary)
                .controlSize(.mini)
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .opacity(state.direction == "neutral" && state.weight == 0 ? 0.65 : 1.0)

            if isExpanded {
                HStack(alignment: .top, spacing: 0) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("IN PLAIN ENGLISH")
                            .font(.system(size: 9, weight: .heavy))
                            .foregroundStyle(IPVColor.green)
                            .kerning(1)
                        Text(param.layman)
                            .font(.caption)
                            .foregroundStyle(IPVColor.textPri)
                            .lineSpacing(4)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(10)

                    Divider().background(IPVColor.border)

                    VStack(alignment: .leading, spacing: 4) {
                        Text("TECHNICAL")
                            .font(.system(size: 9, weight: .heavy))
                            .foregroundStyle(IPVColor.accent)
                            .kerning(1)
                        Text(param.technical)
                            .font(.caption)
                            .foregroundStyle(IPVColor.textPri)
                            .lineSpacing(4)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(10)
                }
                .background(IPVColor.bg)
                .clipShape(RoundedRectangle(cornerRadius: 6))
                .padding(.horizontal, 8)
                .padding(.bottom, 8)
            }
        }
    }
}
