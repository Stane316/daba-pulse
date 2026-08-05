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
  const headers: HeadersInit = { ...(init?.headers || {}) }
  if (!(init?.body instanceof FormData)) {
    ;(headers as Record<string, string>)['Content-Type'] =
      (headers as Record<string, string>)['Content-Type'] || 'application/json'
  }
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(body || `Erreur ${res.status}`)
  }
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) {
    return res.json() as Promise<T>
  }
  return res.text() as unknown as T
}

export interface DataPreview {
  columns: string[]
  sample_rows: Record<string, unknown>[]
  nb_lignes: number
  nb_boutiques: number
  nb_produits: number
  periode_debut?: string
  periode_fin?: string
  source?: string
  type?: string
  avertissements?: string[]
}

export interface UploadResult {
  status: DataStatus
  preview: DataPreview
  message: string
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export const api = {
  health: () =>
    request<{ status: string; ai_available: boolean; data_loaded: boolean }>(
      '/api/health',
    ),
  dataStatus: () => request<DataStatus>('/api/data/status'),
  dataPreview: (n = 5) => request<DataPreview>(`/api/data/preview?n=${n}`),
  dataReload: () =>
    request<DataStatus>('/api/data/reload', { method: 'POST', body: '{}' }),
  uploadCsv: async (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return request<UploadResult>('/api/data/upload', {
      method: 'POST',
      body: fd,
    })
  },
  executive: () => request<ExecutiveSummary>('/api/executive'),
  situation: (id: string) => request<SituationRisque>(`/api/situations/${id}`),
  decision: (id: string) => request<DecisionAction>(`/api/decisions/${id}`),
  decisions: (limit = 5) =>
    request<DecisionAction[]>(`/api/decisions?limit=${limit}`),
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

  downloadExport: async (
    situationId: string,
    opts?: { quantite?: number; format?: 'json' | 'markdown' },
  ) => {
    const format = opts?.format ?? 'markdown'
    const q =
      opts?.quantite != null
        ? `&quantite=${encodeURIComponent(opts.quantite)}`
        : ''
    const res = await fetch(
      `${BASE}/api/export/decision/${encodeURIComponent(situationId)}?format=${format}${q}`,
    )
    if (!res.ok) {
      throw new Error(await res.text())
    }
    const blob = await res.blob()
    const ext = format === 'markdown' ? 'md' : 'json'
    downloadBlob(blob, `dabapulse-decision-${situationId}.${ext}`)
  },
}

