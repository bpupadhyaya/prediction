// Video Intelligence Store — IndexedDB v2 extension
// Additive upgrade: v1 stores (paramStates, snapshots, settings) are untouched.
// New stores added only in the v2 upgrade block.

import { openDB, type DBSchema, type IDBPDatabase } from 'idb';
import type { VideoSource, VideoTranscript, VideoSignal, ChannelTrack } from './types';

// ─── Schema ──────────────────────────────────────────────────────────────────

interface VideoIntelligenceDB extends DBSchema {
  // ── v1 stores (must be declared even though we don't modify them) ──
  paramStates: {
    key: string;
    value: { ticker: string; states: Record<string, unknown>; updatedAt: string };
  };
  snapshots: {
    key: string;
    value: {
      id: string; ticker: string; date: string; snapshotNum: number;
      states: Record<string, unknown>; probUp: number; confidence: number;
      notes: string; createdAt: string;
    };
    indexes: { 'by-ticker-date': [string, string] };
  };
  settings: {
    key: string;
    value: Record<string, unknown> & { key: string };
  };

  // ── v2 stores ──
  videoSources: {
    key: string;           // id
    value: VideoSource;
    indexes: { 'by-created': string };
  };
  videoTranscripts: {
    key: string;           // videoId
    value: VideoTranscript;
  };
  videoSignals: {
    key: string;           // id
    value: VideoSignal;
    indexes: { 'by-video': string; 'by-ticker': string };
  };
  channelTracks: {
    key: string;           // channelId
    value: ChannelTrack;
  };
  videoSettings: {
    key: string;
    value: { key: string; val: string };
  };
}

// ─── Singleton ───────────────────────────────────────────────────────────────

let _vdb: IDBPDatabase<VideoIntelligenceDB> | null = null;

async function getVDB(): Promise<IDBPDatabase<VideoIntelligenceDB>> {
  if (_vdb) return _vdb;

  _vdb = await openDB<VideoIntelligenceDB>('stock-predictor', 2, {
    upgrade(db, oldVersion) {
      // Create v1 stores if migrating from scratch (oldVersion === 0)
      if (oldVersion < 1) {
        db.createObjectStore('paramStates', { keyPath: 'ticker' });
        const ss = db.createObjectStore('snapshots', { keyPath: 'id' });
        ss.createIndex('by-ticker-date', ['ticker', 'date']);
        db.createObjectStore('settings', { keyPath: 'key' });
      }

      // Add v2 stores — never touch v1 stores here
      if (oldVersion < 2) {
        const vs = db.createObjectStore('videoSources', { keyPath: 'id' });
        vs.createIndex('by-created', 'createdAt');

        db.createObjectStore('videoTranscripts', { keyPath: 'videoId' });

        const sig = db.createObjectStore('videoSignals', { keyPath: 'id' });
        sig.createIndex('by-video', 'videoId');
        sig.createIndex('by-ticker', 'ticker');

        db.createObjectStore('channelTracks', { keyPath: 'channelId' });
        db.createObjectStore('videoSettings', { keyPath: 'key' });
      }
    },
  });

  return _vdb;
}

// ─── VideoSource ─────────────────────────────────────────────────────────────

export async function saveVideoSource(v: VideoSource): Promise<void> {
  const db = await getVDB();
  await db.put('videoSources', v);
}

export async function getVideoSource(id: string): Promise<VideoSource | undefined> {
  const db = await getVDB();
  return db.get('videoSources', id);
}

export async function getAllVideoSources(): Promise<VideoSource[]> {
  const db = await getVDB();
  const all = await db.getAll('videoSources');
  return all.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
}

export async function updateVideoSourceStatus(
  id: string,
  status: VideoSource['status'],
  errorMsg?: string,
): Promise<void> {
  const db = await getVDB();
  const existing = await db.get('videoSources', id);
  if (!existing) return;
  const updated: VideoSource = {
    ...existing,
    status,
    ...(errorMsg !== undefined ? { errorMsg } : {}),
    ...(status === 'done' ? { processedAt: new Date().toISOString() } : {}),
  };
  await db.put('videoSources', updated);
}

// ─── VideoTranscript ──────────────────────────────────────────────────────────

export async function saveTranscript(t: VideoTranscript): Promise<void> {
  const db = await getVDB();
  await db.put('videoTranscripts', t);
}

export async function getTranscript(videoId: string): Promise<VideoTranscript | undefined> {
  const db = await getVDB();
  return db.get('videoTranscripts', videoId);
}

// ─── VideoSignal ──────────────────────────────────────────────────────────────

export async function saveVideoSignals(signals: VideoSignal[]): Promise<void> {
  const db = await getVDB();
  const tx = db.transaction('videoSignals', 'readwrite');
  await Promise.all([...signals.map(s => tx.store.put(s)), tx.done]);
}

export async function getSignalsForVideo(videoId: string): Promise<VideoSignal[]> {
  const db = await getVDB();
  return db.getAllFromIndex('videoSignals', 'by-video', videoId);
}

export async function getAllSignals(ticker?: string, days?: number): Promise<VideoSignal[]> {
  const db = await getVDB();
  let signals: VideoSignal[];

  if (ticker) {
    signals = await db.getAllFromIndex('videoSignals', 'by-ticker', ticker);
  } else {
    signals = await db.getAll('videoSignals');
  }

  if (days !== undefined && days > 0) {
    const cutoff = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString();
    signals = signals.filter(s => s.extractedAt >= cutoff);
  }

  return signals.sort((a, b) => b.extractedAt.localeCompare(a.extractedAt));
}

// ─── ChannelTrack ─────────────────────────────────────────────────────────────

export async function saveChannelTrack(ct: ChannelTrack): Promise<void> {
  const db = await getVDB();
  await db.put('channelTracks', ct);
}

export async function getAllChannelTracks(): Promise<ChannelTrack[]> {
  const db = await getVDB();
  return db.getAll('channelTracks');
}

export async function removeChannelTrack(channelId: string): Promise<void> {
  const db = await getVDB();
  await db.delete('channelTracks', channelId);
}

// ─── VideoSettings ────────────────────────────────────────────────────────────

export async function getVideoSetting(key: string): Promise<string | null> {
  const db = await getVDB();
  const row = await db.get('videoSettings', key);
  return row?.val ?? null;
}

export async function setVideoSetting(key: string, value: string): Promise<void> {
  const db = await getVDB();
  await db.put('videoSettings', { key, val: value });
}
