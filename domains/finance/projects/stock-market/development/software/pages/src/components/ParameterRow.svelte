<script lang="ts">
  import type { Parameter, ParamState, Direction } from '../lib/types';
  export let param: Parameter;
  export let state: ParamState = { weight: 0, direction: 'neutral', value: null };
  export let onResearch: (p: Parameter) => void;
  export let expanded = false;

  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher<{ change: ParamState; toggle: void }>();

  function setDirection(d: Direction) {
    state = { ...state, direction: d };
    dispatch('change', state);
  }
  function setWeight(e: Event) {
    state = { ...state, weight: Number((e.target as HTMLInputElement).value) };
    dispatch('change', state);
  }
  function setValue(e: Event) {
    const raw = (e.target as HTMLInputElement).value;
    state = { ...state, value: raw === '' ? null : Number(raw) };
    dispatch('change', state);
  }
  function clickUp()       { setDirection(upActive   ? 'neutral' : 'up'); }
  function clickDown()     { setDirection(downActive ? 'neutral' : 'down'); }
  function clickResearch() { onResearch(param); }
  function clickToggle()   { dispatch('toggle'); }

  $: upActive   = state.direction === 'up';
  $: downActive = state.direction === 'down';
  $: neutral    = state.direction === 'neutral';
</script>

<tr class:neutral class:expanded>
  <td class="name-cell">
    <button class="expand-btn" on:click={clickToggle} title="Show definitions for {param.label}" aria-label="Toggle definition for {param.label}">
      <span class="chev" class:open={expanded}>▶</span>
    </button>
    <div class="name-info">
      <span class="param-name">{param.name}</span>
      <span class="param-label">{param.label}</span>
    </div>
  </td>
  <td class="value-cell">
    <input
      type="number"
      class="value-input"
      value={state.value ?? param.defaultValue}
      on:change={setValue}
      step="any"
      aria-label="Current value for {param.label}"
    />
    <span class="unit">{param.unit}</span>
  </td>
  <td class="weight-cell">
    <div class="weight-row">
      <input
        type="range"
        min="0"
        max="100"
        value={state.weight}
        on:input={setWeight}
        class="weight-slider"
        aria-label="Weight for {param.label}"
      />
      <span class="weight-val">{state.weight}</span>
    </div>
  </td>
  <td class="dir-cell">
    <div class="dir-btns">
      <button
        class="dir-btn up"
        class:active={upActive}
        on:click={clickUp}
        title="Set {param.label} direction to UP (bullish)"
      >▲ UP</button>
      <button
        class="dir-btn down"
        class:active={downActive}
        on:click={clickDown}
        title="Set {param.label} direction to DOWN (bearish)"
      >▼ DOWN</button>
    </div>
  </td>
  <td class="research-cell">
    <button class="research-btn" on:click={clickResearch} title="Research {param.label}" aria-label="Open research assistant for {param.label}">🔬</button>
  </td>
</tr>

<style>
  tr { border-bottom: 1px solid rgba(42,45,58,0.5); transition: background 0.15s; }
  tr:hover td { background: rgba(79,142,247,0.05); }
  tr.neutral  { opacity: 0.7; }
  tr.expanded td { background: rgba(79,142,247,0.06); }
  td { padding: 0.45rem 0.5rem; vertical-align: middle; }

  .name-cell { min-width: 180px; display: flex !important; align-items: center; gap: 0.4rem; overflow: hidden; }
  .expand-btn {
    background: none;
    border: none;
    padding: 0.15rem 0.3rem;
    color: var(--muted);
    cursor: pointer;
    flex-shrink: 0;
    line-height: 1;
    transition: color 0.15s;
    border-radius: 4px;
  }
  .expand-btn:hover { color: var(--accent); }
  .chev { font-size: 0.6rem; display: inline-block; transition: transform 0.18s; }
  .chev.open { transform: rotate(90deg); color: var(--accent); }
  .name-info { display: flex; flex-direction: column; gap: 1px; overflow: hidden; min-width: 0; }
  .param-name  {
    font-family: monospace;
    font-size: 0.78rem;
    color: var(--text);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .param-label {
    font-size: 0.75rem;
    color: var(--muted);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .value-cell { white-space: nowrap; }
  .value-input {
    width: 80px;
    font-size: 0.78rem;
    padding: 0.2rem 0.4rem;
    border-radius: 8px;
    transition: border-color 0.15s;
  }
  .unit { font-size: 0.75rem; color: var(--muted); margin-left: 0.25rem; }

  .weight-cell { min-width: 140px; }
  .weight-row  { display: flex; align-items: center; gap: 0.4rem; }
  .weight-slider { flex: 1; accent-color: var(--accent); cursor: pointer; }
  .weight-val    { font-size: 0.78rem; font-family: monospace; color: var(--accent); min-width: 24px; text-align: right; }

  .dir-cell { white-space: nowrap; }
  .dir-btns { display: flex; gap: 0.3rem; }
  .dir-btn {
    font-size: 0.75rem;
    padding: 0.2rem 0.5rem;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: none;
    color: var(--muted);
    cursor: pointer;
    transition: all 0.15s;
  }
  .dir-btn.up:hover,   .dir-btn.up.active   { background: rgba(52,211,153,0.15); border-color: var(--accent2); color: var(--accent2); }
  .dir-btn.down:hover, .dir-btn.down.active { background: rgba(248,113,113,0.15); border-color: var(--danger);  color: var(--danger); }

  .research-btn {
    background: none;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.2rem 0.45rem;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.15s;
  }
  .research-btn:hover { background: rgba(79,142,247,0.1); border-color: var(--accent); }
</style>
