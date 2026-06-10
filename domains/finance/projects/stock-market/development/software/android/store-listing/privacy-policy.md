# Privacy Policy — Stock Prediction — AI Predictor (Android)

**Effective Date:** June 9, 2026
**App:** Stock Prediction — AI Predictor
**Developer:** Bhim Upadhyaya
**Contact:** bpupadhyaya5@gmail.com
**Privacy Policy URL:** https://bpupadhyaya.github.io/prediction/stock-prediction/privacy

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
- Contacts, calendar, photos, or media
- Device identifiers (Android Advertising ID or similar)
- Usage analytics or behavioral telemetry
- Crash reports or diagnostics sent to external servers
- IP addresses or network identifiers

---

## On-Device Processing

All computation performed by this app happens locally on your device:

- **Parameter prediction engine**: Score aggregation runs in-process using only local data you enter.
- **LLM research assistant**: Language model weights (Phi-3.5 Mini, Gemma 2, Llama 3.2) are downloaded once and then run entirely on-device. Your questions are never sent to any server.
- **ONNX prediction model**: The GradientBoosting classifier runs via the on-device ONNX Runtime library. No data is transmitted during inference.
- **Snapshot storage**: Saved snapshots are stored in your device's local storage. Data never goes to our servers.

---

## Network Access

The app requests INTERNET permission solely to download optional LLM model weights when you choose to install them. These are downloaded from public model repositories. We do not log, track, or store any information about these downloads.

No user data, parameter inputs, or prediction results are ever sent over the network.

---

## Permissions

| Permission | Reason |
|---|---|
| INTERNET | Download optional on-device LLM model weights only |
| READ_EXTERNAL_STORAGE / WRITE_EXTERNAL_STORAGE (Android < 10) | Export snapshots to Downloads folder |

No other permissions are requested.

---

## Children's Privacy

This app is rated Everyone on Google Play. Because we collect no data from any user, we do not collect data from children under 13.

---

## Third-Party SDKs

This app does not include any third-party analytics, advertising, or tracking SDKs. The only third-party libraries used are local inference runtimes (ONNX Runtime, llama.cpp bindings) that perform no network communication.

---

## Changes to This Policy

If this Privacy Policy changes, the updated version will be published at the URL above and the effective date will be updated. Because we collect no data, changes will be rare.

---

## Contact

Questions about this privacy policy:

**Bhim Upadhyaya**
bpupadhyaya5@gmail.com
https://bpupadhyaya.github.io/prediction/stock-prediction/
