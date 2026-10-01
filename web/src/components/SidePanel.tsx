import { ArrowDownRight, ArrowUpRight, ChevronRight } from 'lucide-react'
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { adrByState, adrReports, adrYearFor } from '@/lib/adr'
import { ADR_REPORT_URL } from './Sources'
import {
  OFFENDER_LABELS, districtValue, formatValue, metricUnit, nationalValue, offenderRec, stateValue,
  type DashboardData, type Filters, type Value,
} from '@/lib/data'

interface Props {
  /** mobile shows location and the headline number in its own summary card */
  hideHeadline?: boolean
  data: DashboardData
  filters: Filters
  setFilters: (f: Partial<Filters>) => void
  state: string | null
  district: string | null
  districtName: (gid: string) => string
  districtsOf: (state: string) => string[]
  stateNames: string[]
  onSelectState: (s: string | null) => void
  onSelectDistrict: (gid: string | null) => void
}

export function SidePanel(p: Props) {
  const { data: d, filters: f, state, district } = p
  const legislators = f.offender === 'legislators'
  const valueAt = (fy: Filters): Value =>
    district ? districtValue(d, district, fy) : state ? stateValue(d, state, fy) : nationalValue(d, fy)
  const current = valueAt(f)
  const prev = valueAt({ ...f, year: f.year - 1 })
  const change = current.value !== undefined && prev.value ? (current.value - prev.value) / prev.value : undefined

  const title = district ? p.districtName(district) : state ?? 'India'
  const label = f.offender === 'all' ? d.cats[f.cat]?.label : `Rape by ${OFFENDER_LABELS[f.offender]?.toLowerCase() ?? f.offender}`

  // Ranking of the level below the selection
  const children: { id: string; name: string; v: Value }[] = district
    ? []
    : state
      ? p.districtsOf(state).map((gid) => ({ id: gid, name: p.districtName(gid), v: districtValue(d, gid, f) }))
      : p.stateNames.map((s) => ({ id: s, name: s, v: stateValue(d, s, f) }))
  const ranked = children.filter((c) => c.v.value !== undefined).sort((a, b) => b.v.value! - a.v.value!)
  const stateRank = state && !district
    ? p.stateNames.map((s) => ({ s, v: stateValue(d, s, f).value })).filter((x) => x.v !== undefined)
        .sort((a, b) => b.v! - a.v!).findIndex((x) => x.s === state)
    : -1
  const rankedCount = p.stateNames.filter((s) => stateValue(d, s, f).value !== undefined).length

  return (
    <div className="flex flex-col gap-6">
      {!p.hideHeadline && <Breadcrumb state={state} district={district ? p.districtName(district).split(',')[0] : null} onIndia={() => p.onSelectState(null)} onState={() => p.onSelectDistrict(null)} />}

      {legislators ? (
        <AdrPanel data={d} year={f.year} state={state} />
      ) : (
        <>
          <section className={p.hideHeadline ? 'hidden' : 'flex flex-col gap-1'}>
            <h2 className="text-balance text-xl font-semibold">{title}</h2>
            <p className="text-sm text-muted-foreground">{label}, {f.year}</p>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-4xl font-semibold tabular-nums">{formatValue(current.value, f.metric)}</span>
              {current.value !== undefined && <span className="text-sm text-muted-foreground">{metricUnit(f.metric)}</span>}
            </div>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              {f.metric === 'rate' && current.count !== undefined && (
                <span className="text-muted-foreground tabular-nums">{current.count.toLocaleString('en-IN')} cases</span>
              )}
              {f.metric === 'count' && current.rate !== undefined && (
                <span className="text-muted-foreground tabular-nums">{formatValue(current.rate, 'rate')} per lakh women</span>
              )}
              {change !== undefined && Number.isFinite(change) && (
                <Badge variant="outline" className="gap-1 tabular-nums">
                  {change >= 0 ? <ArrowUpRight className="size-3" /> : <ArrowDownRight className="size-3" />}
                  {change >= 0 ? '+' : ''}{(change * 100).toFixed(1)}% vs {f.year - 1}
                </Badge>
              )}
              {stateRank >= 0 && (
                <Badge variant="secondary" className="tabular-nums">
                  {ordinal(stateRank + 1)} highest of {rankedCount}
                </Badge>
              )}
            </div>
            {current.via && (
              <p className="mt-1 text-xs text-muted-foreground">Reported for {current.via} in this year.</p>
            )}
            {district && (
              <p className="mt-1 text-xs text-muted-foreground">
                District totals for 2001–2014 cover the 7 major IPC heads; from 2015 they are NCRB's full total. District rates use Census 2011 population. Districts created after 2010 are counted in their parent district.
              </p>
            )}
          </section>

          <Trend data={d} filters={f} valueAt={valueAt} onPick={(y) => p.setFilters({ year: y })} />

          {f.offender === 'all' && <Breakdown data={d} filters={f} state={state} district={district} setFilters={p.setFilters} />}

          <OffenderSplit data={d} state={district ? null : state} year={f.year} hidden={!!district} />

          <Separator />

          {ranked.length > 0 && (
            <section className="flex flex-col gap-2">
              <h3 className="text-sm font-medium">{state ? 'Districts' : 'States and UTs'}, highest first</h3>
              <BarList
                items={ranked.slice(0, 12).map((r) => ({ id: r.id, label: r.name.split(',')[0], value: r.v.value! }))}
                format={(v) => formatValue(v, f.metric)}
                onPick={(id) => (state ? p.onSelectDistrict(id) : p.onSelectState(id))}
              />
              {ranked.length > 12 && <p className="text-xs text-muted-foreground">Showing 12 of {ranked.length}.</p>}
            </section>
          )}

          <Separator />
          <AdrPanel data={d} year={f.year} state={state} compact />
        </>
      )}
    </div>
  )
}

function Breadcrumb(props: { state: string | null; district: string | null; onIndia: () => void; onState: () => void }) {
  return (
    <nav aria-label="Location" className="flex flex-wrap items-center gap-1 text-sm">
      <button type="button" className="text-muted-foreground hover:text-foreground hover:underline" onClick={props.onIndia}>India</button>
      {props.state && (
        <>
          <ChevronRight className="size-3.5 text-muted-foreground" />
          <button type="button" className={props.district ? 'text-muted-foreground hover:text-foreground hover:underline' : 'font-medium'} onClick={props.onState}>
            {props.state}
          </button>
        </>
      )}
      {props.district && (
        <>
          <ChevronRight className="size-3.5 text-muted-foreground" />
          <span className="font-medium">{props.district}</span>
        </>
      )}
    </nav>
  )
}

function Trend(props: { data: DashboardData; filters: Filters; valueAt: (f: Filters) => Value; onPick: (y: number) => void }) {
  const { data: d, filters: f } = props
  const rows = d.years.map((y) => ({ year: y, v: props.valueAt({ ...f, year: y }).value ?? null }))
  const has = rows.filter((r) => r.v !== null)
  if (has.length < 2) return null
  return (
    <section className="flex flex-col gap-2">
      <h3 className="text-sm font-medium">Trend, {metricUnit(f.metric)}</h3>
      <p className="text-xs text-muted-foreground">Definitions widened in 2013 (Criminal Law Amendment), so later figures aren't directly comparable with earlier ones.</p>
      <div className="h-44 w-full">
        <ResponsiveContainer>
          <LineChart data={rows} margin={{ top: 8, right: 12, bottom: 0, left: 0 }} onClick={(e) => e?.activeLabel && props.onPick(Number(e.activeLabel))}>
            <CartesianGrid vertical={false} stroke="var(--border)" />
            <XAxis dataKey="year" tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={24} />
            <YAxis tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} tickLine={false} axisLine={false} width={48} tickFormatter={(v: number) => compact(v)} />
            <Tooltip
              cursor={{ stroke: 'var(--muted-foreground)', strokeDasharray: '3 3' }}
              contentStyle={{ background: 'var(--popover)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12, color: 'var(--popover-foreground)' }}
              formatter={(v) => [formatValue(v as number, f.metric), metricUnit(f.metric)]}
            />
            {rows.some((r) => r.year === 2012 && r.v !== null) && (
              <ReferenceLine x={2013} stroke="var(--border)" strokeWidth={6} ifOverflow="hidden" label={{ value: '2013 law change', position: 'insideTopLeft', fontSize: 10, fill: 'var(--muted-foreground)' }} />
            )}
            <ReferenceLine x={f.year} stroke="var(--muted-foreground)" strokeDasharray="2 3" />
            <Line type="monotone" dataKey="v" stroke="var(--ramp-4)" strokeWidth={2} dot={false} activeDot={{ r: 4 }} connectNulls={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}

function Breakdown(props: { data: DashboardData; filters: Filters; state: string | null; district: string | null; setFilters: (f: Partial<Filters>) => void }) {
  const { data: d, filters: f } = props
  const keys = Object.values(d.catGroups).flat().filter((k) => k !== 'total')
  const items = keys
    .map((k) => {
      const fk = { ...f, cat: k }
      const v = props.district ? districtValue(d, props.district, fk) : props.state ? stateValue(d, props.state, fk) : nationalValue(d, fk)
      return { id: k, label: d.cats[k].label, value: v.value }
    })
    .filter((x): x is { id: string; label: string; value: number } => x.value !== undefined && x.value > 0)
    .sort((a, b) => b.value - a.value)
  if (!items.length) return <p className="text-xs text-muted-foreground">No breakdown by crime type for {f.year} at this level.</p>
  return (
    <section className="flex flex-col gap-2">
      <h3 className="text-sm font-medium">By crime type, {f.year}</h3>
      <BarList items={items.slice(0, 10)} format={(v) => formatValue(v, f.metric)} onPick={(id) => props.setFilters({ cat: id })} active={f.cat} />
      <p className="text-xs text-muted-foreground">Sub-heads (e.g. stalking within molestation) overlap their parent head.</p>
    </section>
  )
}

function OffenderSplit(props: { data: DashboardData; state: string | null; year: number; hidden: boolean }) {
  if (props.hidden) return null
  const rel = offenderRec(props.data, props.state, props.year)
  if (!rel) return null
  const keys = Object.keys(OFFENDER_LABELS).filter((k) => k !== 'all' && k !== 'known' && !k.startsWith('custodial') && rel[k] !== undefined)
  const items = keys.map((k) => ({ id: k, label: OFFENDER_LABELS[k], value: rel[k] }))
  return (
    <section className="flex flex-col gap-2">
      <h3 className="text-sm font-medium">Rape cases by offender, {props.year}</h3>
      <BarList items={items.sort((a, b) => b.value - a.value)} format={(v) => v.toLocaleString('en-IN')} />
      <p className="text-xs text-muted-foreground">
        NCRB offender relation to victim. Its categories change over the years (e.g. father/brother is reported separately only for 2014–2016).
      </p>
    </section>
  )
}

function AdrPanel(props: { data: DashboardData; year: number; state: string | null; compact?: boolean }) {
  const reports = adrReports(props.data)
  if (!reports.length) return null
  const ry = adrYearFor(props.data, props.year)
  const report = reports.find((r) => r.year === ry) ?? reports[0]
  const byState = ry ? adrByState(props.data, ry) : {}
  const stateCount = props.state ? byState[props.state] : undefined
  const total = report.houses.reduce((s, h) => s + h.count, 0)
  const who = report.houses.every((h) => h.house === 'State Assembly') ? 'MLAs' : 'MPs/MLAs'

  return (
    <section className="flex flex-col gap-3">
      <div>
        <h3 className="text-sm font-medium">Public representatives with declared cases</h3>
        <p className="text-xs text-muted-foreground">
          ADR analysis of election affidavits, report of {report.date}. Pending cases, not convictions.
          {report.houses.every((h) => h.house === 'State Assembly') && ' This report covers MLAs only.'}
          {ADR_REPORT_URL[report.year] && (
            <>
              {' '}
              <a href={ADR_REPORT_URL[report.year]} target="_blank" rel="noopener noreferrer" className="text-foreground underline underline-offset-2">
                Read the ADR {report.year} report
              </a>
            </>
          )}
        </p>
      </div>
      {props.state ? (
        <p className="text-sm">
          <span className="text-2xl font-semibold tabular-nums">{stateCount?.total ?? 0}</span>{' '}
          sitting {who} from {props.state}
          {stateCount?.rape ? `, ${stateCount.rape} with rape charges` : ''}.
        </p>
      ) : (
        <p className="text-sm">
          <span className="text-2xl font-semibold tabular-nums">{total}</span> sitting {who} across India.
        </p>
      )}
      {!props.compact && (
        <>
          <BarList items={report.houses.map((h) => ({ id: h.house, label: h.house, value: h.count }))} format={(v) => String(v)} />
          {report.parties.length > 0 && (
            <>
              <h4 className="text-xs font-medium text-muted-foreground">By party</h4>
              <BarList items={report.parties.map((x) => ({ id: x.party, label: x.party, value: x.count, title: x.name }))} format={(v) => String(v)} />
            </>
          )}
          {report.charges.length > 0 && (
            <>
              <h4 className="text-xs font-medium text-muted-foreground">By charge</h4>
              <BarList items={report.charges.slice(0, 8).map((x) => ({ id: x.label, label: x.label, value: x.count }))} format={(v) => String(v)} />
            </>
          )}
          <p className="text-xs text-muted-foreground">
            Reports: {reports.map((r) => `${r.year}${r.partial ? ' (headline figures only)' : ''}`).join(', ')}. The map uses the latest full report on or before the selected year.
          </p>
        </>
      )}
    </section>
  )
}

interface BarItem { id: string; label: string; value: number; title?: string }

function BarList(props: { items: BarItem[]; format: (v: number) => string; onPick?: (id: string) => void; active?: string }) {
  const max = Math.max(...props.items.map((i) => i.value), 1)
  return (
    <ul className="flex flex-col gap-1">
      {props.items.map((i) => {
        const body = (
          <>
            <span className="relative z-10 truncate">{i.label}</span>
            <span className="relative z-10 shrink-0 tabular-nums text-muted-foreground">{props.format(i.value)}</span>
            <span aria-hidden className="absolute inset-y-0 left-0 rounded-[4px] bg-[var(--ramp-2)] opacity-60" style={{ width: `${(i.value / max) * 100}%` }} />
          </>
        )
        const cls = `relative flex w-full items-center justify-between gap-3 overflow-hidden rounded-[4px] px-2 py-1 text-left text-sm ${
          props.active === i.id ? 'ring-1 ring-foreground/40' : ''
        }`
        return (
          <li key={i.id} title={i.title}>
            {props.onPick ? (
              <button type="button" className={`${cls} hover:bg-accent focus-visible:outline-2 focus-visible:outline-ring`} onClick={() => props.onPick!(i.id)}>
                {body}
              </button>
            ) : (
              <div className={cls}>{body}</div>
            )}
          </li>
        )
      })}
    </ul>
  )
}

const compact = (v: number) => (v >= 1e5 ? `${(v / 1e5).toFixed(1)}L` : v >= 1e3 ? `${(v / 1e3).toFixed(0)}k` : String(Math.round(v * 10) / 10))
const ordinal = (n: number) => `${n}${['th', 'st', 'nd', 'rd'][n % 100 > 10 && n % 100 < 14 ? 0 : n % 10] ?? 'th'}`
