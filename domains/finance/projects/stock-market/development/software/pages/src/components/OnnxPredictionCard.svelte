<script lang="ts">
  import { onMount } from 'svelte';
  import { loadModel, predictOnnx, isModelLoaded } from '../lib/onnx';
  import type { OnnxFeatures, OnnxPrediction } from '../lib/onnx';

  export let ticker: string;

  // Loading state
  let modelLoading = false;
  let modelReady = false;
  let loadError = '';
  let loadProgress = 0;

  // Inference state
  let inferring = false;
  let inferError = '';
  let prediction: OnnxPrediction | null = null;

  // Feature inputs — sensible defaults
  let features: OnnxFeatures = {
    return_1d:    0,
    return_5d:    0,
    return_20d:   0,
    ma5_ratio:    1.0,
    ma20_ratio:   1.0,
    ma50_ratio:   1.0,
    volatility_20: 0.02,
    volume_ratio:  1.0,
    rsi:          50,
  };

  onMount(async () => {
    if (isModelLoaded()) {
      modelReady = true;
      return;
    }
    modelLoading = true;
    loadError = '';
    try {
      await loadModel((pct) => { loadProgress = pct; });
      modelReady = true;
    } catch (err) {
      loadError = err instanceof Error ? err.message : String(err);
    } finally {
      modelLoading = false;
    }
  });

  async function handleRunModel() {
    inferError = '';
    prediction = null;
    inferring = true;
    try {
      prediction = await predictOnnx(features);
    } catch (err) {
      inferError = err instanceof Error ? err.message : String(err);
    } finally {
      inferring = false;
    }
  }

  function directionColor(dir: 'up' | 'down' | 'neutral'): string {
    if (dir === 'up')   return 'badge-up';
    if (dir === 'down') return 'badge-down';
    return 'badge-neutral';
  }

  function directionLabel(dir: 'up' | 'down' | 'neutral'): string {
    if (dir === 'up')   return 'Bullish';
    if (dir === 'down') return 'Bearish';
    return 'Neutral';
  }
</script>

<div class="onnx-card">
  <h2>Automated Model Prediction</h2>
  <p class="subtitle">
    GradientBoosting classifier — enter the 9 technical features for <strong>{ticker}</strong> to
    get a model-driven directional probability.
  </p>

  <!-- Loading state -->
  {#if modelLoading}
    <div class="loading-box">
      <div class="loading-label">Loading ONNX model… {loadProgress}%</div>
      <div class="progress-bar">
        <div class="progress-fill" style="width:{loadProgress}%"></div>
      </div>
      <div class="loading-note">~226 KB · runs entirely in your browser</div>
    </div>
  {:else if loadError}
    <div class="error-box">
      <div class="error-title">Failed to load model</div>
      <div class="error-msg">{loadError}</div>
      <button class="btn-retry" on:click={() => {
        loadError = '';
        modelLoading = true;
        loadProgress = 0;
        loadModel(pct => { loadProgress = pct; })
          .then(() => { modelReady = true; })
          .catch(e => { loadError = e instanceof Error ? e.message : String(e); })
          .finally(() => { modelLoading = false; });
      }}>Retry</button>
    </div>
  {:else if modelReady}
    <!-- Feature inputs -->
    <div class="features-grid">
      <div class="feature-group">
        <h3>Returns</h3>
        <label>
          <span>1-day return</span>
          <input type="number" step="0.001" bind:value={features.return_1d} />
          <span class="hint">e.g. 0.012 = +1.2%</span>
        </label>
        <label>
          <span>5-day return</span>
          <input type="number" step="0.001" bind:value={features.return_5d} />
          <span class="hint">e.g. -0.03 = -3%</span>
        </label>
        <label>
          <span>20-day return</span>
          <input type="number" step="0.001" bind:value={features.return_20d} />
        </label>
      </div>

      <div class="feature-group">
        <h3>Moving Average Ratios</h3>
        <label>
          <span>MA5 ratio (close / MA5)</span>
          <input type="number" step="0.001" bind:value={features.ma5_ratio} />
          <span class="hint">1.0 = at 5-day MA</span>
        </label>
        <label>
          <span>MA20 ratio (close / MA20)</span>
          <input type="number" step="0.001" bind:value={features.ma20_ratio} />
        </label>
        <label>
          <span>MA50 ratio (close / MA50)</span>
          <input type="number" step="0.001" bind:value={features.ma50_ratio} />
        </label>
      </div>

      <div class="feature-group">
        <h3>Momentum &amp; Volume</h3>
        <label>
          <span>Volatility 20d (std dev of returns)</span>
          <input type="number" step="0.001" min="0" bind:value={features.volatility_20} />
          <span class="hint">e.g. 0.02 = 2% daily vol</span>
        </label>
        <label>
          <span>Volume ratio (vol / 20d avg)</span>
          <input type="number" step="0.01" min="0" bind:value={features.volume_ratio} />
          <span class="hint">1.0 = average volume</span>
        </label>
        <label>
          <span>RSI (14-period, 0–100)</span>
          <input type="number" step="0.1" min="0" max="100" bind:value={features.rsi} />
          <span class="hint">50 = neutral</span>
        </label>
      </div>
    </div>

    <!-- Run button -->
    <div class="run-row">
      <button class="btn-run" on:click={handleRunModel} disabled={inferring}>
        {inferring ? 'Running…' : 'Run Model'}
      </button>
    </div>

    <!-- Inference error -->
    {#if inferError}
      <div class="error-box">
        <div class="error-title">Inference error</div>
        <div class="error-msg">{inferError}</div>
      </div>
    {/if}

    <!-- Result -->
    {#if prediction}
      <div class="result-card">
        <div class="result-header">
          <span class="result-ticker">{ticker}</span>
          <span class="direction-badge {directionColor(prediction.direction)}">
            {directionLabel(prediction.direction)}
          </span>
        </div>
        <div class="result-metrics">
          <div class="metric">
            <div class="metric-label">Prob(UP)</div>
            <div class="metric-value up">{prediction.probUp.toFixed(1)}%</div>
          </div>
          <div class="metric">
            <div class="metric-label">Prob(DOWN)</div>
            <div class="metric-value down">{prediction.probDown.toFixed(1)}%</div>
          </div>
          <div class="metric">
            <div class="metric-label">Confidence</div>
            <div class="metric-value">{prediction.confidence}%</div>
          </div>
        </div>
        <div class="result-bar-wrap">
          <div class="result-bar-up" style="width:{prediction.probUp}%"></div>
          <div class="result-bar-down" style="width:{prediction.probDown}%"></div>
        </div>
        <p class="result-note">
          Model: GradientBoosting classifier · 9 features · runs locally in your browser
        </p>
      </div>
    {/if}
  {/if}
</div>

<style>
  .onnx-card {
    max-width: 860px;
  }

  h2 {
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 0.3rem;
  }

  .subtitle {
    font-size: 0.82rem;
    color: var(--muted);
    margin-bottom: 1.25rem;
    line-height: 1.6;
  }

  /* Loading */
  .loading-box {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.25rem 1.5rem;
  }

  .loading-label {
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
  }

  .progress-bar {
    height: 6px;
    background: rgba(79, 142, 247, 0.15);
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 0.4rem;
  }

  .progress-fill {
    height: 100%;
    background: var(--accent);
    border-radius: 3px;
    transition: width 0.2s ease;
  }

  .loading-note {
    font-size: 0.72rem;
    color: var(--muted);
  }

  /* Error */
  .error-box {
    background: rgba(239, 68, 68, 0.06);
    border: 1px solid rgba(239, 68, 68, 0.25);
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 1rem;
  }

  .error-title {
    font-weight: 700;
    font-size: 0.85rem;
    color: var(--danger);
    margin-bottom: 0.3rem;
  }

  .error-msg {
    font-size: 0.78rem;
    color: var(--danger);
    line-height: 1.5;
    word-break: break-word;
  }

  .btn-retry {
    margin-top: 0.6rem;
    background: none;
    border: 1px solid var(--danger);
    color: var(--danger);
    padding: 0.3rem 0.9rem;
    border-radius: 6px;
    font-size: 0.8rem;
  }

  .btn-retry:hover {
    background: rgba(239, 68, 68, 0.08);
  }

  /* Feature inputs */
  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .feature-group {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.9rem 1rem;
  }

  h3 {
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--accent);
    margin-bottom: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    margin-bottom: 0.6rem;
    font-size: 0.8rem;
    font-weight: 600;
  }

  label input[type="number"] {
    width: 100%;
    font-size: 0.85rem;
  }

  .hint {
    font-size: 0.68rem;
    font-weight: 400;
    color: var(--muted);
  }

  /* Run button */
  .run-row {
    margin-bottom: 1rem;
  }

  .btn-run {
    background: var(--accent);
    border: none;
    color: #fff;
    padding: 0.5rem 2rem;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 600;
  }

  .btn-run:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }

  .btn-run:not(:disabled):hover {
    filter: brightness(1.1);
  }

  /* Result card */
  .result-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.1rem 1.25rem;
    margin-top: 0.5rem;
  }

  .result-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.9rem;
  }

  .result-ticker {
    font-weight: 800;
    font-size: 1rem;
    letter-spacing: 0.04em;
  }

  .direction-badge {
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.18rem 0.65rem;
    border-radius: 99px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .badge-up {
    background: rgba(52, 211, 153, 0.15);
    color: var(--accent2);
    border: 1px solid rgba(52, 211, 153, 0.3);
  }

  .badge-down {
    background: rgba(239, 68, 68, 0.12);
    color: var(--danger);
    border: 1px solid rgba(239, 68, 68, 0.3);
  }

  .badge-neutral {
    background: rgba(100, 116, 139, 0.15);
    color: var(--muted);
    border: 1px solid rgba(100, 116, 139, 0.3);
  }

  .result-metrics {
    display: flex;
    gap: 2rem;
    margin-bottom: 0.9rem;
  }

  .metric {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
  }

  .metric-label {
    font-size: 0.72rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .metric-value {
    font-size: 1.3rem;
    font-weight: 800;
  }

  .metric-value.up   { color: var(--accent2); }
  .metric-value.down { color: var(--danger); }

  /* Probability bar */
  .result-bar-wrap {
    display: flex;
    height: 8px;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 0.65rem;
    background: rgba(100, 116, 139, 0.15);
  }

  .result-bar-up {
    background: var(--accent2);
    transition: width 0.3s ease;
  }

  .result-bar-down {
    background: var(--danger);
    transition: width 0.3s ease;
  }

  .result-note {
    font-size: 0.68rem;
    color: var(--muted);
  }
</style>
