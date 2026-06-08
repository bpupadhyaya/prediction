# Prediction — Android

Top-level Android app (`com.prediction.app`) composing all prediction modules. Currently includes: Stock Market.

## Build

```bash
./gradlew assembleDebug

# Install on emulator
adb install -r app/build/outputs/apk/debug/app-debug.apk

# Install on physical device (transport_id)
adb -t <transport_id> install -r app/build/outputs/apk/debug/app-debug.apk

# Launch
adb shell am start -n com.prediction.app/.MainActivity
```

## Architecture

The `app` module includes the stock-market source via an additional `srcDir` in `build.gradle.kts`:

```
app/src/main/java/com/prediction/app/
  PredictionApp.kt        — @HiltAndroidApp Application class
  MainActivity.kt         — shows PredictionHomeScreen; navigates into modules

# Linked sources (additional srcDir, not copied):
../../domains/finance/projects/stock-market/development/software/android/app/src/main/java/
  com/prediction/stockmarket/ui/prediction/PredictionHomeScreen.kt
  com/prediction/stockmarket/ui/prediction/PredictionTheme.kt
  com/prediction/stockmarket/ui/…   — all stock market screens
  com/prediction/stockmarket/data/… — data layer (Room, sync)
```

`StockPredictionApp.kt` and `MainActivity.kt` from stock-market are excluded via `java { exclude(…) }` — top-level provides its own Application and Activity.

## Standalone Individual Projects

- Stock Market: `../../domains/finance/projects/stock-market/development/software/android/`
