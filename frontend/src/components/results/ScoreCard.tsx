import { ChevronDown } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { Analysis, Band } from '../../types'
import { Panel } from './Panel'

const BAND: Record<Band, { label: string; verdict: string }> = {
  high: { label: 'High potential', verdict: 'Most of this process can run without manual effort.' },
  moderate: { label: 'Moderate potential', verdict: 'Parts of this process are worth automating; others need people.' },
  limited: { label: 'Limited potential', verdict: 'Only a few steps are worth automating.' },
  keep_human_led: { label: 'Keep human-led', verdict: 'The core of this process depends on human judgment. Support it; don’t automate it.' },
}

export function ScoreCard({ score }: { score: Analysis['score'] }) {
  const [showReasoning, setShowReasoning] = useState(false)
  const band = BAND[score.band]

  return (
    <Panel
      id="score"
      title="Automation potential"
      description="Calculated by a fixed scoring model from the facts in your description. The AI does not pick this number."
      className="lg:col-span-2"
    >
      <div className="grid gap-8 md:grid-cols-[auto_minmax(0,1fr)]">
        <div className="flex items-center gap-5 md:flex-col md:items-start md:gap-4">
          <ScoreRing value={score.score} />
          <div className="md:max-w-[15rem]">
            <div className="text-base font-semibold">{band.label}</div>
            <p className="mt-1 text-[13px] leading-relaxed text-ink-2">{band.verdict}</p>
          </div>
        </div>

        <div>
          <ul className="flex flex-col gap-3">
            {score.factors.map((f) => (
              <li key={f.key}>
                <div className="flex items-baseline justify-between gap-3 text-[13px]">
                  <span className="flex items-center gap-2 text-ink">
                    {f.label}
                    {f.assumed && (
                      <span className="rounded bg-sidebar px-1.5 py-px text-[11px] text-ink-3" title="Not stated in the description; scored at a neutral value.">
                        Assumed
                      </span>
                    )}
                  </span>
                  <span className="text-ink-3 tnum">
                    <span className="text-ink">{fmt(f.points)}</span> / {f.weight}
                  </span>
                </div>
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-sidebar" aria-hidden>
                  <div
                    className={`h-full rounded-full transition-[width] duration-700 ease-[var(--ease-out-expo)] ${f.assumed ? 'bg-line-strong' : 'bg-ink-2'}`}
                    style={{ width: `${(f.points / f.weight) * 100}%` }}
                  />
                </div>
                {showReasoning && <p className="animate-rise mt-1.5 text-xs leading-relaxed text-ink-3">{f.explanation}</p>}
              </li>
            ))}
            {score.penalties.map((p) => (
              <li key={p.key} className="flex items-baseline justify-between gap-3 border-t border-dashed border-line pt-3 text-[13px]">
                <div>
                  <span>{p.label}</span>
                  {showReasoning && <p className="animate-rise mt-1 text-xs leading-relaxed text-ink-3">{p.explanation}</p>}
                </div>
                <span className="shrink-0 text-danger tnum">−{fmt(Math.abs(p.points))}</span>
              </li>
            ))}
          </ul>
          <button
            type="button"
            onClick={() => setShowReasoning((v) => !v)}
            aria-expanded={showReasoning}
            className="mt-4 inline-flex items-center gap-1 rounded-md text-[13px] font-medium text-brand-ink hover:underline hover:underline-offset-4"
          >
            {showReasoning ? 'Hide reasoning' : 'Show how each factor was scored'}
            <ChevronDown className={`size-3.5 transition-transform duration-200 ${showReasoning ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>
    </Panel>
  )
}

function ScoreRing({ value }: { value: number }) {
  const r = 46
  const c = 2 * Math.PI * r
  const [shown, setShown] = useState(0)
  useEffect(() => {
    const id = requestAnimationFrame(() => setShown(value))
    return () => cancelAnimationFrame(id)
  }, [value])

  return (
    <div className="relative size-28 shrink-0" role="img" aria-label={`Score ${value} out of 100`}>
      <svg viewBox="0 0 112 112" className="size-full -rotate-90">
        <circle cx="56" cy="56" r={r} fill="none" stroke="var(--color-sidebar)" strokeWidth="9" />
        <circle
          cx="56" cy="56" r={r} fill="none" stroke="var(--color-brand)" strokeWidth="9" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - shown / 100)}
          style={{ transition: 'stroke-dashoffset 900ms var(--ease-out-expo)' }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center">
        <div className="text-center leading-none">
          <span className="text-[32px] font-semibold tracking-tight tnum">{value}</span>
          <span className="block pt-1 text-[11px] text-ink-3">of 100</span>
        </div>
      </div>
    </div>
  )
}

function fmt(n: number) {
  return Number.isInteger(n) ? String(n) : n.toFixed(1)
}
