<script lang="ts">
  import { onMount } from 'svelte';
  import { loadSnapshots } from '../lib/store';
  import type { PredictionSnapshot } from '../lib/types';
  export let ticker: string;

  let snapshots: PredictionSnapshot[] = [];

  onMount(async () => {
    snapshots = await loadSnapshots(ticker);
  });

  $: dirColor = (p: number) => p >= 0.5 ? 'var(--accent2)' : 'var(--danger)';
  $: dirLabel = (p: number) => p >= 0.52 ? '▲ UP' : p <= 0.48 ? '▼ DOWN' : '— NEUTRAL';
</script>

<div class="history-header">
  <h2>Prediction History — {ticker}</h2>
  <p class="note">Up to 2 interactive snapshots saved per day. Click any snapshot to review parameter settings.</p>
</div>

{#if !snapshots.length}
  <div class="empty">No snapshots saved yet for {ticker}. Use the Predict tab and click "Save Snapshot".</div>
{:else}
  <div class="snapshot-list">
    {#each snapshots as snap}
      <div class="snapshot-card">
        <div class="snap-top">
          <span class="snap-date">{snap.date}</span>
          <span class="snap-time">{new Date(snap.createdAt).toLocaleTimeString()}</span>
          <span class="snap-dir" style="color:{dirColor(snap.probUp)}">{dirLabel(snap.probUp)}</span>
          <span class="snap-prob">Prob(UP) = {(snap.probUp * 100).toFixed(1)}%</span>
          <span class="snap-conf">Confidence: {(snap.confidence * 100).toFixed(1)}%</span>
        </div>
        <div class="snap-params">
          {#each Object.entries(snap.states).filter(([,s]) => s.direction !== 'neutral') as [name, state]}
            <span class="param-chip {state.direction}">
              {name} {state.direction === 'up' ? '▲' : '▼'} w={state.weight}
            </span>
          {/each}
        </div>
      </div>
    {/each}
  </div>
{/if}

<style>
  .history-header { margin-bottom: 1.25rem; }
  h2 { font-size: 1rem; font-weight: 700; margin-bottom: 0.3rem; }
  .note { font-size: 0.78rem; color: var(--muted); }
  .empty { color: var(--muted); font-size: 0.88rem; padding: 2rem; text-align: center; }
  .snapshot-list { display: flex; flex-direction: column; gap: 0.75rem; }
  .snapshot-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 0.9rem 1.1rem;
  }
  .snap-top { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.6rem; }
  .snap-date { font-weight: 700; font-size: 0.88rem; }
  .snap-time { font-size: 0.75rem; color: var(--muted); }
  .snap-dir  { font-weight: 700; font-size: 0.95rem; }
  .snap-prob, .snap-conf { font-size: 0.78rem; color: var(--muted); }
  .snap-params { display: flex; flex-wrap: wrap; gap: 0.3rem; }
  .param-chip {
    font-family: monospace; font-size: 0.68rem; padding: 0.12rem 0.4rem;
    border-radius: 4px; border: 1px solid var(--border);
  }
  .param-chip.up   { background: rgba(52,211,153,0.1);  color: var(--accent2); border-color: rgba(52,211,153,0.2); }
  .param-chip.down { background: rgba(248,113,113,0.1); color: var(--danger);  border-color: rgba(248,113,113,0.2); }
</style>
