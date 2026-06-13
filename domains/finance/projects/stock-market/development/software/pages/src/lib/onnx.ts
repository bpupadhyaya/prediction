// Browser ONNX inference — the SAME 16-feature mobile model the iOS/Android apps
// bundle, running locally in the browser. One model per horizon (1d/1w/1m).
//
// Input : (1, 16) float32 tensor "input".
// Output: "probabilities" (1, 2) float32 — [probDown, probUp].

import * as ort from 'onnxruntime-web';

export type Horizon = '1d' | '1w' | '1m';

// Bundled with the site (public/). BASE_URL handles the GitHub Pages subpath.
const MODEL_FILES: Record<Horizon, string> = {
  '1d': 'stock_predictor_1d.onnx',
  '1w': 'stock_predictor.onnx',
  '1m': 'stock_predictor_1m.onnx',
};

function modelUrl(horizon: Horizon): string {
  const base = (import.meta as any).env?.BASE_URL || '/';
  return `${base}${MODEL_FILES[horizon]}`;
}

export interface OnnxPrediction {
  probUp: number;       // 0–100, one decimal
  probDown: number;
  direction: 'up' | 'down' | 'neutral';
  confidence: number;   // 0–100
}

// One cached InferenceSession per horizon.
const sessions: Partial<Record<Horizon, ort.InferenceSession>> = {};

export async function loadModel(
  horizon: Horizon = '1w',
  onProgress?: (pct: number) => void,
): Promise<void> {
  if (sessions[horizon]) return;
  onProgress?.(0);

  const response = await fetch(modelUrl(horizon));
  if (!response.ok) {
    throw new Error(`Failed to fetch model: ${response.status} ${response.statusText}`);
  }

  const total = parseInt(response.headers.get('Content-Length') || '0', 10);
  const reader = response.body?.getReader();
  if (!reader) {
    sessions[horizon] = await ort.InferenceSession.create(await response.arrayBuffer());
    onProgress?.(100);
    return;
  }

  const chunks: Uint8Array[] = [];
  let received = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    if (value) {
      chunks.push(value);
      received += value.byteLength;
      if (total > 0) onProgress?.(Math.min(99, Math.round((received / total) * 100)));
    }
  }
  const buffer = new Uint8Array(received);
  let offset = 0;
  for (const c of chunks) { buffer.set(c, offset); offset += c.byteLength; }

  sessions[horizon] = await ort.InferenceSession.create(buffer.buffer);
  onProgress?.(100);
}

/** Run the 16-feature model. `features` must be in MOBILE_FEATURES order. */
export async function predictOnnx(features: Float32Array, horizon: Horizon = '1w'): Promise<OnnxPrediction> {
  const session = sessions[horizon];
  if (!session) throw new Error(`Model for ${horizon} not loaded. Call loadModel() first.`);
  if (features.length !== 16) throw new Error(`Expected 16 features, got ${features.length}`);

  const tensor = new ort.Tensor('float32', features, [1, 16]);
  const results = await session.run({ input: tensor });

  const probsTensor = results['probabilities'] ?? results[Object.keys(results).slice(-1)[0]];
  const probs = probsTensor.data as Float32Array;
  const probDown = probs[0] ?? 0.5;
  const probUp = probs[1] ?? 0.5;

  const diff = Math.abs(probUp - probDown);
  const direction: 'up' | 'down' | 'neutral' =
    diff < 0.02 ? 'neutral' : probUp > probDown ? 'up' : 'down';

  return {
    probUp: Math.round(probUp * 1000) / 10,
    probDown: Math.round(probDown * 1000) / 10,
    direction,
    confidence: Math.round(Math.max(probUp, probDown) * 100),
  };
}

export function isModelLoaded(horizon: Horizon = '1w'): boolean {
  return !!sessions[horizon];
}
