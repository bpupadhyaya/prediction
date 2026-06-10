<script lang="ts">
  import { PARAMETERS, DOMAIN_ORDER, DOMAIN_LABELS } from '../lib/parameters';
  import { exportJSON, exportCSV, exportPDF, exportXLSX } from '../lib/export';
  import type { PredictionResult } from '../lib/prediction';
  import type { ParamState } from '../lib/types';

  export let result: PredictionResult;
  export let states: Record<string, ParamState>;
  export let ticker: string;
  export let onClose: () => void;

  const today = new Date().toISOString().slice(0, 10);

  $: totalParams = PARAMETERS.length;
  $: neutralCount = PARAMETERS.filter(p => (states[p.name]?.direction ?? 'neutral') === 'neutral').length;
  $: changedCount = totalParams - neutralCount;
  $: allNeutral = changedCount === 0;
  $: mostlyNeutral = changedCount < totalParams * 0.05; // fewer than 5% set

  $: domainBreakdown = DOMAIN_ORDER.map(domain => {
    const params = PARAMETERS.filter(p => p.domain === domain);
    let up = 0, down = 0, neutral = 0, netScore = 0, totalW = 0;
    for (const p of params) {
      const dir = states[p.name]?.direction ?? 'neutral';
      const w   = states[p.name]?.weight ?? 50;
      if (dir === 'up')      { up++;   netScore += w; totalW += w; }
      else if (dir === 'down') { down++; netScore -= w; totalW += w; }
      else neutral++;
    }
    return {
      label:   DOMAIN_LABELS[domain] ?? domain,
      count:   params.length,
      up, down, neutral,
      netDir:  netScore > 0 ? 'up' : netScore < 0 ? 'down' : 'neutral',
    };
  });

  $: changedParams = PARAMETERS
    .filter(p => (states[p.name]?.direction ?? 'neutral') !== 'neutral')
    .slice(0, 30);

  $: dirColor = result.direction === 'up' ? 'var(--accent2)' : result.direction === 'down' ? 'var(--danger)' : 'var(--muted)';
  $: dirLabel = result.direction === 'up' ? '▲ UP' : result.direction === 'down' ? '▼ DOWN' : '— NEUTRAL';

  function payload() {
    return { ticker, date: today, result, states, parameters: PARAMETERS };
  }

  let exporting = false;
  async function doXLSX() {
    exporting = true;
    try { await exportXLSX(payload()); } finally { exporting = false; }
  }
</script>

<div class="overlay" role="dialog" aria-modal="true" on:click|self={onClose}>
  <div class="modal">

    <div class="modal-header">
      <span class="modal-title">▶ Prediction — {ticker}</span>
      <span class="modal-date">{today}</span>
      <button class="close-btn" on:click={onClose}>✕</button>
    </div>

    <div class="modal-body">

      <!-- Hero result -->
      <div class="result-hero" style="border-color:{dirColor}">
        <span class="dir-label" style="color:{dirColor}">{dirLabel}</span>
        <div class="result-stats">
          <div class="stat">
            <span class="stat-val">{(result.probUp * 100).toFixed(1)}%</span>
            <span class="stat-lbl">Prob(UP)</span>
          </div>
          <div class="stat">
            <span class="stat-val">{(result.probDown * 100).toFixed(1)}%</span>
            <span class="stat-lbl">Prob(DOWN)</span>
          </div>
          <div class="stat">
            <span class="stat-val" style="color:{dirColor}">{(result.confidence * 100).toFixed(1)}%</span>
            <span class="stat-lbl">Confidence</span>
          </div>
          <div class="stat">
            <span class="stat-val">{changedCount} / {totalParams}</span>
            <span class="stat-lbl">Params Set</span>
          </div>
        </div>
      </div>

      <!-- Warning if nothing / almost nothing set -->
      {#if allNeutral}
        <div class="warn warn-error">
          ⚠️ No parameters changed from defaults. This result carries no signal — all directions are neutral.
          Set UP or DOWN on factors you have a view on to generate a meaningful prediction.
        </div>
      {:else if mostlyNeutral}
        <div class="warn warn-mild">
          ℹ️ Only {changedCount} of {totalParams} parameters have been set ({(changedCount/totalParams*100).toFixed(0)}%).
          For a stronger signal, set directions on more factors you have conviction about.
        </div>
      {/if}

      <!-- Domain breakdown -->
      <div class="section-label">Domain Breakdown</div>
      <table class="breakdown-table">
        <thead>
          <tr><th>Domain</th><th># Params</th><th class="up">▲ UP</th><th class="dn">▼ DOWN</th><th class="nu">— Neutral</th><th>Net Signal</th></tr>
        </thead>
        <tbody>
          {#each domainBreakdown as d}
            <tr>
              <td>{d.label}</td>
              <td class="center muted">{d.count}</td>
              <td class="center up">{d.up}</td>
              <td class="center dn">{d.down}</td>
              <td class="center nu">{d.neutral}</td>
              <td class="net-{d.netDir}">
                {d.netDir === 'up' ? '▲ Bullish' : d.netDir === 'down' ? '▼ Bearish' : '— Neutral'}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>

      <!-- Params user set -->
      {#if changedParams.length > 0}
        <div class="section-label">
          Your Signals ({changedCount} params set{changedCount > 30 ? ' — showing first 30' : ''})
        </div>
        <table class="changed-table">
          <thead>
            <tr><th>Parameter</th><th>Domain</th><th>Direction</th><th>Weight</th></tr>
          </thead>
          <tbody>
            {#each changedParams as p}
              {@const s = states[p.name]}
              <tr>
                <td>
                  <span class="p-name">{p.name}</span>
                  <span class="p-label">{p.label}</span>
                </td>
                <td class="muted">{p.domainLabel}</td>
                <td class="{s.direction === 'up' ? 'dir-up' : 'dir-dn'}">
                  {s.direction === 'up' ? '▲ UP' : '▼ DOWN'}
                </td>
                <td class="center mono">{s.weight}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}

    </div><!-- end modal-body -->

    <!-- Export bar -->
    <div class="export-bar">
      <span class="export-lbl">Export:</span>
      <button class="exp-btn" on:click={() => exportJSON(payload())}>📄 JSON</button>
      <button class="exp-btn" on:click={() => exportCSV(payload())}>📊 CSV</button>
      <button class="exp-btn" on:click={() => exportPDF(payload())}>🖨️ PDF</button>
      <button class="exp-btn" on:click={doXLSX} disabled={exporting}>
        {exporting ? '...' : '📈 Excel'}
      </button>
    </div>

  </div>
</div>

<style>
  .overlay {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.78);
    display: flex; align-items: center; justify-content: center;
    z-index: 600; padding: 1rem;
  }
  .modal {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; width: 100%; max-width: 820px;
    max-height: 90vh; display: flex; flex-direction: column; overflow: hidden;
  }
  .modal-header {
    display: flex; align-items: center; gap: 0.75rem;
    padding: 0.9rem 1.25rem; border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }
  .modal-title { font-size: 0.95rem; font-weight: 700; }
  .modal-date  { font-size: 0.78rem; color: var(--muted); margin-left: 0.25rem; }
  .close-btn   { margin-left: auto; background: none; border: none; color: var(--muted); font-size: 1.1rem; line-height: 1; padding: 0.2rem; cursor: pointer; }
  .close-btn:hover { color: var(--text); }

  .modal-body { overflow-y: auto; padding: 1.25rem; flex: 1; }

  .result-hero {
    border: 2px solid; border-radius: 10px;
    padding: 1rem 1.5rem; margin-bottom: 1rem;
    display: flex; align-items: center; gap: 2rem; flex-wrap: wrap;
  }
  .dir-label { font-size: 2.2rem; font-weight: 900; line-height: 1; }
  .result-stats { display: flex; gap: 1.75rem; flex-wrap: wrap; }
  .stat { display: flex; flex-direction: column; align-items: center; gap: 2px; }
  .stat-val { font-size: 1.2rem; font-weight: 700; }
  .stat-lbl { font-size: 0.62rem; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }

  .warn {
    border-radius: 8px; padding: 0.7rem 1rem;
    font-size: 0.82rem; margin-bottom: 1rem;
  }
  .warn-error { background: rgba(248,113,113,0.12); border: 1px solid var(--danger); color: var(--danger); }
  .warn-mild  { background: rgba(251,191,36,0.12); border: 1px solid var(--warn); color: var(--warn); }

  .section-label {
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .08em; color: var(--muted); margin: 1rem 0 0.4rem;
  }

  .breakdown-table, .changed-table {
    width: 100%; border-collapse: collapse; font-size: 0.79rem; margin-bottom: 0.5rem;
  }
  .breakdown-table th, .changed-table th {
    text-align: left; padding: 0.3rem 0.5rem; font-size: 0.68rem;
    color: var(--muted); font-weight: 500; border-bottom: 1px solid var(--border);
  }
  .breakdown-table td, .changed-table td {
    padding: 0.32rem 0.5rem; border-bottom: 1px solid rgba(42,45,58,0.35);
  }
  .center { text-align: center; }
  .muted  { color: var(--muted); }
  .mono   { font-family: monospace; }
  .up, .net-up   { color: var(--accent2); font-weight: 600; }
  .dn, .net-down { color: var(--danger);  font-weight: 600; }
  .nu, .net-neutral { color: var(--muted); }
  .dir-up { color: var(--accent2); font-weight: 600; }
  .dir-dn { color: var(--danger);  font-weight: 600; }
  .p-name  { font-family: monospace; font-size: 0.77rem; display: block; }
  .p-label { font-size: 0.64rem; color: var(--muted); }

  .export-bar {
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.75rem 1.25rem; border-top: 1px solid var(--border);
    flex-shrink: 0; flex-wrap: wrap;
  }
  .export-lbl { font-size: 0.75rem; color: var(--muted); }
  .exp-btn {
    background: var(--surface); border: 1px solid var(--border);
    color: var(--text); padding: 0.32rem 0.85rem;
    border-radius: 6px; font-size: 0.79rem; cursor: pointer; transition: all 0.12s;
  }
  .exp-btn:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); background: rgba(79,142,247,0.08); }
  .exp-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
