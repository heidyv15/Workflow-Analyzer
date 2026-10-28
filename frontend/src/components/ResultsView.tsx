import { ArrowLeft } from 'lucide-react'
import { useCallback, useState } from 'react'
import type { Analysis, AnalyzeResponse } from '../types'
import { AiFitCard } from './results/AiFitCard'
import { ArchitecturePanel } from './results/ArchitecturePanel'
import { AssumptionsPanel } from './results/AssumptionsPanel'
import { ImpactCard } from './results/ImpactCard'
import { RiskPanel } from './results/RiskPanel'
import { ScoreCard } from './results/ScoreCard'
import { StepTable } from './results/StepTable'
import { WorkflowComparison } from './results/WorkflowComparison'

export function ResultsView({ response, onBack }: { response: AnalyzeResponse; onBack: () => void }) {
  const original = response.analysis!
  // Editing assumptions replaces the analysis with a server recalculation.
  const [analysis, setAnalysis] = useState<Analysis>(original)
  // Hovering a step in the diagram or the table highlights it in both.
  const [activeStep, setActiveStep] = useState<string | null>(null)

  // Recalculation returns the template summary; keep a model-written one, which never cites time figures.
  const applyRecalculation = useCallback((next: Analysis) => {
    setAnalysis(original.meta.summary_source === 'model'
      ? { ...next, summary: original.summary, meta: { ...next.meta, summary_source: 'model' } }
      : next)
  }, [original])

  return (
    <div className="mx-auto w-full max-w-6xl px-5 pb-20 pt-8 sm:px-8 lg:pt-10">
      <button type="button" onClick={onBack} className="-ml-2 inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-sm text-ink-3 transition-colors hover:bg-sidebar hover:text-ink">
        <ArrowLeft className="size-4" /> New analysis
      </button>

      <header className="animate-rise mt-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-[26px] font-semibold leading-tight tracking-[-0.02em] sm:text-[30px]">{analysis.process_name}</h1>
          <p className="mt-2 max-w-[72ch] text-[15px] leading-relaxed text-ink-2">{analysis.summary}</p>
        </div>
        <RunLabel run={response.run} />
      </header>

      <div className="mt-8 grid grid-cols-[minmax(0,1fr)] gap-4 lg:grid-cols-3">
        <ScoreCard score={analysis.score} />
        <AiFitCard analysis={analysis} />
        <WorkflowComparison analysis={analysis} activeStep={activeStep} onActiveStep={setActiveStep} />
        <ImpactCard analysis={analysis} original={original} extraction={response.extraction} onAnalysis={applyRecalculation} />
        <RiskPanel risk={analysis.risk} />
        <StepTable steps={analysis.step_analysis} activeStep={activeStep} onActiveStep={setActiveStep} />
        <ArchitecturePanel analysis={analysis} />
        <AssumptionsPanel analysis={analysis} run={response.run} />
      </div>
    </div>
  )
}

function RunLabel({ run }: { run: AnalyzeResponse['run'] }) {
  if (run.source === 'example') {
    return <span className="shrink-0 self-start rounded-md bg-sidebar px-2 py-1 text-xs text-ink-2 sm:self-auto">Built-in example</span>
  }
  const secs = run.latency_ms != null ? (run.latency_ms / 1000).toFixed(1) : null
  return (
    <span className="shrink-0 text-xs text-ink-3 tnum">
      Steps extracted by {run.model}{secs && ` in ${secs}s`}
      {run.attempts != null && run.attempts > 1 && ' (after one repair)'}
    </span>
  )
}
