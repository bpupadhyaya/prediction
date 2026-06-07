# Android Platform — Stock Market Prediction

Fully offline Jetpack Compose app. Works without internet after first sync; optional GitHub Releases sync refreshes data and predictions.

## Requirements

- Android Studio Hedgehog (2023.1.1) or later
- JDK 17
- Android SDK 34 (minSdk 26 = Android 8.0+)

## Build

```bash
cd platforms/android
# Open in Android Studio, or:
./gradlew assembleDebug          # debug APK
./gradlew assembleRelease        # release APK (set up signing first)
```

## Architecture

```
MVVM + Hilt dependency injection + Room database + ONNX Runtime

com.prediction.stockmarket/
  data/
    database/   AppDatabase.kt  Entities.kt  Daos.kt  (Room + SQLite)
    sync/       SyncManager.kt  (GitHub Releases → SQLite import)
    repository/ StockRepository.kt
  prediction/   PredictionEngine.kt  (ONNX Runtime on-device inference)
  ui/
    home/       HomeScreen + HomeViewModel
    stock/      StockDetailScreen + StockDetailViewModel + SearchScreen + SearchViewModel
    portfolio/  PortfolioScreen + PortfolioViewModel
    watchlist/  WatchlistScreen + WatchlistViewModel
    sync/       SyncScreen + SyncViewModel
    theme/      Theme.kt  (dark Material3)
  di/           AppModule.kt  (Hilt module)
  MainActivity.kt  StockPredictionApp.kt  AppNavigation.kt
```

## Data flow

1. **First launch** — empty Room DB; user taps Sync.
2. **Sync** — `SyncManager` fetches latest GitHub Release, downloads `market.sqlite.gz`, decompresses to temp file, imports into Room.
3. **Prediction** — `PredictionEngine` loads `stock_predictor.onnx` from `assets/`; builds features from Room price data; runs ONNX inference; upserts result.
4. **Model update** — bundled ONNX model is updated with each GitHub Release tag.

## Publishing

Developers build and sign with their own Google Play Developer account. Change `applicationId` in `app/build.gradle.kts` from `com.prediction.stockmarket` to your own reverse-domain. The Play Developer Program fee is $25 one-time.
