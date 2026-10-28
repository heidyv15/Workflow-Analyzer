import { UserCheck } from 'lucide-react'
import type { StepAssessment } from '../../types'
import { CategoryBadge } from '../CategoryBadge'
import { Panel } from './Panel'

const RULES: Record<string, string> = {
  R1: 'Consequential decisions stay with a person',
  R2: 'Sensitive or consequential judgment stays human',
  R3: 'Fully specifiable steps use rules, not AI',
  R4: 'Low-stakes judgment: AI suggests, a person confirms',
  R5: 'Language or unstructured input: AI drafts',
  R6: 'Not enough detail to decide',
}

interface Props {
  steps: StepAssessment[]
  activeStep: string | null
  onActiveStep: (id: string | null) => void
}

export function StepTable({ steps, activeStep, onActiveStep }: Props) {
  return (
    <Panel
      id="steps"
      title="Step-by-step analysis"
      description="Each recommendation comes from a named rule applied to the facts extracted from your description, so the same facts always get the same answer."
      className="lg:col-span-3"
    >
      <div className="-mx-5 overflow-x-auto sm:-mx-6">
        <table className="w-full min-w-[46rem] border-collapse text-left text-[13px]">
          <thead>
            <tr className="border-y border-line bg-canvas text-[11px] font-semibold uppercase tracking-[0.06em] text-ink-3">
              <th scope="col" className="w-10 py-2 pl-5 pr-2 font-semibold sm:pl-6">#</th>
              <th scope="col" className="w-[24%] px-3 py-2 font-semibold">Current step</th>
              <th scope="col" className="w-36 px-3 py-2 font-semibold">Classification</th>
              <th scope="col" className="w-[24%] px-3 py-2 font-semibold">Recommendation</th>
              <th scope="col" className="py-2 pl-3 pr-5 font-semibold sm:pr-6">Why</th>
            </tr>
          </thead>
          <tbody>
            {steps.map((s, i) => (
              <tr
                key={s.step_id}
                onMouseEnter={() => onActiveStep(s.step_id)}
                onMouseLeave={() => onActiveStep(null)}
                className={`border-b border-line align-top transition-colors duration-150 last:border-b-0 ${activeStep === s.step_id ? 'bg-canvas' : ''}`}
              >
                <td className="py-3.5 pl-5 pr-2 text-ink-3 tnum sm:pl-6">{i + 1}</td>
                <td className="px-3 py-3.5 font-medium">{s.label}</td>
                <td className="px-3 py-3.5"><CategoryBadge category={s.classification} /></td>
                <td className="px-3 py-3.5 text-ink-2">
                  {s.recommendation}
                  {s.review_gate && (
                    <span className="mt-1.5 flex items-center gap-1 text-xs text-human-ink">
                      <UserCheck className="size-3.5" aria-hidden /> Reviewed before use
                    </span>
                  )}
                </td>
                <td className="py-3.5 pl-3 pr-5 leading-relaxed text-ink-2 sm:pr-6">
                  {s.reason}
                  <span
                    title={RULES[s.rule_id]}
                    className="ml-1.5 inline-block cursor-help rounded bg-sidebar px-1.5 py-px align-[1px] text-[11px] font-medium text-ink-3 tnum"
                  >
                    Rule {s.rule_id.slice(1)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  )
}
