<script lang="ts">
  import { onMount } from 'svelte';
  import { loadAllSnapshots, deleteSnapshot } from '../lib/store';
  import { PARAMETERS } from '../lib/parameters';
  import { exportJSON, exportCSV, exportPDF, exportXLSX } from '../lib/export';
  import type { PredictionSnapshot } from '../lib/types';
  import type { PredictionResult } from '../lib/prediction';

  let snapshots: PredictionSnapshot[] = [];
  let loading = true;

  onMount(async () => {
    snapshots = await loadAllSnapshots();
    loading = false;
  });

  // Group snapshots by ticker, preserving recency order
  $: grouped = (() => {
    const map = new Map<string, PredictionSnapshot[]>();
    for (const s of snapshots) {
      if (!map.has(s.ticker)) map.set(s.ticker, []);
      map.get(s.ticker)!.push(s);
    }
    return map;
  })();

  function dirColor(p: number) { return p >= 0.52 ? 'var(--accent2)' : p <= 0.48 ? 'var(--danger)' : 'var(--muted)'; }
  function dirLabel(p: number) { return p >= 0.52 ? '▲ UP' : p <= 0.48 ? '▼ DOWN' : '— NEUTRAL'; }

  function resultFromSnap(snap: PredictionSnapshot): PredictionResult {
    const probUp = snap.probUp;
    const probDown = 1 - probUp;
    const paramsSet = Object.values(snap.states).filter(s => s.direction !== 'neutral').length;
    return {
      probUp,
      probDown,
      confidence: snap.confidence,
      direction: probUp > 0.52 ? 'up' : probUp < 0.48 ? 'down' : 'neutral',
      paramsSet,
      weightedScore: probUp * 2 - 1,
    };
  }

  function handleExportJSON(snap: PredictionSnapshot) {
    exportJSON({ ticker: snap.ticker, date: snap.date, result: resultFromSnap(snap), states: snap.states, parameters: PARAMETERS });
  }
  function handleExportCSV(snap: PredictionSnapshot) {
    exportCSV({ ticker: snap.ticker, date: snap.date, result: resultFromSnap(snap), states: snap.states, parameters: PARAMETERS });
  }
  function handleExportPDF(snap: PredictionSnapshot) {
    exportPDF({ ticker: snap.ticker, date: snap.date, result: resultFromSnap(snap), states: snap.states, parameters: PARAMETERS });
  }
  function handleExportXLSX(snap: PredictionSnapshot) {
    exportXLSX({ ticker: snap.ticker, date: snap.date, result: resultFromSnap(snap), states: snap.states, parameters: PARAMETERS });
  }

  async function handleDelete(id: string) {
    if (!confirm('Delete this snapshot?')) return;
    await deleteSnapshot(id);
    snapshots = snapshots.filter(s => s.id !== id);
  }
</script>

<div class="history-header">
  <h2>Prediction History — All Tickers</h2>
  <p class="note">All saved snapshots across tickers. Up to 2 per ticker per day. Each export includes all {PARAMETERS.length} parameters with your values, weights, directions, and the final prediction.</p>
</div>

{#if loading}
  <div class="empty">Loading...</div>
{:else if !snapshots.length}
  <div class="empty">No snapshots saved yet. Go to the Predict tab, set your parameters, and click "Save Snapshot".</div>
{:else}
  {#each [...grouped.entries()] as [ticker, snaps]}
    <div class="ticker-section">
      <div class="ticker-heading">
        <span class="ticker-label">{ticker}</span>
        <span class="ticker-count">{snaps.length} snapshot{snaps.length !== 1 ? 's' : ''}</span>
      </div>

      {#each snaps as snap (snap.id)}
        {@const setCount = Object.values(snap.states).filter(s => s.direction !== 'neutral').length}
        <div class="snapshot-card">
          <div class="snap-top">
            <div class="snap-meta">
              <span class="snap-date">{snap.date}</span>
              <span class="snap-time">{new Date(snap.createdAt).toLocaleTimeString()}</span>
            </div>
            <div class="snap-result">
              <span class="snap-dir" style="color:{dirColor(snap.probUp)}">{dirLabel(snap.probUp)}</span>
              <span class="snap-stat">Prob(UP) <b>{(snap.probUp * 100).toFixed(1)}%</b></span>
              <span class="snap-stat">Confidence <b>{(snap.confidence * 100).toFixed(1)}%</b></span>
              <span class="snap-stat">Signals <b>{setCount} / {PARAMETERS.length}</b></span>
            </div>
          </div>

          {#if setCount > 0}
            <div class="snap-chips">
              {#each Object.entries(snap.states).filter(([, s]) => s.direction !== 'neutral').slice(0, 12) as [name, state]}
                <span class="param-chip {state.direction}">
                  {name} {state.direction === 'up' ? '▲' : '▼'} w={state.weight}
                </span>
              {/each}
              {#if setCount > 12}
                <span class="param-chip more">+{setCount - 12} more</span>
              {/if}
            </div>
          {/if}

          <div class="snap-actions">
            <div class="export-btns">
              <span class="export-label">Download:</span>
              <button class="export-btn" on:click={() => handleExportJSON(snap)} title="Export as JSON">📄 JSON</button>
              <button class="export-btn" on:click={() => handleExportCSV(snap)} title="Export as CSV">📊 CSV</button>
              <button class="export-btn" on:click={() => handleExportPDF(snap)} title="Export as PDF">🖨️ PDF</button>
              <button class="export-btn" on:click={() => handleExportXLSX(snap)} title="Export as Excel">📈 Excel</button>
            </div>
            <button class="delete-btn" on:click={() => handleDelete(snap.id)} title="Delete snapshot">🗑 Delete</button>
          </div>
        </div>
      {/each}
    </div>
  {/each}
{/if}

<style>
  .history-header { margin-bottom: 1.25rem; }
  h2 { font-size: 1rem; font-weight: 700; margin-bottom: 0.3rem; }
  .note { font-size: 0.78rem; color: var(--muted); }
  .empty { color: var(--muted); font-size: 0.88rem; padding: 2rem; text-align: center; }

  .ticker-section { margin-bottom: 1.5rem; }
  .ticker-heading {
    display: flex; align-items: center; gap: 0.6rem;
    padding: 0.4rem 0.75rem; margin-bottom: 0.5rem;
    background: rgba(79,142,247,0.06); border-left: 3px solid var(--accent);
    border-radius: 0 6px 6px 0;
  }
  .ticker-label { font-family: monospace; font-size: 0.95rem; font-weight: 700; color: var(--accent); }
  .ticker-count { font-size: 0.72rem; color: var(--muted); }

  .snapshot-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 0.85rem 1rem;
    margin-bottom: 0.6rem;
  }

  .snap-top { display: flex; align-items: center; gap: 1.25rem; flex-wrap: wrap; margin-bottom: 0.55rem; }
  .snap-meta { display: flex; flex-direction: column; gap: 1px; min-width: 90px; }
  .snap-date { font-weight: 700; font-size: 0.88rem; color: var(--text); }
  .snap-time { font-size: 0.72rem; color: var(--muted); }
  .snap-result { display: flex; align-items: center; gap: 0.9rem; flex-wrap: wrap; }
  .snap-dir { font-weight: 700; font-size: 0.95rem; }
  .snap-stat { font-size: 0.75rem; color: var(--muted); }
  .snap-stat b { color: var(--text); }

  .snap-chips { display: flex; flex-wrap: wrap; gap: 0.28rem; margin-bottom: 0.65rem; }
  .param-chip {
    font-family: monospace; font-size: 0.67rem; padding: 0.1rem 0.38rem;
    border-radius: 4px; border: 1px solid var(--border);
  }
  .param-chip.up   { background: rgba(52,211,153,0.1);  color: var(--accent2); border-color: rgba(52,211,153,0.2); }
  .param-chip.down { background: rgba(248,113,113,0.1); color: var(--danger);  border-color: rgba(248,113,113,0.2); }
  .param-chip.more { color: var(--muted); background: none; }

  .snap-actions {
    display: flex; align-items: center; justify-content: space-between;
    gap: 0.5rem; flex-wrap: wrap;
    padding-top: 0.55rem; border-top: 1px solid var(--border);
  }
  .export-btns { display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap; }
  .export-label { font-size: 0.7rem; color: var(--muted); }
  .export-btn {
    font-size: 0.72rem; padding: 0.22rem 0.6rem;
    background: none; border: 1px solid var(--border); border-radius: 5px;
    color: var(--text); cursor: pointer; transition: all 0.12s;
  }
  .export-btn:hover { background: rgba(79,142,247,0.1); border-color: var(--accent); color: var(--accent); }
  .delete-btn {
    font-size: 0.72rem; padding: 0.22rem 0.6rem;
    background: none; border: 1px solid transparent; border-radius: 5px;
    color: var(--muted); cursor: pointer; transition: all 0.12s;
  }
  .delete-btn:hover { background: rgba(248,113,113,0.1); border-color: var(--danger); color: var(--danger); }
</style>
