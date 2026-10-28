// Lightweight hints shown while the user types. They only nudge toward a better
// description; the backend decides what is actually missing.

export interface DetailHint {
  key: string
  label: string
  present: boolean
}

const FREQUENCY = /\b(every|each|daily|weekly|monthly|quarterly|whenever|when(ever)? (someone|a|an|we)|once a|twice|per (day|week|month)|mondays?|tuesdays?|wednesdays?|thursdays?|fridays?|morning|end of (the )?(day|week|month))\b/i
const TIME = /\b\d+\s*(min|mins|minutes?|hrs?|hours?)\b|\b(an|half an|one|two|three) hours?\b|\ba few minutes\b/i
const TOOLS = /\b(excel|spreadsheets?|sheets|outlook|gmail|email|e-mail|sharepoint|teams|slack|salesforce|crm|erp|quickbooks|pdf|forms?|database|drive|calendar|system|portal|app)\b/i

export function detailHints(text: string): DetailHint[] {
  const steps = text
    .split(/,|;|\.|\bthen\b|\band\b/i)
    .map((s) => s.trim())
    .filter((s) => s.split(/\s+/).length >= 2)
  return [
    { key: 'trigger', label: 'When it happens', present: FREQUENCY.test(text) },
    { key: 'steps', label: 'The steps', present: steps.length >= 3 },
    { key: 'tools', label: 'Tools used', present: TOOLS.test(text) },
    { key: 'time', label: 'Time it takes', present: TIME.test(text) },
  ]
}
