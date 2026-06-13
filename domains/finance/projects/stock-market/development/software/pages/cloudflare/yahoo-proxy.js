/**
 * Cloudflare Worker — keyless Yahoo Finance proxy for the free Pages predictor.
 *
 * Yahoo's chart API has the daily OHLCV history the 16-feature model needs and
 * needs no API key, but it does NOT send CORS headers, so a browser can't call
 * it directly. This ~30-line worker re-serves Yahoo with permissive CORS, giving
 * the public site keyless prediction for ANY global stock — no Twelve Data key.
 *
 * Deploy (one time, free tier):
 *   1. npm i -g wrangler && wrangler login
 *   2. wrangler deploy pages/cloudflare/yahoo-proxy.js --name yahoo-proxy
 *      (or paste this into a new Worker in the Cloudflare dashboard)
 *   3. Copy the deployed URL (e.g. https://yahoo-proxy.<you>.workers.dev) into
 *      the app: Settings → "Yahoo proxy URL".
 *
 * Request:  GET <worker>/?symbol=AAPL&range=2y&interval=1d
 * Response: the raw Yahoo chart JSON, with CORS headers.
 */

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export default {
  async fetch(request) {
    if (request.method === 'OPTIONS') return new Response(null, { headers: CORS });

    const { searchParams } = new URL(request.url);
    const symbol = (searchParams.get('symbol') || '').trim();
    if (!symbol) {
      return json({ error: 'missing ?symbol' }, 400);
    }
    const range = searchParams.get('range') || '2y';
    const interval = searchParams.get('interval') || '1d';

    const upstream =
      `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}` +
      `?range=${encodeURIComponent(range)}&interval=${encodeURIComponent(interval)}`;

    try {
      const resp = await fetch(upstream, {
        headers: { 'User-Agent': 'Mozilla/5.0', Accept: 'application/json' },
        cf: { cacheTtl: 600, cacheEverything: true },   // cache 10 min
      });
      const body = await resp.text();
      return new Response(body, {
        status: resp.status,
        headers: { 'Content-Type': 'application/json', ...CORS },
      });
    } catch (e) {
      return json({ error: String(e) }, 502);
    }
  },
};

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { 'Content-Type': 'application/json', ...CORS },
  });
}
