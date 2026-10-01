// "Arrest to verdict" page: state map of one justice measure, and its controls and ranking.
import type { DashboardData } from '@/lib/data'
import { cn } from '@/lib/utils'
import type { JusticeData } from './Justice'

export type JusticeMeasure = 'conviction_rate' | 'chargesheeting_rate' | 'pendency_pct' | 'pendency_pct_investigation'

export const MEASURES: Record<JusticeMeasure, { label: string; short: string; about: string }> = {
  conviction_rate: {
    label: 'Conviction rate',
    short: 'convicted',
    about: 'Of trials completed in the year, the share that ended in conviction.',
  },
  chargesheeting_rate: {
    label: 'Charge-sheeting rate',
    short: 'charge-sheeted',
    about: 'Of cases police finished investigating, the share sent to court with a charge-sheet.',
  },
  pendency_pct: {
    label: 'Awaiting trial',
    short: 'awaiting trial',
    about: 'Of all cases before the courts in the year, the share still pending at the end of it.',
  },
  pendency_pct_investigation: {
    label: 'Awaiting investigation',
    short: 'under investigation',
    about: 'Of all cases with the police in the year, the share still under investigation at the end of it.',
  },
}

export const justiceOf = (data: DashboardData) => (data as DashboardData & { justice?: JusticeData }).justice

export function stateMeasure(j: JusticeData, state: string, year: number, m: JusticeMeasure): number | undefined {
  const v = j.states[state]?.[String(year)]?.[m]
  return typeof v === 'number' ? v : undefined
}

export function nationalMeasure(j: JusticeData, year: number, m: JusticeMeasure): number | undefined {
  const v = j.national[String(year)]?.total?.[m]
  return typeof v === 'number' ? v : undefined
}

/** Years in which most states report the measure. */
export function justiceYears(j: JusticeData, m: JusticeMeasure): number[] {
  const count: Record<string, number> = {}
  for (const years of Object.values(j.states))
    for (const [y, rec] of Object.entries(years)) if (typeof rec[m] === 'number') count[y] = (count[y] ?? 0) + 1
  return Object.entries(count)
    .filter(([, n]) => n >= 20)
    .map(([y]) => Number(y))
    .sort((a, b) => a - b)
}

export function JusticeControls(props: {
  measure: JusticeMeasure
  setMeasure: (m: JusticeMeasure) => void
  year: number
  setYear: (y: number) => void
  years: number[]
  compact?: boolean
}) {
  return (
    <div className={cn('flex flex-col', props.compact ? 'gap-3' : 'gap-5')}>
      {!props.compact && (
        <div>
          <h2 className="text-lg font-semibold">From arrest to verdict</h2>
          <p className="text-sm text-muted-foreground">
            What happens after a crime against a woman is reported: investigation, charge-sheet, trial and verdict
            (NCRB).
          </p>
        </div>
      )}
      <div className="flex flex-col gap-2">
        <span className="text-sm font-medium">Show on the map</span>
        <div className="grid grid-cols-2 gap-1.5">
          {(Object.keys(MEASURES) as JusticeMeasure[]).map((k) => (
            <button
              key={k}
              type="button"
              onClick={() => props.setMeasure(k)}
              aria-pressed={props.measure === k}
              className={cn(
                'rounded-md border px-2.5 py-2 text-left text-sm font-medium',
                props.measure === k ? 'border-transparent bg-primary text-primary-foreground' : 'bg-background hover:bg-accent',
              )}
            >
              {MEASURES[k].label}
            </button>
          ))}
        </div>
        <p className="text-xs text-muted-foreground">{MEASURES[props.measure].about}</p>
      </div>
      <label className="flex items-center justify-between gap-3 text-sm font-medium">
        Year
        <select
          value={props.year}
          onChange={(e) => props.setYear(Number(e.target.value))}
          className="h-9 rounded-md border bg-background px-2 text-sm"
        >
          {[...props.years].reverse().map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
      </label>
      {!props.compact && (
        <p className="text-xs text-muted-foreground">
          State figures are published for all crimes against women combined. Tap a state for its full breakdown; India's
          figures by crime type follow the crime type chosen on the Statistics page.
        </p>
      )}
    </div>
  )
}

/** States ranked by the measure, highest first. */
export function StateRanking(props: {
  j: JusticeData
  year: number
  measure: JusticeMeasure
  selected: string | null
  onSelect: (s: string) => void
}) {
  const rows = Object.keys(props.j.states)
    .map((s) => ({ s, v: stateMeasure(props.j, s, props.year, props.measure) }))
    .filter((r): r is { s: string; v: number } => r.v !== undefined)
    .sort((a, b) => b.v - a.v)
  if (!rows.length) return null
  return (
    <section className="flex flex-col gap-2 border-t pt-4">
      <h3 className="text-sm font-medium">
        {MEASURES[props.measure].label} by state, {props.year}
      </h3>
      <ol className="flex flex-col">
        {rows.map((r, i) => (
          <li key={r.s}>
            <button
              type="button"
              onClick={() => props.onSelect(r.s)}
              className={cn(
                'grid w-full grid-cols-[1.5rem_1fr_5rem_3rem] items-center gap-2 rounded px-1 py-1 text-left text-xs hover:bg-accent',
                props.selected === r.s && 'bg-accent font-semibold',
              )}
            >
              <span className="text-muted-foreground tabular-nums">{i + 1}</span>
              <span className="truncate">{r.s}</span>
              <span className="h-2 overflow-hidden rounded-full bg-muted">
                <span className="block h-full rounded-full bg-[var(--ramp-4)]" style={{ width: `${Math.min(100, r.v)}%` }} />
              </span>
              <span className="text-right tabular-nums">{r.v.toFixed(1)}%</span>
            </button>
          </li>
        ))}
      </ol>
    </section>
  )
}
