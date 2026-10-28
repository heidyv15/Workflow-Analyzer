import { CATEGORY_ORDER, categoryStyle, toNodeCategory } from '../../lib/categories'
import type { Analysis } from '../../types'
import { Panel } from './Panel'

export function AiFitCard({ analysis }: { analysis: Analysis }) {
  const steps = analysis.step_analysis
  const counts = CATEGORY_ORDER.map((c) => ({
    category: c,
    count: steps.filter((s) => toNodeCategory(s.classification) === c).length,
  })).filter((c) => c.count > 0)
  const human = steps.filter((s) => s.classification === 'human_review').map((s) => s.label)

  return (
    <Panel id="ai-fit" title="Where AI fits" description="AI is recommended only where a step involves language or ambiguity.">
      <div className="flex h-2 gap-0.5 overflow-hidden rounded-full" role="img"
        aria-label={counts.map((c) => `${c.count} ${categoryStyle(c.category).short}`).join(', ')}>
        {counts.map((c) => (
          <div key={c.category} className={categoryStyle(c.category).bar} style={{ flexGrow: c.count }} />
        ))}
      </div>
      <ul className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-2 tnum">
        {counts.map((c) => (
          <li key={c.category} className="flex items-center gap-1.5">
            <span className={`size-1.5 rounded-full ${categoryStyle(c.category).dot}`} aria-hidden />
            {c.count} {categoryStyle(c.category).short.replace(/^[A-Z](?=[a-z])/, (m) => m.toLowerCase())}
          </li>
        ))}
      </ul>

      <div className="mt-6 flex flex-col gap-5 text-[13px]">
        <Group title="AI is used for" empty="Nothing. Every step is better handled by rules or by people." items={analysis.ai_used_for} />
        <Group
          title="No AI needed"
          note={analysis.ai_not_needed.length ? 'Rule-based automation is cheaper, faster, and more predictable here.' : undefined}
          empty="No step is fully rule-based."
          items={analysis.ai_not_needed}
        />
        {human.length > 0 && <Group title="Stays with a person" items={human} />}
      </div>
    </Panel>
  )
}

function Group({ title, items, empty, note }: { title: string; items: string[]; empty?: string; note?: string }) {
  return (
    <div>
      <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-ink-3">{title}</h3>
      {items.length === 0 ? (
        <p className="mt-1.5 leading-relaxed text-ink-2">{empty}</p>
      ) : (
        <ul className="mt-1.5 flex flex-col gap-1">
          {items.map((label) => <li key={label} className="leading-snug">{label}</li>)}
        </ul>
      )}
      {note && <p className="mt-1.5 text-xs leading-relaxed text-ink-3">{note}</p>}
    </div>
  )
}
