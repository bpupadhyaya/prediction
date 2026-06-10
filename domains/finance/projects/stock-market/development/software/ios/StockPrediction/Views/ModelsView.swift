import SwiftUI

struct ModelsView: View {
    @StateObject private var dm = LLMDownloadManager.shared

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    hardwareCard

                    if let activeId = dm.activeModelId,
                       let m = llmCatalog.first(where: { $0.id == activeId }) {
                        activeModelBanner(m)
                    }

                    ForEach(llmCatalog) { model in
                        ModelCard(model: model, dm: dm)
                    }

                    Text("Models run 100% on-device. No internet needed after download. LLM reasoning is a work-in-progress feature; GBM predictions are always available.")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 16)
                }
                .padding(16)
            }
            .navigationTitle("Models")
            .navigationBarTitleDisplayMode(.large)
        }
    }

    private var hardwareCard: some View {
        let ram = dm.totalRAMGB
        let cpu = ProcessInfo.processInfo.processorCount
        let isAppleSilicon: Bool = {
            #if arch(arm64)
            return true
            #else
            return false
            #endif
        }()

        return VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 24) {
                LabeledValue(label: "RAM", value: String(format: "%.0f GB", ram))
                LabeledValue(label: "CPU Cores", value: "\(cpu)")
                if isAppleSilicon {
                    LabeledValue(label: "GPU", value: "Metal ✓")
                }
            }
            Text("Models folder: \(LLMDownloadManager.shared.modelPath(for: llmCatalog[0]).deletingLastPathComponent().path)")
                .font(.caption2)
                .foregroundStyle(.secondary)
                .lineLimit(2)
        }
        .padding(16)
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private func activeModelBanner(_ model: LLMModel) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("Active LLM")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text(model.name)
                    .font(.subheadline.bold())
                    .foregroundStyle(.primary)
            }
            Spacer()
            Button("Use GBM Only") { dm.deactivate() }
                .font(.caption)
                .buttonStyle(.bordered)
        }
        .padding(16)
        .background(Color.blue.opacity(0.1))
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color.blue.opacity(0.3)))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

// MARK: - ModelCard

struct ModelCard: View {
    let model: LLMModel
    @ObservedObject var dm: LLMDownloadManager

    var body: some View {
        let compat = model.compatibility(totalRAMGB: dm.totalRAMGB)
        let isDownloaded = dm.isDownloaded(model)
        let isActive = dm.activeModelId == model.id
        let status = dm.downloadStatus[model.id]
        let progress = dm.downloadProgress[model.id] ?? 0

        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    HStack(spacing: 6) {
                        Text(model.name)
                            .font(.headline)
                            .foregroundStyle(.primary)
                        ForEach(model.tags, id: \.self) { tag in
                            Text(tag)
                                .font(.caption2)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.blue.opacity(0.15))
                                .foregroundStyle(.blue)
                                .clipShape(Capsule())
                        }
                    }
                    Text("\(String(format: "%.1f", model.paramsB))B params · \(model.quantization) · \(String(format: "%.1f", model.sizeGB)) GB · \(Int(model.ramMinGB)) GB RAM required")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text(model.description)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                compatBadge(compat)
            }

            if status == "downloading" {
                VStack(alignment: .leading, spacing: 4) {
                    ProgressView(value: progress)
                        .animation(.easeInOut(duration: 0.3), value: progress)
                    Text("\(Int(progress * 100))% downloaded")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }

            if status == "error" {
                Label("Download failed — check your connection and try again", systemImage: "exclamationmark.triangle.fill")
                    .font(.caption)
                    .foregroundStyle(.red)
            }

            if isDownloaded, let gb = dm.diskSizeGB(model) {
                Text(dm.modelPath(for: model).path)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
                Text(String(format: "On disk: %.2f GB", gb))
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }

            HStack(spacing: 8) {
                if status == "downloading" {
                    Text("Downloading…")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } else if !isDownloaded {
                    Button("Download \(String(format: "%.1f", model.sizeGB)) GB") {
                        dm.download(model)
                    }
                    .buttonStyle(.borderedProminent)
                } else if !isActive {
                    Button("Activate") { dm.activate(model) }
                        .buttonStyle(.borderedProminent)
                    Button("Clear") { dm.deleteModel(model) }
                        .buttonStyle(.bordered)
                        .tint(.red)
                } else {
                    Button("Deactivate") { dm.deactivate() }
                        .buttonStyle(.bordered)
                    Button("Clear from Disk") { dm.deleteModel(model) }
                        .buttonStyle(.bordered)
                        .tint(.red)
                }
            }
        }
        .padding(16)
        .background(Color(.systemGray6))
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(isActive ? Color.blue : Color.clear, lineWidth: 1.5)
        )
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private func compatBadge(_ compat: ModelCompatibility) -> some View {
        let color: Color = switch compat {
        case .compatible:   .green
        case .marginal:     Color(red: 0.72, green: 0.53, blue: 0.04)   // readable amber instead of .yellow
        case .insufficient: .red
        }
        return Text(compat.rawValue)
            .font(.caption2.bold())
            .foregroundStyle(color)
    }
}

// MARK: - LabeledValue

struct LabeledValue: View {
    let label: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label)
                .font(.caption2)
                .foregroundStyle(.secondary)
            Text(value)
                .font(.subheadline.bold())
                .foregroundStyle(.primary)
        }
    }
}
