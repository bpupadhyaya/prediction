const BASE = "/api";

export interface StockInfo {
  ticker: string;
  name: string;
  sector: string;
  industry: string;
  market_cap: number;
}

export interface PriceBar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  adj_close: number;
}

export interface PredictionResult {
  ticker: string;
  horizon: string;
  direction: "up" | "down" | "unknown";
  probability: number;
  expected_return_low: number;
  expected_return_high: number;
  volatility: number;
  model_accuracy: number;
  model_ready: boolean;
  disclaimer: string;
}

export interface PortfolioHolding {
  ticker: string;
  quantity: number;
  purchase_price?: number;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  predict: (ticker: string, horizon = "1w") =>
    get<PredictionResult>(`/predict/${ticker}?horizon=${horizon}`),

  topPredictions: (limit = 20) =>
    get<PredictionResult[]>(`/predict/batch/top?limit=${limit}`),

  stockInfo: (ticker: string) =>
    get<StockInfo>(`/stocks/${ticker}/info`),

  prices: (ticker: string, days = 365) =>
    get<PriceBar[]>(`/stocks/${ticker}/prices?days=${days}`),

  analyzePortfolio: (holdings: PortfolioHolding[], horizon = "1w") =>
    post<{ total_value: number; holdings: unknown[]; summary: unknown; disclaimer: string }>(
      `/portfolio/analyze`,
      { holdings, horizon }
    ),

  triggerSync: () =>
    post<{ status: string; message: string }>("/sync/refresh", {}),

  syncStatus: () =>
    get<{ running: boolean; last_completed: string | null; message: string }>("/sync/status"),

  saveInteractiveSnapshot: (payload: {
    ticker: string;
    prob_up: number;
    confidence: number;
    direction: string;
    user_signals: Array<{ name: string; domain: string; direction: string; weight: number; value: number | null }>;
    source: string;
  }) =>
    post<{ status: string }>("/interactive/predictions", payload),
};
