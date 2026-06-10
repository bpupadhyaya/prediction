<script lang="ts">
  import type { PredictionResult } from '../lib/prediction';
  export let ticker: string;
  export let result: PredictionResult;
  export let onSave: () => void;
  export let onReset: () => void;
  export let onPredict: () => void;

  $: dirColor = result.direction === 'up' ? 'var(--accent2)' : result.direction === 'down' ? 'var(--danger)' : 'var(--muted)';
  $: dirLabel = result.direction === 'up' ? '▲ UP' : result.direction === 'down' ? '▼ DOWN' : '— NEUTRAL';
  $: confPct  = (result.confidence * 100).toFixed(1);
  $: probUpPct = (result.probUp * 100).toFixed(1);
</script>

<div class="score-header">
  <div class="ticker-section">
    <span class="ticker-label">{ticker}</span>
    <span class="dir-badge" style="color:{dirColor}">
      {dirLabel}
    </span>
    <span class="confidence" style="color:{dirColor}">
      {#if result.paramsSet > 0}{confPct}% confidence{:else}Set weights & directions below{/if}
    </span>
  </div>

  <div class="meta">
    <span class="meta-item">Prob(UP) = {probUpPct}%</span>
    <span class="meta-item">{result.paramsSet} params set</span>
  </div>

  <div class="actions">
    <button class="btn-reset" on:click={onReset} title="Reset all parameter weights and directions">↺ Reset</button>
    <button class="btn-predict" on:click={onPredict} title="View full prediction breakdown">▶ Predict</button>
    <button class="btn-save" on:click={onSave} disabled={result.paramsSet === 0} title={result.paramsSet === 0 ? 'Set at least one parameter to save' : 'Save prediction snapshot'}>
      💾 Save Snapshot
    </button>
  </div>
</div>

<style>
  .score-header {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    display: flex;
    align-items: center;
    gap: 1.5rem;
    flex-wrap: wrap;
    margin-bottom: 1.25rem;
    position: sticky;
    top: 53px;
    z-index: 90;
  }
  .ticker-section { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
  .ticker-label { font-size: 1.1rem; font-weight: 700; color: var(--text); }
  .dir-badge { font-size: 1.2rem; font-weight: 800; }
  .confidence { font-size: 0.82rem; }
  .meta { display: flex; gap: 1rem; flex: 1; flex-wrap: wrap; }
  .meta-item { font-size: 0.8rem; color: var(--muted); }
  .actions { display: flex; gap: 0.5rem; margin-left: auto; flex-wrap: wrap; }
  .btn-save {
    background: var(--accent);
    border: none;
    color: #fff;
    padding: 0.4rem 1rem;
    border-radius: 8px;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.15s;
  }
  .btn-save:not(:disabled):hover { filter: brightness(1.1); }
  .btn-save:disabled { opacity: 0.4; cursor: not-allowed; }
  .btn-predict {
    background: var(--accent2);
    border: none;
    color: #0f1117;
    padding: 0.4rem 1.1rem;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.15s;
  }
  .btn-predict:hover { opacity: 0.85; }
  .btn-reset {
    background: none;
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 0.4rem 0.8rem;
    border-radius: 8px;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.15s;
  }
  .btn-reset:hover { border-color: var(--accent); color: var(--text); }
</style>
