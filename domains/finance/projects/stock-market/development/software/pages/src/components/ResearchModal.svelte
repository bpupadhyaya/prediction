<script lang="ts">
  import type { Parameter, AppSettings } from '../lib/types';
  export let param: Parameter | null = null;
  export let settings: AppSettings;
  export let onClose: () => void;
  export let onApply: (direction: 'up' | 'down', weight: number) => void;

  import { fetchUrl, extractText } from '../lib/url-fetcher';
  import { chat } from '../lib/webllm';

  let urlInput = '';
  let pasteText = '';
  let contextItems: { label: string; content: string }[] = [];
  let chatMessages: { role: 'user' | 'ai'; text: string }[] = [];
  let userInput = '';
  let loading = false;
  let fetchError = '';
  let llmError = '';

  async function handleFetch() {
    if (!urlInput.trim()) return;
    fetchError = '';
    loading = true;
    try {
      const res = await fetchUrl(urlInput.trim(), settings.corsProxyEnabled);
      if (res.ok) {
        const text = extractText(res.content);
        contextItems = [...contextItems, { label: urlInput.trim().slice(0, 60) + '…', content: text }];
        urlInput = '';
      } else {
        fetchError = res.error ?? 'Fetch failed';
      }
    } catch (err) {
      fetchError = `Fetch failed: ${err instanceof Error ? err.message : String(err)}`;
    } finally {
      loading = false;
    }
  }

  function addPaste() {
    if (!pasteText.trim()) return;
    contextItems = [...contextItems, { label: 'Pasted content', content: pasteText.trim() }];
    pasteText = '';
  }

  async function sendMessage() {
    if (!userInput.trim() || !param) return;
    llmError = '';
    const msg = userInput.trim();
    userInput = '';
    chatMessages = [...chatMessages, { role: 'user', text: msg }];
    chatMessages = [...chatMessages, { role: 'ai', text: '' }];
    const idx = chatMessages.length - 1;

    const systemPrompt = `You are a financial analyst helping evaluate the parameter "${param.name}" (${param.label}) for stock prediction.
Current value: ${param.defaultValue} ${param.unit}.
Parameter description: ${param.layman}
Context documents provided by user: ${contextItems.map(c => c.content).join('\n\n---\n\n').slice(0, 15000)}

Based on the context and your knowledge, help the user determine:
1. Direction: should this parameter push the prediction UP or DOWN?
2. Weight/importance: how important is this parameter right now (1-100)?

End your response with a line: SUGGESTION: Direction=UP|DOWN, Weight=<number>`;

    try {
      await chat(systemPrompt, msg, (token: string) => {
        chatMessages[idx] = { ...chatMessages[idx], text: chatMessages[idx].text + token };
        chatMessages = [...chatMessages];
      });
      // Parse suggestion from last AI message
      const lastMsg = chatMessages[idx].text;
      const match = lastMsg.match(/SUGGESTION:\s*Direction=(UP|DOWN),\s*Weight=(\d+)/i);
      if (match) {
        suggestedDir = match[1].toLowerCase() as 'up' | 'down';
        suggestedWeight = Math.min(100, Math.max(1, parseInt(match[2], 10)));
        showSuggestion = true;
      }
    } catch (e: unknown) {
      llmError = e instanceof Error ? e.message : 'LLM error';
      chatMessages[idx] = { ...chatMessages[idx], text: `[Error: ${llmError}]` };
      chatMessages = [...chatMessages];
    }
  }

  let suggestedDir: 'up' | 'down' | null = null;
  let suggestedWeight = 50;
  let showSuggestion = false;

  function applySuggestion() {
    if (!suggestedDir) return;
    onApply(suggestedDir, suggestedWeight);
    showSuggestion = false;
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') onClose();
  }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if param}
<div class="overlay" on:click|self={onClose} role="dialog" aria-modal="true" aria-label="Research assistant for {param.name}">
  <div class="modal">
    <div class="modal-header">
      <div class="header-text">
        <div class="modal-title">🔬 Research — <span class="param-highlight">{param.name}</span></div>
        <div class="modal-subtitle">{param.label} · {param.layman}</div>
      </div>
      <button class="close-btn" on:click={onClose} title="Close research modal" aria-label="Close">✕ Close</button>
    </div>

    <div class="modal-body">
      <!-- Context loading -->
      <div class="section">
        <div class="section-label">Add context (URLs or paste text)</div>
        <div class="url-row">
          <input
            type="url"
            placeholder="https://…"
            bind:value={urlInput}
            aria-label="URL to fetch"
            on:keydown={e => e.key === 'Enter' && handleFetch()}
          />
          <button class="btn-fetch" on:click={handleFetch} disabled={loading} title="Fetch URL content">
            {loading ? '⏳' : 'Fetch'}
          </button>
        </div>
        {#if loading}
          <div class="fetch-loading" role="status">Fetching…</div>
        {/if}
        {#if fetchError}<div class="error-msg" role="alert">{fetchError}</div>{/if}
        <textarea
          placeholder="Or paste text / notes here…"
          bind:value={pasteText}
          rows="3"
          aria-label="Paste research text"
        ></textarea>
        <button class="btn-add" on:click={addPaste} disabled={!pasteText.trim()} title="Add pasted text to context">Add to context</button>

        {#if contextItems.length}
          <div class="context-chips" role="list" aria-label="Context items">
            {#each contextItems as item, i}
              <span class="context-chip" role="listitem">
                {item.label}
                <button
                  on:click={() => contextItems = contextItems.filter((_, j) => j !== i)}
                  title="Remove this context item"
                  aria-label="Remove context item: {item.label}"
                >✕</button>
              </span>
            {/each}
          </div>
        {:else}
          <div class="context-empty">No context added yet. Fetch a URL or paste text above.</div>
        {/if}
      </div>

      <!-- LLM Chat -->
      <div class="section">
        <div class="section-label">Chat with AI</div>
        {#if llmError && llmError.includes('not yet implemented')}
          <div class="llm-placeholder">
            <div class="placeholder-icon">🤖</div>
            <div class="placeholder-text">
              <strong>AI Research Assistant — Coming in Phase 2</strong><br>
              The LLM integration (WebLLM) is not yet available. To analyze this parameter:
              <ul>
                <li>Fetch or paste relevant documents above</li>
                <li>Read the technical description: <em>{param.technical}</em></li>
                <li>Set your own weight and direction using your judgment</li>
              </ul>
            </div>
          </div>
        {:else}
          {#if llmError && !llmError.includes('not yet implemented')}
            <div class="error-msg" role="alert">{llmError}</div>
          {/if}
          <div class="chat-messages" role="log" aria-live="polite" aria-label="Chat messages">
            {#each chatMessages as msg}
              <div class="chat-msg {msg.role}">
                <span class="chat-role" aria-hidden="true">{msg.role === 'ai' ? '🤖' : '👤'}</span>
                <span class="chat-text">{msg.text || (msg.role === 'ai' ? '⏳ Thinking…' : '')}</span>
              </div>
            {/each}
            {#if chatMessages.length === 0}
              <div class="chat-empty">Ask a question about this parameter to get AI analysis.</div>
            {/if}
          </div>
          <div class="chat-input-row">
            <input
              type="text"
              placeholder="Ask about this parameter…"
              bind:value={userInput}
              aria-label="Chat message"
              on:keydown={e => e.key === 'Enter' && sendMessage()}
            />
            <button
              on:click={sendMessage}
              disabled={!userInput.trim()}
              title="Send message"
              aria-label="Send chat message"
            >Send</button>
          </div>
        {/if}

        {#if showSuggestion && suggestedDir}
          <div class="suggestion-card" role="region" aria-label="AI suggestion">
            <span class="suggestion-label">AI Suggestion</span>
            <span class="suggestion-dir" style="color:{suggestedDir==='up'?'var(--accent2)':'var(--danger)'}">
              {suggestedDir === 'up' ? '▲ UP' : '▼ DOWN'}
            </span>
            <span class="suggestion-weight">Weight: {suggestedWeight}</span>
            <button class="btn-apply" on:click={applySuggestion} title="Apply AI suggestion to parameter">
              Apply
            </button>
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>
{/if}

<style>
  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 1rem;
  }
  .modal {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    width: 100%;
    max-width: 680px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  .modal-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--border);
    gap: 1rem;
    overflow: hidden;
  }
  .header-text { flex: 1; min-width: 0; overflow: hidden; }
  .modal-title { font-weight: 700; font-size: 1rem; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .param-highlight { color: var(--accent); font-family: monospace; }
  .modal-subtitle {
    font-size: 0.75rem;
    color: var(--muted);
    margin-top: 0.2rem;
    max-width: 460px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .close-btn {
    background: none;
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 0.3rem 0.7rem;
    border-radius: 8px;
    font-size: 0.8rem;
    white-space: nowrap;
    cursor: pointer;
    flex-shrink: 0;
    transition: all 0.15s;
  }
  .close-btn:hover { border-color: var(--accent); color: var(--text); }
  .modal-body { flex: 1; overflow-y: auto; padding: 1rem 1.25rem; display: flex; flex-direction: column; gap: 1rem; }
  .section { display: flex; flex-direction: column; gap: 0.5rem; }
  .section-label { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); }
  .url-row { display: flex; gap: 0.4rem; }
  .url-row input { flex: 1; border-radius: 8px; }
  .btn-fetch {
    background: var(--accent);
    border: none;
    color: #fff;
    padding: 0.4rem 0.8rem;
    border-radius: 8px;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
  }
  .btn-fetch:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-fetch:not(:disabled):hover { filter: brightness(1.1); }
  .fetch-loading { font-size: 0.78rem; color: var(--muted); }
  .btn-add {
    background: none;
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 0.3rem 0.7rem;
    border-radius: 8px;
    font-size: 0.8rem;
    align-self: flex-start;
    cursor: pointer;
    transition: all 0.15s;
  }
  .btn-add:not(:disabled):hover { border-color: var(--accent); color: var(--text); }
  .btn-add:disabled { opacity: 0.4; cursor: not-allowed; }
  textarea {
    resize: vertical;
    min-height: 60px;
    border-radius: 8px;
    font-size: 0.85rem;
  }
  .error-msg { font-size: 0.78rem; color: var(--danger); }
  .context-empty { font-size: 0.78rem; color: var(--muted); }
  .context-chips { display: flex; flex-wrap: wrap; gap: 0.35rem; }
  .context-chip {
    background: rgba(79,142,247,0.1);
    border: 1px solid rgba(79,142,247,0.2);
    color: var(--accent);
    font-size: 0.72rem;
    padding: 0.15rem 0.5rem;
    border-radius: 99px;
    display: flex;
    align-items: center;
    gap: 0.3rem;
    overflow: hidden;
    max-width: 240px;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
  .context-chip button {
    background: none;
    border: none;
    color: var(--muted);
    font-size: 0.75rem;
    padding: 0;
    cursor: pointer;
    flex-shrink: 0;
    transition: color 0.15s;
  }
  .context-chip button:hover { color: var(--danger); }
  .llm-placeholder {
    background: rgba(79,142,247,0.06);
    border: 1px solid rgba(79,142,247,0.15);
    border-radius: 8px;
    padding: 1rem;
    display: flex;
    gap: 0.75rem;
  }
  .placeholder-icon { font-size: 1.5rem; flex-shrink: 0; }
  .placeholder-text { font-size: 0.8rem; color: var(--muted); line-height: 1.6; }
  .placeholder-text strong { color: var(--text); }
  .placeholder-text ul { margin: 0.4rem 0 0 1rem; }
  .chat-messages {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    max-height: 240px;
    overflow-y: auto;
    overflow-x: hidden;
  }
  .chat-empty { font-size: 0.78rem; color: var(--muted); padding: 0.5rem 0; }
  .chat-msg { display: flex; gap: 0.5rem; font-size: 0.82rem; line-height: 1.5; }
  .chat-role { font-size: 1rem; flex-shrink: 0; }
  .chat-text { white-space: pre-wrap; word-break: break-word; }
  .chat-msg.ai .chat-text { color: var(--text); }
  .chat-msg.user .chat-text { color: var(--muted); }
  .chat-input-row { display: flex; gap: 0.4rem; }
  .chat-input-row input { flex: 1; border-radius: 8px; }
  .chat-input-row button {
    background: var(--accent);
    border: none;
    color: #fff;
    padding: 0.4rem 0.8rem;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
  }
  .chat-input-row button:disabled { opacity: 0.5; cursor: not-allowed; }
  .chat-input-row button:not(:disabled):hover { filter: brightness(1.1); }
  .suggestion-card {
    background: rgba(52,211,153,0.08);
    border: 1px solid rgba(52,211,153,0.2);
    border-radius: 8px;
    padding: 0.65rem 1rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
  }
  .suggestion-label { font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
  .suggestion-dir { font-weight: 700; font-size: 0.9rem; }
  .suggestion-weight { font-size: 0.82rem; color: var(--muted); }
  .btn-apply {
    margin-left: auto;
    background: var(--accent2);
    border: none;
    color: #000;
    padding: 0.3rem 0.8rem;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
  }
  .btn-apply:hover { filter: brightness(1.1); }
</style>
