// Phase 2 — WebLLM browser inference
// Uses @mlc-ai/web-llm to run a local LLM entirely in-browser via WebGPU.
// SharedArrayBuffer is required by WebLLM; enabled via coi-serviceworker on
// GitHub Pages (which cannot set COOP/COEP headers natively).

import { MLCEngine, deleteModelAllInfoInCache, type InitProgressReport } from '@mlc-ai/web-llm';

export interface LLMStatus {
  available: boolean;
  modelId: string | null;
  downloading: boolean;
  progress: number;      // 0–1
  error: string | null;
}

export const LLM_MODELS = [
  { id: 'Phi-3.5-mini-instruct-q4f16_1-MLC', label: 'Phi-3.5 Mini (2.4 GB)', description: 'Fast, good for research summaries', sizeGB: 2.4 },
  { id: 'gemma-2-2b-it-q4f16_1-MLC', label: 'Gemma 2 2B (1.5 GB)', description: 'Compact, efficient inference', sizeGB: 1.5 },
  { id: 'Llama-3.2-3B-Instruct-q4f16_1-MLC', label: 'Llama 3.2 3B (2.0 GB)', description: 'Strong reasoning, balanced size', sizeGB: 2.0 },
] as const;

// Module-level singleton
let engine: MLCEngine | null = null;
let loadedModelId: string | null = null;

export function isModelLoaded(): boolean {
  return engine !== null && loadedModelId !== null;
}

export function getLoadedModelId(): string | null {
  return loadedModelId;
}

export function getStatus(): LLMStatus {
  return {
    available: isModelLoaded(),
    modelId: loadedModelId,
    downloading: false,
    progress: 0,
    error: isModelLoaded() ? null : 'No model loaded',
  };
}

/**
 * Download (or reload from cache) a model by ID.
 * Calls onProgress with a 0–100 percentage and a status text string.
 */
export async function downloadModel(
  modelId: string,
  onProgress: (progress: number, text: string) => void
): Promise<void> {
  try {
    // Reuse existing engine or create a new one
    if (!engine) {
      engine = new MLCEngine();
    }

    engine.setInitProgressCallback((report: InitProgressReport) => {
      const pct = Math.round(report.progress * 100);
      onProgress(pct, report.text);
    });

    onProgress(0, 'Initializing…');
    await engine.reload(modelId);
    loadedModelId = modelId;
    onProgress(100, 'Model ready');
  } catch (err: unknown) {
    // Reset engine on failure so the next attempt starts fresh
    engine = null;
    loadedModelId = null;
    const msg = err instanceof Error ? err.message : String(err);
    throw new Error(`Failed to download model "${modelId}": ${msg}`);
  }
}

/**
 * Send a chat message to the loaded model with streaming token callbacks.
 * Matches the signature already expected by ResearchModal.svelte.
 *
 * @param systemPrompt  System-role context for the LLM.
 * @param userMessage   The user's message.
 * @param onToken       Called for each streamed token fragment.
 * @returns             The full assembled response string.
 */
export async function chat(
  systemPrompt: string,
  userMessage: string,
  onToken: (token: string) => void
): Promise<string> {
  if (!engine || !loadedModelId) {
    throw new Error(
      'No LLM model loaded. Go to Settings → AI Research Assistant and download a model first.'
    );
  }

  try {
    const chunks = await engine.chat.completions.create({
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userMessage },
      ],
      stream: true,
      temperature: 0.7,
      max_tokens: 512,
    });

    let fullText = '';
    for await (const chunk of chunks) {
      const delta = chunk.choices[0]?.delta?.content ?? '';
      if (delta) {
        onToken(delta);
        fullText += delta;
      }
    }
    return fullText;
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    throw new Error(`LLM inference failed: ${msg}`);
  }
}

/**
 * Remove model weights from browser cache/OPFS.
 * After calling this, the model will need to be re-downloaded.
 */
export async function removeModel(modelId: string): Promise<void> {
  try {
    await deleteModelAllInfoInCache(modelId);
  } catch (err: unknown) {
    // Non-fatal — model may not have been cached
    console.warn('removeModel: could not delete cache for', modelId, err);
  }
  if (loadedModelId === modelId) {
    if (engine) {
      try { await engine.unload(); } catch { /* ignore */ }
    }
    engine = null;
    loadedModelId = null;
  }
}
