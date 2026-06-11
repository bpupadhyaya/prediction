import SwiftUI

// MARK: - Supporting Types

enum TimeRange: String, CaseIterable, Identifiable {
    case hour1   = "1h"
    case hour6   = "6h"
    case day1    = "1d"
    case week1   = "1w"
    case month1  = "1mo"
    case month3  = "3mo"
    case year1   = "1yr"
    case year5   = "5yr"
    case year10  = "10yr"
    case year20  = "20yr"

    var id: String { rawValue }

    var displayName: String { rawValue }

    var days: Int {
        switch self {
        case .hour1:   return 1
        case .hour6:   return 1
        case .day1:    return 1
        case .week1:   return 7
        case .month1:  return 30
        case .month3:  return 90
        case .year1:   return 365
        case .year5:   return 365 * 5
        case .year10:  return 365 * 10
        case .year20:  return 365 * 20
        }
    }

    static var shortRanges: [TimeRange] { [.hour1, .hour6, .day1, .week1, .month1] }
    static var longRanges:  [TimeRange] { [.month3, .year1, .year5, .year10, .year20] }
}

// MARK: - Influential Speakers Seed Data

private struct SpeakerSeed: Identifiable {
    let id = UUID()
    let name: String
    let channelId: String
}

private let influentialSpeakers: [SpeakerSeed] = [
    SpeakerSeed(name: "Elon Musk",      channelId: "UCEb7pOMZ5h3MdqN7fYPD5mw"),
    SpeakerSeed(name: "Warren Buffett", channelId: "UCIRYBXDze5krPDzAEOxFGVA"),
    SpeakerSeed(name: "Jerome Powell",  channelId: "UCTk_-XgFDfSf6EGpJQJhRdA"),
    SpeakerSeed(name: "Jensen Huang",   channelId: "UCeeFfhMcJa1kjtfZAGskOCA"),
    SpeakerSeed(name: "Tim Cook",       channelId: "UCE_M8A5yxnLfW0KghEeajjw"),
    SpeakerSeed(name: "Cathie Wood",    channelId: "UCimKczFRuRUKPPHarX6v_jQ"),
    SpeakerSeed(name: "Jim Cramer",     channelId: "UCFiJ9iqkIEYQlFa_WJyRGqQ"),
    SpeakerSeed(name: "Michael Saylor", channelId: "UCVHVFAm24e5i3kEi0IG3ItQ"),
]

// MARK: - Theme helpers (local aliases for readability)

private extension Color {
    static let yvisBackground  = Color(red: 0.043, green: 0.118, blue: 0.212)
    static let yvisCard        = Color(red: 0.086, green: 0.157, blue: 0.259)
    static let yvisCardLight   = Color(red: 0.102, green: 0.188, blue: 0.302)
}

// MARK: - VideoIntelligenceView

struct VideoIntelligenceView: View {
    @StateObject private var manager = VideoIntelligenceManager.shared

    @State private var urlInput = ""
    @State private var selectedShortRange: TimeRange = .week1
    @State private var selectedLongRange: TimeRange = .year1
    @State private var useShortRange = true
    @State private var showAddChannelSheet = false
    @State private var newChannelName = ""
    @State private var newChannelId = ""
    @State private var newSpeakerName = ""
    @State private var trackedChannels: [ChannelTrackRecord] = []
    @State private var showAppliedAlert = false
    @State private var appliedSignalTitle = ""

    private var selectedTimeRange: TimeRange {
        useShortRange ? selectedShortRange : selectedLongRange
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    urlInputCard
                    if !manager.processingJobs.isEmpty {
                        processingQueueCard
                    }
                    trackedSpeakersCard
                    timeRangeCard
                    signalFeedCard
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 32)
            }
            .background(Color.yvisBackground.ignoresSafeArea())
            .navigationTitle("Video Intelligence")
            .navigationBarTitleDisplayMode(.large)
            .toolbarColorScheme(.dark, for: .navigationBar)
            .toolbarBackground(Color(red: 0.051, green: 0.122, blue: 0.212), for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
            .alert("Error", isPresented: Binding(
                get: { manager.errorMessage != nil },
                set: { if !$0 { manager.errorMessage = nil } }
            )) {
                Button("OK", role: .cancel) { manager.errorMessage = nil }
            } message: {
                Text(manager.errorMessage ?? "")
            }
            .alert("Signal Applied", isPresented: $showAppliedAlert) {
                Button("OK", role: .cancel) {}
            } message: {
                Text("'\(appliedSignalTitle)' has been applied to the prediction engine.")
            }
            .sheet(isPresented: $showAddChannelSheet) {
                addChannelSheet
            }
            .task {
                await manager.loadRecent()
                await loadTrackedChannels()
            }
            .refreshable {
                await manager.loadRecent()
                await loadTrackedChannels()
            }
        }
    }

    // MARK: - URL Input Card

    private var urlInputCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Analyze YouTube Video", systemImage: "video.badge.waveform")
                .font(.headline)
                .foregroundStyle(.white)

            HStack(spacing: 10) {
                TextField("Paste YouTube URL…", text: $urlInput)
                    .textFieldStyle(.plain)
                    .foregroundStyle(.white)
                    .autocorrectionDisabled()
                    .textInputAutocapitalization(.never)
                    .keyboardType(.URL)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 10)
                    .background(Color.yvisCardLight)
                    .clipShape(RoundedRectangle(cornerRadius: 8))

                Button {
                    analyzeURL()
                } label: {
                    Text("Analyze")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundStyle(.white)
                        .padding(.horizontal, 14)
                        .padding(.vertical, 10)
                        .background(Color.blue)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                }
                .disabled(urlInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }

            Text("Requires an LLM model to be active (Models tab) and Speech Recognition permission.")
                .font(.caption2)
                .foregroundStyle(.white.opacity(0.45))
        }
        .padding(16)
        .background(Color.yvisCard)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Processing Queue Card

    private var processingQueueCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Label("Processing", systemImage: "gear.circle")
                .font(.headline)
                .foregroundStyle(.white)

            ForEach(Array(manager.processingJobs.values).sorted(by: { $0.startedAt < $1.startedAt })) { job in
                processingJobRow(job: job)
            }
        }
        .padding(16)
        .background(Color.yvisCard)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private func processingJobRow(job: ProcessingJob) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                statusBadge(for: job.status)
                Spacer()
                Text(timeAgo(job.startedAt))
                    .font(.caption2)
                    .foregroundStyle(.white.opacity(0.5))
            }
            Text(job.statusMessage)
                .font(.caption)
                .foregroundStyle(.white.opacity(0.75))
                .lineLimit(1)
            if !job.status.isFinal {
                ProgressView(value: job.progress)
                    .tint(.blue)
            }
        }
        .padding(10)
        .background(Color.yvisCardLight)
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private func statusBadge(for status: ProcessingStatus) -> some View {
        let (label, color): (String, Color) = {
            switch status {
            case .queued:       return ("Queued", .gray)
            case .downloading:  return ("Downloading", .orange)
            case .transcribing: return ("Transcribing", .purple)
            case .extracting:   return ("Extracting", .blue)
            case .done:         return ("Done", .green)
            case .failed:       return ("Failed", .red)
            }
        }()
        return Text(label)
            .font(.caption2.weight(.semibold))
            .foregroundStyle(.white)
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(color.opacity(0.85))
            .clipShape(Capsule())
    }

    // MARK: - Tracked Speakers Card

    private var trackedSpeakersCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Label("Tracked Speakers", systemImage: "person.2.wave.2")
                    .font(.headline)
                    .foregroundStyle(.white)
                Spacer()
                Button {
                    showAddChannelSheet = true
                } label: {
                    Image(systemName: "plus.circle.fill")
                        .foregroundStyle(.blue)
                        .font(.title3)
                }
            }

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    // Pre-seeded speakers
                    ForEach(influentialSpeakers) { speaker in
                        speakerChip(
                            name: speaker.name,
                            channelId: speaker.channelId,
                            isTracked: trackedChannels.contains(where: { $0.channelId == speaker.channelId })
                        )
                    }
                    // User-added channels
                    ForEach(trackedChannels.filter { ct in
                        !influentialSpeakers.contains(where: { $0.channelId == ct.channelId })
                    }) { ct in
                        speakerChip(
                            name: ct.speakerName.isEmpty ? ct.channelName : ct.speakerName,
                            channelId: ct.channelId,
                            isTracked: true
                        )
                    }
                }
                .padding(.vertical, 2)
            }
        }
        .padding(16)
        .background(Color.yvisCard)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private func speakerChip(name: String, channelId: String, isTracked: Bool) -> some View {
        HStack(spacing: 4) {
            if isTracked {
                Image(systemName: "checkmark.circle.fill")
                    .font(.caption2)
                    .foregroundStyle(.green)
            }
            Text(name)
                .font(.caption.weight(.medium))
                .foregroundStyle(isTracked ? .white : .white.opacity(0.7))
                .lineLimit(1)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(isTracked ? Color.blue.opacity(0.35) : Color.yvisCardLight)
        .overlay(
            RoundedRectangle(cornerRadius: 20)
                .stroke(isTracked ? Color.blue.opacity(0.6) : Color.white.opacity(0.15), lineWidth: 1)
        )
        .clipShape(Capsule())
        .onTapGesture {
            if isTracked {
                Task {
                    await manager.removeTrackedChannel(channelId)
                    await loadTrackedChannels()
                }
            } else {
                let seed = influentialSpeakers.first(where: { $0.channelId == channelId })
                Task {
                    await manager.trackChannel(channelId, name: seed?.name ?? name, speaker: seed?.name ?? name)
                    await loadTrackedChannels()
                }
            }
        }
    }

    // MARK: - Time Range Card

    private var timeRangeCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Label("Signal Time Range", systemImage: "calendar")
                    .font(.headline)
                    .foregroundStyle(.white)
                Spacer()
                Menu {
                    ForEach(TimeRange.longRanges) { range in
                        Button(range.displayName) {
                            selectedLongRange = range
                            useShortRange = false
                        }
                    }
                } label: {
                    HStack(spacing: 4) {
                        Text(useShortRange ? "More" : selectedLongRange.displayName)
                            .font(.caption.weight(.medium))
                        Image(systemName: "chevron.down")
                            .font(.caption2)
                    }
                    .foregroundStyle(useShortRange ? .white.opacity(0.6) : .blue)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(Color.yvisCardLight)
                    .clipShape(Capsule())
                }
            }

            Picker("Range", selection: $selectedShortRange) {
                ForEach(TimeRange.shortRanges) { range in
                    Text(range.displayName).tag(range)
                }
            }
            .pickerStyle(.segmented)
            .onChange(of: selectedShortRange) { _ in useShortRange = true }
        }
        .padding(16)
        .background(Color.yvisCard)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Signal Feed Card

    private var signalFeedCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Signal Feed", systemImage: "waveform.path.ecg")
                .font(.headline)
                .foregroundStyle(.white)

            let filteredSignals = manager.recentSignals.filter {
                Date().timeIntervalSince($0.extractedAt) <= Double(selectedTimeRange.days) * 86_400
            }

            if filteredSignals.isEmpty {
                emptySignalState
            } else {
                ForEach(filteredSignals) { signal in
                    signalCard(signal)
                }
            }
        }
        .padding(16)
        .background(Color.yvisCard)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var emptySignalState: some View {
        VStack(spacing: 8) {
            Image(systemName: "waveform.slash")
                .font(.system(size: 32))
                .foregroundStyle(.white.opacity(0.3))
            Text("No signals in this time range")
                .font(.subheadline)
                .foregroundStyle(.white.opacity(0.45))
            Text("Paste a YouTube URL above to analyze a video.")
                .font(.caption)
                .foregroundStyle(.white.opacity(0.3))
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 24)
    }

    private func signalCard(_ signal: VideoSignalRecord) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            // Top row: direction badge + ticker + domain + weight
            HStack(spacing: 8) {
                directionBadge(signal.direction)
                if let ticker = signal.ticker {
                    Text(ticker)
                        .font(.caption.weight(.bold))
                        .foregroundStyle(.white)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 3)
                        .background(Color.white.opacity(0.12))
                        .clipShape(RoundedRectangle(cornerRadius: 4))
                }
                domainBadge(signal.domain)
                Spacer()
                Text("W:\(signal.weight)")
                    .font(.caption2.weight(.semibold))
                    .foregroundStyle(.white.opacity(0.6))
            }

            // Parameter name
            Text(signal.parameterName)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(.white)

            // Key quote
            if !signal.keyQuote.isEmpty {
                Text("\"\(signal.keyQuote)\"")
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.65))
                    .lineLimit(2)
                    .italic()
            }

            // Source line
            HStack(spacing: 4) {
                if let title = signal.videoTitle {
                    Image(systemName: "play.rectangle")
                        .font(.caption2)
                        .foregroundStyle(.white.opacity(0.4))
                    Text(title)
                        .font(.caption2)
                        .foregroundStyle(.white.opacity(0.5))
                        .lineLimit(1)
                    Spacer()
                } else {
                    Spacer()
                }
                Text(timeAgo(signal.extractedAt))
                    .font(.caption2)
                    .foregroundStyle(.white.opacity(0.4))
            }

            // Confidence bar + Apply button
            HStack(spacing: 10) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Confidence \(Int(signal.confidence * 100))%")
                        .font(.caption2)
                        .foregroundStyle(.white.opacity(0.5))
                    GeometryReader { geo in
                        ZStack(alignment: .leading) {
                            RoundedRectangle(cornerRadius: 2)
                                .fill(Color.white.opacity(0.12))
                                .frame(height: 4)
                            RoundedRectangle(cornerRadius: 2)
                                .fill(signal.direction == "up" ? Color.green : Color.red)
                                .frame(width: geo.size.width * signal.confidence, height: 4)
                        }
                    }
                    .frame(height: 4)
                }
                Spacer()
                Button {
                    Task {
                        await manager.applySignalToPrediction(signal)
                        appliedSignalTitle = signal.parameterName
                        showAppliedAlert = true
                    }
                } label: {
                    Text("Apply")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.white)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 5)
                        .background(Color.blue.opacity(0.7))
                        .clipShape(Capsule())
                }
            }
        }
        .padding(12)
        .background(Color.yvisCardLight)
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }

    private func directionBadge(_ direction: String) -> some View {
        let isUp = direction.lowercased() == "up"
        return Text(isUp ? "▲ UP" : "▼ DOWN")
            .font(.caption2.weight(.bold))
            .foregroundStyle(.white)
            .padding(.horizontal, 7)
            .padding(.vertical, 3)
            .background(isUp ? Color.green.opacity(0.85) : Color.red.opacity(0.85))
            .clipShape(Capsule())
    }

    private func domainBadge(_ domain: String) -> some View {
        Text(domain.replacingOccurrences(of: "_", with: " ").capitalized)
            .font(.caption2.weight(.medium))
            .foregroundStyle(.blue)
            .padding(.horizontal, 7)
            .padding(.vertical, 3)
            .background(Color.blue.opacity(0.15))
            .overlay(
                Capsule().stroke(Color.blue.opacity(0.35), lineWidth: 1)
            )
            .clipShape(Capsule())
    }

    // MARK: - Add Channel Sheet

    private var addChannelSheet: some View {
        NavigationStack {
            Form {
                Section("Channel Info") {
                    TextField("Speaker / Analyst Name", text: $newSpeakerName)
                    TextField("Channel Name", text: $newChannelName)
                    TextField("YouTube Channel ID", text: $newChannelId)
                        .autocorrectionDisabled()
                        .textInputAutocapitalization(.never)
                }
                Section {
                    Text("Find the channel ID in the YouTube channel URL: youtube.com/channel/UC…")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Track Channel")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { showAddChannelSheet = false }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Add") {
                        let id = newChannelId.trimmingCharacters(in: .whitespacesAndNewlines)
                        let name = newChannelName.trimmingCharacters(in: .whitespacesAndNewlines)
                        let speaker = newSpeakerName.trimmingCharacters(in: .whitespacesAndNewlines)
                        guard !id.isEmpty, !name.isEmpty else { return }
                        Task {
                            await manager.trackChannel(id, name: name, speaker: speaker)
                            await loadTrackedChannels()
                        }
                        newChannelId = ""
                        newChannelName = ""
                        newSpeakerName = ""
                        showAddChannelSheet = false
                    }
                    .disabled(
                        newChannelId.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ||
                        newChannelName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                    )
                }
            }
        }
    }

    // MARK: - Private Helpers

    private func analyzeURL() {
        let trimmed = urlInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        urlInput = ""
        Task { await manager.processURL(trimmed) }
    }

    private func loadTrackedChannels() async {
        trackedChannels = await manager.getTrackedChannels()
    }

    private func timeAgo(_ date: Date) -> String {
        let diff = Date().timeIntervalSince(date)
        switch diff {
        case ..<60:          return "just now"
        case ..<3600:        return "\(Int(diff / 60))m ago"
        case ..<86400:       return "\(Int(diff / 3600))h ago"
        case ..<604800:      return "\(Int(diff / 86400))d ago"
        default:
            let formatter = DateFormatter()
            formatter.dateStyle = .short
            formatter.timeStyle = .none
            return formatter.string(from: date)
        }
    }
}

// MARK: - Preview

#Preview {
    VideoIntelligenceView()
}
