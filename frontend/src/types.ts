// Mirrors backend/app/schemas.py and the response models in backend/app/main.py.

export type Classification = 'traditional_automation' | 'ai_assisted' | 'human_review' | 'manual'
export type NodeCategory = 'automated' | 'ai_assisted' | 'human_review' | 'manual'
export type Band = 'high' | 'moderate' | 'limited' | 'keep_human_led'
export type Level3 = 'low' | 'moderate' | 'high'
export type ValueSource = 'stated' | 'inferred' | 'unknown'
export type Frequency = 'daily' | 'weekly' | 'biweekly' | 'monthly' | 'quarterly' | 'ad_hoc' | 'unknown'

export interface MissingInfo {
  field: 'frequency' | 'duration' | 'steps' | 'systems' | 'volume' | 'other'
  question: string
}

export interface ExtractedStep {
  id: string
  label: string
  future_label: string
  action_type: string
  input_data: string
  output_nature: string
  requires_judgment: boolean
  stakes: string
  external_facing: boolean
  sensitivity: string[]
  minutes: number | null
  minutes_source: ValueSource
  systems: string[]
}

export interface Extraction {
  is_analyzable: boolean
  process_name: string
  trigger: string
  frequency: Frequency
  frequency_source: ValueSource
  consistency: string
  data_access: string
  total_minutes: number | null
  total_minutes_source: ValueSource
  steps: ExtractedStep[]
  missing_information: MissingInfo[]
}

export interface StepAssessment {
  step_id: string
  label: string
  classification: Classification
  recommendation: string
  reason: string
  rule_id: string
  review_gate: boolean
  minutes: number | null
  minutes_source: ValueSource
}

export interface WorkflowNode {
  id: string
  label: string
  category: NodeCategory
  source_step_id: string | null
  inserted: boolean
  note: string | null
}

export interface FactorScore {
  key: string
  label: string
  weight: number
  value: number
  points: number
  explanation: string
  assumed: boolean
}

export interface Penalty {
  key: string
  label: string
  points: number
  explanation: string
}

export interface Range {
  low: number
  high: number
}

export interface Analysis {
  process_name: string
  summary: string
  score: { score: number; band: Band; factors: FactorScore[]; penalties: Penalty[] }
  step_analysis: StepAssessment[]
  current_workflow: WorkflowNode[]
  future_workflow: WorkflowNode[]
  impact: {
    current_minutes_per_run: number | null
    future_minutes_per_run: Range | null
    saved_minutes_per_run: Range | null
    runs_per_year: number | null
    saved_hours_per_year: Range | null
    confidence: 'high' | 'medium' | 'low'
    basis: string[]
    missing: MissingInfo[]
  }
  risk: { level: Level3; factors: { key: string; label: string; severity: Level3; why: string }[] }
  complexity: { level: Level3; drivers: string[] }
  architecture: { stage: string; tool: string; why: string; kind: 'trigger' | 'integration' | 'processing' | 'ai' | 'human' | 'delivery' }[]
  ai_used_for: string[]
  ai_not_needed: string[]
  assumptions: { field: string; detail: string }[]
  missing_information: MissingInfo[]
  meta: { engine_version: string; summary_source: 'template' | 'model' }
}

export interface RunInfo {
  source: 'live' | 'example'
  engine_version: string
  prompt_version: string | null
  model: string | null
  attempts: number | null
  latency_ms: number | null
}

export interface AnalyzeResponse {
  status: 'complete' | 'needs_detail'
  analysis: Analysis | null
  extraction: Extraction | null
  questions: MissingInfo[]
  run: RunInfo
}

export interface ExampleSummary {
  id: string
  title: string
  tagline: string
  description: string
}

export interface Overrides {
  frequency?: Frequency
  runs_per_year?: number
  step_minutes?: Record<string, number>
}

export interface Methodology {
  rules: { id: string; description: string; outcome: Classification }[]
  factors: { key: string; label: string; measures: string; weight: number }[]
  penalties: { risk: Record<string, number>; complexity: Record<string, number> }
  bands: { band: Band; min_score: number }[]
  ai_step_credit: number
  time_removed: Record<string, { low: number; high: number }>
  runs_per_year: Record<string, number>
}
