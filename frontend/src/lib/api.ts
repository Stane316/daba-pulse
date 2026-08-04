import type {
  AIExplainResponse,
  DataStatus,
  DecisionAction,
  ExecutiveSummary,
  SimulationResult,
  SituationRisque,
} from '../types'

const BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, '') || ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(body || `Erreur ${res.status}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  health: () => request<{ status: string; ai_available: boolean; data_loaded: boolean }>('/api/health'),
  dataStatus: () => request<DataStatus>('/api/data/status'),
  executive: () => request<ExecutiveSummary>('/api/executive'),
  situation: (id: string) => request<SituationRisque>(`/api/situations/${id}`),
  decision: (id: string) => request<DecisionAction>(`/api/decisions/${id}`),
  decisions: (limit = 5) => request<DecisionAction[]>(`/api/decisions?limit=${limit}`),
  simulate: (situationId: string, quantite?: number) =>
    request<SimulationResult>('/api/simulate', {
      method: 'POST',
      body: JSON.stringify({
        situation_id: situationId,
        quantite: quantite ?? null,
      }),
    }),
  explain: (situationId: string, question?: string) =>
    request<AIExplainResponse>('/api/ai/explain', {
      method: 'POST',
      body: JSON.stringify({
        situation_id: situationId,
        question: question || null,
        mode: question ? 'qa' : 'resume',
      }),
    }),
  hypotheses: () => request<Record<string, unknown>>('/api/hypotheses'),
}
