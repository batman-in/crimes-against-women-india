// "From arrest to verdict": what happened to the accused, and juveniles apprehended (NCRB).
// National figures exist by crime head; state figures only for all crimes against women combined.
import type { DashboardData } from '@/lib/data'
import { describeYears } from '@/lib/data'

export interface JusticeData {
  national: Record<string, Record<string, Record<string, number>>> // year -> crime head -> measure
  states: Record<string, Record<string, Record<string, number | string>>> // state -> year -> measure
  juvenile: {
    national: Record<string, Record<string, Record<string, number>>> // year -> head -> apprehended/age_*
    allJuvenile: Record<string, number> // year -> all juveniles apprehended (every crime)
    states: Record<string, Record<string, Record<string, number>>> // state -> year -> head -> cases against juveniles
  }
}

const fmt = (v: number | undefined) => (v === undefined ? '–' : Math.round(v).toLocaleString('en-IN'))
const lakh = (v: number) => (v >= 1e5 ? `${(v / 1e5).toFixed(1)} lakh` : fmt(v))
const pct = (a: number, b: number) => (b ? (a / b) * 100 : 0)

// Offender-relation mode and minor-girls heads map onto the nearest head NCRB reports disposal for
const HEAD_ALIAS: Record<string, string> = { pocso_girls: 'pocso_girls', custodial_rape: 'rape' }

export function Justice(props: { data: DashboardData; cat: string; year: number; state: string | null; district: string | null }) {
  const j = (props.data as DashboardData & { justice?: JusticeData }).justice
  if (!j || !j.national) return null
  const { data, year, state } = props
  const y = String(year)
  const catLabel = data.cats[props.cat]?.label ?? 'All crimes against women'

  // --- disposal: state totals, or national by crime head -----------------------------------
  let rec: Record<string, number | string> | undefined
  let scope: string
  let headNote: string | undefined
  const years = state
    ? Object.keys(j.states[state] ?? {}).map(Number).sort((a, b) => a - b)
    : Object.keys(j.national).map(Number).sort((a, b) => a - b)
  if (state) {
    rec = j.states[state]?.[y]
    scope = `${state} · all crimes against women`
    if (props.cat !== 'total') headNote = 'State figures are published only for all crimes against women combined.'
    if (props.district) headNote = 'NCRB does not publish these by district; showing the state.'
    if (rec?.via) headNote = `Reported for ${rec.via} in this year.`
  } else {
    const head = HEAD_ALIAS[props.cat] ?? props.cat
    rec = j.national[y]?.[head]
    scope = `India · ${catLabel}`
    if (!rec && j.national[y]?.total) {
      rec = j.national[y].total
      scope = 'India · all crimes against women'
      headNote = `Not published separately for ${catLabel.toLowerCase()}; showing all crimes against women.`
    }
  }
  const n = (k: string) => (typeof rec?.[k] === 'number' ? (rec[k] as number) : undefined)

  return (
    <section className="flex flex-col gap-4" aria-labelledby="justice-title">
      <div>
        <h3 id="justice-title" className="text-sm font-medium">From arrest to verdict, {year}</h3>
        <p className="text-xs text-muted-foreground">{scope}</p>
        {headNote && <p className="mt-1 text-xs text-muted-foreground">{headNote}</p>}
      </div>

      {!rec ? (
        <p className="text-xs text-muted-foreground">
          No arrest and trial figures for {year}. Available for {describeYears(years)}.
        </p>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-2">
            <Stat label="Conviction rate" value={n('conviction_rate') !== undefined ? `${n('conviction_rate')}%` : '–'} hint="of trials completed" strong />
            <Stat
              label="Awaiting trial"
              value={n('cases_pending') !== undefined ? lakh(n('cases_pending')!) : '–'}
              hint={n('pendency_pct') !== undefined ? `${n('pendency_pct')}% of cases` : 'cases'}
            />
            <Stat label="Charge-sheeted" value={n('chargesheeting_rate') !== undefined ? `${n('chargesheeting_rate')}%` : '–'} hint="of cases investigated" />
          </div>

          {n('cases_trials_completed') ? (
            <Outcome convicted={n('cases_convicted') ?? 0} acquitted={n('cases_acquitted') ?? 0} discharged={n('cases_discharged') ?? 0} completed={n('cases_trials_completed')!} />
          ) : null}

          <div className="flex flex-col gap-1">
            <p className="text-xs font-medium text-muted-foreground">People accused, {year}</p>
            <dl className="grid grid-cols-[1fr_auto] gap-x-3 gap-y-1 text-sm">
              {[
                ['Arrested', 'arrested'],
                ['Charge-sheeted', 'chargesheeted'],
                ['Convicted', 'convicted'],
                ['Acquitted', 'acquitted'],
                ['Discharged', 'discharged'],
              ]
                .filter(([, k]) => n(k) !== undefined)
                .map(([label, k]) => (
                  <div key={k} className="contents">
                    <dt>{label}</dt>
                    <dd className="text-right tabular-nums">{fmt(n(k))}</dd>
                  </div>
                ))}
            </dl>
            <p className="text-xs text-muted-foreground">
              Charge-sheets and verdicts in a year include people arrested in earlier years, so these don't form a strict funnel.
            </p>
          </div>

          <p className="rounded-md bg-muted px-3 py-2 text-xs text-muted-foreground">
            <span className="font-medium text-foreground">Punishment given:</span> NCRB does not publish the sentences awarded (death, life
            imprisonment, years in prison, fines) for crimes against women, so they can't be shown.
          </p>
        </>
      )}

      <Juveniles j={j} data={data} cat={props.cat} year={year} state={state} rec={rec} />
    </section>
  )
}

function Stat(props: { label: string; value: string; hint: string; strong?: boolean }) {
  return (
    <div className="flex flex-col gap-0.5 rounded-md border px-2.5 py-2">
      <span className="text-[11px] text-muted-foreground">{props.label}</span>
      <span className={`tabular-nums ${props.strong ? 'text-xl font-semibold' : 'text-lg font-semibold'}`}>{props.value}</span>
      <span className="text-[10px] leading-tight text-muted-foreground">{props.hint}</span>
    </div>
  )
}

/** How completed trials ended: one stacked bar, labelled directly. */
function Outcome(props: { convicted: number; acquitted: number; discharged: number; completed: number }) {
  const parts = [
    { key: 'Convicted', v: props.convicted, cls: 'bg-[var(--ramp-4)]' },
    { key: 'Acquitted', v: props.acquitted, cls: 'bg-muted-foreground/45' },
    { key: 'Discharged', v: props.discharged, cls: 'bg-muted-foreground/20' },
  ]
  const total = parts.reduce((t, p) => t + p.v, 0) || props.completed
  return (
    <div className="flex flex-col gap-1.5">
      <p className="text-xs font-medium text-muted-foreground">How {fmt(props.completed)} completed trials ended (cases)</p>
      <div className="flex h-3 w-full overflow-hidden rounded-full" role="img" aria-label={parts.map((p) => `${p.key} ${pct(p.v, total).toFixed(0)}%`).join(', ')}>
        {parts.map((p) => (
          <span key={p.key} className={`${p.cls} h-full`} style={{ width: `${pct(p.v, total)}%` }} />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs">
        {parts.map((p) => (
          <span key={p.key} className="inline-flex items-center gap-1.5">
            <span className={`${p.cls} size-2.5 rounded-sm`} aria-hidden />
            {p.key} <span className="text-muted-foreground tabular-nums">{pct(p.v, total).toFixed(0)}% · {fmt(p.v)}</span>
          </span>
        ))}
      </div>
    </div>
  )
}

function Juveniles(props: { j: JusticeData; data: DashboardData; cat: string; year: number; state: string | null; rec?: Record<string, number | string> }) {
  const { j, year, state } = props
  const y = String(year)
  const isPocso = props.cat.startsWith('pocso')
  const head = isPocso ? 'pocso' : props.cat
  const label = isPocso ? 'POCSO (all child victims)' : props.data.cats[props.cat]?.label ?? 'crimes against women'

  if (state) {
    const heads = j.juvenile.states[state]?.[y]
    const v = heads?.[head] ?? (isPocso ? undefined : heads?.total)
    const shownTotal = heads && heads[head] === undefined
    return (
      <div className="flex flex-col gap-1 border-t pt-3">
        <p className="text-sm font-medium">Juveniles (under 18)</p>
        {v === undefined ? (
          <p className="text-xs text-muted-foreground">No juvenile figures for {state} in {year}.</p>
        ) : (
          <p className="text-sm">
            <span className="text-xl font-semibold tabular-nums">{v.toLocaleString('en-IN')}</span> cases against juveniles in {state},{' '}
            {shownTotal ? 'all crimes against women' : label.toLowerCase()}.
          </p>
        )}
        <p className="text-xs text-muted-foreground">State figures count cases; the number of juveniles is published only for India.</p>
      </div>
    )
  }

  const nat = j.juvenile.national[y]
  const r = nat?.[head] ?? nat?.total
  if (!r) return null
  const usedTotal = nat?.[head] === undefined
  const accused = typeof props.rec?.arrested === 'number' ? (props.rec.arrested as number) : undefined
  const all = j.juvenile.allJuvenile[y]
  const ages = [
    { k: 'Under 12', v: r.age_below_12 ?? 0 },
    { k: '12–16', v: r.age_12_16 ?? 0 },
    { k: '16–18', v: r.age_16_18 ?? 0 },
  ]
  const ageTotal = ages.reduce((t, a) => t + a.v, 0) || r.apprehended
  return (
    <div className="flex flex-col gap-2 border-t pt-3">
      <p className="text-sm font-medium">Juveniles (under 18), {year}</p>
      <p className="text-sm">
        <span className="text-xl font-semibold tabular-nums">{(r.apprehended ?? 0).toLocaleString('en-IN')}</span> juveniles apprehended for{' '}
        {usedTotal ? 'crimes against women' : label.toLowerCase()}
        {accused && !usedTotal ? (
          <span className="text-muted-foreground"> · {pct(r.apprehended, accused + r.apprehended).toFixed(1)}% of all accused</span>
        ) : null}
      </p>
      <div className="flex flex-col gap-1">
        {ages.map((a) => (
          <div key={a.k} className="grid grid-cols-[4.5rem_1fr_auto] items-center gap-2 text-xs">
            <span>{a.k}</span>
            <span className="h-2 overflow-hidden rounded-full bg-muted">
              <span className="block h-full rounded-full bg-[var(--ramp-4)]" style={{ width: `${pct(a.v, ageTotal)}%` }} />
            </span>
            <span className="text-muted-foreground tabular-nums">{a.v.toLocaleString('en-IN')}</span>
          </div>
        ))}
      </div>
      <p className="text-xs text-muted-foreground">
        {usedTotal && props.cat !== 'total' ? `Not published separately for ${label.toLowerCase()}; showing all crimes against women. ` : ''}
        {head === 'total' && all ? `That is ${pct(r.apprehended, all).toFixed(1)}% of the ${all.toLocaleString('en-IN')} juveniles apprehended for all crimes. ` : ''}
        {isPocso ? 'POCSO figures include boys as victims. ' : ''}
        The "crimes against women" total excludes POCSO.
      </p>
    </div>
  )
}
