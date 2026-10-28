import type { LucideIcon } from 'lucide-react'
import { Clock, Cog, FolderSync, Send } from 'lucide-react'
import { categoryStyle } from '../../lib/categories'
import type { Analysis, NodeCategory } from '../../types'
import { Panel } from './Panel'

type Kind = Analysis['architecture'][number]['kind']

// Infrastructure stages are deterministic, so they share the "automated" color.
const KIND: Record<Kind, { category: NodeCategory; Icon?: LucideIcon }> = {
  trigger: { category: 'automated', Icon: Clock },
  integration: { category: 'automated', Icon: FolderSync },
  processing: { category: 'automated', Icon: Cog },
  ai: { category: 'ai_assisted' },
  human: { category: 'human_review' },
  delivery: { category: 'automated', Icon: Send },
}

const COMPLEXITY = { low: 'Low complexity', moderate: 'Moderate complexity', high: 'High complexity' }

export function ArchitecturePanel({ analysis }: { analysis: Analysis }) {
  const { architecture, complexity } = analysis
  return (
    <Panel
      id="architecture"
      title="Suggested implementation"
      description="Tools are matched to the systems you mentioned. An AI stage appears only when a step needs one."
      className="lg:col-span-2"
      aside={<span className="rounded-md bg-sidebar px-2 py-1 text-xs text-ink-2">{COMPLEXITY[complexity.level]}</span>}
    >
      <ol className="relative flex flex-col">
        {architecture.map((node, i) => {
          const k = KIND[node.kind]
          const s = categoryStyle(k.category)
          const Icon = k.Icon ?? s.Icon
          const last = i === architecture.length - 1
          return (
            <li key={`${node.stage}-${i}`} className="relative grid grid-cols-[2rem_minmax(0,1fr)] gap-x-4 pb-5 last:pb-0">
              {!last && <span className="absolute bottom-0 left-4 top-8 w-px -translate-x-1/2 bg-line-strong" aria-hidden />}
              <span className={`relative grid size-8 place-items-center rounded-lg ${s.badge}`}>
                <Icon className="size-4" strokeWidth={2} aria-hidden />
              </span>
              <div className="min-w-0 pt-0.5">
                <div className="flex flex-wrap items-baseline gap-x-2.5 gap-y-0.5">
                  <span className="text-[11px] font-semibold uppercase tracking-[0.06em] text-ink-3">{node.stage}</span>
                  <span className="text-[13.5px] font-medium">{node.tool}</span>
                </div>
                <p className="mt-0.5 text-[13px] leading-relaxed text-ink-3">{node.why}</p>
              </div>
            </li>
          )
        })}
      </ol>

      <div className="mt-6 border-t border-line pt-4">
        <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-ink-3">What drives the effort</h3>
        <ul className="mt-2 flex flex-col gap-1 text-[13px] text-ink-2">
          {complexity.drivers.map((d) => <li key={d}>{d}</li>)}
        </ul>
      </div>
    </Panel>
  )
}
