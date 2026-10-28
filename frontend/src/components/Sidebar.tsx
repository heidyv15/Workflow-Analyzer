import { BookOpen, Plus } from 'lucide-react'
import type { HistoryEntry } from '../lib/history'
import { relativeTime } from '../lib/history'
import type { ExampleSummary } from '../types'

export type Selection = { kind: 'new' } | { kind: 'methodology' } | { kind: 'example'; id: string } | { kind: 'history'; id: string } | null

interface Props {
  examples: ExampleSummary[]
  history: HistoryEntry[]
  selection: Selection
  onNew: () => void
  onOpenMethodology: () => void
  onOpenExample: (id: string) => void
  onOpenHistory: (entry: HistoryEntry) => void
}

export function Sidebar({ examples, history, selection, onNew, onOpenMethodology, onOpenExample, onOpenHistory }: Props) {
  return (
    <nav aria-label="Analyses" className="flex h-full flex-col gap-7 px-3 py-5">
      <div className="flex items-center gap-2.5 px-2">
        <img src="/favicon.svg" alt="" className="size-7" />
        <div className="leading-tight">
          <div className="text-[15px] font-semibold tracking-[-0.01em]">Workflow Analyzer</div>
          <div className="text-xs text-ink-3">Automation opportunity review</div>
        </div>
      </div>

      <button
        type="button"
        onClick={onNew}
        aria-current={selection?.kind === 'new' ? 'page' : undefined}
        className={`flex items-center gap-2 rounded-lg px-2.5 py-2 text-sm font-medium transition-colors duration-150 ${
          selection?.kind === 'new'
            ? 'bg-surface text-ink shadow-[0_0_0_1px_var(--color-line)]'
            : 'text-ink-2 hover:bg-surface/70 hover:text-ink'
        }`}
      >
        <Plus className="size-4" strokeWidth={2} />
        New analysis
      </button>

      <Section title="Examples">
        {examples.map((e) => (
          <NavItem
            key={e.id}
            active={selection?.kind === 'example' && selection.id === e.id}
            onClick={() => onOpenExample(e.id)}
            title={e.title}
            meta={e.tagline}
          />
        ))}
      </Section>

      <Section title="Recent">
        {history.length === 0 ? (
          <p className="px-2.5 text-xs leading-relaxed text-ink-3">Analyses you run are saved here, in this browser only.</p>
        ) : (
          history.map((h) => (
            <NavItem
              key={h.id}
              active={selection?.kind === 'history' && selection.id === h.id}
              onClick={() => onOpenHistory(h)}
              title={h.title}
              meta={relativeTime(h.savedAt)}
              trailing={
                <span className="rounded-md bg-surface px-1.5 py-0.5 text-xs font-medium text-ink-2 shadow-[0_0_0_1px_var(--color-line)] tnum">
                  {h.score}
                </span>
              }
            />
          ))
        )}
      </Section>

      <div className="mt-auto flex flex-col gap-3">
        <button
          type="button"
          onClick={onOpenMethodology}
          aria-current={selection?.kind === 'methodology' ? 'page' : undefined}
          className={`flex items-center gap-2 rounded-lg px-2.5 py-2 text-sm transition-colors duration-150 ${
            selection?.kind === 'methodology'
              ? 'bg-surface font-medium text-ink shadow-[0_0_0_1px_var(--color-line)]'
              : 'text-ink-2 hover:bg-surface/70 hover:text-ink'
          }`}
        >
          <BookOpen className="size-4" strokeWidth={2} />
          How it works
        </button>
        <p className="px-2.5 text-xs leading-relaxed text-ink-3">
          Estimates are directional and based only on what you describe.
        </p>
      </div>
    </nav>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      <h2 className="mb-1 px-2.5 text-[11px] font-semibold uppercase tracking-[0.06em] text-ink-3">{title}</h2>
      {children}
    </div>
  )
}

function NavItem(props: { title: string; meta: string; active: boolean; onClick: () => void; trailing?: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={props.onClick}
      aria-current={props.active ? 'page' : undefined}
      className={`group flex w-full items-start gap-2 rounded-lg px-2.5 py-2 text-left transition-colors duration-150 ${
        props.active ? 'bg-surface shadow-[0_0_0_1px_var(--color-line)]' : 'hover:bg-surface/70'
      }`}
    >
      <span className="min-w-0 flex-1">
        <span className={`block truncate text-sm ${props.active ? 'font-medium text-ink' : 'text-ink-2 group-hover:text-ink'}`}>
          {props.title}
        </span>
        <span className="block truncate text-xs text-ink-3">{props.meta}</span>
      </span>
      {props.trailing && <span className="pt-0.5">{props.trailing}</span>}
    </button>
  )
}
