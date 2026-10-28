import { useEffect, useState } from 'react'

// Honest progress: the model call is the only slow part, so we say that and
// show elapsed time rather than inventing staged percentages.
export function AnalyzingView({ description, startedAt, onCancel }: { description: string; startedAt: number; onCancel: () => void }) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 250)
    return () => clearInterval(id)
  }, [])
  const seconds = Math.max(0, Math.floor((now - startedAt) / 1000))

  return (
    <div className="mx-auto w-full max-w-5xl px-5 pb-16 pt-10 sm:px-8 lg:pt-14" aria-busy="true">
      <div className="animate-rise flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-sm font-medium" role="status">
            <span className="relative flex size-2">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-brand opacity-60" />
              <span className="relative inline-flex size-2 rounded-full bg-brand" />
            </span>
            Identifying the steps in your process
            <span className="text-ink-3 tnum">{seconds}s</span>
          </p>
          <p className="mt-1 text-[13px] text-ink-3">
            {seconds < 25
              ? 'Claude reads the description once. The classifications, score, and estimates are calculated by rules.'
              : 'Taking longer than usual. Hang tight, or cancel and try again.'}
          </p>
        </div>
        <button type="button" onClick={onCancel} className="self-start rounded-lg px-3 py-1.5 text-sm font-medium text-ink-2 shadow-[0_0_0_1px_var(--color-line)] transition-colors hover:bg-surface hover:text-ink">
          Cancel
        </button>
      </div>

      <blockquote className="mt-6 line-clamp-3 max-w-[70ch] border-line text-[14px] leading-relaxed text-ink-2">
        “{description.trim()}”
      </blockquote>

      {/* Skeleton mirrors the results layout so the page doesn't jump when it arrives. */}
      <div className="mt-10 grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)]" aria-hidden>
        <div className="rounded-xl bg-surface p-5 shadow-[0_0_0_1px_var(--color-line)]">
          <div className="skeleton h-3 w-28" />
          <div className="mt-5 flex items-center gap-5">
            <div className="skeleton size-24 !rounded-full" />
            <div className="flex-1 space-y-2.5">
              <div className="skeleton h-6 w-20" />
              <div className="skeleton h-3 w-32" />
            </div>
          </div>
        </div>
        <div className="rounded-xl bg-surface p-5 shadow-[0_0_0_1px_var(--color-line)]">
          <div className="skeleton h-3 w-36" />
          <div className="mt-6 flex items-center gap-3">
            {[0, 1, 2, 3, 4].map((i) => (
              <div key={i} className="skeleton h-16 flex-1" style={{ animationDelay: `${i * 120}ms` }} />
            ))}
          </div>
        </div>
        <div className="rounded-xl bg-surface p-5 shadow-[0_0_0_1px_var(--color-line)] lg:col-span-2">
          <div className="skeleton h-3 w-32" />
          <div className="mt-5 space-y-3">
            {[0, 1, 2].map((i) => <div key={i} className="skeleton h-9 w-full" />)}
          </div>
        </div>
      </div>
    </div>
  )
}
