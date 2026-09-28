// Shape of public/data/data.json (written by scripts/build_data.py) and helpers over it.

export type Rec = Record<string, number | string | undefined> & { pop?: number; via?: string }
export type YearMap = Record<string, Rec>

export interface DashboardData {
  cats: Record<string, { label: string; legal: string }>
  catGroups: Record<string, string[]>
  coverage: Record<string, { state?: number[]; district?: number[] }>
  years: number[]
  national: YearMap
  states: Record<string, YearMap>
  districts: Record<string, YearMap>
  districtPop: Record<string, number>
  offenders: Record<string, Record<string, Record<string, number>>>
  offendersNational: Record<string, Record<string, number>>
  adr: Record<string, Record<string, string | number | null>[]>
  points: { states: Record<string, [number, number]>; districts: Record<string, [number, number]> }
}

export type Metric = 'count' | 'rate'

/** Offender filter: "all", a relation key from the NCRB rape tables, or custodial rape. */
export const OFFENDER_LABELS: Record<string, string> = {
  all: 'All offenders',
  family: 'Family members',
  father_brother: 'Father, brother, grandfather or son',
  family_other: 'Other close family',
  relatives: 'Relatives',
  neighbours: 'Neighbours',
  employers: 'Employers / co-workers',
  friends: 'Friends, partners, or on promise of marriage',
  acquaintances: 'Neighbours, employers & other acquaintances',
  other_known: 'Other known persons',
  known: 'Anyone known to the victim',
  unknown: 'Strangers (not known)',
  custodial: 'Police / public servants (custodial rape, all)',
  custodial_police: 'Police personnel (incl. armed forces, in custody)',
  custodial_public_servant: 'Public servants (in custody)',
  custodial_jail: 'Jail / remand home staff',
  custodial_hospital: 'Hospital staff (in custody)',
}

export interface Filters {
  year: number
  cat: string
  offender: string
  metric: Metric
}

export async function loadData(): Promise<DashboardData> {
  const res = await fetch(`${import.meta.env.BASE_URL}data/data.json`)
  if (!res.ok) throw new Error(`Could not load data.json (${res.status})`)
  return res.json()
}

const num = (v: unknown): number | undefined => (typeof v === 'number' && Number.isFinite(v) ? v : undefined)

/** Offender relation counts for one state (or India) in one year, with "unknown" derived. */
export function offenderRec(d: DashboardData, state: string | null, year: number) {
  const rel = state ? d.offenders[state]?.[year] : d.offendersNational[year]
  if (!rel) return undefined
  const rape = num((state ? d.states[state]?.[year] : d.national[year])?.rape)
  const out: Record<string, number> = { ...rel }
  if (rape !== undefined && rel.known !== undefined && rel.unknown === undefined) out.unknown = Math.max(rape - rel.known, 0)
  return out
}

/** Raw count for an entity-year record under the current filters. */
function countFor(d: DashboardData, rec: Rec | undefined, f: Filters, state: string | null, isDistrict: boolean) {
  if (!rec) return undefined
  if (f.offender === 'all') return num(rec[f.cat])
  if (f.offender === 'custodial') return num(rec.custodial_rape)
  if (isDistrict) return undefined // relation data is state level only
  return offenderRec(d, state, f.year)?.[f.offender]
}

export interface Value {
  count?: number
  rate?: number
  value?: number
  via?: string
}

export function stateValue(d: DashboardData, state: string, f: Filters): Value {
  const rec = d.states[state]?.[f.year]
  return withRate(countFor(d, rec, f, state, false), num(rec?.pop), f.metric, rec?.via)
}

export function nationalValue(d: DashboardData, f: Filters): Value {
  const rec = d.national[f.year]
  return withRate(countFor(d, rec, f, null, false), num(rec?.pop), f.metric)
}

export function districtValue(d: DashboardData, gid: string, f: Filters): Value {
  const rec = d.districts[gid]?.[f.year]
  return withRate(countFor(d, rec, f, null, true), d.districtPop[gid], f.metric)
}

function withRate(count: number | undefined, pop: number | undefined, metric: Metric, via?: string): Value {
  const rate = count !== undefined && pop ? (count / pop) * 1e5 : undefined
  return { count, rate, value: metric === 'rate' ? rate : count, via }
}

/** Years in which the current filter has data at a level. */
export function yearsWithData(d: DashboardData, f: Omit<Filters, 'year'>, level: 'state' | 'district'): number[] {
  if (f.offender === 'custodial') return d.coverage.custodial_rape?.[level] ?? []
  if (f.offender !== 'all') {
    if (level === 'district') return []
    const ys = new Set<number>()
    for (const [y, rec] of Object.entries(d.offendersNational)) {
      if (rec[f.offender] !== undefined || (f.offender === 'unknown' && rec.known !== undefined)) ys.add(+y)
    }
    return [...ys].sort((a, b) => a - b)
  }
  return d.coverage[f.cat]?.[level] ?? []
}

/** Offender options that exist anywhere in the data. */
export function offenderOptions(d: DashboardData): string[] {
  const keys = new Set<string>()
  for (const rec of Object.values(d.offendersNational)) Object.keys(rec).forEach((k) => keys.add(k))
  if (keys.has('known')) keys.add('unknown')
  if (d.coverage.custodial_rape) keys.add('custodial')
  return ['all', ...Object.keys(OFFENDER_LABELS).filter((k) => k !== 'all' && keys.has(k))]
}

export function formatValue(v: number | undefined, metric: Metric): string {
  if (v === undefined) return 'No data'
  if (metric === 'rate') return v >= 100 ? v.toFixed(0) : v >= 10 ? v.toFixed(1) : v.toFixed(2)
  return v.toLocaleString('en-IN')
}

export const metricUnit = (m: Metric) => (m === 'rate' ? 'per 1 lakh women' : 'cases')

/** Contiguous year ranges, for labels like "2001–2014, 2020–2022". */
export function describeYears(ys: number[]): string {
  if (!ys.length) return 'none'
  const parts: string[] = []
  let start = ys[0]
  let prev = ys[0]
  for (const y of ys.slice(1).concat(Number.NaN)) {
    if (y !== prev + 1) {
      parts.push(start === prev ? `${start}` : `${start}–${prev}`)
      start = y
    }
    prev = y
  }
  return parts.join(', ')
}
