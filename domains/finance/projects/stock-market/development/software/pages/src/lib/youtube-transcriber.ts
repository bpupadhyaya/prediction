// YouTube Audio Extraction + Whisper Transcription
// Audio download requires a user-deployed Cloudflare Worker (CF CORS proxy).
// Transcription uses @huggingface/transformers (Whisper ONNX, runs in-browser).

import type { WhisperModelInfo } from './types';
import { getVideoSetting } from './video-intelligence-store';

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

// Default model when no preference is stored
const DEFAULT_MODEL_ID = 'base';

export function getActiveModel(): string {
  return DEFAULT_MODEL_ID;
}

// ─── Cloudflare Worker template ───────────────────────────────────────────────

export const CF_WORKER_TEMPLATE = `// Cloudflare Worker — YouTube Audio Proxy
// Deploy at: https://workers.cloudflare.com/
// Free tier: 100,000 req/day, no cost
export default {
  async fetch(request) {
    const url = new URL(request.url);
    const ytUrl = url.searchParams.get('url');
    if (!ytUrl) return new Response('Missing url param', { status: 400 });

    // Validate it's a YouTube URL
    if (!ytUrl.includes('youtube.com') && !ytUrl.includes('youtu.be')) {
      return new Response('Only YouTube URLs allowed', { status: 400 });
    }

    // Fetch YouTube page to find audio stream URL
    const pageRes = await fetch(ytUrl, {
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible)' }
    });
    const html = await pageRes.text();

    // Extract ytInitialPlayerResponse
    const match = html.match(/ytInitialPlayerResponse\\s*=\\s*({.+?});/);
    if (!match) return new Response('Could not parse YouTube page', { status: 500 });

    const playerResponse = JSON.parse(match[1]);
    const formats = playerResponse?.streamingData?.adaptiveFormats || [];
    const audioFormat = formats.find(f => f.mimeType?.includes('audio/webm') || f.mimeType?.includes('audio/mp4'));

    if (!audioFormat?.url) return new Response('No audio stream found', { status: 500 });

    // Proxy the audio stream
    const audioRes = await fetch(audioFormat.url);
    return new Response(audioRes.body, {
      headers: {
        'Content-Type': audioFormat.mimeType || 'audio/webm',
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'public, max-age=3600',
      }
    });
  }
};`;

// ─── YouTube audio fetching ───────────────────────────────────────────────────

/**
 * Download audio from a YouTube URL via the user's Cloudflare Worker proxy.
 * Throws a descriptive error if no CF Worker URL is configured.
 */
export async function fetchYouTubeAudio(youtubeUrl: string): Promise<Blob> {
  const cfWorkerUrl = await getVideoSetting('cfWorkerUrl');

  if (!cfWorkerUrl) {
    throw new Error(
      'Cloudflare Worker not configured.\n\n' +
      'YouTube audio cannot be fetched directly from the browser due to CORS restrictions. ' +
      'You need to deploy the included Cloudflare Worker script (free, ~30 lines) to proxy ' +
      'the audio stream. See the "Cloudflare Worker Setup" section in the Intelligence tab, ' +
      'deploy it at workers.cloudflare.com, then paste your Worker URL in the settings field.'
    );
  }

  const proxyUrl = `${cfWorkerUrl.replace(/\/$/, '')}?url=${encodeURIComponent(youtubeUrl)}`;

  let response: Response;
  try {
    response = await fetch(proxyUrl);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    throw new Error(`Failed to reach Cloudflare Worker at "${cfWorkerUrl}": ${msg}`);
  }

  if (!response.ok) {
    const body = await response.text().catch(() => '');
    throw new Error(
      `Cloudflare Worker returned HTTP ${response.status}` +
      (body ? `: ${body}` : '') +
      `. Check your Worker URL and that the Worker is deployed correctly.`
    );
  }

  return response.blob();
}

// ─── Whisper transcription ────────────────────────────────────────────────────

// Lazy-loaded pipeline cache: modelId → pipeline instance
// We use `any` here because @huggingface/transformers types are deep/conditional.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const _pipelines: Map<string, any> = new Map();

/**
 * Transcribe an audio Blob using Whisper (via transformers.js ONNX in-browser).
 *
 * @param audioBlob  Audio data (webm, mp4, wav, etc.)
 * @param modelId    One of the WHISPER_MODELS ids (default: 'base')
 * @param onProgress Called with 0–100 and a status message
 */
export async function transcribeAudioBlob(
  audioBlob: Blob,
  modelId: string = DEFAULT_MODEL_ID,
  onProgress?: (pct: number, msg: string) => void,
): Promise<{ fullText: string; chunks: Array<{ start: number; end: number; text: string }>; wordCount: number }> {
  const modelInfo = WHISPER_MODELS.find(m => m.id === modelId) ?? WHISPER_MODELS[1];

  onProgress?.(0, `Loading Whisper model (${modelInfo.label})…`);

  // Dynamic import so the heavy transformers.js bundle is only pulled in when needed
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let transformers: any;
  try {
    transformers = await import('@huggingface/transformers');
  } catch (err) {
    throw new Error(
      `@huggingface/transformers could not be loaded. ` +
      `Ensure it is installed (npm install @huggingface/transformers). ` +
      `Original error: ${err instanceof Error ? err.message : String(err)}`
    );
  }

  const { pipeline, env } = transformers;

  // Configure OPFS caching and WASM threads
  env.useBrowserCache = true;
  if (env.backends?.onnx?.wasm) {
    env.backends.onnx.wasm.numThreads = 4;
  }

  let transcriber = _pipelines.get(modelInfo.hfModelId);
  if (!transcriber) {
    onProgress?.(5, `Downloading model weights (${modelInfo.label})… this may take a few minutes on first use`);

    transcriber = await pipeline(
      'automatic-speech-recognition',
      modelInfo.hfModelId,
      {
        chunk_length_s: 30,
        stride_length_s: 5,
        // Progress callback during model loading
        progress_callback: (progress: { status: string; progress?: number; file?: string }) => {
          if (progress.status === 'downloading' && progress.progress != null) {
            const pct = Math.min(40, Math.round(5 + progress.progress * 0.35));
            onProgress?.(pct, `Downloading model: ${progress.file ?? ''} (${Math.round(progress.progress)}%)`);
          } else if (progress.status === 'loading') {
            onProgress?.(42, `Loading model into memory…`);
          }
        },
      },
    );
    _pipelines.set(modelInfo.hfModelId, transcriber);
  }

  onProgress?.(45, 'Decoding audio…');

  // Convert Blob to ArrayBuffer then to Float32Array via AudioContext
  const arrayBuffer = await audioBlob.arrayBuffer();

  let audioData: Float32Array;
  try {
    // Use AudioContext to decode and resample to 16 kHz (Whisper requirement)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const AudioCtx: typeof AudioContext = (window.AudioContext || (window as any).webkitAudioContext);
    const ctx = new AudioCtx({ sampleRate: 16000 });
    const decoded = await ctx.decodeAudioData(arrayBuffer);
    audioData = decoded.getChannelData(0); // mono
    ctx.close();
  } catch (_e) {
    // Fallback: pass raw bytes — transformers.js can handle several formats natively
    audioData = new Float32Array(arrayBuffer);
  }

  onProgress?.(50, 'Transcribing audio… (this may take a while for long videos)');

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const output: any = await transcriber(audioData, {
    return_timestamps: true,
    language: 'english',
  });

  onProgress?.(95, 'Finalising transcript…');

  // Normalise output shape — transformers.js returns { text, chunks } or just text
  const fullText: string = output?.text ?? (typeof output === 'string' ? output : '');
  const rawChunks: Array<{ timestamp: [number, number]; text: string }> = output?.chunks ?? [];

  const chunks = rawChunks.map(c => ({
    start: c.timestamp?.[0] ?? 0,
    end: c.timestamp?.[1] ?? 0,
    text: c.text ?? '',
  }));

  const wordCount = fullText.trim().split(/\s+/).filter(Boolean).length;

  onProgress?.(100, 'Transcription complete');

  return { fullText, chunks, wordCount };
}
