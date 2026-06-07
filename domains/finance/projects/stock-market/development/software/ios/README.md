# iOS Platform — Stock Market Prediction

Fully offline SwiftUI app. After initial setup the app works without internet; optional GitHub Releases sync refreshes data and models.

## System Requirements

### Device (end user)

| Resource | Minimum | Notes |
|----------|---------|-------|
| **Device** | iPhone X / iPad (6th gen) or newer | A12 Bionic chip or newer recommended for fast ONNX inference |
| **iOS** | 17.0+ | — |
| **RAM** | 2 GB device RAM | Typical modern iPhone — ONNX model loaded into memory at runtime |
| **Storage** | 150 MB free | ~50 MB app + bundled ONNX model; ~100 MB SQLite database after first sync |
| **Network** | Optional | Required only for initial Sync; all predictions run fully on-device |

### Developer (build environment)

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **Mac RAM** | 8 GB | 16 GB — Xcode + simulator |
| **Mac Disk** | 15 GB free | 20 GB — Xcode, iOS SDKs, simulators |
| **Xcode** | 15.2 | latest stable |
| **macOS** | 14.0 (Sonoma) | — |
| **XcodeGen** | any | `brew install xcodegen` |

## Software Requirements

- Xcode 15.2+
- iOS 17.0+ deployment target
- [XcodeGen](https://github.com/yonaskolb/XcodeGen) (`brew install xcodegen`)

## Build

```bash
cd domains/finance/projects/stock-market/development/software/ios
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
