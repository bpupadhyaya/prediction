<script lang="ts">
  import { onMount } from 'svelte';
  import {
    loadModel, predictOnnx, explainOnnx, rationale,
    type Horizon, type OnnxPrediction, type FeatureContribution,
  } from '../lib/onnx';
  import {
    CRYPTO_PRODUCTS, fetchCryptoBars, fetchStockBars, STOCK_PRESETS,
    computeFeatures, MIN_BARS,
  } from '../lib/market-data';
  import { loadSettings } from '../lib/store';

  const HORIZONS: Horizon[] = ['1d', '1w', '1m'];
  const HORIZON_LABELS: Record<Horizon, string> = { '1d': '1 Day', '1w': '1 Week', '1m': '1 Month' };

  let mode: 'crypto' | 'stock' = 'crypto';
  let productId = 'BTC-USD';
  let stockSymbol = 'AAPL';
  let twelveKey = '';
  let yahooProxy = '';
  let modelLoading = true;
  let loadError = '';
  let running = false;
  let runError = '';
  let results: Partial<Record<Horizon, OnnxPrediction>> = {};
  let drivers: FeatureContribution[] = [];
  let driversRationale = '';
  let selectedHorizon: Horizon = '1w';
  let lastPrice: number | null = null;
  let asOf = '';
  let resultLabel = '';

  // Crypto Radar — scan the whole keyless crypto universe, rank by conviction.
  interface ScanRow { id: string; label: string; probUp: number; direction: 'up' | 'down' | 'neutral'; }
  let scanning = false;
  let scanError = '';
  let scanDone = 0;
  let scanRows: ScanRow[] = [];

  onMount(async () => {
    modelLoading = true;
    loadError = '';
    try {
      // Load all three horizon models up front (each ~110 KB, runs in-browser).
      await Promise.all(HORIZONS.map((h) => loadModel(h)));
      const s = await loadSettings();
      twelveKey = s.twelveDataApiKey ?? '';
      yahooProxy = s.yahooProxyUrl ?? '';
    } catch (err) {
      loadError = err instanceof Error ? err.message : String(err);
    } finally {
      modelLoading = false;
    }
  });

  let lastFeatures: Float32Array | null = null;

  async function run() {
    runError = '';
    results = {};
    drivers = [];
    driversRationale = '';
    running = true;
    try {
      const label = mode === 'crypto' ? productId : stockSymbol.trim().toUpperCase();
      if (mode === 'stock' && !label) throw new Error('Enter a stock symbol.');
      const bars = mode === 'crypto'
        ? await fetchCryptoBars(productId)
        : await fetchStockBars(label, { apiKey: twelveKey, proxyUrl: yahooProxy });
      if (bars.length < MIN_BARS) {
        throw new Error(`Only ${bars.length} days of history available (need ${MIN_BARS}).`);
      }
      lastPrice = bars[0].close;
      asOf = new Date(bars[0].time * 1000).toLocaleDateString();
      resultLabel = label;
      const features = computeFeatures(bars);
      if (!features) throw new Error('Could not compute features.');
      lastFeatures = features;
      const out: Partial<Record<Horizon, OnnxPrediction>> = {};
      for (const h of HORIZONS) out[h] = await predictOnnx(features, h);
      results = out;
      await explainFor(selectedHorizon);
    } catch (err) {
      runError = err instanceof Error ? err.message : String(err);
    } finally {
      running = false;
    }
  }

  // Compute the top drivers + rationale for one horizon (perturbation attribution).
  async function explainFor(h: Horizon) {
    selectedHorizon = h;
    if (!lastFeatures || !results[h]) { drivers = []; driversRationale = ''; return; }
    drivers = await explainOnnx(lastFeatures, h);
    driversRationale = rationale(results[h]!.direction, drivers);
  }

  function fmtDelta(d: number): string {
    const pts = Math.abs(d) * 100;
    return `${d >= 0 ? '+' : '−'}${pts.toFixed(1)} pts`;
  }

  // Scan every crypto product (keyless Coinbase), predict 1-week, rank by P(up).
  async function scanCrypto() {
    scanError = '';
    scanRows = [];
    scanDone = 0;
    scanning = true;
    const rows: ScanRow[] = [];
    try {
      for (const p of CRYPTO_PRODUCTS) {
        try {
          const bars = await fetchCryptoBars(p.id);
          const feats = bars.length >= MIN_BARS ? computeFeatures(bars) : null;
          if (feats) {
            const r = await predictOnnx(feats, '1w');
            rows.push({ id: p.id, label: p.label, probUp: r.probUp, direction: r.direction });
          }
        } catch {
          /* skip a coin that fails to fetch — keep scanning the rest */
        }
        scanDone += 1;
        scanRows = [...rows].sort((a, b) => b.probUp - a.probUp);
      }
      if (rows.length === 0) throw new Error('No crypto could be scanned right now. Try again shortly.');
    } catch (err) {
      scanError = err instanceof Error ? err.message : String(err);
    } finally {
      scanning = false;
    }
  }

  function badgeClass(dir: 'up' | 'down' | 'neutral'): string {
    return dir === 'up' ? 'badge-up' : dir === 'down' ? 'badge-down' : 'badge-neutral';
  }
  function dirLabel(dir: 'up' | 'down' | 'neutral'): string {
    return dir === 'up' ? 'Bullish' : dir === 'down' ? 'Bearish' : 'Neutral';
  }
  function fmtPrice(v: number): string {
    if (v >= 1000) return v.toLocaleString(undefined, { maximumFractionDigits: 0 });
    if (v >= 1) return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
    return v.toFixed(4);
  }
</script>

<div class="onnx-card">
  <h2>Live Market Prediction</h2>
  <p class="subtitle">
    The same 16-feature model the mobile apps use, running entirely in your browser.
    Crypto uses Coinbase (no key, works anywhere); stocks use Twelve Data
    (AAPL free, any global ticker with a free key in Settings).
  </p>

  {#if modelLoading}
    <div class="loading-box" role="status" aria-live="polite">
      <div class="loading-label">Loading models…</div>
      <div class="loading-note">3 horizon models · ~330 KB total · runs locally</div>
    </div>
  {:else if loadError}
    <div class="error-box" role="alert">
      <div class="error-title">Failed to load models</div>
      <div class="error-msg">{loadError}</div>
    </div>
  {:else}
    <div class="mode-toggle" role="tablist" aria-label="Asset type">
      <button role="tab" class:active={mode === 'crypto'} aria-selected={mode === 'crypto'}
              on:click={() => (mode = 'crypto')} disabled={running}>Crypto</button>
      <button role="tab" class:active={mode === 'stock'} aria-selected={mode === 'stock'}
              on:click={() => (mode = 'stock')} disabled={running}>Stocks</button>
    </div>

    <div class="run-row">
      {#if mode === 'crypto'}
        <select bind:value={productId} aria-label="Cryptocurrency" disabled={running}>
          {#each CRYPTO_PRODUCTS as p}
            <option value={p.id}>{p.label} ({p.id})</option>
          {/each}
        </select>
      {:else}
        <input
          type="text"
          bind:value={stockSymbol}
          aria-label="Stock symbol"
          placeholder="Symbol (AAPL, 7203:XTKS, RELIANCE:NSE…)"
          disabled={running}
          on:keydown={(e) => e.key === 'Enter' && run()}
        />
      {/if}
      <button class="btn-run" on:click={run} disabled={running}>
        {running ? '⏳ Fetching & predicting…' : 'Predict'}
      </button>
    </div>

    {#if mode === 'crypto'}
      <div class="scan-row">
        <button class="btn-scan" on:click={scanCrypto} disabled={scanning || running}>
          {scanning ? `⏳ Scanning… ${scanDone}/${CRYPTO_PRODUCTS.length}` : '📡 Scan all crypto — rank by conviction'}
        </button>
        <span class="scan-note">1-week outlook across {CRYPTO_PRODUCTS.length} coins · calibrated · keyless</span>
      </div>
    {/if}

    {#if mode === 'stock'}
      <div class="preset-row">
        {#each STOCK_PRESETS as s}
          <button class="preset-chip" class:sel={stockSymbol.trim().toUpperCase() === s}
                  on:click={() => (stockSymbol = s)} disabled={running}>{s}</button>
        {/each}
        {#if !twelveKey}
          <span class="preset-note">Only AAPL without a key · add a free Twelve Data key in Settings for any ticker</span>
        {/if}
      </div>
    {/if}

    {#if runError}
      <div class="error-box" role="alert">
        <div class="error-title">Could not predict</div>
        <div class="error-msg">{runError}</div>
      </div>
    {/if}

    {#if scanError}
      <div class="error-box" role="alert">
        <div class="error-title">Scan failed</div>
        <div class="error-msg">{scanError}</div>
      </div>
    {/if}

    {#if scanRows.length > 0}
      <div class="result-card" role="region" aria-label="Crypto conviction ranking">
        <div class="result-header">
          <span class="result-ticker">Crypto Radar</span>
          <span class="result-asof">1-week outlook · ranked by P(up){scanning ? ` · ${scanDone}/${CRYPTO_PRODUCTS.length}` : ''}</span>
        </div>
        <ol class="rank-list">
          {#each scanRows as row, i}
            <li class="rank-item">
              <span class="rank-num">{i + 1}</span>
              <span class="rank-label">{row.label}</span>
              <span class="rank-id">{row.id}</span>
              <span class="direction-badge {badgeClass(row.direction)}">{dirLabel(row.direction)}</span>
              <span class="rank-prob" class:up={row.probUp >= 50} class:down={row.probUp < 50}>{row.probUp.toFixed(1)}%</span>
              <span class="rank-bar-wrap" role="presentation">
                <span class="rank-bar" class:up={row.probUp >= 50} class:down={row.probUp < 50} style="width:{row.probUp}%"></span>
              </span>
            </li>
          {/each}
        </ol>
        <p class="result-note">
          Same on-device model, calibrated · ranks the strongest 1-week bullish → bearish read.
          Probabilistic — not financial advice.
        </p>
      </div>
    {/if}

    {#if Object.keys(results).length > 0}
      <div class="result-card" role="region" aria-label="Model prediction result">
        <div class="result-header">
          <span class="result-ticker">{resultLabel}</span>
          {#if lastPrice !== null}
            <span class="result-price">${fmtPrice(lastPrice)}</span>
          {/if}
          <span class="result-asof">as of {asOf}</span>
        </div>

        <div class="horizon-grid">
          {#each HORIZONS as h}
            {#if results[h]}
              {@const r = results[h]}
              <button
                class="horizon-cell"
                class:explained={selectedHorizon === h}
                on:click={() => explainFor(h)}
                title="Show what drives the {HORIZON_LABELS[h]} prediction"
              >
                <div class="horizon-label">{HORIZON_LABELS[h]}</div>
                <span class="direction-badge {badgeClass(r.direction)}">{dirLabel(r.direction)}</span>
                <div class="horizon-prob">
                  <span class="up">{r.probUp.toFixed(1)}%</span> up
                </div>
                <div class="result-bar-wrap" role="presentation">
                  <div class="result-bar-up" style="width:{r.probUp}%"></div>
                  <div class="result-bar-down" style="width:{r.probDown}%"></div>
                </div>
                {#if r.accuracy > 0}
                  <div class="horizon-acc">{r.accuracy.toFixed(1)}% accurate</div>
                {/if}
              </button>
            {/if}
          {/each}
        </div>

        {#if drivers.length > 0}
          {@const selAcc = results[selectedHorizon]?.accuracy ?? 0}
          <div class="why-box">
            <div class="why-head">
              Why this {HORIZON_LABELS[selectedHorizon]} prediction
              {#if selAcc > 0}
                <span class="why-acc">model {selAcc.toFixed(1)}% accurate out-of-sample</span>
              {/if}
            </div>
            {#if driversRationale}
              <p class="why-rationale">{driversRationale}</p>
            {/if}
            <ul class="why-list">
              {#each drivers as d}
                <li class="why-item">
                  <span class="why-arrow" class:up={d.pushesUp} class:down={!d.pushesUp}>
                    {d.pushesUp ? '▲' : '▼'}
                  </span>
                  <span class="why-label">{d.label}</span>
                  <span class="why-delta" class:up={d.pushesUp} class:down={!d.pushesUp}>{fmtDelta(d.delta)}</span>
                </li>
              {/each}
            </ul>
            <p class="why-foot">
              Each driver = how much P(up) moves when that signal is reset to its historical norm.
              Tap a horizon above to explain it.
            </p>
          </div>
        {/if}

        <p class="result-note">
          16-feature GradientBoosting classifier · same model as iOS/Android · 100% on-device.
          Probabilities are calibrated; accuracy is out-of-sample. Probabilistic — not financial advice.
        </p>
      </div>
    {/if}
  {/if}
</div>

<style>
  .onnx-card { max-width: 860px; }
  h2 { font-size: 1.1rem; font-weight: 700; margin-bottom: 0.3rem; color: var(--text); }
  .subtitle { font-size: 0.82rem; color: var(--muted); margin-bottom: 1.25rem; line-height: 1.6; }

  .loading-box {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 1.25rem 1.5rem;
  }
  .loading-label { font-size: 0.85rem; font-weight: 600; color: var(--text); margin-bottom: 0.4rem; }
  .loading-note { font-size: 0.75rem; color: var(--muted); }

  .error-box {
    background: rgba(239, 68, 68, 0.06); border: 1px solid rgba(239, 68, 68, 0.25);
    border-radius: 10px; padding: 0.9rem 1.1rem; margin-bottom: 1rem;
  }
  .error-title { font-weight: 700; font-size: 0.85rem; color: var(--danger); margin-bottom: 0.3rem; }
  .error-msg { font-size: 0.78rem; color: var(--danger); line-height: 1.5; word-break: break-word; }

  .mode-toggle { display: inline-flex; gap: 0; margin-bottom: 0.9rem; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
  .mode-toggle button {
    background: var(--surface); color: var(--muted); border: none; cursor: pointer;
    padding: 0.4rem 1.1rem; font-size: 0.82rem; font-weight: 600; transition: all 0.15s;
  }
  .mode-toggle button.active { background: var(--accent); color: #fff; }
  .mode-toggle button:disabled { cursor: not-allowed; }

  .run-row { display: flex; gap: 0.6rem; align-items: center; margin-bottom: 0.7rem; flex-wrap: wrap; }
  .run-row select, .run-row input[type="text"] {
    flex: 1; min-width: 180px; font-size: 0.85rem; padding: 0.5rem 0.7rem;
    border-radius: 8px; background: var(--surface); color: var(--text); border: 1px solid var(--border);
  }

  .preset-row { display: flex; gap: 0.4rem; flex-wrap: wrap; align-items: center; margin-bottom: 1rem; }
  .preset-chip {
    background: rgba(100, 116, 139, 0.08); border: 1px solid var(--border); color: var(--text);
    border-radius: 99px; padding: 0.25rem 0.7rem; font-size: 0.76rem; font-weight: 600; cursor: pointer; transition: all 0.15s;
  }
  .preset-chip.sel { background: var(--accent); color: #fff; border-color: var(--accent); }
  .preset-chip:disabled { opacity: 0.55; cursor: not-allowed; }
  .preset-note { font-size: 0.72rem; color: var(--muted); margin-left: 0.3rem; }
  .btn-run {
    background: var(--accent); border: none; color: #fff; padding: 0.5rem 1.6rem;
    border-radius: 8px; font-size: 0.9rem; font-weight: 600; cursor: pointer; transition: all 0.15s;
  }
  .btn-run:disabled { opacity: 0.55; cursor: not-allowed; }
  .btn-run:not(:disabled):hover { filter: brightness(1.1); }

  .result-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 1.1rem 1.25rem; margin-top: 0.5rem;
  }
  .result-header { display: flex; align-items: baseline; gap: 0.75rem; margin-bottom: 1rem; flex-wrap: wrap; }
  .result-ticker { font-weight: 800; font-size: 1rem; letter-spacing: 0.04em; color: var(--text); }
  .result-price { font-weight: 700; font-size: 0.95rem; color: var(--accent2); }
  .result-asof { font-size: 0.72rem; color: var(--muted); }

  .horizon-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 0.9rem; margin-bottom: 0.8rem;
  }
  .horizon-cell {
    background: rgba(100, 116, 139, 0.06); border: 1px solid var(--border);
    border-radius: 10px; padding: 0.8rem 0.9rem;
    width: 100%; text-align: left; cursor: pointer; font: inherit; color: inherit;
    transition: border-color 0.15s, background 0.15s;
  }
  .horizon-cell:hover { border-color: var(--accent); }
  .horizon-cell.explained { border-color: var(--accent); background: rgba(99, 102, 241, 0.07); }
  .horizon-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); margin-bottom: 0.5rem; }
  .horizon-prob { font-size: 0.78rem; color: var(--muted); margin: 0.45rem 0 0.4rem; }
  .horizon-prob .up { color: var(--accent2); font-weight: 700; }
  .horizon-acc { font-size: 0.68rem; color: var(--muted); margin-top: 0.35rem; }

  .why-box {
    background: rgba(99, 102, 241, 0.05); border: 1px solid var(--border);
    border-radius: 10px; padding: 0.9rem 1rem; margin-bottom: 0.8rem;
  }
  .why-head { font-size: 0.82rem; font-weight: 700; color: var(--text); display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: baseline; }
  .why-acc { font-size: 0.7rem; font-weight: 600; color: var(--muted); }
  .why-rationale { font-size: 0.8rem; color: var(--text); line-height: 1.55; margin: 0.5rem 0 0.7rem; }
  .why-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0.35rem; }
  .why-item { display: flex; align-items: center; gap: 0.55rem; font-size: 0.8rem; }
  .why-arrow { font-size: 0.7rem; width: 0.9rem; text-align: center; }
  .why-arrow.up, .why-delta.up { color: var(--accent2); }
  .why-arrow.down, .why-delta.down { color: var(--danger); }
  .why-label { flex: 1; color: var(--text); }
  .why-delta { font-weight: 700; font-variant-numeric: tabular-nums; }
  .why-foot { font-size: 0.7rem; color: var(--muted); margin: 0.7rem 0 0; line-height: 1.5; }

  .direction-badge {
    font-size: 0.72rem; font-weight: 700; padding: 0.18rem 0.65rem;
    border-radius: 99px; text-transform: uppercase; letter-spacing: 0.05em;
  }
  .badge-up { background: rgba(52, 211, 153, 0.15); color: var(--accent2); border: 1px solid rgba(52, 211, 153, 0.3); }
  .badge-down { background: rgba(239, 68, 68, 0.12); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.3); }
  .badge-neutral { background: rgba(100, 116, 139, 0.15); color: var(--muted); border: 1px solid rgba(100, 116, 139, 0.3); }

  .result-bar-wrap {
    display: flex; height: 7px; border-radius: 4px; overflow: hidden;
    background: rgba(100, 116, 139, 0.15);
  }
  .result-bar-up { background: var(--accent2); transition: width 0.3s ease; }
  .result-bar-down { background: var(--danger); transition: width 0.3s ease; }

  .result-note { font-size: 0.75rem; color: var(--muted); margin: 0.6rem 0 0; line-height: 1.5; }

  .scan-row { display: flex; align-items: center; gap: 0.7rem; flex-wrap: wrap; margin-bottom: 1rem; }
  .btn-scan {
    background: rgba(99, 102, 241, 0.1); border: 1px solid var(--accent); color: var(--text);
    padding: 0.45rem 1rem; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer; transition: all 0.15s;
  }
  .btn-scan:not(:disabled):hover { background: rgba(99, 102, 241, 0.18); }
  .btn-scan:disabled { opacity: 0.6; cursor: not-allowed; }
  .scan-note { font-size: 0.72rem; color: var(--muted); }

  .rank-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0.3rem; }
  .rank-item {
    display: grid; grid-template-columns: 1.4rem 1fr auto auto auto; align-items: center;
    gap: 0.55rem; padding: 0.35rem 0; border-bottom: 1px solid var(--border); font-size: 0.82rem;
  }
  .rank-item:last-child { border-bottom: none; }
  .rank-num { color: var(--muted); font-variant-numeric: tabular-nums; text-align: center; font-weight: 700; }
  .rank-label { color: var(--text); font-weight: 600; }
  .rank-id { color: var(--muted); font-size: 0.72rem; }
  .rank-prob { font-weight: 700; font-variant-numeric: tabular-nums; }
  .rank-prob.up { color: var(--accent2); }
  .rank-prob.down { color: var(--danger); }
  .rank-bar-wrap { grid-column: 1 / -1; height: 5px; border-radius: 3px; background: rgba(100,116,139,0.15); overflow: hidden; }
  .rank-bar { display: block; height: 100%; }
  .rank-bar.up { background: var(--accent2); }
  .rank-bar.down { background: var(--danger); }
</style>
