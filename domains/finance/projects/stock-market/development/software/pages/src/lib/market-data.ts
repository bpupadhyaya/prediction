// Live market data + on-device feature engineering for the browser predictor.
//
// Crypto uses Coinbase's public candles API, which is CORS-enabled and needs no
// key or proxy — so the FREE public site predicts real crypto in any browser,
// anywhere, with zero infrastructure. The 16 features computed here MUST match
// trainer.build_features() / the mobile PredictionEngines exactly (same order,
// same math, prices newest-first).

export interface Bar {
  time: number;   // unix seconds
  close: number;
  volume: number;
}

export interface CryptoProduct {
  id: string;     // Coinbase product id, e.g. "BTC-USD"
  label: string;
}

// Coinbase-listed pairs that overlap the app's crypto universe.
export const CRYPTO_PRODUCTS: CryptoProduct[] = [
  { id: 'BTC-USD', label: 'Bitcoin' },
  { id: 'ETH-USD', label: 'Ethereum' },
  { id: 'SOL-USD', label: 'Solana' },
  { id: 'XRP-USD', label: 'XRP' },
  { id: 'ADA-USD', label: 'Cardano' },
  { id: 'DOGE-USD', label: 'Dogecoin' },
  { id: 'AVAX-USD', label: 'Avalanche' },
  { id: 'DOT-USD', label: 'Polkadot' },
  { id: 'LINK-USD', label: 'Chainlink' },
  { id: 'LTC-USD', label: 'Litecoin' },
  { id: 'BCH-USD', label: 'Bitcoin Cash' },
  { id: 'XLM-USD', label: 'Stellar' },
  { id: 'ATOM-USD', label: 'Cosmos' },
  { id: 'UNI-USD', label: 'Uniswap' },
  { id: 'AAVE-USD', label: 'Aave' },
  { id: 'ALGO-USD', label: 'Algorand' },
  { id: 'NEAR-USD', label: 'NEAR' },
  { id: 'FIL-USD', label: 'Filecoin' },
];

/**
 * Fetch daily candles from Coinbase (newest-first), returning bars sorted
 * newest-first to match the mobile feature contract.
 * Coinbase candle = [time, low, high, open, close, volume].
 */
export async function fetchCryptoBars(productId: string): Promise<Bar[]> {
  const url = `https://api.exchange.coinbase.com/products/${productId}/candles?granularity=86400`;
  const resp = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!resp.ok) throw new Error(`Coinbase ${resp.status} for ${productId}`);
  const raw = (await resp.json()) as number[][];
  // Already newest-first; map to Bar and sort defensively.
  return raw
    .map((c) => ({ time: c[0], close: c[4], volume: c[5] }))
    .sort((a, b) => b.time - a.time);
}

/** Sample standard deviation (ddof=1) — matches pandas rolling().std(). */
function sampleStd(values: number[]): number {
  if (values.length < 2) return 0;
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const variance = values.reduce((a, b) => a + (b - mean) * (b - mean), 0) / (values.length - 1);
  return Math.sqrt(variance);
}

/** Standard 14-period SMA RSI on newest-first closes. */
function computeRSI(closes: number[], period = 14): number {
  if (closes.length <= period) return 50;
  let gains = 0;
  let losses = 0;
  for (let i = 0; i < period; i++) {
    const change = closes[i] - closes[i + 1];
    if (change > 0) gains += change;
    else losses -= change;
  }
  const avgGain = gains / period;
  const avgLoss = losses / period;
  if (avgLoss === 0) return 100;
  const rs = avgGain / avgLoss;
  return 100 - 100 / (1 + rs);
}

export const MIN_BARS = 253;

/**
 * Compute the 16 model features from newest-first bars, in MOBILE_FEATURES order:
 *   return_1d, return_5d, return_20d, return_60d, return_126d, return_252d,
 *   ma_5, ma_20, ma_50, ma_200, volatility_20, volatility_60,
 *   volume_ratio, dollar_volume_turnover, rsi, high_52w_ratio
 * Returns null when there is insufficient history.
 */
export function computeFeatures(bars: Bar[]): Float32Array | null {
  if (bars.length < MIN_BARS) return null;
  const closes = bars.map((b) => b.close);
  const volumes = bars.map((b) => b.volume);
  const c0 = closes[0];

  const ret = (n: number) => (c0 - closes[n]) / closes[n];
  const maDev = (n: number) => closes.slice(0, n).reduce((a, b) => a + b, 0) / n / c0 - 1;
  const volStd = (n: number) => {
    const r: number[] = [];
    for (let i = 0; i < n; i++) r.push(closes[i] / closes[i + 1] - 1);
    return sampleStd(r);
  };

  const avgVol = volumes.slice(0, 20).reduce((a, b) => a + b, 0) / 20;
  const volRatio = avgVol > 0 ? volumes[0] / avgVol : 1;
  const dollar: number[] = [];
  for (let i = 0; i < 20; i++) dollar.push(closes[i] * volumes[i]);
  const avgDollar = dollar.reduce((a, b) => a + b, 0) / 20;
  const dollarTurnover = avgDollar > 0 ? dollar[0] / avgDollar : 1;
  const rsi = computeRSI(closes.slice(0, 15));
  const high52w = Math.max(...closes.slice(0, 252));
  const high52wRatio = high52w > 0 ? c0 / high52w : 1;

  return new Float32Array([
    ret(1), ret(5), ret(20), ret(60), ret(126), ret(252),
    maDev(5), maDev(20), maDev(50), maDev(200),
    volStd(20), volStd(60),
    volRatio, dollarTurnover,
    rsi, high52wRatio,
  ]);
}
