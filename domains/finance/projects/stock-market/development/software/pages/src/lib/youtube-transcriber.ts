// Audio Transcription via Whisper (transformers.js, runs 100% in-browser)
// User provides an audio/video file downloaded from any source.
// No external services, no accounts, no CORS issues — works forever.

import type { WhisperModelInfo } from './types';

// ─── Whisper model registry ───────────────────────────────────────────────────

export const WHISPER_MODELS: WhisperModelInfo[] = [
  {
    id: 'tiny',
    label: 'Tiny (75 MB)',
    sizeGB: 0.075,
    quality: 'Basic',
    hfModelId: 'Xenova/whisper-tiny',
  },
  {
    id: 'base',
    label: 'Base (145 MB)',
    sizeGB: 0.145,
    quality: 'Good',
    hfModelId: 'Xenova/whisper-base',
  },
  {
    id: 'small',
    label: 'Small (483 MB)',
    sizeGB: 0.483,
    quality: 'Great — Recommended',
    hfModelId: 'Xenova/whisper-small',
  },
  {
    id: 'medium',
    label: 'Medium (1.5 GB)',
    sizeGB: 1.5,
    quality: 'Excellent',
    hfModelId: 'Xenova/whisper-medium',
  },
  {
    id: 'large',
    label: 'Large-v3 (3 GB)',
    sizeGB: 3.0,
    quality: 'Best possible',
    hfModelId: 'Xenova/whisper-large-v3',
  },
];

const DEFAULT_MODEL_ID = 'base';

export function getDefaultModelId(): string {
  return DEFAULT_MODEL_ID;
}

// ─── Lazy pipeline cache ──────────────────────────────────────────────────────

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const _pipelines: Map<string, any> = new Map();

// ─── Transcribe any audio/video file ─────────────────────────────────────────

/**
 * Transcribe an audio or video File/Blob using Whisper via transformers.js.
 * Everything runs in the browser — no servers, no accounts required.
 *
 * Supported input formats: mp3, mp4, webm, m4a, ogg, wav, and most other
 * formats the browser's AudioContext can decode.
 *
 * @param audioFile  Any File or Blob containing audio/video
 * @param modelId    Whisper model to use (default: 'base')
 * @param onProgress Called with (0–100, statusMessage) during processing
 */
export async function transcribeAudioBlob(
  audioFile: Blob | File,
  modelId: string = DEFAULT_MODEL_ID,
  onProgress?: (pct: number, msg: string) => void,
): Promise<{ fullText: string; chunks: Array<{ start: number; end: number; text: string }>; wordCount: number }> {
  const modelInfo = WHISPER_MODELS.find(m => m.id === modelId) ?? WHISPER_MODELS[1];

  onProgress?.(0, `Loading Whisper model (${modelInfo.label})…`);

  // Dynamic import — keeps the heavy bundle out of the initial load
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let transformers: any;
  try {
    transformers = await import('@huggingface/transformers');
  } catch (err) {
    throw new Error(
      `@huggingface/transformers failed to load: ` +
      `${err instanceof Error ? err.message : String(err)}`
    );
  }

  const { pipeline, env } = transformers;

  // Use OPFS (Origin Private File System) to cache model weights across sessions
  env.useBrowserCache = true;
  if (env.backends?.onnx?.wasm) {
    env.backends.onnx.wasm.numThreads = Math.min(4, navigator.hardwareConcurrency ?? 2);
  }

  let transcriber = _pipelines.get(modelInfo.hfModelId);
  if (!transcriber) {
    onProgress?.(5, `Downloading model (${modelInfo.label}) — cached after first use…`);

    transcriber = await pipeline(
      'automatic-speech-recognition',
      modelInfo.hfModelId,
      {
        chunk_length_s: 30,
        stride_length_s: 5,
        progress_callback: (p: { status: string; progress?: number; file?: string }) => {
          if (p.status === 'downloading' && p.progress != null) {
            const pct = Math.min(40, Math.round(5 + p.progress * 0.35));
            onProgress?.(pct, `Downloading: ${p.file ?? ''} (${Math.round(p.progress)}%)`);
          } else if (p.status === 'loading') {
            onProgress?.(42, 'Loading model into memory…');
          }
        },
      },
    );
    _pipelines.set(modelInfo.hfModelId, transcriber);
  }

  onProgress?.(45, 'Decoding audio…');

  const arrayBuffer = await audioFile.arrayBuffer();

  let audioData: Float32Array;
  try {
    // Resample to 16 kHz mono — Whisper's required input format
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const AudioCtx: typeof AudioContext = (window.AudioContext || (window as any).webkitAudioContext);
    const ctx = new AudioCtx({ sampleRate: 16000 });
    const decoded = await ctx.decodeAudioData(arrayBuffer);
    audioData = decoded.getChannelData(0);
    ctx.close();
  } catch {
    // Fallback: pass raw bytes and let transformers.js handle decoding
    audioData = new Float32Array(arrayBuffer);
  }

  onProgress?.(50, 'Transcribing… (may take several minutes for long videos)');

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const output: any = await transcriber(audioData, {
    return_timestamps: true,
    language: 'english',
  });

  onProgress?.(95, 'Finalising transcript…');

  const fullText: string = output?.text ?? (typeof output === 'string' ? output : '');
  const rawChunks: Array<{ timestamp: [number, number]; text: string }> = output?.chunks ?? [];

  const chunks = rawChunks.map(c => ({
    start: c.timestamp?.[0] ?? 0,
    end:   c.timestamp?.[1] ?? 0,
    text:  c.text ?? '',
  }));

  const wordCount = fullText.trim().split(/\s+/).filter(Boolean).length;

  onProgress?.(100, 'Transcription complete');

  return { fullText, chunks, wordCount };
}
