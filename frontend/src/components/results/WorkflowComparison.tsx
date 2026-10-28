import { ArrowDown, ArrowRight } from 'lucide-react'
import type { CSSProperties } from 'react'
import { CATEGORY_ORDER, categoryStyle } from '../../lib/categories'
import type { Analysis, StepAssessment, WorkflowNode } from '../../types'
import { Panel } from './Panel'

interface Column {
  future: WorkflowNode
  current: WorkflowNode | null
  step: StepAssessment | null
  number: number | null
}

interface Props {
  analysis: Analysis
  activeStep: string | null
  onActiveStep: (id: string | null) => void
}

export function WorkflowComparison({ analysis, activeStep, onActiveStep }: Props) {
  const currentBySource = new Map(analysis.current_workflow.map((n) => [n.source_step_id, n]))
  const stepById = new Map(analysis.step_analysis.map((s) => [s.step_id, s]))
  const numberById = new Map(analysis.current_workflow.map((n, i) => [n.source_step_id, i + 1]))

  const columns: Column[] = analysis.future_workflow.map((f) => ({
    future: f,
    current: f.source_step_id ? currentBySource.get(f.source_step_id) ?? null : null,
    step: f.source_step_id ? stepById.get(f.source_step_id) ?? null : null,
    number: f.source_step_id ? numberById.get(f.source_step_id) ?? null : null,
  }))
  const real = columns.map((c, i) => (c.current ? i : -1)).filter((i) => i >= 0)
  const firstReal = real[0] ?? 0
  const lastReal = real[real.length - 1] ?? 0
  const inserted = analysis.future_workflow.filter((n) => n.inserted && n.note)
  const present = CATEGORY_ORDER.filter((c) => analysis.future_workflow.some((n) => n.category === c))

  const hover = (c: Column) => ({
    onMouseEnter: () => c.future.source_step_id && onActiveStep(c.future.source_step_id),
    onMouseLeave: () => onActiveStep(null),
  })
  const dim = (c: Column) =>
    activeStep && c.future.source_step_id !== activeStep ? 'opacity-40' : 'opacity-100'

  return (
    <Panel
      id="workflow"
      title="Current vs. recommended workflow"
      description={`Each manual step mapped to what it becomes.${inserted.length ? ' Dashed steps were added by the analyzer.' : ''}`}
      aside={<Legend categories={present} hasInserted={inserted.length > 0} />}
      className="lg:col-span-3"
    >
      {/* Wide screens: two aligned lanes. */}
      <div className="-mx-1 hidden overflow-x-auto px-1 pb-2 md:block">
        <div
          className="grid min-w-fit gap-x-4"
          style={{ gridTemplateColumns: `1rem repeat(${columns.length}, minmax(6.25rem, 13rem))` } as CSSProperties}
        >
          <LaneLabel>Today</LaneLabel>
          {columns.map((c, i) => (
            <div key={`cur-${c.future.id}`} className={`relative transition-opacity duration-200 ${dim(c)}`} {...hover(c)}>
              {c.current ? (
                <CurrentNode node={c.current} step={c.step} number={c.number} active={activeStep === c.future.source_step_id} />
              ) : (
                i > firstReal && i < lastReal && <div className="absolute inset-x-0 top-1/2 border-t border-dashed border-line-strong" aria-hidden />
              )}
              {i < columns.length - 1 && i >= firstReal && i < lastReal && (
                <Connector arrow={Boolean(columns[i + 1].current)} />
              )}
            </div>
          ))}

          <div />
          {columns.map((c) => (
            <div key={`link-${c.future.id}`} className={`flex h-10 justify-center transition-opacity duration-200 ${dim(c)}`} aria-hidden>
              {c.current && (
                <div className="flex flex-col items-center">
                  <div className="w-px flex-1 bg-line-strong" />
                  <ArrowDown className="-mt-1 size-3.5 text-ink-3" strokeWidth={2} />
                </div>
              )}
            </div>
          ))}

          <LaneLabel>Recommended</LaneLabel>
          {columns.map((c, i) => (
            <div
              key={`fut-${c.future.id}`}
              className={`relative animate-rise transition-opacity duration-200 ${dim(c)}`}
              style={{ animationDelay: `${120 + i * 45}ms` }}
              {...hover(c)}
            >
              <FutureNode node={c.future} active={activeStep !== null && activeStep === c.future.source_step_id} />
              {i < columns.length - 1 && <Connector arrow />}
            </div>
          ))}
        </div>
      </div>

      {/* Narrow screens: one row per step, today on the left. */}
      <div className="md:hidden">
        <div className="mb-2 grid grid-cols-[minmax(0,1fr)_1rem_minmax(0,1.15fr)] gap-x-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-ink-3">
          <span>Today</span><span /><span>Recommended</span>
        </div>
        <ol className="flex flex-col gap-2">
          {columns.map((c) => (
            <li key={c.future.id} className="grid grid-cols-[minmax(0,1fr)_1rem_minmax(0,1.15fr)] items-center gap-x-2">
              {c.current ? (
                <CurrentNode node={c.current} step={c.step} number={c.number} active={false} />
              ) : (
                <span className="text-xs text-ink-3">New step</span>
              )}
              <ArrowRight className="size-3.5 text-ink-3" aria-hidden />
              <FutureNode node={c.future} active={false} />
            </li>
          ))}
        </ol>
      </div>

      {inserted.length > 0 && (
        <dl className="mt-6 grid gap-x-8 gap-y-3 border-t border-line pt-5 sm:grid-cols-2 lg:grid-cols-3">
          {inserted.map((n) => (
            <div key={n.id} className="text-[13px] leading-relaxed">
              <dt className="font-medium">{n.label}</dt>
              <dd className="text-ink-3">{n.note}</dd>
            </div>
          ))}
        </dl>
      )}
    </Panel>
  )
}

function LaneLabel({ children }: { children: string }) {
  return (
    <div className="flex items-center justify-center">
      <span className="rotate-180 text-[10.5px] font-semibold uppercase tracking-[0.08em] text-ink-3 [writing-mode:vertical-rl]">
        {children}
      </span>
    </div>
  )
}

function Connector({ arrow }: { arrow: boolean }) {
  return (
    <svg className="absolute -right-4 top-1/2 h-2.5 w-4 -translate-y-1/2 text-line-strong" viewBox="0 0 16 10" fill="none" aria-hidden>
      <line x1="1" y1="5" x2={arrow ? 13 : 16} y2="5" stroke="currentColor" strokeWidth="1.25" />
      {arrow && <path d="M10.5 1.5 L14 5 L10.5 8.5" stroke="var(--color-ink-3)" strokeWidth="1.25" strokeLinecap="round" strokeLinejoin="round" />}
    </svg>
  )
}

function CurrentNode({ node, step, number, active }: { node: WorkflowNode; step: StepAssessment | null; number: number | null; active: boolean }) {
  return (
    <div className={`flex h-full flex-col gap-1.5 rounded-lg bg-canvas px-3 py-2.5 shadow-[inset_0_0_0_1px_var(--color-line)] transition-shadow duration-200 ${active ? 'shadow-[inset_0_0_0_1.5px_var(--color-line-strong)]' : ''}`}>
      <div className="flex items-center justify-between gap-2 text-[11px] text-ink-3 tnum">
        <span>Step {number}</span>
        {step?.minutes != null && (
          <span title={step.minutes_source === 'stated' ? 'From your description' : 'Estimated'}>
            {step.minutes_source === 'stated' ? '' : '~'}{Math.round(step.minutes)} min
          </span>
        )}
      </div>
      <p className="line-clamp-3 text-[12.5px] font-medium leading-snug text-ink-2">{node.label}</p>
    </div>
  )
}

function FutureNode({ node, active }: { node: WorkflowNode; active: boolean }) {
  const s = categoryStyle(node.category)
  const surface = node.inserted
    ? `${s.badge} outline-[1.5px] outline-dashed -outline-offset-[1.5px] ${s.dashed}`
    : s.node
  return (
    <div
      title={node.note ?? undefined}
      className={`flex h-full min-h-24 flex-col gap-2 rounded-lg px-3 py-2.5 transition-transform duration-200 ${surface} ${active ? '-translate-y-0.5' : ''}`}
    >
      <div className={`flex min-w-0 items-center gap-1.5 text-[11px] font-medium ${s.ink}`}>
        <s.Icon className="size-3.5 shrink-0" strokeWidth={2} aria-hidden />
        <span className="truncate">{s.nodeLabel}</span>
        {node.inserted && <span className="sr-only">(added step)</span>}
      </div>
      <p className="line-clamp-3 text-[12.5px] font-medium leading-snug text-ink">{node.label}</p>
    </div>
  )
}

function Legend({ categories, hasInserted }: { categories: WorkflowNode['category'][]; hasInserted: boolean }) {
  return (
    <ul className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-ink-2">
      {categories.map((c) => {
        const s = categoryStyle(c)
        return (
          <li key={c} className="flex items-center gap-1.5">
            <span className={`size-2 rounded-full ${s.dot}`} aria-hidden />
            {s.short}
          </li>
        )
      })}
      {hasInserted && (
        <li className="flex items-center gap-1.5">
          <span className="size-2.5 rounded-[3px] outline-[1.5px] outline-dashed outline-ink-3" aria-hidden />
          Added step
        </li>
      )}
    </ul>
  )
}
