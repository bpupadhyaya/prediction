// Browser ONNX inference — the SAME 16-feature mobile model the iOS/Android apps
// bundle, running locally in the browser. One model per horizon (1d/1w/1m).
//
// Input : (1, 16) float32 tensor "input".
// Output: "probabilities" (1, 2) float32 — [probDown, probUp].
//
// Alongside the model we load mobile_model_meta.json (the SAME sidecar the mobile
// apps bundle): it carries the honest out-of-sample accuracy, a probability
// calibration map, and per-feature baselines used for on-device explanations.

import * as ort from 'onnxruntime-web';

export type Horizon = '1d' | '1w' | '1m';

// Bundled with the site (public/). BASE_URL handles the GitHub Pages subpath.
const MODEL_FILES: Record<Horizon, string> = {
  '1d': 'stock_predictor_1d.onnx',
  '1w': 'stock_predictor.onnx',
  '1m': 'stock_predictor_1m.onnx',
};

// 16 features in MOBILE_FEATURES order + human labels for explanations.
export const FEATURE_NAMES = [
  'return_1d', 'return_5d', 'return_20d', 'return_60d', 'return_126d', 'return_252d',
  'ma_5', 'ma_20', 'ma_50', 'ma_200',
  'volatility_20', 'volatility_60',
  'volume_ratio', 'dollar_volume_turnover',
  'rsi', 'high_52w_ratio',
] as const;

export const FEATURE_LABELS: Record<string, string> = {
  return_1d: '1-day momentum', return_5d: '1-week momentum', return_20d: '1-month momentum',
  return_60d: '3-month momentum', return_126d: '6-month momentum', return_252d: '12-month momentum',
  ma_5: 'Price vs 5-day avg', ma_20: 'Price vs 20-day avg', ma_50: 'Price vs 50-day avg',
  ma_200: 'Price vs 200-day avg', volatility_20: '20-day volatility', volatility_60: '60-day volatility',
  volume_ratio: 'Volume vs average', dollar_volume_turnover: 'Dollar-volume turnover',
  rsi: 'RSI (momentum)', high_52w_ratio: 'Proximity to 52-week high',
};

function modelUrl(horizon: Horizon): string {
  const base = (import.meta as any).env?.BASE_URL || '/';
  return `${base}${MODEL_FILES[horizon]}`;
}

export interface OnnxPrediction {
  probUp: number;       // 0–100, one decimal (CALIBRATED)
  probDown: number;
  direction: 'up' | 'down' | 'neutral';
  confidence: number;   // 0–100
  accuracy: number;     // honest out-of-sample directional accuracy, 0–100
}

export interface FeatureContribution {
  feature: string;
  label: string;
  value: number;
  delta: number;        // change in P(up) when this feature is set to its baseline
  pushesUp: boolean;
}

// One cached InferenceSession per horizon.
const sessions: Partial<Record<Horizon, ort.InferenceSession>> = {};

// ── Model metadata (calibration + accuracy + baselines) ────────────────────
interface HorizonMeta {
  backtest_accuracy: number;
  calibration: { w: number; b: number };
}
interface ModelMeta {
  features: string[];
  baselines: Record<string, number>;
  horizons: Record<string, HorizonMeta>;
}
let metaPromise: Promise<ModelMeta | null> | null = null;

function metaUrl(): string {
  const base = (import.meta as any).env?.BASE_URL || '/';
  return `${base}mobile_model_meta.json`;
}

/** Load the bundled metadata once. Returns null if absent (callers degrade gracefully). */
export async function loadMeta(): Promise<ModelMeta | null> {
  if (!metaPromise) {
    metaPromise = (async () => {
      try {
        const resp = await fetch(metaUrl());
        if (!resp.ok) return null;
        return (await resp.json()) as ModelMeta;
      } catch {
        return null;
      }
    })();
  }
  return metaPromise;
}

const sigmoid = (z: number) => 1 / (1 + Math.exp(-z));

/** Map a raw model probability to an honest, calibrated one: sigmoid(w*p + b). */
function calibrate(rawProbUp: number, meta: ModelMeta | null, horizon: Horizon): number {
  const c = meta?.horizons?.[horizon]?.calibration;
  if (!c) return rawProbUp;
  return sigmoid(c.w * rawProbUp + c.b);
}

export async function loadModel(
  horizon: Horizon = '1w',
  onProgress?: (pct: number) => void,
): Promise<void> {
  loadMeta();   // kick off metadata fetch in parallel (cheap, cached)
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

/** Raw P(up) straight from the ONNX graph (uncalibrated). */
async function rawProbUp(features: Float32Array, horizon: Horizon): Promise<number> {
  const session = sessions[horizon];
  if (!session) throw new Error(`Model for ${horizon} not loaded. Call loadModel() first.`);
  if (features.length !== 16) throw new Error(`Expected 16 features, got ${features.length}`);

  const tensor = new ort.Tensor('float32', features, [1, 16]);
  const results = await session.run({ input: tensor });
  const probsTensor = results['probabilities'] ?? results[Object.keys(results).slice(-1)[0]];
  const probs = probsTensor.data as Float32Array;
  return probs[1] ?? 0.5;
}

/** Run the 16-feature model and return a CALIBRATED prediction. */
export async function predictOnnx(features: Float32Array, horizon: Horizon = '1w'): Promise<OnnxPrediction> {
  const meta = await loadMeta();
  const raw = await rawProbUp(features, horizon);
  const probUp = calibrate(raw, meta, horizon);
  const probDown = 1 - probUp;

  const diff = Math.abs(probUp - probDown);
  const direction: 'up' | 'down' | 'neutral' =
    diff < 0.02 ? 'neutral' : probUp > probDown ? 'up' : 'down';

  const acc = meta?.horizons?.[horizon]?.backtest_accuracy;
  return {
    probUp: Math.round(probUp * 1000) / 10,
    probDown: Math.round(probDown * 1000) / 10,
    direction,
    confidence: Math.round(Math.max(probUp, probDown) * 100),
    accuracy: acc != null ? Math.round(acc * 1000) / 10 : 0,
  };
}

/**
 * Explain a prediction by perturbation: for each feature, set it to its training
 * baseline, re-run the (calibrated) model, and record how much P(up) moved. The
 * signed change is that feature's local contribution. Returns the strongest
 * contributors first. 16 extra single-row inferences — cheap for this tiny model.
 */
export async function explainOnnx(
  features: Float32Array,
  horizon: Horizon = '1w',
  topN = 4,
): Promise<FeatureContribution[]> {
  const meta = await loadMeta();
  if (!meta?.baselines) return [];
  const base = calibrate(await rawProbUp(features, horizon), meta, horizon);

  const contribs: FeatureContribution[] = [];
  for (let i = 0; i < FEATURE_NAMES.length; i++) {
    const name = FEATURE_NAMES[i];
    const baseline = meta.baselines[name];
    if (baseline == null) continue;
    const perturbed = Float32Array.from(features);
    perturbed[i] = baseline;
    const p = calibrate(await rawProbUp(perturbed, horizon), meta, horizon);
    const delta = base - p;   // how much THIS feature's actual value moved P(up)
    contribs.push({
      feature: name,
      label: FEATURE_LABELS[name] ?? name,
      value: features[i],
      delta,
      pushesUp: delta >= 0,
    });
  }
  contribs.sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
  return contribs.slice(0, topN);
}

/** Plain-English one-liner from the top contributors. */
export function rationale(direction: 'up' | 'down' | 'neutral', contribs: FeatureContribution[]): string {
  if (contribs.length === 0) return '';
  const dirWord = direction === 'up' ? 'UP' : direction === 'down' ? 'DOWN' : 'flat';
  const supporting = contribs.filter((c) => c.pushesUp === (direction === 'up'));
  const opposing = contribs.filter((c) => c.pushesUp !== (direction === 'up'));
  const top = supporting.slice(0, 2).map((c) => c.label.toLowerCase());
  let s = top.length
    ? `Leaning ${dirWord} mainly because ${top.join(' and ')} ${top.length > 1 ? 'are' : 'is'} favorable`
    : `Leaning ${dirWord}`;
  if (opposing.length) s += `, partly offset by ${opposing[0].label.toLowerCase()}`;
  return s + '.';
}

export function isModelLoaded(horizon: Horizon = '1w'): boolean {
  return !!sessions[horizon];
}
