// Phase 3 — ONNX browser inference
// GradientBoosting classifier hosted at GitHub Releases.
// Input: (1, 9) float32 tensor "X" with 9 technical features.
// Output: (1, 2) float32 — [probDown, probUp].

import * as ort from 'onnxruntime-web';

const MODEL_URL =
  'https://github.com/bpupadhyaya/prediction/releases/download/v1.0.0/stock_predictor.onnx';

export interface OnnxFeatures {
  return_1d: number;
  return_5d: number;
  return_20d: number;
  ma5_ratio: number;
  ma20_ratio: number;
  ma50_ratio: number;
  volatility_20: number;
  volume_ratio: number;
  rsi: number;
}

export interface OnnxPrediction {
  probUp: number;
  probDown: number;
  direction: 'up' | 'down' | 'neutral';
  confidence: number;
}

// Module-level singleton — loaded once, reused.
let session: ort.InferenceSession | null = null;

/**
 * Download the ONNX model and create an InferenceSession.
 * Reports download progress via onProgress (0–100).
 */
export async function loadModel(onProgress?: (pct: number) => void): Promise<void> {
  if (session) return; // already loaded

  onProgress?.(0);

  const response = await fetch(MODEL_URL);
  if (!response.ok) {
    throw new Error(`Failed to fetch ONNX model: ${response.status} ${response.statusText}`);
  }

  const contentLength = response.headers.get('Content-Length');
  const total = contentLength ? parseInt(contentLength, 10) : 0;

  // Read body with progress tracking if Content-Length is known.
  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('Streaming response body not supported in this browser.');
  }

  const chunks: Uint8Array[] = [];
  let received = 0;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    if (value) {
      chunks.push(value);
      received += value.byteLength;
      if (total > 0) {
        onProgress?.(Math.min(99, Math.round((received / total) * 100)));
      }
    }
  }

  // Concatenate all chunks into a single ArrayBuffer.
  const buffer = new Uint8Array(received);
  let offset = 0;
  for (const chunk of chunks) {
    buffer.set(chunk, offset);
    offset += chunk.byteLength;
  }

  session = await ort.InferenceSession.create(buffer.buffer);
  onProgress?.(100);
}

/**
 * Run inference on a set of 9 technical features.
 * The model must be loaded first via loadModel().
 */
export async function predictOnnx(features: OnnxFeatures): Promise<OnnxPrediction> {
  if (!session) {
    throw new Error('ONNX model is not loaded. Call loadModel() first.');
  }

  // Features in the exact order the model expects.
  const data = new Float32Array([
    features.return_1d,
    features.return_5d,
    features.return_20d,
    features.ma5_ratio,
    features.ma20_ratio,
    features.ma50_ratio,
    features.volatility_20,
    features.volume_ratio,
    features.rsi,
  ]);

  const tensor = new ort.Tensor('float32', data, [1, 9]);
  const results = await session.run({ X: tensor });

  // Extract output — first output tensor contains [probDown, probUp].
  const outputKey = Object.keys(results)[0];
  const outputData = results[outputKey].data as Float32Array;
  const probDown = outputData[0];
  const probUp = outputData[1];

  const diff = Math.abs(probUp - probDown);
  const direction: 'up' | 'down' | 'neutral' =
    diff < 0.05 ? 'neutral' : probUp > probDown ? 'up' : 'down';
  const confidence = Math.round(Math.max(probUp, probDown) * 100);

  return {
    probUp: Math.round(probUp * 1000) / 10,    // one decimal percent
    probDown: Math.round(probDown * 1000) / 10,
    direction,
    confidence,
  };
}

/** Returns true if the model session is ready for inference. */
export function isModelLoaded(): boolean {
  return session !== null;
}
