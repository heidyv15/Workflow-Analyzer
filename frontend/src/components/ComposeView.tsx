import { ArrowRight, Check } from 'lucide-react'
import { useMemo, useRef } from 'react'
import { detailHints } from '../lib/detailCheck'
import type { ExampleSummary, MissingInfo } from '../types'
import { Notice } from './Notice'

export const MIN_CHARS = 20
export const MAX_CHARS = 4000

export type ComposeNotice =
  | { kind: 'error'; message: string; canRetry: boolean }
  | { kind: 'needs_detail'; questions: MissingInfo[] }
  | null

interface Props {
  description: string
  onChange: (value: string) => void
  onSubmit: () => void
  notice: ComposeNotice
  onDismissNotice: () => void
  examples: ExampleSummary[]
  onUseExample: (example: ExampleSummary) => void
  onViewExample: (id: string) => void
}

const PLACEHOLDER =
  'e.g. Every Friday I download three Excel reports, combine the numbers, compare them with last week, ' +
  'write a summary of anything unusual, and email it to my manager. It takes about 45 minutes.'

export function ComposeView(props: Props) {
  const { description, onChange, onSubmit, notice } = props
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const hints = useMemo(() => detailHints(description), [description])
  const length = description.trim().length
  const canSubmit = length >= MIN_CHARS && length <= MAX_CHARS

  const submit = () => {
    if (canSubmit) onSubmit()
    else textareaRef.current?.focus()
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-5 pb-16 pt-10 sm:px-8 lg:pt-16">
      <header className="animate-rise">
        <h1 className="text-[26px] font-semibold leading-tight tracking-[-0.02em] sm:text-[30px]">
          What process would you like to analyze?
        </h1>
        <p className="mt-3 max-w-[62ch] text-[15px] leading-relaxed text-ink-2">
          Describe a repetitive workflow in your organization. Include what triggers it, the steps involved,
          the tools you use, and roughly how long it takes.
        </p>
      </header>

      {notice?.kind === 'error' && (
        <Notice tone="danger" className="mt-6" onDismiss={props.onDismissNotice}
          action={notice.canRetry ? { label: 'Try again', onClick: submit } : undefined}>
          {notice.message}
        </Notice>
      )}
      {notice?.kind === 'needs_detail' && (
        <Notice tone="info" className="mt-6" onDismiss={props.onDismissNotice}
          title="A bit more detail is needed before this can be analyzed responsibly.">
          <ul className="mt-2 flex list-disc flex-col gap-1 pl-5">
            {notice.questions.map((q) => <li key={q.question}>{q.question}</li>)}
          </ul>
        </Notice>
      )}

      <form
        className="mt-7 overflow-hidden rounded-xl bg-surface shadow-[0_0_0_1px_var(--color-line),0_1px_2px_oklch(0.2_0.02_290/0.04)] transition-shadow duration-200 focus-within:shadow-[0_0_0_1px_var(--color-brand),0_0_0_4px_var(--color-brand-soft)]"
        onSubmit={(e) => { e.preventDefault(); submit() }}
      >
        <label htmlFor="description" className="sr-only">Process description</label>
        <textarea
          id="description"
          ref={textareaRef}
          value={description}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); submit() }
          }}
          placeholder={PLACEHOLDER}
          maxLength={MAX_CHARS}
          rows={7}
          className="block w-full resize-y bg-transparent px-5 py-4 text-[15px] leading-relaxed text-ink outline-none placeholder:text-ink-3 focus-visible:outline-none"
        />
        <div className="flex flex-col gap-3 border-t border-line px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <ul className="flex flex-wrap gap-x-4 gap-y-1.5" aria-label="Helpful details">
            {hints.map((h) => (
              <li key={h.key} className={`flex items-center gap-1.5 text-xs transition-colors duration-200 ${h.present ? 'text-ink' : 'text-ink-3'}`}>
                <span className={`grid size-3.5 place-items-center rounded-full transition-colors duration-200 ${h.present ? 'bg-ink text-surface' : 'shadow-[inset_0_0_0_1.5px_var(--color-line-strong)]'}`}>
                  {h.present && <Check className="size-2.5" strokeWidth={3.5} />}
                </span>
                {h.label}
                <span className="sr-only">{h.present ? '(included)' : '(not yet included)'}</span>
              </li>
            ))}
          </ul>
          <div className="flex items-center justify-between gap-3 sm:justify-end">
            <span className={`whitespace-nowrap text-xs tnum ${length > MAX_CHARS * 0.9 ? 'text-human-ink' : 'text-ink-3'}`}>
              {length.toLocaleString()} / {MAX_CHARS.toLocaleString()}
            </span>
            <button
              type="submit"
              aria-disabled={!canSubmit}
              title={canSubmit ? 'Analyze (⌘ Enter)' : `Describe the process in at least ${MIN_CHARS} characters`}
              className={`inline-flex shrink-0 items-center gap-2 whitespace-nowrap rounded-lg px-3.5 py-2 text-sm font-medium transition-colors duration-150 ${
                canSubmit ? 'bg-brand text-surface hover:bg-brand-hover active:translate-y-px' : 'cursor-not-allowed bg-line text-ink-3'
              }`}
            >
              Analyze workflow
              <ArrowRight className="size-4" strokeWidth={2} />
            </button>
          </div>
        </div>
      </form>

      {props.examples.length > 0 && (
        <section className="mt-12" aria-labelledby="examples-heading">
          <div className="flex items-baseline justify-between gap-4">
            <h2 id="examples-heading" className="text-sm font-semibold">Start from an example</h2>
            <p className="hidden text-xs text-ink-3 sm:block">Each one leads to a different recommendation.</p>
          </div>
          <ol className="mt-3 divide-y divide-line overflow-hidden rounded-xl bg-surface shadow-[0_0_0_1px_var(--color-line)]">
            {props.examples.map((ex, i) => (
              <li key={ex.id} className="flex flex-col gap-3 px-4 py-3.5 sm:flex-row sm:items-center sm:gap-4">
                <span className="hidden size-6 shrink-0 place-items-center rounded-md bg-sidebar text-xs font-medium text-ink-3 tnum sm:grid">
                  {i + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium">{ex.title}</div>
                  <div className="text-[13px] text-ink-3">{ex.tagline}</div>
                </div>
                <div className="flex shrink-0 items-center gap-1">
                  <button
                    type="button"
                    onClick={() => { props.onUseExample(ex); textareaRef.current?.focus() }}
                    className="rounded-md px-2.5 py-1.5 text-[13px] font-medium text-ink-2 transition-colors duration-150 hover:bg-sidebar hover:text-ink"
                  >
                    Use this text
                  </button>
                  <button
                    type="button"
                    onClick={() => props.onViewExample(ex.id)}
                    className="inline-flex items-center gap-1 rounded-md px-2.5 py-1.5 text-[13px] font-medium text-brand-ink transition-colors duration-150 hover:bg-brand-soft"
                  >
                    View result
                    <ArrowRight className="size-3.5" strokeWidth={2} />
                  </button>
                </div>
              </li>
            ))}
          </ol>
        </section>
      )}
    </div>
  )
}
