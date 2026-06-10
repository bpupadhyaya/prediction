import SwiftUI

// MARK: - Data Model

struct ParameterSignal: Identifiable {
    let id = UUID()
    var name: String
    var domain: String          // "Macro" | "Fundamental" | "Technical" | "Sentiment" | "Cross-Asset" | "Geopolitical"
    var direction: String       // "up" | "down" | "neutral"
    var weight: Int             // 0–100
    var notes: String
}

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
    static let accent      = Color(red: 0.231, green: 0.510, blue: 0.965)   // #3B82F6
    static let green       = Color(red: 0.204, green: 0.827, blue: 0.600)   // #34d399
    static let red         = Color(red: 0.973, green: 0.443, blue: 0.443)   // #f87171
    static let border      = Color.white.opacity(0.10)
    static let textPri     = Color.white
    static let textSec     = Color.white.opacity(0.60)
    static let textMuted   = Color.white.opacity(0.35)
}

private let signalDomains = ["Macro", "Fundamental", "Technical", "Sentiment", "Cross-Asset", "Geopolitical"]

// MARK: - Main View

struct InteractiveParameterView: View {
    let ticker: String
    @EnvironmentObject var store: AppStore

    // Signal state
    @State private var signals: [ParameterSignal] = []
    @State private var showAddSignal = false
    @State private var newSignalName = ""
    @State private var newSignalDomain = "Technical"

    // Computed prediction
    @State private var probUp: Double = 0.5
    @State private var confidence: Double = 0.0
    @State private var direction: String = "neutral"

    // LLM chat
    @State private var currentQuestion = ""
    @State private var llmResponse: String = ""
    @State private var isStreaming = false
    @State private var llmError: String? = nil

    // UI state
    @State private var showSaveAlert = false
    @State private var scrollToBottom = false

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ZStack {
            IPVColor.bg.ignoresSafeArea()

            ScrollViewReader { proxy in
                ScrollView {
                    VStack(spacing: 16) {
                        headerSection
                        signalListSection
                        addSignalSection
                        llmResearchSection
                        saveButton
                            .id("bottom")
                    }
                    .padding(.horizontal, 16)
                    .padding(.bottom, 32)
                }
                .onChange(of: scrollToBottom) { _, scroll in
                    if scroll {
                        withAnimation { proxy.scrollTo("bottom", anchor: .bottom) }
                        scrollToBottom = false
                    }
                }
            }
        }
        .navigationTitle("Interactive Predict — \(ticker)")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarLeading) {
                Button("Cancel") { dismiss() }
                    .foregroundStyle(IPVColor.textSec)
            }
        }
        .alert("Prediction Saved", isPresented: $showSaveAlert) {
            Button("OK") { dismiss() }
        } message: {
            Text("Your parameter signals have been recorded. Backend persistence will be wired in Phase 4.")
        }
        .onChange(of: signals) { _, _ in recompute() }
        .onAppear { seedDefaultSignals() }
    }

    // MARK: - Header / Computed Prediction

    private var headerSection: some View {
        VStack(spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(ticker)
                        .font(.system(size: 28, weight: .bold))
                        .foregroundStyle(IPVColor.textPri)
                    Text("Interactive Parameter Analysis")
                        .font(.caption)
                        .foregroundStyle(IPVColor.textSec)
                }
                Spacer()
                directionBadge
            }

            HStack(spacing: 0) {
                metricTile(value: String(format: "%.1f%%", probUp * 100), label: "Prob Up")
                divider
                metricTile(value: String(format: "%.1f%%", confidence * 100), label: "Confidence")
                divider
                metricTile(value: directionLabel, label: "Direction", color: directionColor)
            }
            .background(IPVColor.card)
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .overlay(RoundedRectangle(cornerRadius: 12).stroke(IPVColor.border, lineWidth: 1))
        }
        .padding(.top, 8)
    }

    private var directionBadge: some View {
        Text(directionLabel.uppercased())
            .font(.system(size: 13, weight: .bold))
            .foregroundStyle(directionColor)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(directionColor.opacity(0.15))
            .clipShape(Capsule())
    }

    private func metricTile(value: String, label: String, color: Color = IPVColor.textPri) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.system(size: 20, weight: .bold))
                .foregroundStyle(color)
            Text(label)
                .font(.caption2)
                .foregroundStyle(IPVColor.textMuted)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 14)
    }

    private var divider: some View {
        Rectangle()
            .fill(IPVColor.border)
            .frame(width: 1)
            .padding(.vertical, 10)
    }

    // MARK: - Signal List

    private var signalListSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Parameter Signals", icon: "slider.horizontal.3", count: signals.count)

            if signals.isEmpty {
                emptySignalsPlaceholder
            } else {
                ForEach($signals) { $signal in
                    SignalRow(signal: $signal, onDelete: {
                        signals.removeAll { $0.id == signal.id }
                    })
                }
            }
        }
    }

    private var emptySignalsPlaceholder: some View {
        HStack {
            Spacer()
            VStack(spacing: 8) {
                Image(systemName: "waveform.path")
                    .font(.system(size: 32))
                    .foregroundStyle(IPVColor.textMuted)
                Text("No signals yet. Tap + Add Signal to begin.")
                    .font(.caption)
                    .foregroundStyle(IPVColor.textMuted)
                    .multilineTextAlignment(.center)
            }
            .padding(.vertical, 24)
            Spacer()
        }
        .background(IPVColor.card)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(IPVColor.border, lineWidth: 1))
    }

    // MARK: - Add Signal

    private var addSignalSection: some View {
        VStack(spacing: 12) {
            Button {
                withAnimation(.spring(response: 0.35)) { showAddSignal.toggle() }
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: showAddSignal ? "minus.circle.fill" : "plus.circle.fill")
                    Text(showAddSignal ? "Cancel" : "Add Signal")
                        .font(.system(size: 15, weight: .semibold))
                }
                .foregroundStyle(IPVColor.accent)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
                .background(IPVColor.accent.opacity(0.12))
                .clipShape(RoundedRectangle(cornerRadius: 10))
                .overlay(RoundedRectangle(cornerRadius: 10).stroke(IPVColor.accent.opacity(0.30), lineWidth: 1))
            }

            if showAddSignal {
                addSignalForm
                    .transition(.move(edge: .top).combined(with: .opacity))
            }
        }
    }

    private var addSignalForm: some View {
        VStack(spacing: 12) {
            TextField("Signal name (e.g. Fed Rate Decision)", text: $newSignalName)
                .textFieldStyle(.plain)
                .font(.system(size: 15))
                .foregroundStyle(IPVColor.textPri)
                .padding(12)
                .background(IPVColor.bg)
                .clipShape(RoundedRectangle(cornerRadius: 8))
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(IPVColor.border, lineWidth: 1))

            VStack(alignment: .leading, spacing: 6) {
                Text("Domain")
                    .font(.caption)
                    .foregroundStyle(IPVColor.textSec)
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(signalDomains, id: \.self) { domain in
                            DomainChip(domain: domain, isSelected: newSignalDomain == domain) {
                                newSignalDomain = domain
                            }
                        }
                    }
                    .padding(.horizontal, 2)
                }
            }

            Button {
                guard !newSignalName.trimmingCharacters(in: .whitespaces).isEmpty else { return }
                let sig = ParameterSignal(
                    name: newSignalName.trimmingCharacters(in: .whitespaces),
                    domain: newSignalDomain,
                    direction: "neutral",
                    weight: 50,
                    notes: ""
                )
                withAnimation { signals.append(sig) }
                newSignalName = ""
                showAddSignal = false
            } label: {
                Text("Add Signal")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(newSignalName.trimmingCharacters(in: .whitespaces).isEmpty
                                ? IPVColor.accent.opacity(0.3)
                                : IPVColor.accent)
                    .clipShape(RoundedRectangle(cornerRadius: 10))
            }
            .disabled(newSignalName.trimmingCharacters(in: .whitespaces).isEmpty)
        }
        .padding(14)
        .background(IPVColor.card)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(IPVColor.border, lineWidth: 1))
    }

    // MARK: - LLM Research

    private var llmResearchSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("AI Research Assistant", icon: "brain.head.profile", count: nil)

            if !LLMInferenceManager.shared.isReady {
                noModelBanner
            }

            VStack(spacing: 10) {
                TextField("Ask a question about \(ticker)...", text: $currentQuestion, axis: .vertical)
                    .lineLimit(2...4)
                    .textFieldStyle(.plain)
                    .font(.system(size: 15))
                    .foregroundStyle(IPVColor.textPri)
                    .padding(12)
                    .background(IPVColor.bg)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(IPVColor.border, lineWidth: 1))
                    .disabled(isStreaming)

                Button {
                    askAI()
                } label: {
                    HStack(spacing: 6) {
                        if isStreaming {
                            ProgressView()
                                .tint(.white)
                                .scaleEffect(0.8)
                        }
                        Text(isStreaming ? "Generating..." : "Ask AI")
                            .font(.system(size: 15, weight: .semibold))
                    }
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(canAsk ? IPVColor.accent : IPVColor.accent.opacity(0.3))
                    .clipShape(RoundedRectangle(cornerRadius: 10))
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
                llmResponseView
            }
        }
    }

    private var canAsk: Bool {
        !isStreaming && !currentQuestion.trimmingCharacters(in: .whitespaces).isEmpty
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

    private var llmResponseView: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "sparkles")
                    .foregroundStyle(IPVColor.accent)
                Text("AI Analysis")
                    .font(.caption.bold())
                    .foregroundStyle(IPVColor.textSec)
                Spacer()
                if isStreaming {
                    ProgressView()
                        .scaleEffect(0.7)
                        .tint(IPVColor.accent)
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

    // MARK: - Save

    private var saveButton: some View {
        Button {
            showSaveAlert = true
        } label: {
            HStack(spacing: 8) {
                Image(systemName: "checkmark.circle.fill")
                Text("Save Prediction")
                    .font(.system(size: 16, weight: .semibold))
            }
            .foregroundStyle(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 15)
            .background(
                LinearGradient(colors: [IPVColor.accent, IPVColor.accent.opacity(0.7)],
                               startPoint: .leading, endPoint: .trailing)
            )
            .clipShape(RoundedRectangle(cornerRadius: 12))
        }
    }

    // MARK: - Helpers

    private func sectionHeader(_ title: String, icon: String, count: Int?) -> some View {
        HStack(spacing: 6) {
            Image(systemName: icon)
                .foregroundStyle(IPVColor.accent)
            Text(title)
                .font(.system(size: 16, weight: .semibold))
                .foregroundStyle(IPVColor.textPri)
            if let n = count {
                Text("(\(n))")
                    .font(.caption)
                    .foregroundStyle(IPVColor.textMuted)
            }
        }
    }

    private var directionLabel: String {
        switch direction {
        case "up":   return "Bullish"
        case "down": return "Bearish"
        default:     return "Neutral"
        }
    }

    private var directionColor: Color {
        switch direction {
        case "up":   return IPVColor.green
        case "down": return IPVColor.red
        default:     return IPVColor.accent
        }
    }

    // MARK: - Prediction Formula
    // Formula matches the web app:
    //   dirValue: up → +1, down → −1, neutral → 0
    //   normalizedScore = Σ(weight × dirValue) / Σ(weight)   [range −1..+1]
    //   probUp = (normalizedScore + 1) / 2                   [range 0..1]
    //   confidence = |normalizedScore|                        [range 0..1]

    private func recompute() {
        guard !signals.isEmpty else {
            probUp = 0.5; confidence = 0.0; direction = "neutral"; return
        }
        let totalWeight = signals.reduce(0) { $0 + $1.weight }
        guard totalWeight > 0 else {
            probUp = 0.5; confidence = 0.0; direction = "neutral"; return
        }
        let weightedSum = signals.reduce(0.0) { acc, sig in
            let dv: Double = sig.direction == "up" ? 1 : sig.direction == "down" ? -1 : 0
            return acc + Double(sig.weight) * dv
        }
        let normalized = weightedSum / Double(totalWeight)  // −1..+1
        probUp     = (normalized + 1) / 2
        confidence = abs(normalized)
        direction  = normalized > 0.05 ? "up" : normalized < -0.05 ? "down" : "neutral"
    }

    private func seedDefaultSignals() {
        signals = [
            ParameterSignal(name: "Market Trend", domain: "Technical",    direction: "neutral", weight: 60, notes: ""),
            ParameterSignal(name: "Fed Policy",   domain: "Macro",        direction: "neutral", weight: 50, notes: ""),
            ParameterSignal(name: "Earnings",     domain: "Fundamental",  direction: "neutral", weight: 70, notes: ""),
        ]
    }

    private func askAI() {
        guard canAsk else { return }
        llmError = nil
        llmResponse = ""
        isStreaming = true

        let question = currentQuestion
        let signalSummary = signals.map { "\($0.name) (\($0.domain)): \($0.direction) w=\($0.weight)" }.joined(separator: "; ")
        let system = "You are a concise financial research assistant specialising in stock market analysis. The user is analysing \(ticker) with the following parameter signals: \(signalSummary.isEmpty ? "none yet" : signalSummary). Provide actionable, structured analysis."

        Task {
            do {
                _ = try await LLMInferenceManager.shared.chat(
                    systemPrompt: system,
                    userMessage: question
                ) { token in
                    Task { @MainActor in
                        self.llmResponse += token
                    }
                }
            } catch {
                llmError = error.localizedDescription
            }
            isStreaming = false
            currentQuestion = ""
            scrollToBottom = true
        }
    }
}

// MARK: - Signal Row

private struct SignalRow: View {
    @Binding var signal: ParameterSignal
    let onDelete: () -> Void

    @State private var isExpanded = false

    var body: some View {
        VStack(spacing: 0) {
            // Collapsed header
            Button {
                withAnimation(.spring(response: 0.3)) { isExpanded.toggle() }
            } label: {
                HStack(spacing: 10) {
                    directionIcon
                    VStack(alignment: .leading, spacing: 2) {
                        Text(signal.name)
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundStyle(IPVColor.textPri)
                            .lineLimit(1)
                        Text("\(signal.domain)  ·  weight \(signal.weight)")
                            .font(.caption2)
                            .foregroundStyle(IPVColor.textMuted)
                    }
                    Spacer()
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.caption)
                        .foregroundStyle(IPVColor.textMuted)
                }
                .padding(12)
            }
            .buttonStyle(.plain)

            if isExpanded {
                Divider().background(IPVColor.border)

                VStack(spacing: 14) {
                    // Direction picker
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Direction")
                            .font(.caption)
                            .foregroundStyle(IPVColor.textSec)
                        HStack(spacing: 8) {
                            directionButton("up",      label: "UP",      color: IPVColor.green)
                            directionButton("neutral", label: "NEUTRAL", color: IPVColor.accent)
                            directionButton("down",    label: "DOWN",    color: IPVColor.red)
                        }
                    }

                    // Weight slider
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text("Weight")
                                .font(.caption)
                                .foregroundStyle(IPVColor.textSec)
                            Spacer()
                            Text("\(signal.weight)")
                                .font(.caption.monospacedDigit())
                                .foregroundStyle(IPVColor.textPri)
                        }
                        Slider(value: Binding(
                            get: { Double(signal.weight) },
                            set: { signal.weight = Int($0) }
                        ), in: 0...100, step: 5)
                        .tint(IPVColor.accent)
                    }

                    // Notes field
                    TextField("Notes (optional)", text: $signal.notes)
                        .textFieldStyle(.plain)
                        .font(.system(size: 13))
                        .foregroundStyle(IPVColor.textPri)
                        .padding(9)
                        .background(IPVColor.bg)
                        .clipShape(RoundedRectangle(cornerRadius: 7))
                        .overlay(RoundedRectangle(cornerRadius: 7).stroke(IPVColor.border, lineWidth: 1))

                    // Delete button
                    Button(role: .destructive) {
                        onDelete()
                    } label: {
                        HStack(spacing: 4) {
                            Image(systemName: "trash")
                            Text("Remove Signal")
                        }
                        .font(.caption)
                        .foregroundStyle(IPVColor.red)
                    }
                }
                .padding(12)
            }
        }
        .background(IPVColor.card)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(IPVColor.border, lineWidth: 1))
    }

    private var directionIcon: some View {
        let (icon, color): (String, Color) = {
            switch signal.direction {
            case "up":   return ("arrow.up.circle.fill", IPVColor.green)
            case "down": return ("arrow.down.circle.fill", IPVColor.red)
            default:     return ("minus.circle.fill", IPVColor.accent)
            }
        }()
        return Image(systemName: icon)
            .font(.system(size: 22))
            .foregroundStyle(color)
    }

    private func directionButton(_ dir: String, label: String, color: Color) -> some View {
        let isSelected = signal.direction == dir
        return Button {
            signal.direction = dir
        } label: {
            Text(label)
                .font(.system(size: 12, weight: .bold))
                .foregroundStyle(isSelected ? .white : color)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 8)
                .background(isSelected ? color : color.opacity(0.12))
                .clipShape(RoundedRectangle(cornerRadius: 8))
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(color.opacity(0.4), lineWidth: 1))
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Domain Chip

private struct DomainChip: View {
    let domain: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(domain)
                .font(.system(size: 12, weight: .semibold))
                .foregroundStyle(isSelected ? .white : IPVColor.accent)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(isSelected ? IPVColor.accent : IPVColor.accent.opacity(0.12))
                .clipShape(Capsule())
                .overlay(Capsule().stroke(IPVColor.accent.opacity(0.35), lineWidth: 1))
        }
        .buttonStyle(.plain)
    }
}
