// Recent analyses, kept in this browser only. Storage can be unavailable
// (private mode, blocked site data), so every access is guarded.

import type { AnalyzeResponse, Band } from '../types'

const KEY = 'workflow-analyzer.history.v1'
const LIMIT = 8

export interface HistoryEntry {
  id: string
  title: string
  score: number
  band: Band
  savedAt: number
  response: AnalyzeResponse
}

export function loadHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? (JSON.parse(raw) as HistoryEntry[]) : []
  } catch {
    return []
  }
}

export function saveToHistory(response: AnalyzeResponse): HistoryEntry | null {
  const analysis = response.analysis
  if (!analysis) return null
  const entry: HistoryEntry = {
    id: crypto.randomUUID(),
    title: analysis.process_name,
    score: analysis.score.score,
    band: analysis.score.band,
    savedAt: Date.now(),
    response,
  }
  try {
    localStorage.setItem(KEY, JSON.stringify([entry, ...loadHistory()].slice(0, LIMIT)))
  } catch {
    // Not persisted; the analysis still shows for this session.
  }
  return entry
}

export function relativeTime(ts: number, now = Date.now()): string {
  const minutes = Math.round((now - ts) / 60000)
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  return days === 1 ? 'Yesterday' : `${days}d ago`
}
