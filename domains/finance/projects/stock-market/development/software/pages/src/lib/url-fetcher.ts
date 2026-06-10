// URL content fetching for Research popup.
// Tiered: direct fetch → CORS proxy fallback → paste prompt.

export interface FetchResult {
  ok: boolean;
  content: string;
  method: 'direct' | 'proxy' | 'failed';
  error?: string;
}

const PROXY = 'https://api.allorigins.win/get?url=';

export async function fetchUrl(url: string, useCorsProxy: boolean): Promise<FetchResult> {
  // Try direct first
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(8000) });
    if (res.ok) {
      const text = await res.text();
      return { ok: true, content: text.slice(0, 30000), method: 'direct' };
    }
  } catch {
    // CORS or network error — fall through
  }

  if (!useCorsProxy) {
    return {
      ok: false,
      content: '',
      method: 'failed',
      error: 'Direct fetch failed. Enable CORS proxy in Settings or paste content manually.',
    };
  }

  // Try CORS proxy
  try {
    const res = await fetch(PROXY + encodeURIComponent(url), { signal: AbortSignal.timeout(12000) });
    if (res.ok) {
      const json = await res.json() as { contents: string };
      return { ok: true, content: json.contents.slice(0, 30000), method: 'proxy' };
    }
    return { ok: false, content: '', method: 'failed', error: `Proxy returned ${res.status}. Please paste content manually.` };
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return { ok: false, content: '', method: 'failed', error: `Proxy fetch failed: ${msg}` };
  }
}

export function extractText(html: string): string {
  // Strip HTML tags and normalize whitespace
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 20000);
}
