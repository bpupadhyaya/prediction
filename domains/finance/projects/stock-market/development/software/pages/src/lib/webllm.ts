// Phase 2 — WebLLM integration stub
// WebLLM requires SharedArrayBuffer (COOP/COEP headers).
// GitHub Pages does not support custom headers natively.
// Solution (Phase 2): bundle coi-serviceworker to add headers via Service Worker.

export interface LLMStatus {
  available: boolean;
  modelId: string | null;
  downloading: boolean;
  progress: number;      // 0–1
  error: string | null;
}

export const LLM_MODELS = [
  { id: 'Phi-3.5-mini-instruct-q4f16_1-MLC', label: 'Phi 3.5 Mini (Recommended)', sizeGB: 2.4, description: 'Best quality/size tradeoff. Requires WebGPU.' },
  { id: 'gemma-2-2b-it-q4f16_1-MLC',         label: 'Gemma 2 2B',                 sizeGB: 1.6, description: 'Smallest good model. Faster download.' },
  { id: 'Llama-3.2-3B-Instruct-q4f16_1-MLC', label: 'Llama 3.2 3B',               sizeGB: 2.1, description: 'Meta open model.' },
] as const;

export function getStatus(): LLMStatus {
  return { available: false, modelId: null, downloading: false, progress: 0, error: 'Phase 2 — not yet implemented' };
}

export async function chat(_systemPrompt: string, _userMessage: string, _onToken: (t: string) => void): Promise<void> {
  throw new Error('WebLLM not yet implemented. Coming in Phase 2.');
}
