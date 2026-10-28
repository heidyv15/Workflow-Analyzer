import type { Category } from '../lib/categories'
import { categoryStyle } from '../lib/categories'

export function CategoryBadge({ category, className = '' }: { category: Category; className?: string }) {
  const s = categoryStyle(category)
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ${s.badge} ${className}`}>
      <span className={`size-1.5 rounded-full ${s.dot}`} aria-hidden />
      {s.short}
    </span>
  )
}
