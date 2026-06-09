<script lang="ts">
  import { onMount } from 'svelte';
  import { loadSettings, saveSettings } from '../lib/store';
  import { LLM_MODELS } from '../lib/webllm';
  import type { AppSettings } from '../lib/types';

  let settings: AppSettings = { fredApiKey: '', corsProxyEnabled: false, llmModelId: null, llmDownloaded: false };
  let saved = false;

  onMount(async () => { settings = await loadSettings(); });

  async function handleSave() {
    await saveSettings(settings);
    saved = true;
    setTimeout(() => saved = false, 2000);
  }
</script>

<div class="settings">
  <h2>Settings</h2>

  <!-- LLM Model Manager -->
  <section>
    <h3>🤖 AI Research Assistant (Phase 2)</h3>
    <p class="phase-note">
      WebLLM integration is coming in Phase 2. When available, you'll be able to download
      a local LLM model that runs entirely in your browser — no data leaves your device.
    </p>
    <div class="model-list">
      {#each LLM_MODELS as model}
        <div class="model-card">
          <div class="model-info">
            <div class="model-label">{model.label}</div>
            <div class="model-desc">{model.description}</div>
            <div class="model-size">{model.sizeGB} GB · stored in browser cache (OPFS)</div>
          </div>
          <div class="model-actions">
            <button class="btn-download" disabled>⬇ Download (Phase 2)</button>
          </div>
        </div>
      {/each}
    </div>
    <p class="storage-note">
      <strong>Storage note:</strong> Models are stored in your browser's Origin Private File System (OPFS),
      managed by the browser itself — not accessible as a regular folder on your computer.
      Use the "Remove" button (available in Phase 2) to free the space, or clear site storage in
      your browser settings (Settings → Privacy → Site data → stock-predictor).
    </p>
  </section>

  <!-- Data Sources -->
  <section>
    <h3>📡 Data Sources</h3>
    <div class="field">
      <label for="fred-key">FRED API Key (free at fred.stlouisfed.org)</label>
      <input id="fred-key" type="password" placeholder="your_fred_api_key"
        bind:value={settings.fredApiKey} />
      <span class="field-note">Used to auto-fetch macro data (VIX, yield curve, etc.) into parameter values.</span>
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

  <button class="btn-save" on:click={handleSave}>
    {saved ? '✓ Saved' : 'Save Settings'}
  </button>
</div>

<style>
  .settings { max-width: 720px; }
  h2 { font-size: 1.1rem; font-weight: 700; margin-bottom: 1.25rem; }
  section { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 1.1rem 1.25rem; margin-bottom: 1rem; }
  h3 { font-size: 0.9rem; font-weight: 700; margin-bottom: 0.6rem; }
  .phase-note { font-size: 0.78rem; color: var(--muted); margin-bottom: 0.75rem; line-height: 1.6; }
  .model-list { display: flex; flex-direction: column; gap: 0.6rem; margin-bottom: 0.75rem; }
  .model-card { display: flex; align-items: center; gap: 1rem; background: rgba(42,45,58,0.3); border: 1px solid var(--border); border-radius: 8px; padding: 0.65rem 0.9rem; }
  .model-info { flex: 1; }
  .model-label { font-weight: 600; font-size: 0.85rem; }
  .model-desc  { font-size: 0.75rem; color: var(--muted); margin: 0.1rem 0; }
  .model-size  { font-size: 0.7rem; color: var(--muted); }
  .btn-download { background: rgba(79,142,247,0.15); border: 1px solid rgba(79,142,247,0.2); color: var(--muted); padding: 0.3rem 0.8rem; border-radius: 6px; font-size: 0.8rem; cursor: not-allowed; }
  .storage-note { font-size: 0.74rem; color: var(--muted); line-height: 1.6; margin-top: 0.5rem; }
  .field { display: flex; flex-direction: column; gap: 0.3rem; margin-bottom: 0.75rem; }
  .field label { font-size: 0.82rem; font-weight: 600; }
  .field input[type="password"] { max-width: 320px; }
  .field-note { font-size: 0.72rem; color: var(--muted); }
  .field-note.warn { color: var(--warn); }
  .toggle-field label { display: flex; align-items: center; gap: 0.4rem; cursor: pointer; font-size: 0.82rem; }
  .btn-save { background: var(--accent); border: none; color: #fff; padding: 0.5rem 1.5rem; border-radius: 8px; font-size: 0.9rem; margin-top: 0.5rem; }
</style>
