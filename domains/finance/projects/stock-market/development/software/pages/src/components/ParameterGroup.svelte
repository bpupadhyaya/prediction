<script lang="ts">
  import type { Parameter, ParamState } from '../lib/types';
  import ParameterRow from './ParameterRow.svelte';
  import { createEventDispatcher } from 'svelte';

  export let domainLabel: string;
  export let params: Parameter[];
  export let states: Record<string, ParamState>;
  export let onResearch: (p: Parameter) => void;

  const dispatch = createEventDispatcher<{ change: { name: string; state: ParamState } }>();

  $: netScore = params.reduce((sum, p) => {
    const s = states[p.name];
    if (!s || s.direction === 'neutral') return sum;
    return sum + s.weight * (s.direction === 'up' ? 1 : -1);
  }, 0);
  $: totalWeight = params.reduce((sum, p) => {
    const s = states[p.name];
    return sum + (s?.direction !== 'neutral' ? (s?.weight ?? 0) : 0);
  }, 0);
  $: netDir = netScore > 0 ? 'positive' : netScore < 0 ? 'negative' : 'neutral';
  $: netLabel = netScore > 0 ? '▲ net bullish' : netScore < 0 ? '▼ net bearish' : '— neutral';
</script>

<div class="group">
  <div class="group-header">
    <span class="domain-name">{domainLabel}</span>
    <span class="group-meta">{params.length} params</span>
    <span class="net-label {netDir}">{netLabel}</span>
  </div>
  <div style="overflow-x:auto">
    <table class="param-table">
      <thead>
        <tr>
          <th>Parameter</th>
          <th>Current Value</th>
          <th>Weight (1–100)</th>
          <th>Direction</th>
          <th>Research</th>
        </tr>
      </thead>
      <tbody>
        {#each params as param (param.name)}
          <ParameterRow
            {param}
            state={states[param.name]}
            {onResearch}
            on:change={e => dispatch('change', { name: param.name, state: e.detail })}
          />
        {/each}
      </tbody>
    </table>
  </div>
</div>

<style>
  .group { margin-bottom: 1rem; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
  .group-header {
    display: flex; align-items: center; gap: 0.75rem;
    padding: 0.6rem 0.9rem;
    background: rgba(30,34,50,0.9);
    border-bottom: 1px solid var(--border);
  }
  .domain-name { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text); }
  .group-meta  { font-size: 0.72rem; color: var(--muted); }
  .net-label   { font-size: 0.75rem; font-weight: 600; margin-left: auto; }
  .net-label.positive { color: var(--accent2); }
  .net-label.negative { color: var(--danger); }
  .net-label.neutral  { color: var(--muted); }
  .param-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
  .param-table th {
    text-align: left; color: var(--muted); font-weight: 500; font-size: 0.72rem;
    padding: 0.35rem 0.5rem; border-bottom: 1px solid var(--border);
    background: var(--surface); position: sticky; top: 0;
  }
</style>
