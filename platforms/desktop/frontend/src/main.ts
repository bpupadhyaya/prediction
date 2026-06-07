import { api, PredictionResult, PriceBar } from "./api";
import { Chart, registerables } from "chart.js";
Chart.register(...registerables);

declare global {
  interface Window {
    showView: (v: string) => void;
    lookupStock: () => void;
    analyzePortfolio: () => void;
    triggerSync: () => void;
  }
}

// ── View navigation ──────────────────────────────────────────────────────────
window.showView = (view: string) => {
  document.querySelectorAll("[id^=view-]").forEach((el) => el.classList.remove("active"));
  document.querySelectorAll("nav button").forEach((b, i) => {
    b.classList.toggle("active", ["home", "stock", "portfolio"][i] === view);
  });
  document.getElementById(`view-${view}`)?.classList.add("active");
};

// ── Helpers ──────────────────────────────────────────────────────────────────
function dirBadge(pred: PredictionResult): string {
  const pct = Math.round(pred.probability * 100);
  const cls = pred.direction === "up" ? "up" : "down";
  const arrow = pred.direction === "up" ? "▲" : "▼";
  return `<span class="badge ${cls}">${arrow} ${pct}% ${pred.direction.toUpperCase()}</span>`;
}

function accuracyBadge(acc: number): string {
  return `<span class="accuracy-badge">Model accuracy: ${Math.round(acc * 100)}%</span>`;
}

function returnRange(pred: PredictionResult): string {
  const lo = (pred.expected_return_low * 100).toFixed(1);
  const hi = (pred.expected_return_high * 100).toFixed(1);
  return `${lo}% to ${hi}%`;
}

// ── Home: top signals ────────────────────────────────────────────────────────
async function loadTopPredictions() {
  const container = document.getElementById("top-cards")!;
  try {
    const preds = await api.topPredictions(20);
    container.innerHTML = preds.map((p) => `
      <div class="card" onclick="window.showView('stock'); (document.getElementById('ticker-input') as HTMLInputElement).value='${p.ticker}'; window.lookupStock()">
        <div class="ticker">${p.ticker}</div>
        ${dirBadge(p)}
        <div class="stat"><span>Expected return</span><span>${returnRange(p)}</span></div>
        <div class="stat"><span>${accuracyBadge(p.model_accuracy)}</span><span>1-week horizon</span></div>
      </div>
    `).join("") || "<p style='color:var(--muted)'>No predictions yet — run setup first.</p>";
  } catch {
    container.innerHTML = "<p style='color:var(--muted)'>Could not load predictions. Is the server running?</p>";
  }
}

// ── Stock lookup ─────────────────────────────────────────────────────────────
let priceChart: Chart | null = null;

window.lookupStock = async () => {
  const input = document.getElementById("ticker-input") as HTMLInputElement;
  const ticker = input.value.trim().toUpperCase();
  if (!ticker) return;

  const container = document.getElementById("stock-result")!;
  container.innerHTML = "<p style='color:var(--muted)'>Loading...</p>";

  try {
    const [pred, prices] = await Promise.all([
      api.predict(ticker, "1w"),
      api.prices(ticker, 252),
    ]);

    container.innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1rem;">
        <div class="card">
          <div class="ticker">${pred.ticker}</div>
          <div style="margin-bottom:0.75rem">${dirBadge(pred)}</div>
          <div class="stat"><span>1-week expected return</span><span>${returnRange(pred)}</span></div>
          <div class="stat"><span>Volatility (annualised)</span><span>${(pred.volatility * 100).toFixed(1)}%</span></div>
          <div class="stat"><span>Model accuracy</span><span>${Math.round(pred.model_accuracy * 100)}%</span></div>
        </div>
        <div class="card" style="display:flex;flex-direction:column;gap:0.5rem;">
          <p style="font-size:0.85rem;color:var(--muted)">Horizons</p>
          <div id="horizon-badges" style="display:flex;gap:0.5rem;flex-wrap:wrap;"></div>
        </div>
      </div>
      <div class="chart-container">
        <h3 style="margin-bottom:1rem;">Price History (1 year)</h3>
        <canvas id="price-chart"></canvas>
      </div>
    `;

    // Multi-horizon badges
    const horizonContainer = document.getElementById("horizon-badges")!;
    for (const horizon of ["1d", "1w", "1m"]) {
      try {
        const p = await api.predict(ticker, horizon);
        const btn = document.createElement("span");
        btn.className = `badge ${p.direction === "up" ? "up" : "down"}`;
        btn.textContent = `${horizon}: ${Math.round(p.probability * 100)}% ${p.direction}`;
        horizonContainer.appendChild(btn);
      } catch { /* skip */ }
    }

    renderPriceChart(prices);
  } catch (e) {
    container.innerHTML = `<p style='color:var(--danger)'>Error: ${e}</p>`;
  }
};

function renderPriceChart(prices: PriceBar[]) {
  const ctx = (document.getElementById("price-chart") as HTMLCanvasElement).getContext("2d")!;
  if (priceChart) priceChart.destroy();
  const sorted = [...prices].reverse();
  priceChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: sorted.map((p) => p.date),
      datasets: [{
        label: "Close Price",
        data: sorted.map((p) => p.adj_close),
        borderColor: "#4f8ef7",
        borderWidth: 2,
        pointRadius: 0,
        fill: false,
        tension: 0.1,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { maxTicksLimit: 8, color: "#64748b" }, grid: { color: "#2a2d3a" } },
        y: { ticks: { color: "#64748b" }, grid: { color: "#2a2d3a" } },
      },
    },
  });
}

// ── Portfolio ────────────────────────────────────────────────────────────────
window.analyzePortfolio = async () => {
  const textarea = document.getElementById("portfolio-input") as HTMLTextAreaElement;
  const lines = textarea.value.trim().split("\n").filter(Boolean);
  const holdings = lines.map((line) => {
    const parts = line.split(":");
    return {
      ticker: parts[0].trim().toUpperCase(),
      quantity: parseFloat(parts[1] ?? "1"),
      purchase_price: parts[2] ? parseFloat(parts[2]) : undefined,
    };
  });

  const container = document.getElementById("portfolio-result")!;
  container.innerHTML = "<p style='color:var(--muted)'>Analyzing...</p>";

  try {
    const result = await api.analyzePortfolio(holdings);
    const h = result.holdings as Array<{
      ticker: string; current_price: number; position_value: number;
      gain_loss_pct: number | null;
      prediction: { direction: string; probability: number; model_accuracy: number };
    }>;

    container.innerHTML = `
      <div class="card" style="margin-bottom:1rem;">
        <div style="font-size:1.1rem;font-weight:600;margin-bottom:0.5rem;">
          Total Value: $${(result.total_value as number).toLocaleString("en-US", { minimumFractionDigits: 2 })}
        </div>
      </div>
      <div class="cards">
        ${h.map((holding) => `
          <div class="card">
            <div class="ticker">${holding.ticker}</div>
            <div class="stat"><span>Price</span><span>$${holding.current_price.toFixed(2)}</span></div>
            <div class="stat"><span>Value</span><span>$${holding.position_value.toFixed(2)}</span></div>
            ${holding.gain_loss_pct !== null ? `<div class="stat"><span>Gain/Loss</span><span style="color:${holding.gain_loss_pct >= 0 ? "var(--accent2)" : "var(--danger)"}">${holding.gain_loss_pct.toFixed(2)}%</span></div>` : ""}
            <div style="margin-top:0.5rem;">
              <span class="badge ${holding.prediction.direction === "up" ? "up" : "down"}">
                ${Math.round(holding.prediction.probability * 100)}% ${holding.prediction.direction}
              </span>
              ${accuracyBadge(holding.prediction.model_accuracy)}
            </div>
          </div>
        `).join("")}
      </div>
      <p class="disclaimer" style="margin-top:1rem;">${result.disclaimer}</p>
    `;
  } catch (e) {
    container.innerHTML = `<p style='color:var(--danger)'>Error: ${e}</p>`;
  }
};

// ── Sync ─────────────────────────────────────────────────────────────────────
window.triggerSync = async () => {
  const status = document.getElementById("sync-status")!;
  status.textContent = "Starting refresh...";
  try {
    await api.triggerSync();
    status.textContent = "Refresh running in background...";
    const poll = setInterval(async () => {
      const s = await api.syncStatus();
      status.textContent = s.running ? s.message : `Last synced: ${s.last_completed ?? "never"}`;
      if (!s.running) clearInterval(poll);
    }, 2000);
  } catch (e) {
    status.textContent = `Sync failed: ${e}`;
  }
};

async function updateSyncStatus() {
  try {
    const s = await api.syncStatus();
    const el = document.getElementById("sync-status")!;
    el.textContent = s.last_completed ? `Last synced: ${new Date(s.last_completed).toLocaleString()}` : "Never synced — click Refresh Data";
  } catch { /* offline */ }
}

// ── Init ─────────────────────────────────────────────────────────────────────
updateSyncStatus();
loadTopPredictions();
