import SwiftUI

struct SyncView: View {
    @EnvironmentObject var store: AppStore

    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                Spacer()

                Image(systemName: "arrow.triangle.2.circlepath")
                    .font(.system(size: 64))
                    .foregroundStyle(.blue)

                VStack(spacing: 8) {
                    Text("Data Sync")
                        .font(.title.bold())
                    Text("Download the latest market data and predictions from GitHub Releases. Works over WiFi or cellular.")
                        .multilineTextAlignment(.center)
                        .foregroundStyle(.secondary)
                        .padding(.horizontal)
                }

                statusView

                syncButton

                Spacer()

                Text("All data is stored locally on your device. No account required.")
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
            }
            .padding()
            .navigationTitle("Sync")
        }
    }

    @ViewBuilder
    private var statusView: some View {
        switch store.syncState {
        case .idle:
            Text("Tap Sync to fetch fresh data")
                .font(.subheadline)
                .foregroundStyle(.secondary)

        case .syncing:
            VStack(spacing: 12) {
                ProgressView()
                    .scaleEffect(1.2)
                Text("Syncing…")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

        case .done(let tag):
            Label("Updated to \(tag)", systemImage: "checkmark.circle.fill")
                .foregroundStyle(.green)

        case .failed(let msg):
            VStack(spacing: 4) {
                Label("Sync failed", systemImage: "xmark.circle.fill")
                    .foregroundStyle(.red)
                Text(msg)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
        }
    }

    private var syncButton: some View {
        Button(action: store.triggerSync) {
            Label("Sync Now", systemImage: "icloud.and.arrow.down")
                .font(.headline)
                .frame(maxWidth: .infinity)
                .padding()
        }
        .buttonStyle(.borderedProminent)
        .disabled(store.syncState == .syncing)
        .padding(.horizontal)
    }
}
