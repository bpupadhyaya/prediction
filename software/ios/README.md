# Prediction — iOS

Top-level iOS app (`com.prediction.app`) that composes all prediction modules. Currently includes: Stock Market.

## Build

```bash
# 1. Generate Xcode project
xcodegen generate

# 2. Open in Xcode
open Prediction.xcodeproj

# 3. Or build from CLI
xcodebuild \
  -project Prediction.xcodeproj \
  -scheme Prediction \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' \
  build

# 4. Deploy to physical device
xcodebuild \
  -project Prediction.xcodeproj \
  -scheme Prediction \
  -destination 'id=<UDID>' \
  -allowProvisioningUpdates \
  build
```

## Architecture

This project compiles the Prediction home screen (module grid) plus all domain module sources via XcodeGen source references:

```
Prediction/App/PredictionApp.swift        — @main entry (com.prediction.app)
Prediction/App/Info.plist
Prediction/Resources/Assets.xcassets/     — AppIcon

# Linked sources (compiled in, not copied):
../../domains/finance/projects/stock-market/development/software/ios/StockPrediction/
  App/PredictionHomeView.swift            — home screen with module cards
  App/PredictionTheme.swift              — module definitions, colours
  Views/*, Database/*, Sync/*, …         — stock market screens & data layer
```

`StockPredictionApp.swift` is excluded — top-level provides its own `PredictionApp.swift`.

## Standalone Individual Projects

Each domain project also builds independently:
- Stock Market: `../../domains/finance/projects/stock-market/development/software/ios/`
