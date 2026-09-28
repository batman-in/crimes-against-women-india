// ADR (Association for Democratic Reforms) analyses of sitting MPs/MLAs who declared
// pending cases of crimes against women in their election affidavits. Aggregates only.
import type { DashboardData } from './data'

type Row = Record<string, string | number | null>

const GEO_NAME: Record<string, string[]> = {
  'Andaman & Nicobar Islands': ['Andaman & Nicobar'],
  'Dadra & Nagar Haveli and Daman & Diu': ['Dadra & Nagar Haveli', 'Daman & Diu'],
}

const isFull = (r: Row) => !String(r.method ?? '').includes('press')

/** Report years with a full state-wise breakdown (2023 exists only as press headlines). */
export function adrMapYears(d: DashboardData): number[] {
  const rows = d.adr.legislators_by_state ?? []
  return [...new Set(rows.filter(isFull).map((r) => Number(r.report_year)))].sort((a, b) => a - b)
}

/** The ADR report shown for a dashboard year: the latest report on or before it, else the first. */
export function adrYearFor(d: DashboardData, year: number): number | undefined {
  const ys = adrMapYears(d)
  return [...ys].reverse().find((y) => y <= year) ?? ys[0]
}

/** Legislators with declared cases, per map state, for one report year. */
export function adrByState(d: DashboardData, reportYear: number) {
  const out: Record<string, { total: number; rape: number }> = {}
  for (const r of d.adr.legislators_by_state ?? []) {
    if (Number(r.report_year) !== reportYear || !isFull(r)) continue
    for (const name of GEO_NAME[String(r.state_ut)] ?? [String(r.state_ut)]) {
      const o = (out[name] ??= { total: 0, rape: 0 })
      o.total += Number(r.legislators_with_cases ?? 0)
      o.rape += Number(r.rape_cases_legislators ?? 0)
    }
  }
  return out
}

export interface AdrReport {
  year: number
  date: string
  partial: boolean
  houses: { house: string; count: number; rape: number; analysed?: number }[]
  parties: { party: string; name: string; count: number }[]
  charges: { label: string; count: number }[]
}

export function adrReports(d: DashboardData): AdrReport[] {
  const houses = d.adr.legislators_by_house ?? []
  const years = [...new Set(houses.map((r) => Number(r.report_year)))].sort((a, b) => b - a)
  return years.map((year) => {
    const h = houses.filter((r) => Number(r.report_year) === year)
    const parties = (d.adr.legislators_by_party ?? [])
      .filter((r) => Number(r.report_year) === year)
      .reduce<Record<string, { party: string; name: string; count: number }>>((acc, r) => {
        const k = String(r.party)
        acc[k] ??= { party: k, name: String(r.party_full ?? k), count: 0 }
        acc[k].count += Number(r.legislators_with_cases ?? 0)
        return acc
      }, {})
    const charges = (d.adr.legislators_by_charge ?? [])
      .filter((r) => Number(r.report_year) === year)
      .reduce<Record<string, number>>((acc, r) => {
        const k = String(r.charge_group ?? r.charge_label)
        acc[k] = (acc[k] ?? 0) + Number(r.legislators_with_charge ?? 0)
        return acc
      }, {})
    return {
      year,
      date: String(h[0]?.report_date ?? ''),
      partial: h.some((r) => !isFull(r)),
      houses: h
        .filter((r) => r.house !== 'Parliament (LS+RS)' || !h.some((x) => x.house === 'Lok Sabha'))
        .map((r) => ({
          house: String(r.house),
          count: Number(r.legislators_with_cases ?? 0),
          rape: Number(r.rape_cases_legislators ?? 0),
          analysed: r.legislators_analysed ? Number(r.legislators_analysed) : undefined,
        })),
      parties: Object.values(parties).sort((a, b) => b.count - a.count).slice(0, 6),
      charges: Object.entries(charges).map(([label, count]) => ({ label, count })).sort((a, b) => b.count - a.count),
    }
  })
}
