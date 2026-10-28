import type { LucideIcon } from 'lucide-react'
import { Cog, Hand, ScanText, UserCheck } from 'lucide-react'
import type { Classification, NodeCategory } from '../types'

export type Category = NodeCategory | Classification

export interface CategoryStyle {
  label: string
  short: string
  nodeLabel: string // compact label for workflow nodes
  Icon: LucideIcon
  badge: string // soft background + ink text
  dot: string
  node: string // workflow node surface
  ink: string
  bar: string
  dashed: string // outline color for steps the analyzer added
}

const STYLES: Record<NodeCategory, CategoryStyle> = {
  automated: {
    label: 'Traditional automation',
    short: 'Automated',
    nodeLabel: 'Automated',
    Icon: Cog,
    badge: 'bg-auto-soft text-auto-ink',
    dot: 'bg-auto',
    node: 'bg-auto-soft shadow-[inset_0_0_0_1px_oklch(0.86_0.05_178)]',
    ink: 'text-auto-ink',
    bar: 'bg-auto',
    dashed: 'outline-auto/70',
  },
  ai_assisted: {
    label: 'AI-assisted',
    short: 'AI-assisted',
    nodeLabel: 'AI-assisted',
    Icon: ScanText,
    badge: 'bg-ai-soft text-ai-ink',
    dot: 'bg-ai',
    node: 'bg-ai-soft shadow-[inset_0_0_0_1px_oklch(0.86_0.06_302)]',
    ink: 'text-ai-ink',
    bar: 'bg-ai',
    dashed: 'outline-ai/70',
  },
  human_review: {
    label: 'Human review',
    short: 'Human review',
    nodeLabel: 'Human',
    Icon: UserCheck,
    badge: 'bg-human-soft text-human-ink',
    dot: 'bg-human',
    node: 'bg-human-soft shadow-[inset_0_0_0_1px_oklch(0.86_0.08_78)]',
    ink: 'text-human-ink',
    bar: 'bg-human',
    dashed: 'outline-human',
  },
  manual: {
    label: 'Needs clarification',
    short: 'Manual',
    nodeLabel: 'Manual',
    Icon: Hand,
    badge: 'bg-sidebar text-ink-2',
    dot: 'bg-ink-3',
    node: 'bg-sidebar shadow-[inset_0_0_0_1px_var(--color-line)]',
    ink: 'text-ink-2',
    bar: 'bg-ink-3',
    dashed: 'outline-ink-3',
  },
}

export function toNodeCategory(c: Category): NodeCategory {
  return c === 'traditional_automation' ? 'automated' : c
}

export function categoryStyle(c: Category): CategoryStyle {
  return STYLES[toNodeCategory(c)]
}

export const CATEGORY_ORDER: NodeCategory[] = ['automated', 'ai_assisted', 'human_review', 'manual']
