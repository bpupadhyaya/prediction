<script lang="ts">
  import { onMount } from 'svelte';
  import type { VideoSource, VideoSignal, ChannelTrack } from '../lib/types';
  import {
    saveVideoSource, getAllVideoSources, updateVideoSourceStatus,
    saveTranscript, getTranscript,
    saveVideoSignals, getSignalsForVideo, getAllSignals,
    saveChannelTrack, getAllChannelTracks, removeChannelTrack,
    getVideoSetting, setVideoSetting,
  } from '../lib/video-intelligence-store';
  import { WHISPER_MODELS, fetchYouTubeAudio, transcribeAudioBlob, CF_WORKER_TEMPLATE } from '../lib/youtube-transcriber';
  import { extractSignalsFromTranscript } from '../lib/video-signal-extractor';

  export let onSignalApply: (signal: VideoSignal) => void = () => { /* no-op */ };

  // ── URL input state ──────────────────────────────────────────────────────────
  let urlInput = '';
  let processing = false;
  let processingStatus = '';
  let processingPct = 0;
  let processError = '';
  let processSuccess = '';

  // ── Model selection ──────────────────────────────────────────────────────────
  let activeModelId = 'base';

  // ── CF Worker setup ──────────────────────────────────────────────────────────
  let cfWorkerUrl = '';
  let cfWorkerSaved = false;
  let cfWorkerError = '';
  let showCFTemplate = false;

  // ── Tracked channels ─────────────────────────────────────────────────────────
  let trackedChannels: ChannelTrack[] = [];
  let customChannelInput = '';
  let customSpeakerInput = '';

  const PRESET_SPEAKERS: Array<{ channelId: string; speakerName: string; channelName: string }> = [
    { channelId: 'elon-musk',      speakerName: 'Elon Musk',      channelName: 'Elon Musk' },
    { channelId: 'warren-buffett', speakerName: 'Warren Buffett', channelName: 'Berkshire Hathaway' },
    { channelId: 'jerome-powell',  speakerName: 'Jerome Powell',  channelName: 'Federal Reserve' },
    { channelId: 'jensen-huang',   speakerName: 'Jensen Huang',   channelName: 'NVIDIA' },
    { channelId: 'tim-cook',       speakerName: 'Tim Cook',       channelName: 'Apple' },
    { channelId: 'cathie-wood',    speakerName: 'Cathie Wood',    channelName: 'ARK Invest' },
    { channelId: 'jim-cramer',     speakerName: 'Jim Cramer',     channelName: "Mad Money/CNBC" },
    { channelId: 'michael-saylor', speakerName: 'Michael Saylor', channelName: 'MicroStrategy' },
  ];

  // ── Video queue ──────────────────────────────────────────────────────────────
  let videoSources: VideoSource[] = [];
  let expandedVideoId: string | null = null;
  let expandedTranscript: string | null = null;

  // ── Signal feed ──────────────────────────────────────────────────────────────
  let signals: VideoSignal[] = [];
  let signalTimeRange = '168'; // hours; default 1 week
  let tickerFilter = '';

  const TIME_RANGE_OPTIONS = [
    { label: '1 hr',   value: '1' },
    { label: '4 hr',   value: '4' },
    { label: '24 hr',  value: '24' },
    { label: '1 week', value: '168' },
    { label: '1 mo',   value: '720' },
    { label: '3 mo',   value: '2160' },
    { label: '6 mo',   value: '4320' },
    { label: '1 yr',   value: '8760' },
    { label: '2 yr',   value: '17520' },
    { label: '3 yr',   value: '26280' },
    { label: '5 yr',   value: '43800' },
    { label: '10 yr',  value: '87600' },
    { label: '15 yr',  value: '131400' },
    { label: '20 yr',  value: '175200' },
    { label: 'All',    value: '0' },
  ];

  // Streaming token buffer for signal extraction UI
  let extractionTokens = '';

  // ── Mount ────────────────────────────────────────────────────────────────────
  onMount(async () => {
    await Promise.all([
      loadInitialData(),
    ]);
  });

  async function loadInitialData() {
    try {
      const [sources, tracks, savedWorker, savedModel] = await Promise.all([
        getAllVideoSources(),
        getAllChannelTracks(),
        getVideoSetting('cfWorkerUrl'),
        getVideoSetting('activeWhisperModel'),
      ]);
      videoSources = sources;
      trackedChannels = tracks;
      if (savedWorker) cfWorkerUrl = savedWorker;
      if (savedModel) activeModelId = savedModel;
      await refreshSignals();
    } catch (err) {
      console.error('YVIS: failed to load initial data', err);
    }
  }

  async function refreshSignals() {
    const days = signalTimeRange === '0' ? undefined : Number(signalTimeRange) / 24;
    const ticker = tickerFilter.trim().toUpperCase() || undefined;
    signals = await getAllSignals(ticker, days);
  }

  // ── URL helpers ───────────────────────────────────────────────────────────────

  function extractYouTubeId(url: string): string | null {
    try {
      const u = new URL(url.trim());
      if (u.hostname.includes('youtu.be')) return u.pathname.slice(1).split('?')[0];
      return u.searchParams.get('v');
    } catch {
      return null;
    }
  }

  function generateVideoId(): string {
    return `vid-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  }

  // ── Main analysis pipeline ────────────────────────────────────────────────────

  async function handleAnalyze() {
    const url = urlInput.trim();
    if (!url) { processError = 'Please enter a YouTube URL.'; return; }

    const videoId = extractYouTubeId(url);
    if (!videoId) { processError = 'Could not extract YouTube video ID. Make sure the URL is a valid YouTube link.'; return; }

    processError = '';
    processSuccess = '';
    processing = true;
    processingPct = 0;
    extractionTokens = '';

    const sourceId = generateVideoId();

    // Create a pending entry immediately so it appears in the queue
    const source: VideoSource = {
      id: sourceId,
      url,
      videoId,
      title: `YouTube: ${videoId}`,
      channelName: 'Unknown',
      channelId: '',
      speakerName: '',
      publishedAt: new Date().toISOString(),
      durationSec: 0,
      viewCount: 0,
      status: 'pending',
      transcriptModel: activeModelId,
      createdAt: new Date().toISOString(),
    };

    try {
      await saveVideoSource(source);
      videoSources = await getAllVideoSources();

      // ── Step 1: Download audio ──────────────────────────────────────────────
      setStatus(sourceId, 'transcribing');
      processingStatus = 'Downloading audio via Cloudflare Worker…';
      processingPct = 5;

      const audioBlob = await fetchYouTubeAudio(url);

      // ── Step 2: Transcribe ─────────────────────────────────────────────────
      processingStatus = 'Transcribing with Whisper…';
      processingPct = 10;

      const transcription = await transcribeAudioBlob(
        audioBlob,
        activeModelId,
        (pct, msg) => {
          processingPct = 10 + Math.round(pct * 0.55);
          processingStatus = msg;
        },
      );

      // Persist transcript
      await saveTranscript({
        videoId,
        fullText: transcription.fullText,
        chunks: transcription.chunks,
        wordCount: transcription.wordCount,
        language: 'en',
        modelUsed: activeModelId,
        transcribedAt: new Date().toISOString(),
      });

      // Update source title/model
      const updatedSource: VideoSource = {
        ...source,
        status: 'extracting',
        transcriptModel: activeModelId,
      };
      await saveVideoSource(updatedSource);
      videoSources = await getAllVideoSources();

      // ── Step 3: Extract signals ────────────────────────────────────────────
      processingStatus = 'Extracting market signals with LLM…';
      processingPct = 70;
      setStatus(sourceId, 'extracting');
      extractionTokens = '';

      const extractedSignals = await extractSignalsFromTranscript(
        transcription.fullText,
        source.title,
        source.channelName,
        videoId,
        (token) => { extractionTokens += token; },
      );

      await saveVideoSignals(extractedSignals);

      // ── Done ────────────────────────────────────────────────────────────────
      await updateVideoSourceStatus(sourceId, 'done');
      videoSources = await getAllVideoSources();
      await refreshSignals();

      processingPct = 100;
      processingStatus = `Done! Extracted ${extractedSignals.length} signal${extractedSignals.length !== 1 ? 's' : ''}.`;
      processSuccess = `Video processed. ${extractedSignals.length} market signal${extractedSignals.length !== 1 ? 's' : ''} extracted.`;
      urlInput = '';

    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      processError = msg;
      await updateVideoSourceStatus(sourceId, 'error', msg);
      videoSources = await getAllVideoSources();
    } finally {
      processing = false;
      setTimeout(() => { processingStatus = ''; processingPct = 0; extractionTokens = ''; }, 8000);
    }
  }

  async function setStatus(sourceId: string, status: VideoSource['status']) {
    await updateVideoSourceStatus(sourceId, status);
    videoSources = await getAllVideoSources();
  }

  // ── Model selection ───────────────────────────────────────────────────────────

  async function selectModel(id: string) {
    activeModelId = id;
    await setVideoSetting('activeWhisperModel', id);
  }

  // ── CF Worker ─────────────────────────────────────────────────────────────────

  async function saveCFWorker() {
    cfWorkerError = '';
    const url = cfWorkerUrl.trim();
    if (!url) { cfWorkerError = 'Please enter a URL.'; return; }
    try {
      new URL(url); // validate
    } catch {
      cfWorkerError = 'Invalid URL format.';
      return;
    }
    try {
      await setVideoSetting('cfWorkerUrl', url);
      cfWorkerSaved = true;
      setTimeout(() => cfWorkerSaved = false, 3000);
    } catch (err) {
      cfWorkerError = err instanceof Error ? err.message : String(err);
    }
  }

  function copyTemplate() {
    navigator.clipboard.writeText(CF_WORKER_TEMPLATE).catch(() => {/* ignore */});
  }

  // ── Channel tracking ─────────────────────────────────────────────────────────

  function isTracked(channelId: string): boolean {
    return trackedChannels.some(c => c.channelId === channelId);
  }

  async function togglePreset(preset: typeof PRESET_SPEAKERS[0]) {
    if (isTracked(preset.channelId)) {
      await removeChannelTrack(preset.channelId);
    } else {
      await saveChannelTrack({
        channelId: preset.channelId,
        channelName: preset.channelName,
        speakerName: preset.speakerName,
        autoProcess: false,
        timeRangeYears: 1,
        createdAt: new Date().toISOString(),
      });
    }
    trackedChannels = await getAllChannelTracks();
  }

  async function trackCustomChannel() {
    const id = customChannelInput.trim();
    const speaker = customSpeakerInput.trim() || id;
    if (!id) return;
    await saveChannelTrack({
      channelId: id,
      channelName: id,
      speakerName: speaker,
      autoProcess: false,
      timeRangeYears: 1,
      createdAt: new Date().toISOString(),
    });
    trackedChannels = await getAllChannelTracks();
    customChannelInput = '';
    customSpeakerInput = '';
  }

  async function untrackChannel(channelId: string) {
    await removeChannelTrack(channelId);
    trackedChannels = await getAllChannelTracks();
  }

  // ── Queue expansion ───────────────────────────────────────────────────────────

  async function toggleExpand(videoId: string) {
    if (expandedVideoId === videoId) {
      expandedVideoId = null;
      expandedTranscript = null;
      return;
    }
    expandedVideoId = videoId;
    expandedTranscript = null;
    try {
      const t = await getTranscript(videoId);
      expandedTranscript = t?.fullText ?? '(no transcript yet)';
    } catch {
      expandedTranscript = '(failed to load transcript)';
    }
  }

  // ── Signal feed helpers ───────────────────────────────────────────────────────

  async function onTimeRangeChange() {
    await refreshSignals();
  }

  async function onTickerFilterChange() {
    await refreshSignals();
  }

  function timeAgo(iso: string): string {
    const diff = Date.now() - new Date(iso).getTime();
    const m = Math.floor(diff / 60000);
    if (m < 1) return 'just now';
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h}h ago`;
    const d = Math.floor(h / 24);
    if (d < 30) return `${d}d ago`;
    return `${Math.floor(d / 30)}mo ago`;
  }

  function statusColor(status: VideoSource['status']): string {
    switch (status) {
      case 'pending': return 'badge-muted';
      case 'transcribing': return 'badge-warn';
      case 'extracting': return 'badge-warn';
      case 'done': return 'badge-done';
      case 'error': return 'badge-danger';
      default: return 'badge-muted';
    }
  }

  // ── Intelligence summary ──────────────────────────────────────────────────────

  $: filteredTicker = tickerFilter.trim().toUpperCase();

  $: tickerSignals = filteredTicker
    ? signals.filter(s => s.ticker === filteredTicker)
    : [];

  $: summaryDirection = (() => {
    if (!tickerSignals.length) return null;
    const upScore = tickerSignals.filter(s => s.direction === 'up').reduce((a, s) => a + s.weight * s.confidence, 0);
    const downScore = tickerSignals.filter(s => s.direction === 'down').reduce((a, s) => a + s.weight * s.confidence, 0);
    return upScore >= downScore ? 'up' : 'down';
  })();

  $: avgConfidence = tickerSignals.length
    ? (tickerSignals.reduce((a, s) => a + s.confidence, 0) / tickerSignals.length)
    : 0;

  $: topQuotes = tickerSignals.slice(0, 5).map(s => s.keyQuote).filter(Boolean);

  // Apply signal to prediction
  function handleApply(signal: VideoSignal) {
    onSignalApply(signal);
  }
</script>

<div class="yvis">
  <!-- ── Header + URL input ──────────────────────────────────────────────── -->
  <div class="page-header">
    <div>
      <h2>🎬 Video Intelligence</h2>
      <p class="subtitle">Transcribe YouTube videos → extract market signals</p>
    </div>
  </div>

  <section class="card">
    <div class="url-row">
      <input
        type="url"
        placeholder="Paste YouTube URL (e.g. https://youtube.com/watch?v=...)"
        bind:value={urlInput}
        disabled={processing}
        aria-label="YouTube URL"
        on:keydown={e => e.key === 'Enter' && !processing && handleAnalyze()}
      />
      <button class="btn-primary" on:click={handleAnalyze} disabled={processing}>
        {processing ? '⏳ Processing…' : '▶ Analyze'}
      </button>
    </div>

    {#if processError}
      <div class="msg-error" role="alert">{processError}</div>
    {/if}
    {#if processSuccess}
      <div class="msg-success" role="status">{processSuccess}</div>
    {/if}

    {#if processing}
      <div class="progress-wrap" role="status" aria-live="polite">
        <div class="progress-bar">
          <div class="progress-fill" style="width:{processingPct}%"></div>
        </div>
        <div class="progress-text">{processingStatus} ({processingPct}%)</div>
        {#if extractionTokens}
          <div class="token-stream">{extractionTokens}</div>
        {/if}
      </div>
    {/if}
  </section>

  <!-- ── Whisper Model Card ────────────────────────────────────────────────── -->
  <section class="card">
    <div class="section-label">TRANSCRIPTION MODEL</div>
    <div class="model-table">
      {#each WHISPER_MODELS as m}
        <div class="model-row" class:model-row--active={activeModelId === m.id}>
          <label class="model-radio">
            <input
              type="radio"
              name="whisper-model"
              value={m.id}
              checked={activeModelId === m.id}
              on:change={() => selectModel(m.id)}
            />
          </label>
          <div class="model-info">
            <span class="model-name">{m.label}</span>
            <span class="quality-badge">{m.quality}</span>
          </div>
          <div class="model-cache-note">
            Cached in browser via OPFS
          </div>
        </div>
      {/each}
    </div>
    <p class="note">Models are downloaded once and cached automatically by transformers.js in your browser's Origin Private File System (OPFS). No server involved.</p>
  </section>

  <!-- ── Cloudflare Worker Setup ───────────────────────────────────────────── -->
  {#if !cfWorkerUrl}
    <section class="card card-warn">
      <div class="section-label">CLOUDFLARE WORKER SETUP REQUIRED</div>
      <p class="note">
        Browsers cannot directly fetch YouTube audio due to CORS restrictions.
        You need to deploy a small Cloudflare Worker (free, ~30 lines of JS) to proxy the audio stream.
        Cloudflare's free tier allows 100,000 requests/day — more than enough.
      </p>

      <div class="cf-steps">
        <p class="step"><strong>1.</strong> Copy the Worker script below</p>
        <p class="step"><strong>2.</strong> Go to <a href="https://workers.cloudflare.com" target="_blank" rel="noopener">workers.cloudflare.com</a> → Create Worker → paste the script → Deploy</p>
        <p class="step"><strong>3.</strong> Copy your Worker URL (e.g. <code>https://my-worker.username.workers.dev</code>) and paste it below</p>
      </div>

      <button class="btn-secondary btn-sm" on:click={() => showCFTemplate = !showCFTemplate}>
        {showCFTemplate ? 'Hide' : 'Show'} Worker Script
      </button>
      <button class="btn-secondary btn-sm" on:click={copyTemplate}>Copy Script</button>

      {#if showCFTemplate}
        <pre class="code-block">{CF_WORKER_TEMPLATE}</pre>
      {/if}

      <div class="cf-input-row">
        <input
          type="url"
          placeholder="https://my-worker.username.workers.dev"
          bind:value={cfWorkerUrl}
          aria-label="Cloudflare Worker URL"
        />
        <button class="btn-primary btn-sm" on:click={saveCFWorker}>
          {cfWorkerSaved ? '✓ Saved' : 'Save URL'}
        </button>
      </div>
      {#if cfWorkerError}
        <div class="msg-error" role="alert">{cfWorkerError}</div>
      {/if}
    </section>
  {:else}
    <section class="card">
      <div class="section-label">CLOUDFLARE WORKER</div>
      <div class="cf-configured-row">
        <span class="badge-done">✓ Configured</span>
        <code class="cf-url">{cfWorkerUrl}</code>
        <button class="btn-ghost btn-sm" on:click={() => cfWorkerUrl = ''}>Change</button>
      </div>
      {#if cfWorkerError}
        <div class="msg-error" role="alert">{cfWorkerError}</div>
      {/if}
    </section>
  {/if}

  <!-- ── Tracked Speakers / Channels ──────────────────────────────────────── -->
  <section class="card">
    <div class="section-label">TRACKED SPEAKERS</div>
    <div class="chips">
      {#each PRESET_SPEAKERS as preset}
        <button
          class="chip"
          class:chip--active={isTracked(preset.channelId)}
          on:click={() => togglePreset(preset)}
          title={isTracked(preset.channelId) ? 'Click to untrack' : 'Click to track'}
        >
          {preset.speakerName}
          <span class="chip-icon">{isTracked(preset.channelId) ? '✓' : '+'}</span>
        </button>
      {/each}
    </div>

    {#if trackedChannels.filter(c => !PRESET_SPEAKERS.some(p => p.channelId === c.channelId)).length > 0}
      <div class="custom-tracks">
        <span class="note">Custom tracked:</span>
        {#each trackedChannels.filter(c => !PRESET_SPEAKERS.some(p => p.channelId === c.channelId)) as ct}
          <div class="custom-track-chip">
            <span>{ct.speakerName || ct.channelId}</span>
            <button class="btn-remove-tiny" on:click={() => untrackChannel(ct.channelId)} title="Untrack">✕</button>
          </div>
        {/each}
      </div>
    {/if}

    <div class="custom-track-input">
      <input
        type="text"
        placeholder="YouTube channel ID or URL"
        bind:value={customChannelInput}
        aria-label="Custom channel ID"
      />
      <input
        type="text"
        placeholder="Speaker name (optional)"
        bind:value={customSpeakerInput}
        aria-label="Speaker name"
      />
      <button class="btn-secondary btn-sm" on:click={trackCustomChannel}>Track</button>
    </div>

    <p class="note">Tracked speakers/channels help you annotate video sources. Auto-processing is not yet implemented — analyze videos manually via the URL input above.</p>
  </section>

  <!-- ── Processing Queue ──────────────────────────────────────────────────── -->
  <section class="card">
    <div class="section-label">PROCESSING QUEUE</div>

    {#if videoSources.length === 0}
      <p class="empty-state">No videos processed yet. Paste a YouTube URL above to get started.</p>
    {:else}
      <div class="queue-list">
        {#each videoSources as vid}
          <div class="queue-item">
            <div class="queue-header" on:click={() => toggleExpand(vid.videoId)} role="button" tabindex="0" on:keydown={e => e.key === 'Enter' && toggleExpand(vid.videoId)}>
              <div class="queue-meta">
                <span class="queue-title">{vid.title}</span>
                <span class="queue-channel">{vid.channelName}</span>
                <span class="queue-time">{timeAgo(vid.createdAt)}</span>
              </div>
              <div class="queue-right">
                <span class="badge {statusColor(vid.status)}">{vid.status}</span>
                {#if vid.status === 'error'}
                  <span class="queue-error-msg" title={vid.errorMsg}>⚠</span>
                {/if}
                <span class="expand-toggle">{expandedVideoId === vid.videoId ? '▲' : '▼'}</span>
              </div>
            </div>

            {#if expandedVideoId === vid.videoId}
              <div class="queue-expand">
                {#if vid.errorMsg}
                  <div class="msg-error">{vid.errorMsg}</div>
                {/if}
                <div class="transcript-preview">
                  {#if expandedTranscript === null}
                    <span class="note">Loading…</span>
                  {:else}
                    <p class="transcript-text">{expandedTranscript.slice(0, 1200)}{expandedTranscript.length > 1200 ? '…' : ''}</p>
                  {/if}
                </div>
              </div>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
  </section>

  <!-- ── Signal Feed ────────────────────────────────────────────────────────── -->
  <section class="card">
    <div class="section-label">SIGNAL FEED</div>

    <div class="feed-filters">
      <div class="filter-group">
        <label for="time-range">Time range</label>
        <select id="time-range" bind:value={signalTimeRange} on:change={onTimeRangeChange}>
          {#each TIME_RANGE_OPTIONS as opt}
            <option value={opt.value}>{opt.label}</option>
          {/each}
        </select>
      </div>
      <div class="filter-group">
        <label for="ticker-filter">Ticker</label>
        <input
          id="ticker-filter"
          type="text"
          placeholder="e.g. AAPL"
          bind:value={tickerFilter}
          on:input={onTickerFilterChange}
          style="width:110px; text-transform:uppercase"
        />
      </div>
    </div>

    {#if signals.length === 0}
      <p class="empty-state">No signals yet. Analyze a video to extract market signals.</p>
    {:else}
      <div class="signal-list">
        {#each signals as sig}
          <div class="signal-card">
            <div class="signal-top">
              <span class="dir-badge" class:dir-up={sig.direction === 'up'} class:dir-down={sig.direction === 'down'}>
                {sig.direction === 'up' ? '▲ UP' : '▼ DOWN'}
              </span>
              <span class="sig-weight">{sig.weight}/100</span>
              {#if sig.ticker}
                <span class="sig-ticker">{sig.ticker}</span>
              {/if}
              <span class="sig-domain">{sig.domain}</span>
              <span class="sig-param">{sig.parameterName}</span>
              <span class="sig-time">{timeAgo(sig.extractedAt)}</span>
            </div>
            <blockquote class="sig-quote">"{sig.keyQuote}"</blockquote>
            <div class="sig-bottom">
              <span class="sig-confidence">confidence: {Math.round(sig.confidence * 100)}%</span>
              <button class="btn-apply" on:click={() => handleApply(sig)}>
                Apply to Prediction
              </button>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </section>

  <!-- ── Intelligence Summary ───────────────────────────────────────────────── -->
  {#if filteredTicker && tickerSignals.length > 0}
    <section class="card">
      <div class="section-label">INTELLIGENCE SUMMARY — {filteredTicker}</div>
      <div class="summary-grid">
        <div class="summary-stat">
          <span class="stat-label">Overall Direction</span>
          <span class="stat-val" class:stat-up={summaryDirection === 'up'} class:stat-down={summaryDirection === 'down'}>
            {summaryDirection === 'up' ? '▲ BULLISH' : '▼ BEARISH'}
          </span>
        </div>
        <div class="summary-stat">
          <span class="stat-label">Signal Count</span>
          <span class="stat-val">{tickerSignals.length}</span>
        </div>
        <div class="summary-stat">
          <span class="stat-label">Avg Confidence</span>
          <span class="stat-val">{Math.round(avgConfidence * 100)}%</span>
        </div>
      </div>
      {#if topQuotes.length > 0}
        <div class="section-label" style="margin-top:0.75rem">TOP QUOTES</div>
        <ol class="quote-list">
          {#each topQuotes as q}
            <li>"{q}"</li>
          {/each}
        </ol>
      {/if}
    </section>
  {/if}
</div>

<style>
  .yvis { max-width: 800px; }

  /* ── Page header ── */
  .page-header { margin-bottom: 1rem; }
  h2 { font-size: 1.1rem; font-weight: 700; color: var(--text); margin-bottom: 0.2rem; }
  .subtitle { font-size: 0.8rem; color: var(--muted); }

  /* ── Cards ── */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.1rem 1.25rem;
    margin-bottom: 1rem;
  }
  .card-warn { border-color: rgba(251,191,36,0.35); }

  /* ── Section labels ── */
  .section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: var(--muted);
    text-transform: uppercase;
    margin-bottom: 0.6rem;
  }

  /* ── URL row ── */
  .url-row { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem; flex-wrap: wrap; }
  .url-row input { flex: 1; min-width: 200px; }

  /* ── Buttons ── */
  .btn-primary {
    background: var(--accent);
    border: none;
    color: #fff;
    padding: 0.4rem 1.1rem;
    border-radius: 8px;
    font-size: 0.875rem;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.15s;
  }
  .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-primary:not(:disabled):hover { filter: brightness(1.1); }
  .btn-secondary {
    background: rgba(79,142,247,0.12);
    border: 1px solid rgba(79,142,247,0.25);
    color: var(--accent);
    padding: 0.35rem 0.85rem;
    border-radius: 8px;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.15s;
  }
  .btn-secondary:hover { background: rgba(79,142,247,0.22); }
  .btn-ghost {
    background: none;
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 0.3rem 0.7rem;
    border-radius: 8px;
    font-size: 0.78rem;
    cursor: pointer;
    transition: all 0.15s;
  }
  .btn-ghost:hover { border-color: var(--accent); color: var(--text); }
  .btn-sm { font-size: 0.78rem; padding: 0.3rem 0.75rem; }
  .btn-apply {
    background: rgba(52,211,153,0.12);
    border: 1px solid rgba(52,211,153,0.3);
    color: var(--accent2);
    padding: 0.25rem 0.7rem;
    border-radius: 8px;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
  }
  .btn-apply:hover { background: rgba(52,211,153,0.22); }
  .btn-remove-tiny {
    background: none;
    border: none;
    color: var(--muted);
    font-size: 0.7rem;
    cursor: pointer;
    padding: 0 0.2rem;
    line-height: 1;
  }
  .btn-remove-tiny:hover { color: var(--danger); }

  /* ── Progress ── */
  .progress-wrap { margin-top: 0.5rem; }
  .progress-bar { height: 4px; background: rgba(79,142,247,0.15); border-radius: 2px; overflow: hidden; }
  .progress-fill { height: 100%; background: var(--accent); border-radius: 2px; transition: width 0.25s ease; }
  .progress-text { font-size: 0.72rem; color: var(--muted); margin-top: 0.25rem; }
  .token-stream {
    font-size: 0.72rem;
    color: var(--muted);
    font-family: monospace;
    background: rgba(42,45,58,0.5);
    border-radius: 6px;
    padding: 0.4rem 0.6rem;
    margin-top: 0.4rem;
    max-height: 80px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-word;
  }

  /* ── Messages ── */
  .msg-error {
    font-size: 0.78rem;
    color: var(--danger);
    background: rgba(248,113,113,0.08);
    border: 1px solid rgba(248,113,113,0.2);
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
    margin-top: 0.5rem;
    white-space: pre-wrap;
    word-break: break-word;
    line-height: 1.5;
  }
  .msg-success {
    font-size: 0.78rem;
    color: var(--accent2);
    background: rgba(52,211,153,0.08);
    border: 1px solid rgba(52,211,153,0.2);
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
    margin-top: 0.5rem;
  }

  /* ── Note ── */
  .note { font-size: 0.75rem; color: var(--muted); line-height: 1.6; margin-top: 0.4rem; }

  /* ── Whisper model table ── */
  .model-table { display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 0.5rem; }
  .model-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: rgba(42,45,58,0.3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.5rem 0.85rem;
    cursor: pointer;
    transition: border-color 0.15s;
  }
  .model-row--active { border-color: rgba(79,142,247,0.4); background: rgba(79,142,247,0.06); }
  .model-radio input { cursor: pointer; }
  .model-info { flex: 1; display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; }
  .model-name { font-size: 0.82rem; font-weight: 600; color: var(--text); }
  .quality-badge {
    font-size: 0.7rem;
    padding: 0.1rem 0.45rem;
    border-radius: 99px;
    background: rgba(79,142,247,0.12);
    color: var(--accent);
    border: 1px solid rgba(79,142,247,0.25);
  }
  .model-cache-note { font-size: 0.72rem; color: var(--muted); white-space: nowrap; }

  /* ── CF Worker ── */
  .cf-steps { margin: 0.6rem 0; }
  .step { font-size: 0.8rem; color: var(--text); margin-bottom: 0.3rem; line-height: 1.5; }
  .step a { color: var(--accent); }
  .step code { font-family: monospace; font-size: 0.78rem; background: rgba(42,45,58,0.6); padding: 0.1rem 0.3rem; border-radius: 4px; }
  .code-block {
    background: rgba(15,17,23,0.7);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.75rem;
    font-family: monospace;
    font-size: 0.7rem;
    color: var(--text);
    overflow-x: auto;
    margin: 0.75rem 0;
    white-space: pre;
    max-height: 240px;
    overflow-y: auto;
  }
  .cf-input-row { display: flex; gap: 0.5rem; align-items: center; margin-top: 0.6rem; flex-wrap: wrap; }
  .cf-input-row input { flex: 1; min-width: 200px; }
  .cf-configured-row { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; }
  .cf-url { font-family: monospace; font-size: 0.78rem; color: var(--muted); word-break: break-all; }

  /* ── Chips ── */
  .chips { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.6rem; }
  .chip {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    background: rgba(42,45,58,0.5);
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 0.3rem 0.75rem;
    border-radius: 99px;
    font-size: 0.78rem;
    cursor: pointer;
    transition: all 0.15s;
  }
  .chip--active { background: rgba(79,142,247,0.15); border-color: rgba(79,142,247,0.4); color: var(--accent); }
  .chip:hover:not(.chip--active) { border-color: var(--accent); color: var(--text); }
  .chip-icon { font-size: 0.7rem; }
  .custom-tracks { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem; margin: 0.5rem 0; }
  .custom-track-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    background: rgba(52,211,153,0.1);
    border: 1px solid rgba(52,211,153,0.3);
    color: var(--accent2);
    padding: 0.2rem 0.55rem;
    border-radius: 99px;
    font-size: 0.75rem;
  }
  .custom-track-input { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.6rem; }
  .custom-track-input input { width: 180px; }

  /* ── Queue ── */
  .queue-list { display: flex; flex-direction: column; gap: 0.5rem; }
  .queue-item {
    background: rgba(42,45,58,0.3);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }
  .queue-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.55rem 0.85rem;
    cursor: pointer;
    gap: 0.5rem;
  }
  .queue-header:hover { background: rgba(79,142,247,0.04); }
  .queue-meta { display: flex; flex-direction: column; gap: 0.1rem; min-width: 0; }
  .queue-title { font-size: 0.82rem; font-weight: 600; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 340px; }
  .queue-channel { font-size: 0.72rem; color: var(--muted); }
  .queue-time { font-size: 0.7rem; color: var(--muted); }
  .queue-right { display: flex; align-items: center; gap: 0.5rem; flex-shrink: 0; }
  .queue-error-msg { color: var(--danger); font-size: 0.8rem; cursor: help; }
  .expand-toggle { color: var(--muted); font-size: 0.75rem; }
  .queue-expand { padding: 0.5rem 0.85rem 0.75rem; border-top: 1px solid var(--border); }
  .transcript-preview { margin-top: 0.4rem; }
  .transcript-text { font-size: 0.75rem; color: var(--muted); line-height: 1.6; white-space: pre-wrap; word-break: break-word; }

  /* ── Badges ── */
  .badge {
    font-size: 0.7rem;
    font-weight: 700;
    padding: 0.15rem 0.5rem;
    border-radius: 99px;
    white-space: nowrap;
  }
  .badge-muted { background: rgba(100,116,139,0.15); color: var(--muted); border: 1px solid rgba(100,116,139,0.25); }
  .badge-warn { background: rgba(251,191,36,0.12); color: var(--warn); border: 1px solid rgba(251,191,36,0.25); }
  .badge-done { background: rgba(52,211,153,0.12); color: var(--accent2); border: 1px solid rgba(52,211,153,0.25); }
  .badge-danger { background: rgba(248,113,113,0.12); color: var(--danger); border: 1px solid rgba(248,113,113,0.25); }

  /* ── Signal Feed ── */
  .feed-filters { display: flex; gap: 1rem; align-items: flex-end; flex-wrap: wrap; margin-bottom: 0.75rem; }
  .filter-group { display: flex; flex-direction: column; gap: 0.2rem; }
  .filter-group label { font-size: 0.75rem; color: var(--muted); }
  .signal-list { display: flex; flex-direction: column; gap: 0.5rem; }
  .signal-card {
    background: rgba(42,45,58,0.3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.65rem 0.9rem;
  }
  .signal-top { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.35rem; }
  .dir-badge {
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.15rem 0.5rem;
    border-radius: 99px;
    white-space: nowrap;
  }
  .dir-up { background: rgba(52,211,153,0.12); color: var(--accent2); border: 1px solid rgba(52,211,153,0.25); }
  .dir-down { background: rgba(248,113,113,0.12); color: var(--danger); border: 1px solid rgba(248,113,113,0.25); }
  .sig-weight { font-size: 0.75rem; font-weight: 600; color: var(--text); }
  .sig-ticker {
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--accent);
    background: rgba(79,142,247,0.1);
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
  }
  .sig-domain { font-size: 0.7rem; color: var(--muted); border: 1px solid var(--border); padding: 0.1rem 0.4rem; border-radius: 4px; }
  .sig-param { font-size: 0.75rem; color: var(--text); flex: 1; }
  .sig-time { font-size: 0.7rem; color: var(--muted); margin-left: auto; white-space: nowrap; }
  .sig-quote {
    font-size: 0.78rem;
    color: var(--muted);
    font-style: italic;
    border-left: 2px solid var(--border);
    padding-left: 0.6rem;
    margin: 0.3rem 0;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
  .sig-bottom { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; }
  .sig-confidence { font-size: 0.72rem; color: var(--muted); }

  /* ── Empty state ── */
  .empty-state { font-size: 0.8rem; color: var(--muted); padding: 0.75rem 0; }

  /* ── Intelligence Summary ── */
  .summary-grid { display: flex; gap: 1.5rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
  .summary-stat { display: flex; flex-direction: column; gap: 0.2rem; }
  .stat-label { font-size: 0.72rem; color: var(--muted); }
  .stat-val { font-size: 1rem; font-weight: 700; color: var(--text); }
  .stat-up { color: var(--accent2); }
  .stat-down { color: var(--danger); }
  .quote-list { list-style: decimal inside; display: flex; flex-direction: column; gap: 0.3rem; }
  .quote-list li { font-size: 0.78rem; color: var(--muted); font-style: italic; }
</style>
