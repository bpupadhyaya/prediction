<script lang="ts">
  import { onMount } from 'svelte';
  import { loadSettings, saveSettings } from '../lib/store';
  import { LLM_MODELS, downloadModel, removeModel, isModelLoaded, getLoadedModelId } from '../lib/webllm';
  import type { AppSettings } from '../lib/types';

  let settings: AppSettings = { fredApiKey: '', corsProxyEnabled: false, llmModelId: null, llmDownloaded: false };
  let saved = false;
  let saveError = '';

  // Download state
  let downloading = false;
  let downloadingModelId: string | null = null;
  let downloadProgress = 0;
  let downloadText = '';
  let downloadError = '';

  onMount(async () => {
    try {
      settings = await loadSettings();
    } catch (err) {
      saveError = `Failed to load settings: ${err instanceof Error ? err.message : String(err)}`;
    }
  });

  async function handleSave() {
    saveError = '';
    try {
      await saveSettings(settings);
      saved = true;
      setTimeout(() => saved = false, 2000);
    } catch (err) {
      saveError = `Failed to save settings: ${err instanceof Error ? err.message : String(err)}`;
      setTimeout(() => saveError = '', 6000);
    }
  }

  async function handleDownload(modelId: string) {
    downloadError = '';
    downloading = true;
    downloadingModelId = modelId;
    downloadProgress = 0;
    downloadText = 'Starting download…';
    try {
      await downloadModel(modelId, (progress, text) => {
        downloadProgress = progress;
        downloadText = text;
      });
      settings = { ...settings, llmModelId: modelId, llmDownloaded: true };
      await saveSettings(settings);
    } catch (err) {
      downloadError = err instanceof Error ? err.message : String(err);
    } finally {
      downloading = false;
      downloadingModelId = null;
    }
  }

  async function handleRemove(modelId: string) {
    downloadError = '';
    try {
      await removeModel(modelId);
      if (settings.llmModelId === modelId) {
        settings = { ...settings, llmModelId: null, llmDownloaded: false };
        await saveSettings(settings);
      }
    } catch (err) {
      downloadError = err instanceof Error ? err.message : String(err);
    }
  }

  function isCurrentModel(modelId: string): boolean {
    return settings.llmModelId === modelId && settings.llmDownloaded;
  }

  function isActivelyLoaded(modelId: string): boolean {
    return isModelLoaded() && getLoadedModelId() === modelId;
  }
</script>

<div class="settings">
  <h2>Settings</h2>

  {#if saveError}
    <div class="error-msg" role="alert">{saveError}</div>
  {/if}

  <!-- LLM Model Manager -->
  <section>
    <h3>🤖 AI Research Assistant</h3>
    <p class="phase-note">
      Download a local LLM model to power the AI Research Assistant. Models run entirely in your
      browser via WebGPU — no data leaves your device. Requires a GPU-capable browser (Chrome 113+
      or Edge 113+).
    </p>

    {#if downloadError}
      <div class="download-error" role="alert">{downloadError}</div>
    {/if}

    <div class="model-list">
      {#each LLM_MODELS as model}
        <div class="model-card" class:model-card--active={isCurrentModel(model.id)}>
          <div class="model-info">
            <div class="model-label">
              {model.label}
              {#if isActivelyLoaded(model.id)}
                <span class="badge-loaded">✓ Loaded</span>
              {:else if isCurrentModel(model.id)}
                <span class="badge-downloaded">✓ Downloaded</span>
              {/if}
            </div>
            <div class="model-desc">{model.description}</div>
            <div class="model-size">{model.sizeGB} GB · stored in browser cache (OPFS)</div>

            {#if downloading && downloadingModelId === model.id}
              <div class="progress-wrap" role="status" aria-live="polite">
                <div
                  class="progress-bar"
                  role="progressbar"
                  aria-valuenow={downloadProgress}
                  aria-valuemin={0}
                  aria-valuemax={100}
                >
                  <div class="progress-fill" style="width:{downloadProgress}%"></div>
                </div>
                <div class="progress-text">{downloadText} ({downloadProgress}%)</div>
              </div>
            {/if}
          </div>

          <div class="model-actions">
            {#if isCurrentModel(model.id)}
              <button
                class="btn-remove"
                on:click={() => handleRemove(model.id)}
                disabled={downloading}
                title="Remove {model.label} from browser cache"
              >
                Remove
              </button>
            {:else}
              <button
                class="btn-download"
                on:click={() => handleDownload(model.id)}
                disabled={downloading}
                title="Download {model.label} ({model.sizeGB} GB)"
              >
                {downloading && downloadingModelId === model.id ? '⏳ Downloading…' : '⬇ Download'}
              </button>
            {/if}
          </div>
        </div>
      {/each}
    </div>

    <p class="storage-note">
      <strong>Storage note:</strong> Models are stored in your browser's Origin Private File System
      (OPFS), managed by the browser — not accessible as a regular folder on your computer.
      Use the "Remove" button to free space, or clear site storage in your browser settings
      (Settings → Privacy → Site data → stock-predictor).
    </p>
  </section>

  <!-- Data Sources -->
  <section>
    <h3>📡 Data Sources</h3>
    <div class="field">
      <label for="fred-key">FRED API Key (free at fred.stlouisfed.org)</label>
      <input
        id="fred-key"
        type="password"
        placeholder="your_fred_api_key"
        bind:value={settings.fredApiKey}
        autocomplete="off"
      />
      <span class="field-note">Used to auto-fetch macro data (VIX, yield curve, etc.) into parameter values.</span>
    </div>
    <div class="field">
      <label for="td-key">Twelve Data API Key (free at twelvedata.com)</label>
      <input
        id="td-key"
        type="password"
        placeholder="your_twelvedata_api_key"
        bind:value={settings.twelveDataApiKey}
        autocomplete="off"
      />
      <span class="field-note">Enables live stock prediction in the Model tab for any global ticker (AAPL works without a key). Crypto needs no key.</span>
    </div>
    <div class="field toggle-field">
      <label>
        <input type="checkbox" bind:checked={settings.corsProxyEnabled} />
        Enable CORS proxy for blocked URLs (api.allorigins.win)
      </label>
      <span class="field-note warn">
        When enabled, URLs you fetch in the Research popup are routed through a third-party proxy.
        Do not fetch sensitive documents when this is on.
      </span>
    </div>
  </section>

  <button class="btn-save" on:click={handleSave} title="Save settings">
    {saved ? '✓ Saved' : 'Save Settings'}
  </button>
</div>

<style>
  .settings { max-width: 720px; }
  h2 { font-size: 1.1rem; font-weight: 700; margin-bottom: 1.25rem; color: var(--text); }
  section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.1rem 1.25rem;
    margin-bottom: 1rem;
    overflow: hidden;
  }
  h3 { font-size: 0.9rem; font-weight: 700; margin-bottom: 0.6rem; color: var(--text); }
  .phase-note { font-size: 0.78rem; color: var(--muted); margin-bottom: 0.75rem; line-height: 1.6; }
  .error-msg {
    font-size: 0.78rem;
    color: var(--danger);
    background: rgba(248,113,113,0.08);
    border: 1px solid rgba(248,113,113,0.2);
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.75rem;
  }
  .model-list { display: flex; flex-direction: column; gap: 0.6rem; margin-bottom: 0.75rem; }
  .model-card {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    background: rgba(42,45,58,0.3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.65rem 0.9rem;
    transition: border-color 0.15s;
  }
  .model-card--active {
    border-color: rgba(52,211,153,0.3);
    background: rgba(52,211,153,0.05);
  }
  .model-info { flex: 1; min-width: 0; }
  .model-label {
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .model-desc  { font-size: 0.75rem; color: var(--muted); margin: 0.1rem 0; }
  .model-size  { font-size: 0.75rem; color: var(--muted); }
  .badge-loaded {
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.1rem 0.45rem;
    border-radius: 99px;
    background: rgba(52,211,153,0.15);
    color: var(--accent2);
    border: 1px solid rgba(52,211,153,0.3);
    white-space: nowrap;
  }
  .badge-downloaded {
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.1rem 0.45rem;
    border-radius: 99px;
    background: rgba(79,142,247,0.12);
    color: var(--accent);
    border: 1px solid rgba(79,142,247,0.25);
    white-space: nowrap;
  }
  .progress-wrap { margin-top: 0.5rem; }
  .progress-bar {
    height: 4px;
    background: rgba(79,142,247,0.15);
    border-radius: 2px;
    overflow: hidden;
  }
  .progress-fill {
    height: 100%;
    background: var(--accent);
    border-radius: 2px;
    transition: width 0.2s ease;
  }
  .progress-text { font-size: 0.72rem; color: var(--muted); margin-top: 0.25rem; }
  .model-actions { display: flex; flex-direction: column; gap: 0.4rem; align-items: flex-end; flex-shrink: 0; padding-top: 0.1rem; }
  .btn-download {
    background: rgba(79,142,247,0.15);
    border: 1px solid rgba(79,142,247,0.3);
    color: var(--accent);
    padding: 0.3rem 0.8rem;
    border-radius: 8px;
    font-size: 0.8rem;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.15s;
  }
  .btn-download:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-download:not(:disabled):hover { background: rgba(79,142,247,0.25); }
  .btn-remove {
    background: none;
    border: 1px solid rgba(239,68,68,0.3);
    color: var(--danger);
    padding: 0.3rem 0.8rem;
    border-radius: 8px;
    font-size: 0.8rem;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.15s;
  }
  .btn-remove:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-remove:not(:disabled):hover { background: rgba(239,68,68,0.08); }
  .download-error {
    font-size: 0.75rem;
    color: var(--danger);
    background: rgba(239,68,68,0.08);
    border: 1px solid rgba(239,68,68,0.2);
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.75rem;
    line-height: 1.5;
    word-break: break-word;
  }
  .storage-note { font-size: 0.75rem; color: var(--muted); line-height: 1.6; margin-top: 0.5rem; }
  .field { display: flex; flex-direction: column; gap: 0.3rem; margin-bottom: 0.75rem; }
  .field label { font-size: 0.82rem; font-weight: 600; color: var(--text); }
  .field input[type="password"] { max-width: 320px; border-radius: 8px; }
  .field-note { font-size: 0.75rem; color: var(--muted); }
  .field-note.warn { color: var(--warn); }
  .toggle-field label { display: flex; align-items: center; gap: 0.4rem; cursor: pointer; font-size: 0.82rem; }
  .btn-save {
    background: var(--accent);
    border: none;
    color: #fff;
    padding: 0.5rem 1.5rem;
    border-radius: 8px;
    font-size: 0.9rem;
    margin-top: 0.5rem;
    cursor: pointer;
    transition: all 0.15s;
  }
  .btn-save:hover { filter: brightness(1.1); }
</style>
