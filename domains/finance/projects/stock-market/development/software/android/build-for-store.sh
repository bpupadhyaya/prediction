#!/bin/bash
# Build Android App Bundle for Play Store submission
set -e

echo "Building release AAB..."
./gradlew bundleRelease

echo "Sign the AAB with your keystore:"
echo "  jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 \\"
echo "    -keystore your-keystore.jks \\"
echo "    app/build/outputs/bundle/release/app-release.aab \\"
echo "    your-key-alias"
echo ""
echo "Then upload app/build/outputs/bundle/release/app-release.aab to Google Play Console"
