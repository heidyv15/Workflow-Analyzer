import { ArrowRight } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, ApiError } from '../api'
import type { Band, Methodology } from '../types'
import { CategoryBadge } from './CategoryBadge'
import { Notice } from './Notice'

const BAND_LABEL: Record<Band, string> = {
  high: 'High potential',
  moderate: 'Moderate potential',
  limited: 'Limited potential',
  keep_human_led: 'Keep human-led',
}
const TIME_LABEL: Record<string, string> = {
  traditional_automation: 'Rule-based automation',
  ai_assisted: 'AI-assisted, spot-checked',
  ai_assisted_reviewed: 'AI-assisted, reviewed by a person',
  human_review: 'Human decision',
  manual: 'Unclear step',
}

export function MethodologyView() {
  const [data, setData] = useState<Methodology | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.methodology().then(setData).catch((e) => setError(e instanceof ApiError ? e.message : 'Could not load the methodology.'))
  }, [])

  return (
    <article className="mx-auto w-full max-w-3xl px-5 pb-20 pt-10 sm:px-8 lg:pt-16">
      <header className="animate-rise">
        <h1 className="text-[26px] font-semibold leading-tight tracking-[-0.02em] sm:text-[30px]">How the analysis works</h1>
        <p className="mt-3 max-w-[64ch] text-[15px] leading-relaxed text-ink-2">
          Good AI implementation starts with understanding the process, not choosing the technology. This tool reads a
          workflow description, then decides where rule-based automation, AI, and people each belong. The AI never
          picks the score.
        </p>
      </header>

      <Section title="Who decides what">
        <ol className="flex flex-col items-stretch gap-2 sm:flex-row sm:items-center">
          {[
            { label: 'Your description', who: 'You' },
            { label: 'Fact extraction', who: 'Claude', ai: true },
            { label: 'Schema validation', who: 'Code' },
            { label: 'Rules & scoring', who: 'Code' },
            { label: 'Summary', who: 'Claude, checked by code', ai: true },
          ].map((s, i, all) => (
            <li key={s.label} className="flex items-center gap-2 sm:flex-1">
              <div className={`flex-1 rounded-lg px-3 py-2.5 ${s.ai ? 'bg-ai-soft' : 'bg-surface shadow-[inset_0_0_0_1px_var(--color-line)]'}`}>
                <div className="text-[13px] font-medium">{s.label}</div>
                <div className={`text-xs ${s.ai ? 'text-ai-ink' : 'text-ink-3'}`}>{s.who}</div>
              </div>
              {i < all.length - 1 && <ArrowRight className="hidden size-3.5 shrink-0 text-ink-3 sm:block" aria-hidden />}
            </li>
          ))}
        </ol>
        <div className="mt-6 grid gap-6 sm:grid-cols-2">
          <List title="Claude is used to" items={[
            'Read the plain-English description and split it into steps.',
            'Record facts about each step from fixed vocabularies: data type, output, stakes, sensitivity.',
            'Put the finished results into a short summary, which is rejected if it cites numbers the analysis doesn’t contain.',
          ]} />
          <List title="Deterministic code is used to" items={[
            'Validate every model response against a schema, with one repair attempt.',
            'Classify each step with an ordered rule table.',
            'Calculate the score, risk level, and time estimates.',
            'Insert triggers, validation checks, and human review gates.',
            'Match tools to the systems you mentioned.',
          ]} />
        </div>
      </Section>

      {error && <Notice tone="danger" className="mt-10">{error}</Notice>}
      {!data && !error && <div className="mt-12 space-y-3" aria-busy="true">{[0, 1, 2, 3].map((i) => <div key={i} className="skeleton h-10" />)}</div>}

      {data && (
        <>
          <Section
            title="Classification rules"
            intro="Rules are checked in order and the first match wins. The order is the philosophy: protect human judgment first, prefer deterministic automation next, and use AI only for language and ambiguity."
          >
            <ol className="divide-y divide-line overflow-hidden rounded-xl bg-surface shadow-[0_0_0_1px_var(--color-line)]">
              {data.rules.map((r) => (
                <li key={r.id} className="grid grid-cols-[3.5rem_minmax(0,1fr)] gap-x-3 gap-y-2 px-4 py-3 sm:grid-cols-[3.5rem_minmax(0,1fr)_8.5rem] sm:items-center">
                  <span className="text-xs font-medium text-ink-3 tnum">Rule {r.id.slice(1)}</span>
                  <span className="text-[13.5px] leading-snug">{r.description}</span>
                  <span className="col-start-2 sm:col-start-auto sm:justify-self-end"><CategoryBadge category={r.outcome} /></span>
                </li>
              ))}
            </ol>
          </Section>

          <Section
            title="Automation potential score"
            intro={`Seven factors, each scored 0 to 1 and multiplied by its weight, minus penalties for risk and complexity. AI-assisted steps count at ${Math.round(data.ai_step_credit * 100)}% of a rule-based step, so the score never rewards using AI for its own sake. Missing information is scored neutrally and labeled as assumed.`}
          >
            <table className="w-full border-collapse text-left text-[13px]">
              <thead>
                <tr className="border-b border-line text-[11px] uppercase tracking-[0.06em] text-ink-3">
                  <th scope="col" className="py-2 pr-4 font-semibold">Factor</th>
                  <th scope="col" className="w-28 py-2 text-right font-semibold">Weight</th>
                </tr>
              </thead>
              <tbody>
                {data.factors.map((f) => (
                  <tr key={f.key} className="border-b border-line align-top">
                    <td className="py-3 pr-4">
                      <div className="font-medium">{f.label}</div>
                      <div className="mt-0.5 leading-relaxed text-ink-3">{f.measures}</div>
                    </td>
                    <td className="py-3">
                      <div className="flex items-center justify-end gap-2">
                        <div className="h-1.5 w-14 overflow-hidden rounded-full bg-sidebar" aria-hidden>
                          <div className="h-full rounded-full bg-ink-2" style={{ width: `${(f.weight / 25) * 100}%` }} />
                        </div>
                        <span className="w-6 text-right tnum">{f.weight}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="mt-6 grid gap-6 sm:grid-cols-2">
              <List title="Penalties" items={[
                ...Object.entries(data.penalties.risk).map(([level, pts]) => `${cap(level)} risk: ${pts} points`),
                ...Object.entries(data.penalties.complexity).map(([level, pts]) => `${cap(level)} complexity: ${pts} points`),
              ]} />
              <List title="Bands" items={data.bands.map((b, i) => {
                const next = data.bands[i - 1]
                return `${BAND_LABEL[b.band]}: ${b.min_score}${next ? `–${next.min_score - 1}` : '+'}`
              })} />
            </div>
          </Section>

          <Section
            title="Time estimates"
            intro="Estimates are ranges built from step durations and frequency. Durations you state are used as given; others are estimated and labeled. Yearly figures are omitted until the frequency is known, and every assumption can be edited on the results page."
          >
            <List title="Share of a step's time removed" items={Object.entries(data.time_removed).map(
              ([k, r]) => `${TIME_LABEL[k] ?? k}: ${Math.round(r.low * 100)}–${Math.round(r.high * 100)}%`,
            )} />
          </Section>

          <Section title="Limitations">
            <List items={[
              'The analysis is only as good as the description. It is a starting point for a conversation with the people who do the work, not a replacement for it.',
              'Time savings are directional. They exclude build and maintenance effort.',
              'Tool suggestions are a lightweight starting architecture, not a vendor recommendation.',
            ]} />
          </Section>
        </>
      )}
    </article>
  )
}

function Section({ title, intro, children }: { title: string; intro?: string; children: React.ReactNode }) {
  return (
    <section className="animate-rise mt-12">
      <h2 className="text-lg font-semibold tracking-[-0.01em]">{title}</h2>
      {intro && <p className="mt-2 max-w-[68ch] text-[14px] leading-relaxed text-ink-2">{intro}</p>}
      <div className="mt-5">{children}</div>
    </section>
  )
}

function List({ title, items }: { title?: string; items: string[] }) {
  return (
    <div>
      {title && <h3 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-ink-3">{title}</h3>}
      <ul className={`flex list-disc flex-col gap-1.5 pl-4 text-[13.5px] leading-relaxed text-ink-2 marker:text-line-strong ${title ? 'mt-2' : ''}`}>
        {items.map((i) => <li key={i}>{i}</li>)}
      </ul>
    </div>
  )
}

function cap(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1)
}
