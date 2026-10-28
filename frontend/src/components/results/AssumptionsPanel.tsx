import { ArrowUpRight } from 'lucide-react'
import type { Analysis, RunInfo } from '../../types'
import { Panel } from './Panel'

// Missing facts that the Impact card's assumption controls can supply directly.
const EDITABLE = new Set(['frequency', 'duration', 'volume'])

export function AssumptionsPanel({ analysis, run }: { analysis: Analysis; run: RunInfo }) {
  const focusImpact = () => {
    document.getElementById('impact')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    window.setTimeout(() => document.getElementById('frequency')?.focus({ preventScroll: true }), 400)
  }

  return (
    <Panel id="assumptions" title="What this is based on" description="Everything not stated in your description is listed here.">
      {analysis.missing_information.length > 0 && (
        <section>
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-ink-3">Open questions</h3>
          <ul className="mt-2 flex flex-col gap-2.5 text-[13px] leading-relaxed">
            {analysis.missing_information.map((m) => (
              <li key={m.question}>
                {m.question}
                {EDITABLE.has(m.field) && (
                  <button type="button" onClick={focusImpact} className="ml-1.5 inline-flex items-center gap-0.5 text-xs font-medium text-brand-ink hover:underline hover:underline-offset-4">
                    Set it <ArrowUpRight className="size-3" />
                  </button>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className={analysis.missing_information.length ? 'mt-6' : ''}>
        <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-ink-3">Assumptions made</h3>
        {analysis.assumptions.length ? (
          <ul className="mt-2 flex flex-col gap-2.5 text-[13px] leading-relaxed text-ink-2">
            {analysis.assumptions.map((a) => <li key={a.detail}>{a.detail}</li>)}
          </ul>
        ) : (
          <p className="mt-2 text-[13px] text-ink-2">None. Every figure came from your description.</p>
        )}
      </section>

      <dl className="mt-6 grid grid-cols-[auto_minmax(0,1fr)] gap-x-3 gap-y-1 border-t border-line pt-4 text-xs text-ink-3">
        <dt>Source</dt>
        <dd className="text-ink-2">{run.source === 'example' ? 'Saved example extraction' : `Extracted by ${run.model}`}</dd>
        {run.prompt_version && (<><dt>Prompt</dt><dd className="text-ink-2">{run.prompt_version}</dd></>)}
        <dt>Summary</dt>
        <dd className="text-ink-2">{analysis.meta.summary_source === 'model' ? 'Written by the model from these results' : 'Generated from a template'}</dd>
        <dt>Scoring engine</dt>
        <dd className="text-ink-2">v{analysis.meta.engine_version}</dd>
      </dl>
    </Panel>
  )
}
