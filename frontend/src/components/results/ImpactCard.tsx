import { RotateCcw } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { api } from '../../api'
import type { Analysis, Extraction, Frequency, Overrides, Range } from '../../types'
import { Panel } from './Panel'

const FREQUENCIES: { value: Frequency; label: string; runs: number }[] = [
  { value: 'daily', label: 'Daily', runs: 250 },
  { value: 'weekly', label: 'Weekly', runs: 52 },
  { value: 'biweekly', label: 'Every two weeks', runs: 26 },
  { value: 'monthly', label: 'Monthly', runs: 12 },
  { value: 'quarterly', label: 'Quarterly', runs: 4 },
]
const CONFIDENCE = {
  high: { label: 'High confidence', dots: 3 },
  medium: { label: 'Medium confidence', dots: 2 },
  low: { label: 'Low confidence', dots: 1 },
} as const

interface Props {
  analysis: Analysis
  original: Analysis
  extraction: Extraction | null
  onAnalysis: (a: Analysis) => void
}

export function ImpactCard({ analysis, original, extraction, onAnalysis }: Props) {
  const impact = analysis.impact
  const [overrides, setOverridesState] = useState<Overrides>({})
  const [status, setStatus] = useState<'idle' | 'saving' | 'error'>('idle')
  const [resetKey, setResetKey] = useState(0)
  const seq = useRef(0)
  const edited = Object.keys(overrides).length > 0

  // Recalculate on the server whenever an assumption changes. No LLM call is involved.
  useEffect(() => {
    if (!extraction || !edited) return
    const id = ++seq.current
    const timer = setTimeout(() => {
      api.recompute(extraction, overrides)
        .then((a) => { if (id === seq.current) { onAnalysis(a); setStatus('idle') } })
        .catch(() => { if (id === seq.current) setStatus('error') })
    }, 350)
    return () => clearTimeout(timer)
  }, [overrides, extraction, edited, onAnalysis])

  const setOverrides = (update: (o: Overrides) => Overrides) => {
    setOverridesState(update)
    setStatus('saving')
  }

  const reset = () => {
    seq.current++
    setOverridesState({})
    setResetKey((k) => k + 1)
    setStatus('idle')
    onAnalysis(original)
  }

  const baseFreq = extraction && FREQUENCIES.some((f) => f.value === extraction.frequency) ? extraction.frequency : 'unset'
  const freqValue: string = overrides.runs_per_year != null ? 'custom' : overrides.frequency ?? baseFreq
  const conf = CONFIDENCE[impact.confidence]

  return (
    <Panel
      id="impact"
      title="Estimated impact"
      description="A directional estimate from what you described, not a measurement. Adjust the assumptions to match reality."
      className="lg:col-span-2"
      aside={
        <span className="flex items-center gap-2 text-xs text-ink-2" title={impact.basis.join(' ')}>
          <span className="flex gap-0.5" aria-hidden>
            {[1, 2, 3].map((i) => (
              <span key={i} className={`h-2.5 w-1 rounded-full ${i <= conf.dots ? 'bg-ink-2' : 'bg-line'}`} />
            ))}
          </span>
          {conf.label}
        </span>
      }
    >
      <dl className={`grid grid-cols-1 gap-x-6 gap-y-4 transition-opacity duration-200 sm:grid-cols-3 ${status === 'saving' ? 'opacity-60' : ''}`} aria-live="polite">
        <Figure label="Today, per run" value={impact.current_minutes_per_run != null ? `${impact.current_minutes_per_run}` : null} unit="min" />
        <Figure label="After, per run" value={fmtRange(impact.future_minutes_per_run)} unit="min" />
        <Figure
          label="Time saved per year"
          value={fmtRange(impact.saved_hours_per_year)}
          unit="hrs"
          emphasis
          missing={impact.runs_per_year == null ? 'Set how often it runs' : undefined}
        />
      </dl>

      {extraction ? (
        <div key={resetKey} className="mt-6 border-t border-line pt-5">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-[13px] font-semibold">Assumptions</h3>
            <span className="flex items-center gap-3 text-xs">
              {status === 'saving' && <span className="text-ink-3">Recalculating…</span>}
              {status === 'error' && <span className="text-danger">Couldn’t recalculate. Try again.</span>}
              {edited && (
                <button type="button" onClick={reset} className="inline-flex items-center gap-1 rounded-md px-1.5 py-1 font-medium text-ink-2 hover:bg-sidebar hover:text-ink">
                  <RotateCcw className="size-3" /> Reset
                </button>
              )}
            </span>
          </div>

          <div className="mt-3 grid grid-cols-[minmax(0,1fr)] gap-x-8 gap-y-4 md:grid-cols-[minmax(0,14rem)_minmax(0,1fr)]">
            <div className="flex flex-col gap-2">
              <label htmlFor="frequency" className="text-xs text-ink-3">How often it runs</label>
              <select
                id="frequency"
                value={freqValue}
                onChange={(e) => {
                  const v = e.target.value
                  setOverrides(({ step_minutes }) => (v === 'custom'
                    ? { step_minutes, runs_per_year: impact.runs_per_year ?? 52 }
                    : { step_minutes, frequency: v as Frequency }))
                }}
                className="h-9 rounded-lg bg-surface px-2.5 text-[13px] shadow-[0_0_0_1px_var(--color-line-strong)] outline-none focus-visible:shadow-[0_0_0_2px_var(--color-brand)]"
              >
                {freqValue === 'unset' && (
                  <option value="unset" disabled>{extraction.frequency === 'ad_hoc' ? 'Case by case' : 'Not stated'}</option>
                )}
                {FREQUENCIES.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
                <option value="custom">Custom…</option>
              </select>
              {overrides.runs_per_year != null && (
                <NumberField
                  label="Times per year"
                  value={overrides.runs_per_year}
                  min={1}
                  max={100000}
                  onChange={(n) => setOverrides((o) => ({ ...o, runs_per_year: n }))}
                />
              )}
            </div>

            <ul className="flex flex-col divide-y divide-line">
              {analysis.step_analysis.map((s) => (
                <li key={s.step_id} className="flex items-center gap-3 py-1.5 first:pt-0">
                  <span className="min-w-0 flex-1 truncate text-[13px] text-ink-2" title={s.label}>{s.label}</span>
                  {s.minutes_source !== 'stated' && <span className="text-[11px] text-ink-3" title="Estimated, not stated in the description">est.</span>}
                  <MinutesInput
                    label={`Minutes for ${s.label}`}
                    value={overrides.step_minutes?.[s.step_id] ?? s.minutes}
                    onChange={(n) => setOverrides((o) => ({ ...o, step_minutes: { ...o.step_minutes, [s.step_id]: n } }))}
                  />
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : (
        <p className="mt-5 text-xs text-ink-3">Assumptions can’t be edited for this saved analysis.</p>
      )}

      <ul className="mt-5 flex flex-col gap-1 text-xs leading-relaxed text-ink-3">
        {impact.basis.map((b) => <li key={b}>{b}</li>)}
      </ul>
    </Panel>
  )
}

function Figure({ label, value, unit, emphasis, missing }: { label: string; value: string | null; unit: string; emphasis?: boolean; missing?: string }) {
  return (
    <div className={emphasis ? 'sm:border-l sm:border-line sm:pl-6' : ''}>
      <dt className="text-xs text-ink-3">{label}</dt>
      <dd className="mt-1">
        {value ? (
          <span className={`font-semibold tracking-tight tnum ${emphasis ? 'text-[26px] text-brand-ink' : 'text-[22px]'}`}>
            {value}<span className="ml-1 text-[13px] font-normal text-ink-3">{unit}</span>
          </span>
        ) : (
          <span className="text-[13px] text-ink-3">{missing ?? 'Not enough detail'}</span>
        )}
      </dd>
    </div>
  )
}

function MinutesInput({ label, value, onChange }: { label: string; value: number | null; onChange: (n: number) => void }) {
  const [text, setText] = useState(value == null ? '' : String(Math.round(value * 10) / 10))
  return (
    <span className="flex items-center gap-1.5">
      <input
        type="number"
        inputMode="decimal"
        aria-label={label}
        min={0}
        max={480}
        value={text}
        onChange={(e) => {
          setText(e.target.value)
          const n = Number(e.target.value)
          if (e.target.value !== '' && Number.isFinite(n) && n >= 0 && n <= 480) onChange(n)
        }}
        className="h-8 w-16 rounded-md bg-surface px-2 text-right text-[13px] tnum shadow-[0_0_0_1px_var(--color-line-strong)] outline-none focus-visible:shadow-[0_0_0_2px_var(--color-brand)]"
      />
      <span className="text-xs text-ink-3">min</span>
    </span>
  )
}

function NumberField({ label, value, min, max, onChange }: { label: string; value: number; min: number; max: number; onChange: (n: number) => void }) {
  const [text, setText] = useState(String(value))
  return (
    <label className="flex items-center gap-2 text-xs text-ink-3">
      <input
        type="number"
        min={min}
        max={max}
        value={text}
        onChange={(e) => {
          setText(e.target.value)
          const n = Math.round(Number(e.target.value))
          if (e.target.value !== '' && n >= min && n <= max) onChange(n)
        }}
        className="h-8 w-24 rounded-md bg-surface px-2 text-right text-[13px] text-ink tnum shadow-[0_0_0_1px_var(--color-line-strong)] outline-none focus-visible:shadow-[0_0_0_2px_var(--color-brand)]"
      />
      {label}
    </label>
  )
}

function fmtRange(r: Range | null): string | null {
  if (!r) return null
  return r.low === r.high ? `${r.low}` : `${r.low}–${r.high}`
}
