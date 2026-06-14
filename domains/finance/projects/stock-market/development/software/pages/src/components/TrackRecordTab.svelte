<script lang="ts">
  import { onMount } from 'svelte';
  import { loadTrackRecord, saveTrackedPrediction, clearTrackRecord, loadSettings } from '../lib/store';
  import { fetchCryptoBars, fetchStockBars } from '../lib/market-data';
  import type { TrackedPrediction } from '../lib/types';

  let record: TrackedPrediction[] = [];
  let resolving = false;
  let resolveMsg = '';
  let loaded = false;

  onMount(async () => {
    record = await loadTrackRecord();
    loaded = true;
    await resolveMatured();
  });

  // Score every matured-but-unresolved prediction by re-fetching the current price.
  async function resolveMatured() {
    const now = Date.now();
    const due = record.filter((p) => !p.resolved && new Date(p.maturesAt).getTime() <= now);
    if (due.length === 0) return;
    resolving = true;
    resolveMsg = `Scoring ${due.length} matured prediction${due.length > 1 ? 's' : ''}…`;
    let settings;
    try { settings = await loadSettings(); } catch { settings = undefined; }
    for (const p of due) {
      try {
        const bars = p.kind === 'crypto'
          ? await fetchCryptoBars(p.assetId)
          : await fetchStockBars(p.assetId, { apiKey: settings?.twelveDataApiKey, proxyUrl: settings?.yahooProxyUrl });
        const current = bars[0]?.close;
        if (!Number.isFinite(current)) continue;   // leave pending; try again next visit
        const ret = ((current - p.priceAtPrediction) / p.priceAtPrediction) * 100;
        p.actualPrice = current;
        p.actualReturnPct = ret;
        p.correct = p.direction === 'up' ? ret > 0 : p.direction === 'down' ? ret < 0 : Math.abs(ret) < 0.5;
        p.resolved = true;
        p.resolvedAt = new Date().toISOString();
        await saveTrackedPrediction(p);
      } catch {
        /* keep pending — likely needs a key/proxy for stocks; retry on next open */
      }
    }
    record = [...record];
    resolving = false;
    resolveMsg = '';
  }

  async function handleClear() {
    if (!confirm('Clear your entire prediction track record? This cannot be undone.')) return;
    await clearTrackRecord();
    record = [];
  }

  // ── derived stats ─────────────────────────────────────────────────────────
  $: scored = record.filter((p) => p.resolved && p.direction !== 'neutral' && p.correct != null);
  $: hits = scored.filter((p) => p.correct).length;
  $: hitRate = scored.length ? (hits / scored.length) * 100 : null;
  $: pending = record.filter((p) => !p.resolved).length;

  const HORIZONS = ['1d', '1w', '1m'] as const;
  function horizonStat(h: string): { n: number; rate: number | null } {
    const s = scored.filter((p) => p.horizon === h);
    return { n: s.length, rate: s.length ? (s.filter((p) => p.correct).length / s.length) * 100 : null };
  }

  $: sorted = [...record].sort((a, b) => new Date(b.predictedAt).getTime() - new Date(a.predictedAt).getTime());

  function fmtDate(iso: string): string { return new Date(iso).toLocaleDateString(); }
  function dirLabel(d: string): string { return d === 'up' ? 'Bullish' : d === 'down' ? 'Bearish' : 'Neutral'; }
</script>

<div class="tr">
  <div class="tr-head">
    <h2>Prediction Track Record</h2>
    {#if record.length > 0}
      <button class="tr-clear" on:click={handleClear}>Clear</button>
    {/if}
  </div>
  <p class="tr-sub">
    Every prediction you run is logged on-device and scored against the real price once its
    horizon elapses — your model's honest, personal hit rate. Nothing leaves your browser.
  </p>

  {#if resolving}<div class="tr-resolving">{resolveMsg}</div>{/if}

  {#if loaded && record.length === 0}
    <div class="tr-empty">
      No predictions logged yet. Run a prediction on the <strong>Model</strong> tab and it will appear
      here; come back after the horizon (1d / 1w / 1m) to see whether it was right.
    </div>
  {:else if record.length > 0}
    <div class="tr-summary">
      <div class="tr-big">
        <span class="tr-rate">{hitRate != null ? hitRate.toFixed(0) + '%' : '—'}</span>
        <span class="tr-rate-label">hit rate{scored.length ? ` · ${hits}/${scored.length} scored` : ''}</span>
      </div>
      <div class="tr-byh">
        {#each HORIZONS as h}
          {@const st = horizonStat(h)}
          <div class="tr-hcell">
            <div class="tr-h">{h}</div>
            <div class="tr-hrate">{st.rate != null ? st.rate.toFixed(0) + '%' : '—'}</div>
            <div class="tr-hn">{st.n} scored</div>
          </div>
        {/each}
      </div>
      {#if pending > 0}<div class="tr-pending">{pending} still maturing</div>{/if}
    </div>

    <ul class="tr-list">
      {#each sorted as p}
        <li class="tr-item">
          <span class="tr-asset">{p.asset}</span>
          <span class="tr-hbadge">{p.horizon}</span>
          <span class="tr-dir" class:up={p.direction === 'up'} class:down={p.direction === 'down'}>{dirLabel(p.direction)} {p.probUp.toFixed(0)}%</span>
          {#if p.resolved && p.direction !== 'neutral'}
            <span class="tr-outcome" class:ok={p.correct} class:bad={!p.correct}>
              {p.correct ? '✓' : '✗'} {p.actualReturnPct != null ? (p.actualReturnPct >= 0 ? '+' : '') + p.actualReturnPct.toFixed(1) + '%' : ''}
            </span>
          {:else if p.resolved}
            <span class="tr-outcome neutral">{p.actualReturnPct != null ? (p.actualReturnPct >= 0 ? '+' : '') + p.actualReturnPct.toFixed(1) + '%' : '—'}</span>
          {:else}
            <span class="tr-outcome wait">matures {fmtDate(p.maturesAt)}</span>
          {/if}
          <span class="tr-when">{fmtDate(p.predictedAt)}</span>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .tr { max-width: 860px; }
  .tr-head { display: flex; align-items: center; justify-content: space-between; }
  h2 { font-size: 1.1rem; font-weight: 700; color: var(--text); margin: 0; }
  .tr-clear {
    background: none; border: 1px solid var(--border); color: var(--muted);
    border-radius: 7px; padding: 0.3rem 0.8rem; font-size: 0.76rem; cursor: pointer;
  }
  .tr-clear:hover { color: var(--danger); border-color: var(--danger); }
  .tr-sub { font-size: 0.82rem; color: var(--muted); margin: 0.4rem 0 1.1rem; line-height: 1.6; }
  .tr-resolving { font-size: 0.78rem; color: var(--accent2); margin-bottom: 0.8rem; }
  .tr-empty {
    background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
    padding: 1.25rem 1.4rem; font-size: 0.85rem; color: var(--muted); line-height: 1.6;
  }

  .tr-summary {
    display: flex; flex-wrap: wrap; gap: 1.5rem; align-items: center;
    background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
    padding: 1.1rem 1.25rem; margin-bottom: 1rem;
  }
  .tr-big { display: flex; flex-direction: column; }
  .tr-rate { font-size: 2rem; font-weight: 800; color: var(--accent2); line-height: 1; }
  .tr-rate-label { font-size: 0.74rem; color: var(--muted); margin-top: 0.3rem; }
  .tr-byh { display: flex; gap: 1.1rem; }
  .tr-hcell { text-align: center; }
  .tr-h { font-size: 0.7rem; text-transform: uppercase; color: var(--muted); letter-spacing: 0.05em; }
  .tr-hrate { font-size: 1.1rem; font-weight: 700; color: var(--text); }
  .tr-hn { font-size: 0.68rem; color: var(--muted); }
  .tr-pending { font-size: 0.74rem; color: var(--muted); margin-left: auto; }

  .tr-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
  .tr-item {
    display: grid; grid-template-columns: 1fr auto auto auto auto; gap: 0.7rem; align-items: center;
    padding: 0.5rem 0.2rem; border-bottom: 1px solid var(--border); font-size: 0.8rem;
  }
  .tr-item:last-child { border-bottom: none; }
  .tr-asset { font-weight: 600; color: var(--text); }
  .tr-hbadge { font-size: 0.68rem; color: var(--muted); border: 1px solid var(--border); border-radius: 5px; padding: 0.05rem 0.35rem; }
  .tr-dir { font-weight: 600; color: var(--muted); }
  .tr-dir.up { color: var(--accent2); }
  .tr-dir.down { color: var(--danger); }
  .tr-outcome { font-weight: 700; font-variant-numeric: tabular-nums; }
  .tr-outcome.ok { color: var(--accent2); }
  .tr-outcome.bad { color: var(--danger); }
  .tr-outcome.wait, .tr-outcome.neutral { color: var(--muted); font-weight: 500; font-size: 0.74rem; }
  .tr-when { color: var(--muted); font-size: 0.72rem; }
</style>
