<script lang="ts">
  import { onMount } from 'svelte';
  import { loadMeta, type ModelMeta, type Horizon } from '../lib/onnx';

  const HORIZONS: Horizon[] = ['1d', '1w', '1m'];
  const HORIZON_LABELS: Record<Horizon, string> = { '1d': '1 Day', '1w': '1 Week', '1m': '1 Month' };

  let meta: ModelMeta | null = null;
  let open = false;

  onMount(async () => { meta = await loadMeta(); });

  const pct = (v: number | undefined) => (v == null ? '—' : `${(v * 100).toFixed(1)}%`);
  const edge = (acc: number, base: number | undefined) =>
    base == null ? '—' : `${acc - base >= 0 ? '+' : '−'}${(Math.abs(acc - base) * 100).toFixed(1)} pts`;
</script>

{#if meta}
  <div class="mt-card">
    <button class="mt-head" on:click={() => (open = !open)} aria-expanded={open}>
      <span>How accurate is this model? <span class="mt-sub">honest, out-of-sample</span></span>
      <span class="mt-chev" class:open>▸</span>
    </button>

    {#if open}
      <div class="mt-body">
        <p class="mt-intro">
          Measured on a <strong>time-ordered hold-out</strong> the model never trained on (no
          look-ahead). "Edge" is how far it beats the naive "always up" guess — the bar a
          coin-flip on a drifting market would clear.
        </p>
        <table class="mt-table">
          <thead>
            <tr><th>Horizon</th><th>Accuracy</th><th>Base rate</th><th>Edge</th><th>Calibrated</th></tr>
          </thead>
          <tbody>
            {#each HORIZONS as h}
              {#if meta.horizons[h]}
                {@const m = meta.horizons[h]}
                <tr>
                  <td>{HORIZON_LABELS[h]}</td>
                  <td class="mt-acc">{pct(m.backtest_accuracy)}</td>
                  <td>{pct(m.test_up_rate)}</td>
                  <td class="mt-edge" class:pos={m.backtest_accuracy - (m.test_up_rate ?? 0) >= 0}>
                    {edge(m.backtest_accuracy, m.test_up_rate)}
                  </td>
                  <td>
                    {#if m.brier_calibrated != null && m.brier_raw != null}
                      <span class="mt-ok">✓</span> Brier {m.brier_raw.toFixed(3)}→{m.brier_calibrated.toFixed(3)}
                    {:else}—{/if}
                  </td>
                </tr>
              {/if}
            {/each}
          </tbody>
        </table>
        {#if meta.horizons['1w']?.n_test}
          <p class="mt-foot">
            Hold-out ≈ {meta.horizons['1w'].n_test?.toLocaleString()} samples per horizon ·
            probabilities are Platt-calibrated so the shown % matches real frequencies ·
            16 OHLCV features, on-device. Directional edge is small by nature — markets are
            near-efficient; honesty about that is the point.
          </p>
        {/if}
      </div>
    {/if}
  </div>
{/if}

<style>
  .mt-card { max-width: 860px; margin-top: 1.25rem; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }
  .mt-head {
    width: 100%; display: flex; justify-content: space-between; align-items: center; gap: 0.5rem;
    background: none; border: none; color: var(--text); cursor: pointer;
    padding: 0.85rem 1.1rem; font-size: 0.9rem; font-weight: 700; text-align: left; font-family: inherit;
  }
  .mt-sub { font-size: 0.72rem; font-weight: 500; color: var(--muted); }
  .mt-chev { color: var(--muted); transition: transform 0.15s; }
  .mt-chev.open { transform: rotate(90deg); }
  .mt-body { padding: 0 1.1rem 1.1rem; }
  .mt-intro { font-size: 0.8rem; color: var(--text); line-height: 1.6; margin: 0 0 0.85rem; }
  .mt-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
  .mt-table th { text-align: left; color: var(--muted); font-weight: 600; font-size: 0.72rem; padding: 0.35rem 0.5rem; border-bottom: 1px solid var(--border); }
  .mt-table td { padding: 0.45rem 0.5rem; border-bottom: 1px solid var(--border); color: var(--text); font-variant-numeric: tabular-nums; }
  .mt-table tr:last-child td { border-bottom: none; }
  .mt-acc { font-weight: 700; color: var(--accent2); }
  .mt-edge.pos { color: var(--accent2); font-weight: 600; }
  .mt-ok { color: var(--accent2); }
  .mt-foot { font-size: 0.72rem; color: var(--muted); line-height: 1.55; margin: 0.85rem 0 0; }
</style>
