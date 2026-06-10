<script lang="ts">
  import type { Parameter, ParamState, Direction } from '../lib/types';
  export let param: Parameter;
  export let state: ParamState = { weight: 50, direction: 'neutral', value: null };
  export let onResearch: (p: Parameter) => void;

  function setDirection(d: Direction) {
    state = { ...state, direction: d };
    dispatch('change', state);
  }
  function setWeight(e: Event) {
    state = { ...state, weight: Number((e.target as HTMLInputElement).value) };
    dispatch('change', state);
  }

  function setValue(e: Event) {
    state = { ...state, value: Number((e.target as HTMLInputElement).value) };
    dispatch('change', state);
  }

  function clickUp() { setDirection(upActive ? 'neutral' : 'up'); }
  function clickDown() { setDirection(downActive ? 'neutral' : 'down'); }
  function clickResearch() { onResearch(param); }

  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher<{ change: ParamState }>();

  $: upActive   = state.direction === 'up';
  $: downActive = state.direction === 'down';
  $: neutral    = state.direction === 'neutral';
</script>

<tr class:neutral>
  <td class="name-cell">
    <span class="param-name">{param.name}</span>
    <span class="param-label">{param.label}</span>
  </td>
  <td class="value-cell">
    <input type="number" class="value-input"
      value={state.value ?? param.defaultValue}
      on:change={setValue}
      step="any"
    />
    <span class="unit">{param.unit}</span>
  </td>
  <td class="weight-cell">
    <div class="weight-row">
      <input type="range" min="1" max="100" value={state.weight}
        on:input={setWeight} class="weight-slider"
      />
      <span class="weight-val">{state.weight}</span>
    </div>
  </td>
  <td class="dir-cell">
    <div class="dir-btns">
      <button class="dir-btn up"   class:active={upActive}   on:click={clickUp}>▲ UP</button>
      <button class="dir-btn down" class:active={downActive} on:click={clickDown}>▼ DOWN</button>
    </div>
  </td>
  <td class="research-cell">
    <button class="research-btn" on:click={clickResearch} title="Open LLM research assistant for {param.label}">
      🔬
    </button>
  </td>
</tr>

<style>
  tr { border-bottom: 1px solid rgba(42,45,58,0.5); transition: background 0.1s; }
  tr:hover td { background: rgba(79,142,247,0.04); }
  tr.neutral { opacity: 0.7; }
  td { padding: 0.45rem 0.5rem; vertical-align: middle; }

  .name-cell { min-width: 160px; }
  .param-name { font-family: monospace; font-size: 0.78rem; color: var(--text); display: block; }
  .param-label { font-size: 0.68rem; color: var(--muted); }

  .value-cell { white-space: nowrap; }
  .value-input { width: 80px; font-size: 0.78rem; padding: 0.2rem 0.4rem; }
  .unit { font-size: 0.65rem; color: var(--muted); margin-left: 0.25rem; }

  .weight-cell { min-width: 140px; }
  .weight-row { display: flex; align-items: center; gap: 0.4rem; }
  .weight-slider { flex: 1; accent-color: var(--accent); cursor: pointer; }
  .weight-val { font-size: 0.78rem; font-family: monospace; color: var(--accent); min-width: 24px; text-align: right; }

  .dir-cell { white-space: nowrap; }
  .dir-btns { display: flex; gap: 0.3rem; }
  .dir-btn {
    font-size: 0.72rem; padding: 0.2rem 0.5rem; border-radius: 4px;
    border: 1px solid var(--border); background: none; color: var(--muted);
    transition: all 0.12s;
  }
  .dir-btn.up:hover,   .dir-btn.up.active   { background: rgba(52,211,153,0.15); border-color: var(--accent2); color: var(--accent2); }
  .dir-btn.down:hover, .dir-btn.down.active { background: rgba(248,113,113,0.15); border-color: var(--danger); color: var(--danger); }

  .research-btn {
    background: none; border: 1px solid var(--border);
    border-radius: 6px; padding: 0.2rem 0.45rem; font-size: 0.9rem;
    transition: all 0.12s;
  }
  .research-btn:hover { background: rgba(79,142,247,0.1); border-color: var(--accent); }
</style>
