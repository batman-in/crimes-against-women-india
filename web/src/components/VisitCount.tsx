import { Eye } from 'lucide-react'
import { useEffect, useState } from 'react'

// One count per page load, even though React may run effects twice in development.
let counted: Promise<number | null> | null = null

function countVisit(): Promise<number | null> {
  counted ??= fetch(`${import.meta.env.BASE_URL}api/visits`, { method: 'POST' })
    .then((r) => (r.ok && r.headers.get('content-type')?.includes('json') ? r.json() : null))
    .then((d) => (typeof d?.total === 'number' ? d.total : null))
    .catch(() => null)
  return counted
}

/** Total visits to the site, shown next to the theme button. Hidden if the counter is unavailable. */
export function VisitCount() {
  const [total, setTotal] = useState<number | null>(null)
  useEffect(() => {
    let alive = true
    countVisit().then((t) => alive && setTotal(t))
    return () => {
      alive = false
    }
  }, [])
  if (total === null) return null
  const text = total.toLocaleString('en-IN')
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium text-muted-foreground tabular-nums"
      title={`${text} total visits`}
      aria-label={`${text} total visits`}
    >
      <Eye className="size-3.5" aria-hidden />
      {text}
    </span>
  )
}
