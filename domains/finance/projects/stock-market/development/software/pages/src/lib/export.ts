import type { Parameter, ParamState } from './types';
import type { PredictionResult } from './prediction';

export interface ExportPayload {
  ticker: string;
  date: string;
  result: PredictionResult;
  states: Record<string, ParamState>;
  parameters: Parameter[];
}

function download(content: string | Uint8Array, filename: string, mime: string): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function exportJSON(p: ExportPayload): void {
  const out = {
    ticker: p.ticker,
    date: p.date,
    exportedAt: new Date().toISOString(),
    prediction: {
      direction: p.result.direction,
      probUp: p.result.probUp,
      probDown: p.result.probDown,
      confidence: p.result.confidence,
      paramsSet: p.result.paramsSet,
      totalParams: p.parameters.length,
    },
    parameters: p.parameters.map(param => ({
      name: param.name,
      label: param.label,
      domain: param.domain,
      domainLabel: param.domainLabel,
      unit: param.unit,
      direction: p.states[param.name]?.direction ?? 'neutral',
      weight: p.states[param.name]?.weight ?? 50,
      value: p.states[param.name]?.value ?? param.defaultValue,
    })),
  };
  download(JSON.stringify(out, null, 2), `${p.ticker}_prediction_${p.date}.json`, 'application/json');
}

export function exportCSV(p: ExportPayload): void {
  const escape = (v: unknown) => `"${String(v).replace(/"/g, '""')}"`;
  const rows: string[][] = [
    ['Interactive Stock Predictor — Prediction Export'],
    [`Ticker: ${p.ticker}`, `Date: ${p.date}`, `Exported: ${new Date().toISOString()}`],
    [],
    ['Direction', 'Prob(UP)', 'Prob(DOWN)', 'Confidence', 'Params Set', 'Total Params'],
    [
      p.result.direction.toUpperCase(),
      `${(p.result.probUp * 100).toFixed(1)}%`,
      `${(p.result.probDown * 100).toFixed(1)}%`,
      `${(p.result.confidence * 100).toFixed(1)}%`,
      String(p.result.paramsSet),
      String(p.parameters.length),
    ],
    [],
    ['Parameter', 'Domain', 'Label', 'Direction Set', 'Weight', 'Value', 'Unit', 'Layman Description', 'Technical Description'],
    ...p.parameters.map(param => {
      const s = p.states[param.name];
      return [
        param.name,
        param.domainLabel,
        param.label,
        s?.direction ?? 'neutral',
        String(s?.weight ?? 50),
        String(s?.value ?? param.defaultValue),
        param.unit,
        param.layman,
        param.technical,
      ];
    }),
  ];
  const csv = rows.map(r => r.map(escape).join(',')).join('\r\n');
  download(csv, `${p.ticker}_prediction_${p.date}.csv`, 'text/csv;charset=utf-8;');
}

export function exportPDF(p: ExportPayload): void {
  const changedParams = p.parameters.filter(param => {
    const s = p.states[param.name];
    return s && s.direction !== 'neutral';
  });

  const dirColor = p.result.direction === 'up' ? '#34d399' : p.result.direction === 'down' ? '#f87171' : '#64748b';
  const dirLabel = p.result.direction === 'up' ? '▲ UP' : p.result.direction === 'down' ? '▼ DOWN' : '— NEUTRAL';

  // Domain breakdown
  const domainMap: Record<string, { label: string; up: number; down: number; neutral: number }> = {};
  for (const param of p.parameters) {
    if (!domainMap[param.domain]) domainMap[param.domain] = { label: param.domainLabel, up: 0, down: 0, neutral: 0 };
    const dir = p.states[param.name]?.direction ?? 'neutral';
    domainMap[param.domain][dir]++;
  }

  const paramRows = changedParams.map(param => {
    const s = p.states[param.name];
    const dir = s?.direction ?? 'neutral';
    return `<tr>
      <td style="font-family:monospace;font-size:11px">${param.name}</td>
      <td>${param.domainLabel}</td>
      <td style="color:${dir === 'up' ? '#16a34a' : '#dc2626'};font-weight:bold">${dir === 'up' ? '▲ UP' : '▼ DOWN'}</td>
      <td style="text-align:center">${s?.weight ?? 50}</td>
    </tr>`;
  }).join('');

  const domainRows = Object.values(domainMap).map(d =>
    `<tr><td>${d.label}</td><td style="color:#16a34a;text-align:center">${d.up}</td><td style="color:#dc2626;text-align:center">${d.down}</td><td style="color:#64748b;text-align:center">${d.neutral}</td></tr>`
  ).join('');

  const html = `<!DOCTYPE html><html><head><title>${p.ticker} Prediction ${p.date}</title>
<style>
  body{font-family:Arial,sans-serif;font-size:12px;color:#111;margin:2rem}
  h1{font-size:18px;margin:0 0 4px}
  .sub{font-size:11px;color:#666;margin:0 0 16px}
  .hero{border:2px solid ${dirColor};border-radius:8px;padding:12px 20px;display:inline-flex;align-items:center;gap:32px;margin-bottom:20px}
  .dir{font-size:28px;font-weight:900;color:${dirColor}}
  .stats{display:flex;gap:24px}
  .stat{text-align:center}
  .sv{font-size:16px;font-weight:700}
  .sl{font-size:10px;color:#666;text-transform:uppercase}
  table{width:100%;border-collapse:collapse;margin-bottom:20px;font-size:11px}
  th{background:#f3f4f6;text-align:left;padding:5px 8px;border-bottom:2px solid #e5e7eb}
  td{padding:4px 8px;border-bottom:1px solid #f3f4f6}
  .section{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#64748b;margin:16px 0 6px}
  @media print{body{margin:.5rem}.no-print{display:none}}
</style></head>
<body>
<h1>${p.ticker} — Interactive Prediction</h1>
<div class="sub">Date: ${p.date} &nbsp;|&nbsp; Exported: ${new Date().toLocaleString()}</div>
<div class="hero">
  <div class="dir">${dirLabel}</div>
  <div class="stats">
    <div class="stat"><div class="sv">${(p.result.probUp*100).toFixed(1)}%</div><div class="sl">Prob(UP)</div></div>
    <div class="stat"><div class="sv">${(p.result.probDown*100).toFixed(1)}%</div><div class="sl">Prob(DOWN)</div></div>
    <div class="stat"><div class="sv" style="color:${dirColor}">${(p.result.confidence*100).toFixed(1)}%</div><div class="sl">Confidence</div></div>
    <div class="stat"><div class="sv">${p.result.paramsSet} / ${p.parameters.length}</div><div class="sl">Params Set</div></div>
  </div>
</div>
<div class="section">Domain Breakdown</div>
<table><thead><tr><th>Domain</th><th>▲ UP</th><th>▼ DOWN</th><th>— Neutral</th></tr></thead>
<tbody>${domainRows}</tbody></table>
${changedParams.length > 0 ? `<div class="section">Parameters You Set (${changedParams.length})</div>
<table><thead><tr><th>Parameter</th><th>Domain</th><th>Direction</th><th>Weight</th></tr></thead>
<tbody>${paramRows}</tbody></table>` : ''}
<button class="no-print" onclick="window.print()" style="margin-top:12px;padding:8px 20px;background:#4f8ef7;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px">🖨️ Print / Save as PDF</button>
</body></html>`;

  const win = window.open('', '_blank', 'width=900,height=700');
  if (!win) {
    alert('Pop-up blocked. Please allow pop-ups for this site to use PDF export.');
    return;
  }
  win.document.write(html);
  win.document.close();
}

export async function exportXLSX(p: ExportPayload): Promise<void> {
  const XLSX = await import('xlsx');

  const wb = XLSX.utils.book_new();

  // Summary sheet
  const summary = [
    ['Ticker', p.ticker],
    ['Date', p.date],
    ['Exported At', new Date().toISOString()],
    [],
    ['Direction', p.result.direction.toUpperCase()],
    ['Prob(UP)', `${(p.result.probUp * 100).toFixed(1)}%`],
    ['Prob(DOWN)', `${(p.result.probDown * 100).toFixed(1)}%`],
    ['Confidence', `${(p.result.confidence * 100).toFixed(1)}%`],
    ['Params Set', p.result.paramsSet],
    ['Total Params', p.parameters.length],
  ];
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(summary), 'Summary');

  // Parameters sheet
  const headers = ['Name', 'Domain', 'Label', 'Unit', 'Direction', 'Weight', 'Value', 'Layman', 'Technical'];
  const rows = p.parameters.map(param => {
    const s = p.states[param.name];
    return [
      param.name,
      param.domainLabel,
      param.label,
      param.unit,
      s?.direction ?? 'neutral',
      s?.weight ?? 50,
      s?.value ?? param.defaultValue,
      param.layman,
      param.technical,
    ];
  });
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet([headers, ...rows]), 'Parameters');

  // Changed-only sheet
  const changedHeaders = ['Name', 'Domain', 'Label', 'Direction', 'Weight', 'Value'];
  const changedRows = p.parameters
    .filter(param => (p.states[param.name]?.direction ?? 'neutral') !== 'neutral')
    .map(param => {
      const s = p.states[param.name];
      return [
        param.name,
        param.domainLabel,
        param.label,
        s?.direction ?? 'neutral',
        s?.weight ?? 50,
        s?.value ?? param.defaultValue,
      ];
    });
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet([changedHeaders, ...changedRows]), 'My Signals');

  XLSX.writeFile(wb, `${p.ticker}_prediction_${p.date}.xlsx`);
}
