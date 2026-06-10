#!/bin/bash
# Build and archive iOS app for App Store submission
set -e

SCHEME="StockPrediction"
WORKSPACE="StockPrediction.xcodeproj"
ARCHIVE_PATH="./build/StockPrediction.xcarchive"
EXPORT_PATH="./build/StockPredictionIPA"

echo "Generating Xcode project from project.yml..."
xcodegen generate

echo "Archiving..."
xcodebuild archive \
  -project "$WORKSPACE" \
  -scheme "$SCHEME" \
  -archivePath "$ARCHIVE_PATH" \
  -destination "generic/platform=iOS" \
  CODE_SIGN_STYLE=Automatic \
  DEVELOPMENT_TEAM=XDC8C9HH9K

echo "Exporting IPA..."
xcodebuild -exportArchive \
  -archivePath "$ARCHIVE_PATH" \
  -exportPath "$EXPORT_PATH" \
  -exportOptionsPlist ExportOptions.plist

echo "Done! IPA at $EXPORT_PATH"
echo "Upload to App Store Connect via: xcrun altool or Transporter app"
