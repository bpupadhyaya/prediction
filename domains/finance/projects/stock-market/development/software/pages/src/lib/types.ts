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
}
