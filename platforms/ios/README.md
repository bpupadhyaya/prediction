# iOS Platform — Stock Market Prediction

Fully offline SwiftUI app. After initial setup the app works without internet; optional GitHub Releases sync refreshes data and models.

## Requirements

- Xcode 15.2+
- iOS 17.0+ deployment target
- [XcodeGen](https://github.com/yonaskolb/XcodeGen) (`brew install xcodegen`)

## Build

```bash
cd platforms/ios
xcodegen generate          # creates StockPrediction.xcodeproj
open StockPrediction.xcodeproj
# Xcode resolves SPM packages (GRDB, OnnxRuntimeGenAI) automatically
# Select your team in Signing & Capabilities, then build and run
```

## Architecture

```
StockPrediction/
  App/             StockPredictionApp.swift  ContentView.swift  AppStore.swift
  Models/          Stock.swift  (Stock, PriceBar, Prediction, WatchlistEntry, PortfolioHolding)
  Database/        DatabaseManager.swift  (GRDB SQLite wrapper, migrations)
  Sync/            SyncManager.swift  (GitHub Releases → SQLite import)
  Prediction/      PredictionEngine.swift  (ONNX Runtime on-device inference)
  Views/           HomeView  SearchView  StockDetailView  PortfolioView  WatchlistView  SyncView
```

## Data flow

1. **First launch** — empty DB; prompt user to Sync.
2. **Sync** — downloads `market.sqlite.gz` from latest GitHub Release, decompresses, merges into local SQLite.
3. **Prediction** — `PredictionEngine` loads bundled `stock_predictor.onnx`; computes features from local prices; returns direction + probability.
4. **Daily background refresh** — if internet is available and app is in foreground, `SyncManager.sync()` is called.

## Publishing

Developers build and sign the app with their own Apple Developer account. The bundle ID is `com.prediction.stockmarket`; change it to match your team's reverse-domain. The project costs nothing beyond the standard Apple Developer Program fee ($99/year).
