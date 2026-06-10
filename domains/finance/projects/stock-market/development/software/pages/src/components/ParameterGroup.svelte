<script lang="ts">
  import type { Parameter, ParamState } from '../lib/types';
  import ParameterRow from './ParameterRow.svelte';
  import { createEventDispatcher } from 'svelte';

  export let domainLabel: string;
  export let params: Parameter[];
  export let states: Record<string, ParamState>;
  export let onResearch: (p: Parameter) => void;

  const dispatch = createEventDispatcher<{ change: { name: string; state: ParamState } }>();

  let expandedParams = new Set<string>();

  function toggleExpand(name: string) {
    if (expandedParams.has(name)) expandedParams.delete(name);
    else expandedParams.add(name);
    expandedParams = expandedParams; // trigger reactivity
  }

  $: netScore = params.reduce((sum, p) => {
    const s = states[p.name];
    if (!s || s.direction === 'neutral') return sum;
    return sum + s.weight * (s.direction === 'up' ? 1 : -1);
  }, 0);
  $: netDir   = netScore > 0 ? 'positive' : netScore < 0 ? 'negative' : 'neutral';
  $: netLabel = netScore > 0 ? '▲ net bullish' : netScore < 0 ? '▼ net bearish' : '— neutral';
</script>

<div class="group">
  <div class="group-header">
    <span class="domain-name">{domainLabel}</span>
    <span class="group-meta">{params.length} params</span>
    <span class="net-label {netDir}">{netLabel}</span>
  </div>
  <div class="table-scroll">
    <table class="param-table">
      <thead>
        <tr>
          <th>Parameter</th>
          <th>Current Value</th>
          <th>Weight (0–100)</th>
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
            expanded={expandedParams.has(param.name)}
            on:toggle={() => toggleExpand(param.name)}
            on:change={e => dispatch('change', { name: param.name, state: e.detail })}
          />
          {#if expandedParams.has(param.name)}
          <tr class="def-row">
            <td colspan="5" class="def-cell">
              <div class="def-inner">
                <div class="def-section plain-section">
                  <span class="def-label plain-label">IN PLAIN ENGLISH</span>
                  <p class="def-text">{param.layman}</p>
                </div>
                <div class="def-section tech-section">
                  <span class="def-label tech-label">TECHNICAL</span>
                  <p class="def-text">{param.technical}</p>
                </div>
              </div>
            </td>
          </tr>
          {/if}
        {/each}
      </tbody>
    </table>
  </div>
</div>

<style>
  .group {
    margin-bottom: 1rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
  }
  .group-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 0.9rem;
    background: rgba(30,34,50,0.9);
    border-bottom: 1px solid var(--border);
  }
  .domain-name {
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .group-meta  { font-size: 0.75rem; color: var(--muted); white-space: nowrap; }
  .net-label   { font-size: 0.75rem; font-weight: 600; margin-left: auto; white-space: nowrap; }
  .net-label.positive { color: var(--accent2); }
  .net-label.negative { color: var(--danger); }
  .net-label.neutral  { color: var(--muted); }

  .table-scroll { overflow-x: auto; }
  .param-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
  .param-table th {
    text-align: left;
    color: var(--muted);
    font-weight: 500;
    font-size: 0.75rem;
    padding: 0.35rem 0.5rem;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
    position: sticky;
    top: 0;
    white-space: nowrap;
  }

  /* Definition row */
  :global(.def-row) { border-bottom: 2px solid rgba(79,142,247,0.2); }
  :global(.def-cell) { padding: 0 !important; }
  :global(.def-inner) {
    display: grid;
    grid-template-columns: 1fr 1fr;
    background: rgba(15,17,23,0.75);
  }
  :global(.def-section) {
    padding: 0.8rem 1.1rem 0.9rem;
    border-top: 1px solid rgba(42,45,58,0.5);
  }
  :global(.plain-section) { border-right: 1px solid rgba(42,45,58,0.5); }
  :global(.def-label) {
    display: block;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
  }
  :global(.plain-label) { color: var(--accent2); }
  :global(.tech-label)  { color: var(--accent); }
  :global(.def-text) {
    font-size: 0.8rem;
    color: var(--text);
    line-height: 1.6;
    margin: 0;
  }
</style>
