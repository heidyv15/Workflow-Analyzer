import type { Analysis, Level3 } from '../../types'
import { Panel } from './Panel'

const LEVEL: Record<Level3, { label: string; filled: number; text: string; summary: string }> = {
  low: { label: 'Low risk', filled: 1, text: 'text-ink', summary: 'Mistakes are easy to catch and cheap to fix.' },
  moderate: { label: 'Moderate risk', filled: 2, text: 'text-ink', summary: 'Safe to automate with the review gates shown.' },
  high: { label: 'High risk', filled: 3, text: 'text-danger', summary: 'Decisions here affect people directly. Keep a person accountable.' },
}
const SEVERITY: Record<Level3, string> = {
  low: 'text-ink-3',
  moderate: 'text-ink-2',
  high: 'text-danger',
}

export function RiskPanel({ risk }: { risk: Analysis['risk'] }) {
  const level = LEVEL[risk.level]
  return (
    <Panel id="risk" title="Risk & human oversight" description="Where a mistake would matter, and how the design guards against it.">
      <div className="flex items-center gap-3">
        <div className="flex gap-1" role="img" aria-label={level.label}>
          {[1, 2, 3].map((i) => (
            <span key={i} className={`h-2 w-7 rounded-full ${i <= level.filled ? (risk.level === 'high' ? 'bg-danger' : 'bg-ink-2') : 'bg-line'}`} />
          ))}
        </div>
        <span className={`text-sm font-semibold ${level.text}`}>{level.label}</span>
      </div>
      <p className="mt-1.5 text-[13px] text-ink-2">{level.summary}</p>

      <ul className="mt-5 flex flex-col gap-4">
        {risk.factors.map((f) => (
          <li key={f.key} className="text-[13px] leading-relaxed">
            <div className="flex items-baseline justify-between gap-3">
              <span className="font-medium">{f.label}</span>
              <span className={`shrink-0 text-xs capitalize ${SEVERITY[f.severity]}`}>{f.severity}</span>
            </div>
            <p className="text-ink-3">{f.why}</p>
          </li>
        ))}
      </ul>
    </Panel>
  )
}
