import type { Direction, ParamState } from './types';

export interface PredictionResult {
  probUp: number;       // 0–1
  probDown: number;     // 0–1
  confidence: number;   // 0–1, distance from 50/50
  direction: 'up' | 'down' | 'neutral';
  paramsSet: number;
  weightedScore: number; // −1 to +1
}

const DIR_VALUE: Record<Direction, number> = { up: 1, down: -1, neutral: 0 };

export function computePrediction(states: Record<string, ParamState>): PredictionResult {
  let totalWeight = 0;
  let weightedScore = 0;
  let paramsSet = 0;

  for (const s of Object.values(states)) {
    if (s.direction === 'neutral') continue;
    const dv = DIR_VALUE[s.direction];
    weightedScore += s.weight * dv;
    totalWeight   += s.weight;
    paramsSet++;
  }

  if (totalWeight === 0) {
    return { probUp: 0.5, probDown: 0.5, confidence: 0, direction: 'neutral', paramsSet: 0, weightedScore: 0 };
  }

  const normalizedScore = weightedScore / totalWeight; // −1 to +1
  const probUp    = (normalizedScore + 1) / 2;
  const probDown  = 1 - probUp;
  const confidence = Math.abs(normalizedScore);
  const direction: 'up' | 'down' | 'neutral' = probUp > 0.52 ? 'up' : probUp < 0.48 ? 'down' : 'neutral';

  return { probUp, probDown, confidence, direction, paramsSet, weightedScore: normalizedScore };
}

export function formatPct(v: number): string {
  return (v * 100).toFixed(1) + '%';
}
