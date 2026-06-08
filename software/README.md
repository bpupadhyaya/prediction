# Prediction — Top-Level Software Project

The **Prediction** umbrella app bundles all domain-specific prediction modules into a single installable app per platform. Each module (Stock Market, Sports, Weather, …) is independently developed in its own domain project and composed here.

## Structure

```
software/
├── ios/        — Prediction iOS app (Xcode, SwiftUI)   bundle: com.prediction.app
├── android/    — Prediction Android app (Jetpack Compose) package: com.prediction.app
├── desktop/    — Prediction desktop aggregator (Python + web UI)
├── install.sh  — Mac/Linux: install all desktop modules
├── install.bat — Windows: install all desktop modules
└── uninstall.sh / uninstall.bat
```

Individual prediction projects live under `../domains/<domain>/projects/<project>/development/software/` and are self-contained — each can be built and deployed independently.

---

## Mobile (iOS & Android)

Mobile apps are distributed through app stores. End-users install a single **Prediction** app and get all modules.

**iOS**
- App Store: search **"Prediction"** by Bhim Upadhyaya *(link added after first submission)*
- Bundle ID: `com.prediction.app`
- Min iOS: 17.0

**Android**
- Google Play: search **"Prediction"** by Bhim Upadhyaya *(link added after first submission)*
- Application ID: `com.prediction.app`
- Min SDK: 26 (Android 8.0)

### Build iOS (developers)

Requirements: Xcode 15+, [XcodeGen](https://github.com/yonaskolb/XcodeGen)

```bash
cd ios
xcodegen generate
open Prediction.xcodeproj
# Build & Run in Xcode, or:
xcodebuild -project Prediction.xcodeproj -scheme Prediction -destination 'platform=iOS Simulator,name=iPhone 17 Pro' build
```

### Build Android (developers)

Requirements: Android Studio / JDK 17+, Android SDK 34

```bash
cd android
./gradlew assembleDebug
# Install on connected device/emulator:
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

---

## Desktop (Mac / Linux / Windows)

The desktop app runs a local Python backend + web frontend. Each prediction module installs into its own virtual environment.

### Mac / Linux

```bash
# Install all modules:
./install.sh

# Install without downloading market data (faster, for dev):
./install.sh --skip-data

# Launch:
./desktop/start.sh

# Remove everything:
./uninstall.sh
```

### Windows

```bat
REM Install all modules:
install.bat

REM Launch:
desktop\start.bat

REM Remove:
uninstall.bat
```

Requirements: Python 3.10–3.12, Node.js 18+. The install script auto-installs Homebrew Python on Mac if needed.

---

## Individual Module Install

Each domain project has its own install script for standalone deployment:

| Module        | Install script                                                            |
|---------------|---------------------------------------------------------------------------|
| Stock Market  | `../domains/finance/projects/stock-market/development/software/desktop/install.sh` |

To install only Stock Market:
```bash
cd ../domains/finance/projects/stock-market/development/software/desktop
./install.sh
```

---

## Adding a New Module

1. Create the domain project at `../domains/<domain>/projects/<name>/development/software/`
2. **iOS**: add the source path to `ios/project.yml` under `targets.Prediction.sources`
3. **Android**: the new module's java sources are auto-included via `sourceSets` in `android/app/build.gradle.kts` — add an additional srcDir entry
4. **Desktop**: add a call to the new project's `install.sh` in `desktop/install.sh`
5. Enable the module card in the shared `predictionModules` list (`../domains/finance/.../ios/StockPrediction/App/PredictionTheme.swift` and the equivalent `PredictionTheme.kt`)
