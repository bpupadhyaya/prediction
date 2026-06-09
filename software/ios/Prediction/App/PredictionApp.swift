import SwiftUI

@main
struct PredictionApp: App {
    @StateObject private var store = AppStore()

    var body: some Scene {
        WindowGroup {
            PredictionMainTabView()
                .environmentObject(store)
                .preferredColorScheme(.dark)
                .task { await store.initialise() }
        }
    }
}
