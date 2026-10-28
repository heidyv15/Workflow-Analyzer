import { CircleAlert, Info, X } from 'lucide-react'

interface Props {
  tone: 'danger' | 'info'
  title?: string
  children: React.ReactNode
  action?: { label: string; onClick: () => void }
  onDismiss?: () => void
  className?: string
}

const TONES = {
  danger: { box: 'bg-danger-soft text-ink shadow-[0_0_0_1px_oklch(0.88_0.05_27)]', icon: 'text-danger', Icon: CircleAlert },
  info: { box: 'bg-human-soft text-ink shadow-[0_0_0_1px_oklch(0.88_0.06_80)]', icon: 'text-human-ink', Icon: Info },
}

export function Notice({ tone, title, children, action, onDismiss, className = '' }: Props) {
  const t = TONES[tone]
  return (
    <div role={tone === 'danger' ? 'alert' : 'status'} className={`animate-rise flex gap-3 rounded-xl px-4 py-3 text-sm ${t.box} ${className}`}>
      <t.Icon className={`mt-0.5 size-4 shrink-0 ${t.icon}`} strokeWidth={2} aria-hidden />
      <div className="min-w-0 flex-1 leading-relaxed">
        {title && <p className="font-medium">{title}</p>}
        <div className={title ? 'text-ink-2' : ''}>{children}</div>
        {action && (
          <button type="button" onClick={action.onClick} className="mt-2 text-sm font-medium text-ink underline decoration-line-strong underline-offset-4 hover:decoration-ink">
            {action.label}
          </button>
        )}
      </div>
      {onDismiss && (
        <button type="button" onClick={onDismiss} aria-label="Dismiss" className="-m-1 h-fit rounded-md p-1 text-ink-3 transition-colors hover:bg-surface/60 hover:text-ink">
          <X className="size-4" />
        </button>
      )}
    </div>
  )
}
