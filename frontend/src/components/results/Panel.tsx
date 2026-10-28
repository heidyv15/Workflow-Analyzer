interface Props {
  title: string
  description?: React.ReactNode
  aside?: React.ReactNode
  children: React.ReactNode
  className?: string
  id?: string
}

export function Panel({ title, description, aside, children, className = '', id }: Props) {
  return (
    <section
      id={id}
      aria-labelledby={id ? `${id}-title` : undefined}
      className={`animate-rise min-w-0 rounded-xl bg-surface p-5 shadow-[0_0_0_1px_var(--color-line),0_1px_2px_oklch(0.2_0.02_290/0.04)] sm:p-6 ${className}`}
    >
      <header className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
        <div className="min-w-0">
          <h2 id={id ? `${id}-title` : undefined} className="text-[15px] font-semibold tracking-[-0.01em]">{title}</h2>
          {description && <p className="mt-1 max-w-[70ch] text-[13px] leading-relaxed text-ink-3">{description}</p>}
        </div>
        {aside}
      </header>
      <div className="mt-5">{children}</div>
    </section>
  )
}
