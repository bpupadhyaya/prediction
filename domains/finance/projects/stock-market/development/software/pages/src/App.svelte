<script lang="ts">
  import PredictTab from './components/PredictTab.svelte';
  import HistoryTab from './components/HistoryTab.svelte';
  import SettingsTab from './components/SettingsTab.svelte';
  import OnnxPredictionCard from './components/OnnxPredictionCard.svelte';

  let activeTab: 'predict' | 'model' | 'history' | 'settings' = 'predict';
  let ticker = 'AAPL';
</script>

<header>
  <div class="brand">📈 Interactive Stock Predictor</div>
  <nav>
    <button class:active={activeTab === 'predict'}  on:click={() => activeTab = 'predict'}>Predict</button>
    <button class:active={activeTab === 'model'}    on:click={() => activeTab = 'model'}>Model</button>
    <button class:active={activeTab === 'history'}  on:click={() => activeTab = 'history'}>History</button>
    <button class:active={activeTab === 'settings'} on:click={() => activeTab = 'settings'}>Settings</button>
  </nav>
</header>

<main>
  {#if activeTab === 'predict'}
    <PredictTab bind:ticker />
  {:else if activeTab === 'model'}
    <OnnxPredictionCard {ticker} />
  {:else if activeTab === 'history'}
    <HistoryTab />
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
