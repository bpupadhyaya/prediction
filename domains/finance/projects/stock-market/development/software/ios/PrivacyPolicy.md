# Privacy Policy — Stock Prediction — AI Predictor

**Effective Date:** June 9, 2026
**App:** Stock Prediction — AI Predictor
**Developer:** Bhim Upadhyaya
**Contact:** bpupadhyaya5@gmail.com

---

## Summary

Stock Prediction — AI Predictor does not collect, transmit, store, or share any personal data. All features — including the 656-parameter prediction engine, the on-device LLM research assistant, and the ONNX automated prediction model — operate entirely on your device.

---

## Data We Do Not Collect

We do not collect:

- Personal identification information (name, email, phone number, address)
- Financial information (brokerage accounts, portfolio data, transaction history)
- Location data (precise or approximate)
- Health or biometric data
- Contacts, calendar, or photos
- Device identifiers (IDFA, IDFV, or similar)
- Usage analytics or behavioral data
- Crash reports or diagnostics sent to external servers
- IP addresses or network identifiers

---

## On-Device Processing

All computation performed by this app happens locally on your device:

- **Parameter prediction engine**: Calculations and score aggregation run in-process.
- **LLM research assistant**: Language models (Phi-3.5 Mini, Gemma 2, Llama 3.2) are downloaded once and then run entirely on-device using Apple's Core ML / Metal stack. Your questions are never sent to any server.
- **ONNX prediction model**: The GradientBoosting classifier runs via on-device ONNX runtime. No data is transmitted during inference.
- **Snapshot storage**: Saved snapshots are stored in your device's local storage (or iCloud if you have iCloud Drive enabled for the app). Data never goes to our servers.

---

## Network Access

The app may access the internet solely to download optional LLM model weights when you choose to install them. These downloads are from public model repositories (e.g., Hugging Face). We do not log, track, or store any information about these downloads.

No user data, parameter inputs, or prediction results are ever sent over the network.

---

## iCloud / CloudKit

If you enable iCloud backup on your device, iOS may back up app data (such as snapshots) to your personal iCloud account. This backup is governed by Apple's iCloud Terms of Service and Privacy Policy. We have no access to any iCloud data.

---

## Children's Privacy

This app is rated 4+ and does not target children. Because we collect no data from any user, we do not collect data from children under 13 either.

---

## Third-Party SDKs

This app does not include any third-party analytics, advertising, or tracking SDKs.

---

## Changes to This Policy

If this Privacy Policy changes, the updated version will be published at the Support URL below and the effective date will be updated. Because we collect no data, changes will be rare.

---

## Contact

Questions about this privacy policy:

**Bhim Upadhyaya**
bpupadhyaya5@gmail.com
https://bpupadhyaya.github.io/prediction/stock-prediction/
