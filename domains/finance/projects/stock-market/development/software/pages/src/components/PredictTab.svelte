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

  export let ticker: string;

  let states: Record<string, ParamState> = initStates();
  let settings: AppSettings = { fredApiKey: '', corsProxyEnabled: false, llmModelId: null, llmDownloaded: false };
  let researchParam: Parameter | null = null;
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
    const today = new Date().toISOString().slice(0, 10);
    const snap: PredictionSnapshot = {
      id: `${ticker}-${Date.now()}`,
      ticker,
      date: today,
      snapshotNum: 1,
      states: JSON.parse(JSON.stringify(states)),
      probUp: result.probUp,
      confidence: result.confidence,
      notes: '',
      createdAt: new Date().toISOString(),
    };
    await saveSnapshot(snap);
    saveMsg = '✓ Snapshot saved';
    setTimeout(() => saveMsg = '', 2500);
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
  {#if saveMsg}<span class="save-msg">{saveMsg}</span>{/if}
</div>

<!-- Live score header -->
<ScoreHeader
  {ticker}
  {result}
  onSave={handleSave}
  onReset={handleReset}
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

<style>
  .ticker-bar { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; }
  .ticker-bar input { width: 160px; font-size: 0.9rem; text-transform: uppercase; }
  .ticker-bar button {
    background: var(--accent); border: none; color: #fff;
    padding: 0.4rem 1rem; border-radius: 6px; font-size: 0.9rem;
  }
  .save-msg { font-size: 0.8rem; color: var(--accent2); margin-left: 0.5rem; }
</style>
