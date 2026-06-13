export type Direction = 'up' | 'down' | 'neutral';

export interface Parameter {
  name: string;
  domain: string;
  domainLabel: string;
  label: string;
  unit: string;
  defaultValue: number;
  layman: string;
  technical: string;
}

export interface ParamState {
  weight: number;       // 1–100
  direction: Direction;
  value: number | null; // user-entered or fetched current value
}

export interface PredictionSnapshot {
  id: string;
  ticker: string;
  date: string;         // YYYY-MM-DD
  snapshotNum: number;  // 1 or 2
  states: Record<string, ParamState>;
  probUp: number;
  confidence: number;
  notes: string;
  createdAt: string;    // ISO timestamp
}

export interface AppSettings {
  fredApiKey: string;
  corsProxyEnabled: boolean;
  llmModelId: string | null;
  llmDownloaded: boolean;
  twelveDataApiKey?: string;   // free key (twelvedata.com) for global stock prediction
}

// ─── Video Intelligence System (YVIS) ───────────────────────────────────────

export interface VideoSource {
  id: string;
  url: string;
  videoId: string;
  title: string;
  channelName: string;
  channelId: string;
  speakerName: string;
  publishedAt: string;   // ISO date
  durationSec: number;
  viewCount: number;
  status: 'pending' | 'transcribing' | 'extracting' | 'done' | 'error';
  errorMsg?: string;
  transcriptModel?: string;
  processedAt?: string;
  createdAt: string;
}

export interface VideoTranscript {
  videoId: string;
  fullText: string;
  chunks: Array<{ start: number; end: number; text: string }>;
  wordCount: number;
  language: string;
  modelUsed: string;
  transcribedAt: string;
}

export interface VideoSignal {
  id: string;
  videoId: string;
  ticker: string | null;
  parameterName: string;
  domain: string;
  direction: 'up' | 'down';
  weight: number;       // 1-100
  confidence: number;   // 0-1
  keyQuote: string;
  extractedAt: string;
}

export interface ChannelTrack {
  channelId: string;
  channelName: string;
  speakerName: string;
  autoProcess: boolean;
  timeRangeYears: number;
  createdAt: string;
}

export interface WhisperModelInfo {
  id: string;
  label: string;
  sizeGB: number;
  quality: string;
  hfModelId: string;  // HuggingFace model ID for transformers.js
}
