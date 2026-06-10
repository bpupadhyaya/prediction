import { openDB, type DBSchema, type IDBPDatabase } from 'idb';
import type { PredictionSnapshot, AppSettings, ParamState } from './types';

interface AppDB extends DBSchema {
  paramStates: {
    key: string;  // ticker
    value: { ticker: string; states: Record<string, ParamState>; updatedAt: string };
  };
  snapshots: {
    key: string;   // snapshot id
    value: PredictionSnapshot;
    indexes: { 'by-ticker-date': [string, string] };
  };
  settings: {
    key: string;
    value: AppSettings & { key: string };
  };
}

let _db: IDBPDatabase<AppDB> | null = null;

async function getDB(): Promise<IDBPDatabase<AppDB>> {
  if (_db) return _db;
  _db = await openDB<AppDB>('stock-predictor', 1, {
    upgrade(db) {
      db.createObjectStore('paramStates', { keyPath: 'ticker' });
      const ss = db.createObjectStore('snapshots', { keyPath: 'id' });
      ss.createIndex('by-ticker-date', ['ticker', 'date']);
      db.createObjectStore('settings', { keyPath: 'key' });
    },
  });
  return _db;
}

export async function loadParamStates(ticker: string): Promise<Record<string, ParamState> | null> {
  const db = await getDB();
  const row = await db.get('paramStates', ticker);
  return row?.states ?? null;
}

export async function saveParamStates(ticker: string, states: Record<string, ParamState>): Promise<void> {
  const db = await getDB();
  await db.put('paramStates', { ticker, states, updatedAt: new Date().toISOString() });
}

export async function saveSnapshot(snap: PredictionSnapshot): Promise<'saved' | 'replaced'> {
  const db = await getDB();
  // Enforce max 2 per ticker per day
  const existing = await db.getAllFromIndex('snapshots', 'by-ticker-date', [snap.ticker, snap.date]);
  let replaced = false;
  if (existing.length >= 2) {
    existing.sort((a, b) => a.createdAt.localeCompare(b.createdAt));
    if (existing[0]) {
      await db.delete('snapshots', existing[0].id);
      replaced = true;
    }
  }
  await db.put('snapshots', snap);
  return replaced ? 'replaced' : 'saved';
}

export async function loadSnapshots(ticker: string): Promise<PredictionSnapshot[]> {
  const db = await getDB();
  const all = await db.getAll('snapshots');
  return all.filter(s => s.ticker === ticker).sort((a, b) => b.createdAt.localeCompare(a.createdAt));
}

export async function loadAllSnapshots(): Promise<PredictionSnapshot[]> {
  const db = await getDB();
  const all = await db.getAll('snapshots');
  return all.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
}

export async function deleteSnapshot(id: string): Promise<void> {
  const db = await getDB();
  await db.delete('snapshots', id);
}

export async function loadSettings(): Promise<AppSettings> {
  const db = await getDB();
  const row = await db.get('settings', 'main');
  if (!row) return { fredApiKey: '', corsProxyEnabled: false, llmModelId: null, llmDownloaded: false };
  const { key: _key, ...settings } = row;
  return settings;
}

export async function saveSettings(s: AppSettings): Promise<void> {
  const db = await getDB();
  await db.put('settings', { ...s, key: 'main' });
}
