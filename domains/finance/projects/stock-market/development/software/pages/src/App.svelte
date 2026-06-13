<script lang="ts">
  import PredictTab from './components/PredictTab.svelte';
  import HistoryTab from './components/HistoryTab.svelte';
  import SettingsTab from './components/SettingsTab.svelte';
  import OnnxPredictionCard from './components/OnnxPredictionCard.svelte';
  import ModelTransparency from './components/ModelTransparency.svelte';
  import VideoIntelligenceTab from './components/VideoIntelligenceTab.svelte';
  import type { VideoSignal } from './lib/types';
  import { PARAMETERS } from './lib/parameters';
  import { loadParamStates, saveParamStates } from './lib/store';

  let activeTab: 'predict' | 'model' | 'history' | 'settings' | 'intelligence' = 'predict';
  let ticker = 'AAPL';

  // When a YVIS signal is applied, inject it into the predict tab's parameter state
  async function handleSignalApply(signal: VideoSignal) {
    // Determine the ticker to update — prefer signal ticker, fall back to current
    const targetTicker = signal.ticker ?? ticker;

    // Load current states for the target ticker
    let states = await loadParamStates(targetTicker);
    if (!states) {
      // Init defaults if no state exists yet
      const s: Record<string, import('./lib/types').ParamState> = {};
      for (const p of PARAMETERS) {
        s[p.name] = { weight: 0, direction: 'neutral', value: null };
      }
      states = s;
    }

    // Find a matching parameter by name (case-insensitive) or use the parameterName directly if it matches
    const matchKey = Object.keys(states).find(
      k => k.toLowerCase() === signal.parameterName.toLowerCase()
    ) ?? signal.parameterName;

    states = {
      ...states,
      [matchKey]: {
        weight: signal.weight,
        direction: signal.direction,
        value: states[matchKey]?.value ?? null,
      },
    };

    await saveParamStates(targetTicker, states);

    // Switch to predict tab and update ticker so user can see the applied signal
    if (signal.ticker) ticker = signal.ticker;
    activeTab = 'predict';
  }
</script>

<header>
  <div class="brand">📈 Interactive Stock Predictor</div>
  <nav>
    <button class:active={activeTab === 'predict'}      on:click={() => activeTab = 'predict'}>Predict</button>
    <button class:active={activeTab === 'model'}        on:click={() => activeTab = 'model'}>Model</button>
    <button class:active={activeTab === 'history'}      on:click={() => activeTab = 'history'}>History</button>
    <button class:active={activeTab === 'intelligence'} on:click={() => activeTab = 'intelligence'}>Intelligence</button>
    <button class:active={activeTab === 'settings'}     on:click={() => activeTab = 'settings'}>Settings</button>
  </nav>
</header>

<main>
  {#if activeTab === 'predict'}
    <PredictTab bind:ticker />
  {:else if activeTab === 'model'}
    <OnnxPredictionCard />
    <ModelTransparency />
  {:else if activeTab === 'history'}
    <HistoryTab />
  {:else if activeTab === 'intelligence'}
    <VideoIntelligenceTab onSignalApply={handleSignalApply} />
  {:else}
    <SettingsTab />
  {/if}
</main>

<style>
  header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0.75rem 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    position: sticky;
    top: 0;
    z-index: 100;
  }
  .brand {
    font-weight: 700;
    font-size: 1rem;
    color: var(--text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  nav { display: flex; gap: 0.4rem; margin-left: auto; flex-wrap: wrap; }
  nav button {
    background: none;
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 0.35rem 0.9rem;
    border-radius: 8px;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.15s;
  }
  nav button.active  { background: var(--accent); border-color: var(--accent); color: #fff; }
  nav button:hover:not(.active) { border-color: var(--accent); color: var(--text); }
  main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1.5rem;
    overflow-x: hidden;
  }
</style>
