// Audio Transcription via Whisper (transformers.js, runs 100% in-browser)
//
// Two input modes:
//   A. File upload  — user drops any audio/video file; no external service needed
//   B. YouTube URL  — fetches audio via a user-deployed Cloudflare Worker proxy
//                     (free tier, ~30 lines of JS; user deploys once, app works forever)

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

export const DEFAULT_MODEL_ID = 'base';

// ─── Cloudflare Worker template ───────────────────────────────────────────────

export const CF_WORKER_TEMPLATE = `// Cloudflare Worker — YouTube Audio Proxy
// Deploy at: https://workers.cloudflare.com/ (free, no credit card)
// Free tier: 100,000 requests/day
export default {
  async fetch(request) {
    const url = new URL(request.url);
    const ytUrl = url.searchParams.get('url');
    if (!ytUrl) return new Response('Missing url param', { status: 400 });
    if (!ytUrl.includes('youtube.com') && !ytUrl.includes('youtu.be'))
      return new Response('Only YouTube URLs allowed', { status: 400 });

    const pageRes = await fetch(ytUrl, {
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible)' }
    });
    const html = await pageRes.text();
    const match = html.match(/ytInitialPlayerResponse\\s*=\\s*({.+?});/);
    if (!match) return new Response('Could not parse YouTube page', { status: 500 });

    const playerResponse = JSON.parse(match[1]);
    const formats = playerResponse?.streamingData?.adaptiveFormats || [];
    const audioFormat = formats.find(f =>
      f.mimeType?.includes('audio/webm') || f.mimeType?.includes('audio/mp4')
    );
    if (!audioFormat?.url) return new Response('No audio stream found', { status: 500 });

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

// ─── YouTube audio fetching (via Cloudflare Worker) ───────────────────────────

/**
 * Download audio from a YouTube URL via the user's Cloudflare Worker proxy.
 * Throws a descriptive error if no Worker URL is configured.
 */
export async function fetchYouTubeAudio(youtubeUrl: string): Promise<Blob> {
  const cfWorkerUrl = await getVideoSetting('cfWorkerUrl');

  if (!cfWorkerUrl) {
    throw new Error(
      'Cloudflare Worker not configured.\n\n' +
      'To use the YouTube URL mode, deploy the included Worker script (free, ~30 lines) ' +
      'at workers.cloudflare.com, then paste your Worker URL in the setup card below.'
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
      `. Check your Worker URL and deployment.`
    );
  }

  return response.blob();
}

// ─── Lazy pipeline cache ──────────────────────────────────────────────────────

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const _pipelines: Map<string, any> = new Map();

// ─── Whisper transcription (works with any Blob/File) ────────────────────────

/**
 * Transcribe an audio or video File/Blob using Whisper via transformers.js.
 * Runs 100% in-browser — no servers required.
 * Works with files from drag-and-drop OR blobs fetched by the CF Worker.
 *
 * @param audioFile  Any File or Blob containing audio/video
 * @param modelId    Whisper model id (default: 'base')
 * @param onProgress Called with (0–100, statusMessage)
 */
export async function transcribeAudioBlob(
  audioFile: Blob | File,
  modelId: string = DEFAULT_MODEL_ID,
  onProgress?: (pct: number, msg: string) => void,
): Promise<{ fullText: string; chunks: Array<{ start: number; end: number; text: string }>; wordCount: number }> {
  const modelInfo = WHISPER_MODELS.find(m => m.id === modelId) ?? WHISPER_MODELS[1];

  onProgress?.(0, `Loading Whisper model (${modelInfo.label})…`);

  // Dynamic import keeps the heavy bundle out of the initial load
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

  // OPFS caches model weights across sessions — downloaded once, reused forever
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
