<script lang="ts">
  import { onMount } from 'svelte';
  import type { VideoSource, VideoSignal, ChannelTrack } from '../lib/types';
  import {
    saveVideoSource, getAllVideoSources, updateVideoSourceStatus,
    saveTranscript, getTranscript,
    saveVideoSignals, getAllSignals,
    saveChannelTrack, getAllChannelTracks, removeChannelTrack,
    getVideoSetting, setVideoSetting,
  } from '../lib/video-intelligence-store';
  import { WHISPER_MODELS, transcribeAudioBlob, getDefaultModelId } from '../lib/youtube-transcriber';
  import { extractSignalsFromTranscript } from '../lib/video-signal-extractor';

  export let onSignalApply: (signal: VideoSignal) => void = () => { /* no-op */ };

  // ── File drop state ──────────────────────────────────────────────────────────
  let droppedFile: File | null = null;
  let isDragging = false;

  // Optional metadata the user can fill in (for labelling; not required)
  let metaTitle = '';
  let metaChannel = '';
  let metaYouTubeUrl = '';   // reference link only — not fetched

  // ── Processing state ─────────────────────────────────────────────────────────
  let processing = false;
  let processingStatus = '';
  let processingPct = 0;
  let processError = '';
  let processSuccess = '';
  let extractionTokens = '';

  // ── Model selection ──────────────────────────────────────────────────────────
  let activeModelId = getDefaultModelId();

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
    { channelId: 'jim-cramer',     speakerName: 'Jim Cramer',     channelName: 'Mad Money/CNBC' },
    { channelId: 'michael-saylor', speakerName: 'Michael Saylor', channelName: 'MicroStrategy' },
  ];

  // ── Video queue ──────────────────────────────────────────────────────────────
  let videoSources: VideoSource[] = [];
  let expandedVideoId: string | null = null;
  let expandedTranscript: string | null = null;

  // ── Signal feed ──────────────────────────────────────────────────────────────
  let signals: VideoSignal[] = [];
  let signalTimeRange = '168';  // hours; default 1 week
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

  // ── Mount ────────────────────────────────────────────────────────────────────
  onMount(async () => {
    try {
      const [sources, tracks, savedModel] = await Promise.all([
        getAllVideoSources(),
        getAllChannelTracks(),
        getVideoSetting('activeWhisperModel'),
      ]);
      videoSources = sources;
      trackedChannels = tracks;
      if (savedModel) activeModelId = savedModel;
      await refreshSignals();
    } catch (err) {
      console.error('YVIS: failed to load initial data', err);
    }
  });

  async function refreshSignals() {
    const days = signalTimeRange === '0' ? undefined : Number(signalTimeRange) / 24;
    const ticker = tickerFilter.trim().toUpperCase() || undefined;
    signals = await getAllSignals(ticker, days);
  }

  // ── File drop / select ────────────────────────────────────────────────────────

  function onDragover(e: DragEvent) {
    e.preventDefault();
    isDragging = true;
  }

  function onDragleave() {
    isDragging = false;
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    isDragging = false;
    const file = e.dataTransfer?.files?.[0];
    if (file) acceptFile(file);
  }

  function onFileInput(e: Event) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) acceptFile(file);
    input.value = '';
  }

  function acceptFile(file: File) {
    if (!file.type.startsWith('audio/') && !file.type.startsWith('video/')) {
      processError = `Unsupported file type: "${file.type}". Drop an audio or video file (mp3, mp4, m4a, webm, wav, ogg…)`;
      return;
    }
    processError = '';
    droppedFile = file;
    // Auto-fill title from filename if empty
    if (!metaTitle) metaTitle = file.name.replace(/\.[^.]+$/, '');
  }

  function clearFile() {
    droppedFile = null;
    metaTitle = '';
    metaChannel = '';
    metaYouTubeUrl = '';
  }

  // ── Main analysis pipeline ────────────────────────────────────────────────────

  async function handleAnalyze() {
    if (!droppedFile) {
      processError = 'Drop an audio or video file to get started.';
      return;
    }

    processError = '';
    processSuccess = '';
    processing = true;
    processingPct = 0;
    extractionTokens = '';

    const sourceId = `vid-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const title   = metaTitle.trim()   || droppedFile.name;
    const channel = metaChannel.trim() || 'Unknown';

    const source: VideoSource = {
      id: sourceId,
      url: metaYouTubeUrl.trim() || `file://${droppedFile.name}`,
      videoId: sourceId,
      title,
      channelName: channel,
      channelId: '',
      speakerName: '',
      publishedAt: new Date().toISOString(),
      durationSec: 0,
      viewCount: 0,
      status: 'transcribing',
      transcriptModel: activeModelId,
      createdAt: new Date().toISOString(),
    };

    try {
      await saveVideoSource(source);
      videoSources = await getAllVideoSources();

      // ── Step 1: Transcribe ────────────────────────────────────────────────────
      processingStatus = 'Starting transcription…';
      processingPct = 5;

      const transcription = await transcribeAudioBlob(
        droppedFile,
        activeModelId,
        (pct, msg) => {
          processingPct = 5 + Math.round(pct * 0.6);
          processingStatus = msg;
        },
      );

      await saveTranscript({
        videoId: sourceId,
        fullText: transcription.fullText,
        chunks: transcription.chunks,
        wordCount: transcription.wordCount,
        language: 'en',
        modelUsed: activeModelId,
        transcribedAt: new Date().toISOString(),
      });

      await updateVideoSourceStatus(sourceId, 'extracting');
      videoSources = await getAllVideoSources();

      // ── Step 2: Extract signals ────────────────────────────────────────────────
      processingStatus = 'Extracting market signals with LLM…';
      processingPct = 70;
      extractionTokens = '';

      const extractedSignals = await extractSignalsFromTranscript(
        transcription.fullText,
        title,
        channel,
        sourceId,
        (token) => { extractionTokens += token; },
      );

      await saveVideoSignals(extractedSignals);
      await updateVideoSourceStatus(sourceId, 'done');
      videoSources = await getAllVideoSources();
      await refreshSignals();

      processingPct = 100;
      processingStatus = `Done! ${extractedSignals.length} signal${extractedSignals.length !== 1 ? 's' : ''} extracted.`;
      processSuccess = `Processed "${title}". ${extractedSignals.length} market signal${extractedSignals.length !== 1 ? 's' : ''} extracted.`;
      clearFile();

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

  // ── Model selection ───────────────────────────────────────────────────────────

  async function selectModel(id: string) {
    activeModelId = id;
    await setVideoSetting('activeWhisperModel', id);
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
        channelId:    preset.channelId,
        channelName:  preset.channelName,
        speakerName:  preset.speakerName,
        autoProcess:  false,
        timeRangeYears: 1,
        createdAt:    new Date().toISOString(),
      });
    }
    trackedChannels = await getAllChannelTracks();
  }

  async function trackCustomChannel() {
    const id = customChannelInput.trim();
    const speaker = customSpeakerInput.trim() || id;
    if (!id) return;
    await saveChannelTrack({
      channelId: id, channelName: id, speakerName: speaker,
      autoProcess: false, timeRangeYears: 1,
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
    if (expandedVideoId === videoId) { expandedVideoId = null; expandedTranscript = null; return; }
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

  async function onTimeRangeChange()   { await refreshSignals(); }
  async function onTickerFilterChange(){ await refreshSignals(); }

  function timeAgo(iso: string): string {
    const diff = Date.now() - new Date(iso).getTime();
    const m = Math.floor(diff / 60000);
    if (m < 1)  return 'just now';
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h}h ago`;
    const d = Math.floor(h / 24);
    if (d < 30) return `${d}d ago`;
    return `${Math.floor(d / 30)}mo ago`;
  }

  function statusColor(status: VideoSource['status']): string {
    switch (status) {
      case 'pending':     return 'badge-muted';
      case 'transcribing':return 'badge-warn';
      case 'extracting':  return 'badge-warn';
      case 'done':        return 'badge-done';
      case 'error':       return 'badge-danger';
      default:            return 'badge-muted';
    }
  }

  // ── Intelligence summary ──────────────────────────────────────────────────────

  $: filteredTicker = tickerFilter.trim().toUpperCase();

  $: tickerSignals = filteredTicker
    ? signals.filter(s => s.ticker === filteredTicker)
    : [];

  $: summaryDirection = (() => {
    if (!tickerSignals.length) return null;
    const up   = tickerSignals.filter(s => s.direction === 'up').reduce((a, s) => a + s.weight * s.confidence, 0);
    const down = tickerSignals.filter(s => s.direction === 'down').reduce((a, s) => a + s.weight * s.confidence, 0);
    return up >= down ? 'up' : 'down';
  })();

  $: avgConfidence = tickerSignals.length
    ? tickerSignals.reduce((a, s) => a + s.confidence, 0) / tickerSignals.length
    : 0;

  $: topQuotes = tickerSignals.slice(0, 5).map(s => s.keyQuote).filter(Boolean);

  function handleApply(signal: VideoSignal) { onSignalApply(signal); }

  // ── File size helper ──────────────────────────────────────────────────────────
  function fmtSize(bytes: number): string {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
</script>

<div class="yvis">
  <!-- ── Header ──────────────────────────────────────────────────────────────── -->
  <div class="page-header">
    <div>
      <h2>Video Intelligence</h2>
      <p class="subtitle">Drop any audio/video file → on-device transcription → market signal extraction</p>
    </div>
  </div>

  <!-- ── File Drop Zone ─────────────────────────────────────────────────────── -->
  <section class="card">
    {#if !droppedFile}
      <!-- Drop target -->
      <!-- svelte-ignore a11y-interactive-supports-focus -->
      <div
        class="drop-zone"
        class:drop-zone--active={isDragging}
        role="button"
        aria-label="Drop audio or video file here"
        on:dragover={onDragover}
        on:dragleave={onDragleave}
        on:drop={onDrop}
        on:click={() => document.getElementById('file-picker')?.click()}
        on:keydown={e => e.key === 'Enter' && document.getElementById('file-picker')?.click()}
        tabindex="0"
      >
        <div class="drop-icon">🎵</div>
        <div class="drop-label">Drop audio or video file here</div>
        <div class="drop-sub">mp3 · mp4 · m4a · webm · wav · ogg · and more</div>
        <button class="btn-secondary btn-sm" type="button" on:click|stopPropagation={() => document.getElementById('file-picker')?.click()}>
          Browse files
        </button>
        <input
          id="file-picker"
          type="file"
          accept="audio/*,video/*"
          style="display:none"
          on:change={onFileInput}
        />
      </div>

      <p class="note drop-how">
        <strong>How to get the audio file:</strong>
        Use <code>yt-dlp -x --audio-format mp3 "URL"</code> in a terminal,
        or any YouTube-to-audio tool you prefer. Drop the file here — transcription runs entirely in your browser.
      </p>

    {:else}
      <!-- File ready -->
      <div class="file-ready">
        <div class="file-icon">🎵</div>
        <div class="file-meta">
          <span class="file-name">{droppedFile.name}</span>
          <span class="file-size">{fmtSize(droppedFile.size)}</span>
        </div>
        <button class="btn-ghost btn-sm" on:click={clearFile} disabled={processing}>✕ Remove</button>
      </div>

      <!-- Optional metadata -->
      <div class="meta-fields">
        <input
          type="text"
          placeholder="Video title (optional)"
          bind:value={metaTitle}
          disabled={processing}
          aria-label="Video title"
        />
        <input
          type="text"
          placeholder="Channel / Speaker (optional)"
          bind:value={metaChannel}
          disabled={processing}
          aria-label="Channel or speaker name"
        />
        <input
          type="url"
          placeholder="YouTube URL for reference (optional)"
          bind:value={metaYouTubeUrl}
          disabled={processing}
          aria-label="YouTube URL reference"
        />
      </div>

      <button class="btn-primary" on:click={handleAnalyze} disabled={processing}>
        {processing ? '⏳ Processing…' : '▶ Transcribe & Extract Signals'}
      </button>
    {/if}

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
          <div class="model-cache-note">Cached in browser (OPFS)</div>
        </div>
      {/each}
    </div>
    <p class="note">Models are downloaded once and cached in your browser's Origin Private File System — no server, no account needed.</p>
  </section>

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
      <input type="text" placeholder="Speaker / channel name" bind:value={customChannelInput} aria-label="Speaker name" />
      <input type="text" placeholder="Display name (optional)" bind:value={customSpeakerInput} aria-label="Display name" />
      <button class="btn-secondary btn-sm" on:click={trackCustomChannel}>Track</button>
    </div>

    <p class="note">Tracked speakers let you annotate and filter signals by source. Download their videos, drop them here to analyze.</p>
  </section>

  <!-- ── Processing Queue ──────────────────────────────────────────────────── -->
  <section class="card">
    <div class="section-label">PROCESSING QUEUE</div>

    {#if videoSources.length === 0}
      <p class="empty-state">No videos analyzed yet. Drop an audio/video file above to get started.</p>
    {:else}
      <div class="queue-list">
        {#each videoSources as vid}
          <div class="queue-item">
            <!-- svelte-ignore a11y-interactive-supports-focus -->
            <div
              class="queue-header"
              role="button"
              tabindex="0"
              on:click={() => toggleExpand(vid.videoId)}
              on:keydown={e => e.key === 'Enter' && toggleExpand(vid.videoId)}
            >
              <div class="queue-meta">
                <span class="queue-title">{vid.title}</span>
                <span class="queue-channel">{vid.channelName}</span>
                <span class="queue-time">{timeAgo(vid.createdAt)}</span>
              </div>
              <div class="queue-right">
                <span class="badge {statusColor(vid.status)}">{vid.status}</span>
                {#if vid.status === 'error'}<span class="queue-error-msg" title={vid.errorMsg ?? ''}>⚠</span>{/if}
                <span class="expand-toggle">{expandedVideoId === vid.videoId ? '▲' : '▼'}</span>
              </div>
            </div>

            {#if expandedVideoId === vid.videoId}
              <div class="queue-expand">
                {#if vid.errorMsg}<div class="msg-error">{vid.errorMsg}</div>{/if}
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
              {#if sig.ticker}<span class="sig-ticker">{sig.ticker}</span>{/if}
              <span class="sig-domain">{sig.domain}</span>
              <span class="sig-param">{sig.parameterName}</span>
              <span class="sig-time">{timeAgo(sig.extractedAt)}</span>
            </div>
            <blockquote class="sig-quote">"{sig.keyQuote}"</blockquote>
            <div class="sig-bottom">
              <span class="sig-confidence">confidence: {Math.round(sig.confidence * 100)}%</span>
              <button class="btn-apply" on:click={() => handleApply(sig)}>Apply to Prediction</button>
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
          {#each topQuotes as q}<li>"{q}"</li>{/each}
        </ol>
      {/if}
    </section>
  {/if}
</div>

<style>
  .yvis { max-width: 800px; }

  .page-header { margin-bottom: 1rem; }
  h2 { font-size: 1.1rem; font-weight: 700; color: var(--text); margin-bottom: 0.2rem; }
  .subtitle { font-size: 0.8rem; color: var(--muted); }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.1rem 1.25rem;
    margin-bottom: 1rem;
  }

  .section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: var(--muted);
    text-transform: uppercase;
    margin-bottom: 0.6rem;
  }

  /* ── Drop zone ── */
  .drop-zone {
    border: 2px dashed var(--border);
    border-radius: 10px;
    padding: 2rem 1.5rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.15s;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
  }
  .drop-zone:hover, .drop-zone--active {
    border-color: var(--accent);
    background: rgba(79,142,247,0.05);
  }
  .drop-icon { font-size: 2rem; }
  .drop-label { font-size: 0.9rem; font-weight: 600; color: var(--text); }
  .drop-sub { font-size: 0.75rem; color: var(--muted); }
  .drop-how { margin-top: 0.4rem; }
  .drop-how code { font-family: monospace; font-size: 0.78rem; background: rgba(42,45,58,0.6); padding: 0.1rem 0.3rem; border-radius: 4px; }

  /* ── File ready ── */
  .file-ready {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: rgba(79,142,247,0.06);
    border: 1px solid rgba(79,142,247,0.25);
    border-radius: 8px;
    padding: 0.6rem 0.85rem;
    margin-bottom: 0.75rem;
  }
  .file-icon { font-size: 1.3rem; }
  .file-meta { flex: 1; display: flex; flex-direction: column; gap: 0.1rem; min-width: 0; }
  .file-name { font-size: 0.82rem; font-weight: 600; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .file-size { font-size: 0.72rem; color: var(--muted); }

  /* ── Metadata fields ── */
  .meta-fields {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    margin-bottom: 0.75rem;
  }
  .meta-fields input { width: 100%; }

  /* ── Buttons ── */
  .btn-primary {
    background: var(--accent);
    border: none;
    color: #fff;
    padding: 0.45rem 1.25rem;
    border-radius: 8px;
    font-size: 0.875rem;
    font-weight: 600;
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
  .progress-wrap { margin-top: 0.75rem; }
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
  .queue-item { background: rgba(42,45,58,0.3); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
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
  .badge { font-size: 0.7rem; font-weight: 700; padding: 0.15rem 0.5rem; border-radius: 99px; white-space: nowrap; }
  .badge-muted  { background: rgba(100,116,139,0.15); color: var(--muted);    border: 1px solid rgba(100,116,139,0.25); }
  .badge-warn   { background: rgba(251,191,36,0.12);  color: var(--warn);     border: 1px solid rgba(251,191,36,0.25); }
  .badge-done   { background: rgba(52,211,153,0.12);  color: var(--accent2);  border: 1px solid rgba(52,211,153,0.25); }
  .badge-danger { background: rgba(248,113,113,0.12); color: var(--danger);   border: 1px solid rgba(248,113,113,0.25); }

  /* ── Signal Feed ── */
  .feed-filters { display: flex; gap: 1rem; align-items: flex-end; flex-wrap: wrap; margin-bottom: 0.75rem; }
  .filter-group { display: flex; flex-direction: column; gap: 0.2rem; }
  .filter-group label { font-size: 0.75rem; color: var(--muted); }
  .signal-list { display: flex; flex-direction: column; gap: 0.5rem; }
  .signal-card { background: rgba(42,45,58,0.3); border: 1px solid var(--border); border-radius: 8px; padding: 0.65rem 0.9rem; }
  .signal-top { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.35rem; }
  .dir-badge { font-size: 0.75rem; font-weight: 700; padding: 0.15rem 0.5rem; border-radius: 99px; white-space: nowrap; }
  .dir-up   { background: rgba(52,211,153,0.12); color: var(--accent2); border: 1px solid rgba(52,211,153,0.25); }
  .dir-down { background: rgba(248,113,113,0.12); color: var(--danger);  border: 1px solid rgba(248,113,113,0.25); }
  .sig-weight { font-size: 0.75rem; font-weight: 600; color: var(--text); }
  .sig-ticker { font-size: 0.75rem; font-weight: 700; color: var(--accent); background: rgba(79,142,247,0.1); padding: 0.1rem 0.4rem; border-radius: 4px; }
  .sig-domain { font-size: 0.7rem; color: var(--muted); border: 1px solid var(--border); padding: 0.1rem 0.4rem; border-radius: 4px; }
  .sig-param  { font-size: 0.75rem; color: var(--text); flex: 1; }
  .sig-time   { font-size: 0.7rem; color: var(--muted); margin-left: auto; white-space: nowrap; }
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

  .empty-state { font-size: 0.8rem; color: var(--muted); padding: 0.75rem 0; }

  /* ── Intelligence Summary ── */
  .summary-grid { display: flex; gap: 1.5rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
  .summary-stat { display: flex; flex-direction: column; gap: 0.2rem; }
  .stat-label { font-size: 0.72rem; color: var(--muted); }
  .stat-val   { font-size: 1rem; font-weight: 700; color: var(--text); }
  .stat-up    { color: var(--accent2); }
  .stat-down  { color: var(--danger); }
  .quote-list { list-style: decimal inside; display: flex; flex-direction: column; gap: 0.3rem; }
  .quote-list li { font-size: 0.78rem; color: var(--muted); font-style: italic; }
</style>
