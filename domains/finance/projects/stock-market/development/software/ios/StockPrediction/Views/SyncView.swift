import SwiftUI

struct SyncView: View {
    @EnvironmentObject var store: AppStore

    @State private var selectedSource: MarketDataSourceType = MarketDataSettings.activeSource
    @State private var apiKey: String = ""
    @State private var isSyncing: Bool = false
    @State private var syncProgress: String = ""
    @State private var syncResult: String = ""
    @State private var syncFailed: Bool = false
    @State private var tickersDone: Int = 0
    @State private var tickersTotal: Int = 0
    @State private var lastSynced: Date? = UserDefaults.standard.object(forKey: "last_sync_date") as? Date

    var body: some View {
        NavigationStack {
            List {
                // MARK: Data Source Section
                Section {
                    Picker("Data Source", selection: $selectedSource) {
                        ForEach(MarketDataSourceType.allCases, id: \.self) { source in
                            Text(source.rawValue).tag(source)
                        }
                    }
                    .pickerStyle(.menu)
                    .onChange(of: selectedSource) { _, newValue in
                        MarketDataSettings.activeSource = newValue
                        apiKey = MarketDataSettings.apiKey(for: newValue)
                        syncResult = ""
                        syncFailed = false
                    }

                    Text(selectedSource.description)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } header: {
                    Text("Market Data Source")
                } footer: {
                    Text("Yahoo Finance is the default — no setup required.")
                }

                // MARK: API Key Section (only when needed)
                if selectedSource.requiresAPIKey {
                    Section {
                        SecureField("Paste API key here", text: $apiKey)
                            .autocorrectionDisabled()
                            .textInputAutocapitalization(.never)
                            .onChange(of: apiKey) { _, newValue in
                                MarketDataSettings.setAPIKey(newValue, for: selectedSource)
                            }
                    } header: {
                        Text("API Key")
                    } footer: {
                        Text(selectedSource.keyHint)
                    }
                }

                // MARK: Sync Status Section
                Section {
                    if isSyncing {
                        VStack(alignment: .leading, spacing: 8) {
                            HStack(spacing: 10) {
                                ProgressView()
                                    .scaleEffect(0.85)
                                Text(syncProgress.isEmpty ? "Starting sync…" : syncProgress)
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                            }
                            if tickersTotal > 0 {
                                ProgressView(value: Double(tickersDone), total: Double(tickersTotal))
                                    .tint(.blue)
                                    .animation(.easeInOut(duration: 0.3), value: tickersDone)
                                Text("\(tickersDone) of \(tickersTotal) tickers")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        .padding(.vertical, 4)
                    } else if syncFailed {
                        Label(syncResult, systemImage: "xmark.circle.fill")
                            .foregroundStyle(.red)
                            .font(.subheadline)
                    } else if !syncResult.isEmpty {
                        Label(syncResult, systemImage: "checkmark.circle.fill")
                            .foregroundStyle(.green)
                            .font(.subheadline)
                    } else {
                        Text("Tap Sync Now to fetch live market data directly from the selected source.")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }

                    if let date = lastSynced {
                        HStack {
                            Image(systemName: "clock")
                                .foregroundStyle(.secondary)
                                .font(.caption)
                            Text("Last synced: \(date.formatted(date: .abbreviated, time: .shortened))")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                } header: {
                    Text("Status")
                }

                // MARK: Sync Button Section
                Section {
                    Button(action: startSync) {
                        HStack {
                            Spacer()
                            if isSyncing {
                                ProgressView()
                                    .scaleEffect(0.85)
                                    .padding(.trailing, 6)
                                Text("Syncing…")
                                    .font(.headline)
                            } else {
                                Label("Sync Now", systemImage: "icloud.and.arrow.down")
                                    .font(.headline)
                            }
                            Spacer()
                        }
                    }
                    .disabled(isSyncing)
                } footer: {
                    Text("Data is fetched for ~60 hot stocks + top 50 S&P 500 constituents and stored locally. No account required.")
                        .multilineTextAlignment(.center)
                }
            }
            .navigationTitle("Sync")
            .navigationBarTitleDisplayMode(.large)
            .onAppear {
                apiKey = MarketDataSettings.apiKey(for: selectedSource)
            }
        }
    }

    private func startSync() {
        guard !isSyncing else { return }
        isSyncing = true
        syncResult = ""
        syncFailed = false
        tickersDone = 0
        tickersTotal = 0

        Task {
            do {
                let result = try await SyncManager.shared.sync { done, total, ticker in
                    Task { @MainActor in
                        tickersDone = done
                        tickersTotal = total
                        if ticker.isEmpty {
                            syncProgress = "Finalizing…"
                        } else {
                            syncProgress = "Syncing \(ticker)… (\(done + 1)/\(total))"
                        }
                    }
                }
                await MainActor.run {
                    isSyncing = false
                    syncResult = result
                    syncFailed = false
                    lastSynced = Date()
                    UserDefaults.standard.set(lastSynced, forKey: "last_sync_date")
                    store.loadLocal()
                }
            } catch {
                await MainActor.run {
                    isSyncing = false
                    syncResult = error.localizedDescription
                    syncFailed = true
                }
            }
        }
    }
}
