import { Menu, X } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { api, ApiError } from './api'
import { AnalyzingView } from './components/AnalyzingView'
import type { ComposeNotice } from './components/ComposeView'
import { ComposeView } from './components/ComposeView'
import { MethodologyView } from './components/MethodologyView'
import { ResultsView } from './components/ResultsView'
import type { Selection } from './components/Sidebar'
import { Sidebar } from './components/Sidebar'
import type { HistoryEntry } from './lib/history'
import { loadHistory, saveToHistory } from './lib/history'
import type { AnalyzeResponse, ExampleSummary } from './types'

type Screen =
  | { kind: 'compose' }
  | { kind: 'analyzing'; startedAt: number }
  | { kind: 'results'; response: AnalyzeResponse }
  | { kind: 'methodology' }

// Shareable links: #/examples/<id> and #/how-it-works. Live analyses stay private to the browser.
function hashFor(sel: Selection): string {
  if (sel?.kind === 'example') return `#/examples/${sel.id}`
  if (sel?.kind === 'methodology') return '#/how-it-works'
  return ''
}
const initialHash = window.location.hash
const linkedExample = initialHash.match(/^#\/examples\/([\w-]+)$/)?.[1]
const linkedMethodology = initialHash === '#/how-it-works'

export default function App() {
  const [screen, setScreen] = useState<Screen>(linkedMethodology ? { kind: 'methodology' } : { kind: 'compose' })
  const [selection, setSelection] = useState<Selection>(linkedMethodology ? { kind: 'methodology' } : { kind: 'new' })
  const [description, setDescription] = useState('')
  const [notice, setNotice] = useState<ComposeNotice>(null)
  const [examples, setExamples] = useState<ExampleSummary[]>([])
  const [history, setHistory] = useState<HistoryEntry[]>(loadHistory)
  const [navOpen, setNavOpen] = useState(false)
  const inflight = useRef<AbortController | null>(null)
  const mainRef = useRef<HTMLElement>(null)

  useEffect(() => {
    api.examples().then(setExamples).catch(() => setExamples([]))
  }, [])

  const show = useCallback((next: Screen, sel: Selection) => {
    setScreen(next)
    setSelection(sel)
    setNavOpen(false)
    window.history.replaceState(null, '', hashFor(sel) || window.location.pathname)
    mainRef.current?.scrollTo({ top: 0 })
  }, [])

  const startNew = () => {
    inflight.current?.abort()
    setNotice(null)
    show({ kind: 'compose' }, { kind: 'new' })
  }

  const analyze = async () => {
    const controller = new AbortController()
    inflight.current = controller
    setNotice(null)
    show({ kind: 'analyzing', startedAt: Date.now() }, { kind: 'new' })
    try {
      const response = await api.analyze(description, controller.signal)
      if (response.status === 'needs_detail') {
        setNotice({ kind: 'needs_detail', questions: response.questions })
        show({ kind: 'compose' }, { kind: 'new' })
        return
      }
      const entry = saveToHistory(response)
      setHistory(loadHistory())
      show({ kind: 'results', response }, entry ? { kind: 'history', id: entry.id } : null)
    } catch (e) {
      if (controller.signal.aborted) return
      const err = e instanceof ApiError ? e : new ApiError(0, 'unknown', 'Something went wrong. Please try again.')
      setNotice({ kind: 'error', message: err.message, canRetry: err.code !== 'not_configured' && err.code !== 'refused' })
      show({ kind: 'compose' }, { kind: 'new' })
    } finally {
      if (inflight.current === controller) inflight.current = null
    }
  }

  const openExample = async (id: string) => {
    try {
      const response = await api.exampleAnalysis(id)
      show({ kind: 'results', response }, { kind: 'example', id })
    } catch (e) {
      setNotice({ kind: 'error', message: e instanceof ApiError ? e.message : 'Could not load that example.', canRetry: false })
      show({ kind: 'compose' }, { kind: 'new' })
    }
  }

  useEffect(() => {
    if (linkedExample) void openExample(linkedExample)
    // Runs once, for the link the page was opened with.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const sidebar = (
    <Sidebar
      examples={examples}
      history={history}
      selection={selection}
      onNew={startNew}
      onOpenMethodology={() => show({ kind: 'methodology' }, { kind: 'methodology' })}
      onOpenExample={openExample}
      onOpenHistory={(h) => show({ kind: 'results', response: h.response }, { kind: 'history', id: h.id })}
    />
  )

  return (
    <div className="flex h-dvh overflow-hidden">
      <aside className="hidden w-64 shrink-0 border-r border-line bg-sidebar lg:block">{sidebar}</aside>

      {/* Small screens: the sidebar becomes a drawer. */}
      {navOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button type="button" aria-label="Close menu" className="absolute inset-0 bg-ink/20" onClick={() => setNavOpen(false)} />
          <aside className="animate-rise absolute inset-y-0 left-0 w-72 max-w-[85vw] overflow-y-auto border-r border-line bg-sidebar">
            <button type="button" aria-label="Close menu" onClick={() => setNavOpen(false)} className="absolute right-3 top-4 rounded-md p-1.5 text-ink-3 hover:bg-surface hover:text-ink">
              <X className="size-4" />
            </button>
            {sidebar}
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-line bg-sidebar px-4 py-3 lg:hidden">
          <button type="button" aria-label="Open menu" onClick={() => setNavOpen(true)} className="-ml-1 rounded-md p-1.5 text-ink-2 hover:bg-surface">
            <Menu className="size-5" />
          </button>
          <img src="/favicon.svg" alt="" className="size-6" />
          <span className="text-sm font-semibold">Workflow Analyzer</span>
        </header>

        <main ref={mainRef} className="flex-1 overflow-y-auto">
          {screen.kind === 'compose' && (
            <ComposeView
              description={description}
              onChange={setDescription}
              onSubmit={analyze}
              notice={notice}
              onDismissNotice={() => setNotice(null)}
              examples={examples}
              onUseExample={(ex) => { setDescription(ex.description); setNotice(null) }}
              onViewExample={openExample}
            />
          )}
          {screen.kind === 'analyzing' && (
            <AnalyzingView description={description} startedAt={screen.startedAt} onCancel={startNew} />
          )}
          {screen.kind === 'methodology' && <MethodologyView />}
          {screen.kind === 'results' && <ResultsView key={JSON.stringify(selection)} response={screen.response} onBack={startNew} />}
        </main>
      </div>
    </div>
  )
}
