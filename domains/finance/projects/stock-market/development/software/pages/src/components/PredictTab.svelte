<script lang="ts">
  import { onMount } from 'svelte';
  import { PARAMETERS, groupByDomain, DOMAIN_ORDER } from '../lib/parameters';
  import { computePrediction } from '../lib/prediction';
  import { loadParamStates, saveParamStates, saveSnapshot, loadSettings } from '../lib/store';
  import type { ParamState, AppSettings, PredictionSnapshot } from '../lib/types';
  import type { Parameter } from '../lib/types';
  import ScoreHeader from './ScoreHeader.svelte';
  import ParameterGroup from './ParameterGroup.svelte';
  import ResearchModal from './ResearchModal.svelte';
  import PredictionResultModal from './PredictionResultModal.svelte';

  export let ticker: string;

  let states: Record<string, ParamState> = initStates();
  let settings: AppSettings = { fredApiKey: '', corsProxyEnabled: false, llmModelId: null, llmDownloaded: false };
  let researchParam: Parameter | null = null;
  let showResultModal = false;
  let saveMsg = '';
  let tickerInput = ticker;

  // Init default states for all params
  function initStates(): Record<string, ParamState> {
    const s: Record<string, ParamState> = {};
    for (const p of PARAMETERS) {
      s[p.name] = { weight: 50, direction: 'neutral', value: null };
    }
    return s;
  }

  onMount(async () => {
    settings = await loadSettings();
    const saved = await loadParamStates(ticker);
    states = saved ?? initStates();
  });

  $: result = computePrediction(states);
  $: grouped = groupByDomain(PARAMETERS);

  async function handleTickerSubmit() {
    ticker = tickerInput.trim().toUpperCase();
    const saved = await loadParamStates(ticker);
    states = saved ?? initStates();
  }

  function handleParamChange(name: string, state: ParamState) {
    states = { ...states, [name]: state };
    // Debounce save to IndexedDB
    clearTimeout(_saveTimer);
    _saveTimer = setTimeout(() => saveParamStates(ticker, states), 800) as unknown as number;
  }
  let _saveTimer: number;

  async function handleSave() {
    const now  = new Date();
    const today = now.toISOString().slice(0, 10);
    const timeStr = now.toTimeString().slice(0, 8).replace(/:/g, '');
    const filename = `${ticker}_snapshot_${today}_${timeStr}.json`;

    const snap: PredictionSnapshot = {
      id: `${ticker}-${Date.now()}`,
      ticker,
      date: today,
      snapshotNum: 1,
      states: JSON.parse(JSON.stringify(states)),
      probUp: result.probUp,
      confidence: result.confidence,
      notes: '',
      createdAt: now.toISOString(),
    };

    const content = JSON.stringify({
      ticker,
      date: today,
      savedAt: snap.createdAt,
      prediction: { probUp: snap.probUp, confidence: snap.confidence },
      parameterStates: snap.states,
    }, null, 2);

    // Try File System Access API (Chrome/Edge) — opens native Save dialog
    let savedToFile = false;
    let savedFilename = filename;
    if ('showSaveFilePicker' in window) {
      try {
        const fh = await (window as any).showSaveFilePicker({
          suggestedName: filename,
          startIn: 'downloads',
          types: [{ description: 'Prediction Snapshot', accept: { 'application/json': ['.json'] } }],
        });
        const w = await fh.createWritable();
        await w.write(content);
        await w.close();
        savedToFile = true;
        savedFilename = fh.name ?? filename;
      } catch (e: any) {
        if (e?.name === 'AbortError') return; // user cancelled — do nothing
        // other error: fall through to download fallback
      }
    }

    // Fallback for Firefox/Safari — downloads directly to OS default Downloads
    if (!savedToFile) {
      const blob = new Blob([content], { type: 'application/json' });
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href = url; a.download = filename;
      document.body.appendChild(a); a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }

    // Also persist to IndexedDB for History tab
    const dbResult = await saveSnapshot(snap);

    saveMsg = savedToFile
      ? `✓ Saved as "${savedFilename}" to chosen folder. Also in History tab.`
      : `✓ Saved as "${filename}" to your Downloads folder. Also in History tab.`;
    if (dbResult === 'replaced') saveMsg += ' (oldest snapshot for today replaced — max 2/day)';
    setTimeout(() => saveMsg = '', 6000);
  }

  function handleReset() {
    if (!confirm('Reset all weights and directions for ' + ticker + '?')) return;
    states = initStates();
    saveParamStates(ticker, states);
  }

  function handleApplySuggestion(direction: 'up' | 'down', weight: number) {
    if (!researchParam) return;
    states = { ...states, [researchParam.name]: { ...states[researchParam.name], direction, weight } };
    saveParamStates(ticker, states);
    researchParam = null;
  }
</script>

<!-- Ticker input -->
<div class="ticker-bar">
  <input
    bind:value={tickerInput}
    placeholder="Ticker (e.g. AAPL)"
    on:keydown={e => e.key === 'Enter' && handleTickerSubmit()}
  />
  <button on:click={handleTickerSubmit}>Load</button>
</div>
{#if saveMsg}<div class="save-msg">{saveMsg}</div>{/if}

<!-- Live score header -->
<ScoreHeader
  {ticker}
  {result}
  onSave={handleSave}
  onReset={handleReset}
  onPredict={() => showResultModal = true}
/>

<!-- Parameter groups -->
{#each DOMAIN_ORDER as domain}
  {#if grouped.get(domain) && (grouped.get(domain) || []).length > 0}
    {@const domainParams = grouped.get(domain) || []}
    <ParameterGroup
      domainLabel={domainParams[0].domainLabel}
      params={domainParams}
      {states}
      onResearch={p => researchParam = p}
      on:change={e => handleParamChange(e.detail.name, e.detail.state)}
    />
  {/if}
{/each}

<!-- Research modal -->
<ResearchModal
  param={researchParam}
  {settings}
  onClose={() => researchParam = null}
  onApply={handleApplySuggestion}
/>

<!-- Prediction result modal -->
{#if showResultModal}
  <PredictionResultModal
    {result}
    {states}
    {ticker}
    onClose={() => showResultModal = false}
  />
{/if}

<style>
  .ticker-bar { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; }
  .ticker-bar input { width: 160px; font-size: 0.9rem; text-transform: uppercase; }
  .ticker-bar button {
    background: var(--accent); border: none; color: #fff;
    padding: 0.4rem 1rem; border-radius: 6px; font-size: 0.9rem;
  }
  .save-msg {
    font-size: 0.78rem; color: var(--accent2);
    background: rgba(52,211,153,0.08); border: 1px solid rgba(52,211,153,0.25);
    border-radius: 6px; padding: 0.4rem 0.85rem; margin-bottom: 0.75rem;
  }
</style>
