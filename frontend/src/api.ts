import type { Analysis, AnalyzeResponse, ExampleSummary, Extraction, Methodology, Overrides } from './types'

export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(path, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    })
  } catch {
    throw new ApiError(0, 'network', "Can't reach the analyzer service. Check that the backend is running.")
  }
  if (res.ok) return res.json() as Promise<T>

  const body = await res.json().catch(() => null)
  const detail = body?.detail
  if (detail && typeof detail === 'object' && 'message' in detail) {
    throw new ApiError(res.status, detail.code, detail.message)
  }
  if (res.status === 422) {
    throw new ApiError(422, 'invalid_input', 'That description couldn’t be accepted. Check its length and try again.')
  }
  throw new ApiError(res.status, 'unknown', 'Something went wrong. Please try again.')
}

export const api = {
  examples: () => request<ExampleSummary[]>('/api/examples'),
  exampleAnalysis: (id: string) => request<AnalyzeResponse>(`/api/examples/${encodeURIComponent(id)}/analysis`),
  analyze: (description: string, signal?: AbortSignal) =>
    request<AnalyzeResponse>('/api/analyze', { method: 'POST', body: JSON.stringify({ description }), signal }),
  methodology: () => request<Methodology>('/api/methodology'),
  recompute: (extraction: Extraction, overrides: Overrides) =>
    request<Analysis>('/api/recompute', { method: 'POST', body: JSON.stringify({ extraction, overrides }) }),
}
