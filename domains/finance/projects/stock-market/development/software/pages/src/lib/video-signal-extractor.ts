// Video Signal Extractor
// Uses the existing WebLLM chat() function to extract market signals from a transcript.

import { chat, isModelLoaded } from './webllm';
import type { VideoSignal } from './types';

const SYSTEM_PROMPT = `You are a financial signal extractor. Given a YouTube video transcript, extract up to 5 key market signals.

Return ONLY a valid JSON array. No prose, no markdown fences.

Each element must have exactly these fields:
{
  "ticker": "<TICKER or null if no specific stock>",
  "domain": "<one of: macro|technical|fundamental|cross_asset|sentiment|geopolitical>",
  "parameter_name": "<concise parameter name>",
  "direction": "<UP or DOWN>",
  "weight": <integer 1-100>,
  "confidence": <float 0.0-1.0>,
  "key_quote": "<short verbatim quote from transcript>"
}

Rules:
- Only include signals with clear directional bias
- weight reflects importance of signal (100 = very high impact)
- confidence reflects how certain the speaker sounds (1.0 = definitive claim)
- key_quote must be ≤ 120 characters
- If no ticker is mentioned, use null
- Maximum 5 signals`;

interface RawSignal {
  ticker?: string | null;
  domain?: string;
  parameter_name?: string;
  direction?: string;
  weight?: number;
  confidence?: number;
  key_quote?: string;
}

const VALID_DOMAINS = new Set(['macro', 'technical', 'fundamental', 'cross_asset', 'sentiment', 'geopolitical']);

function generateId(): string {
  return `sig-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function validateAndNormalise(raw: RawSignal, videoId: string): VideoSignal | null {
  if (!raw || typeof raw !== 'object') return null;

  const direction = (raw.direction ?? '').toUpperCase();
  if (direction !== 'UP' && direction !== 'DOWN') return null;

  const domain = (raw.domain ?? 'macro').toLowerCase();
  const weight = Math.min(100, Math.max(1, Math.round(Number(raw.weight) || 50)));
  const confidence = Math.min(1, Math.max(0, Number(raw.confidence) || 0.5));
  const parameterName = String(raw.parameter_name ?? 'market signal').slice(0, 80);
  const keyQuote = String(raw.key_quote ?? '').slice(0, 120);
  const ticker = raw.ticker && typeof raw.ticker === 'string' && raw.ticker !== 'null'
    ? raw.ticker.toUpperCase().replace(/[^A-Z0-9.]/g, '').slice(0, 10)
    : null;

  return {
    id: generateId(),
    videoId,
    ticker,
    parameterName,
    domain: VALID_DOMAINS.has(domain) ? domain : 'macro',
    direction: direction === 'UP' ? 'up' : 'down',
    weight,
    confidence,
    keyQuote,
    extractedAt: new Date().toISOString(),
  };
}

/**
 * Extract up to 5 market signals from a video transcript using the loaded WebLLM model.
 *
 * @param transcript  Full transcript text (will be truncated if very long)
 * @param title       Video title for context
 * @param channel     Channel/speaker name for context
 * @param videoId     Source video ID (stored on each signal)
 * @param onToken     Optional streaming token callback (for live display)
 */
export async function extractSignalsFromTranscript(
  transcript: string,
  title: string,
  channel: string,
  videoId: string,
  onToken?: (token: string) => void,
): Promise<VideoSignal[]> {
  if (!isModelLoaded()) {
    throw new Error(
      'No LLM model is loaded. Go to Settings → AI Research Assistant and download a model first, ' +
      'then return to the Intelligence tab to extract signals.'
    );
  }

  // Truncate transcript to avoid exceeding model context window (~3500 chars is safe for 4K context)
  const maxChars = 3500;
  const truncated = transcript.length > maxChars
    ? transcript.slice(0, maxChars) + '… [truncated]'
    : transcript;

  const userMessage =
    `Video title: "${title}"\n` +
    `Channel/Speaker: "${channel}"\n\n` +
    `Transcript:\n${truncated}`;

  let rawJson = '';

  try {
    rawJson = await chat(
      SYSTEM_PROMPT,
      userMessage,
      onToken ?? (() => { /* no-op */ }),
    );
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    throw new Error(`LLM inference failed during signal extraction: ${msg}`);
  }

  // Try to parse JSON — handle cases where model wraps output in markdown fences
  let parsed: unknown;
  try {
    // Strip markdown code fences if present
    const cleaned = rawJson
      .replace(/^```(?:json)?\s*/i, '')
      .replace(/```\s*$/, '')
      .trim();

    // Find the JSON array bounds
    const start = cleaned.indexOf('[');
    const end = cleaned.lastIndexOf(']');
    if (start === -1 || end === -1) {
      throw new Error('No JSON array found in LLM output');
    }

    parsed = JSON.parse(cleaned.slice(start, end + 1));
  } catch (parseErr) {
    console.warn('YVIS: Failed to parse LLM JSON output:', rawJson, parseErr);
    // Return empty array rather than throwing — partial failure is better than crash
    return [];
  }

  if (!Array.isArray(parsed)) return [];

  const signals: VideoSignal[] = [];
  for (const item of parsed as RawSignal[]) {
    const signal = validateAndNormalise(item, videoId);
    if (signal) signals.push(signal);
    if (signals.length >= 5) break;
  }

  return signals;
}
