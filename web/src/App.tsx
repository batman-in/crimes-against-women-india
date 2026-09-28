import { ChevronLeft, ChevronRight, Moon, Pause, Play, SlidersHorizontal, Sun } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { feature } from 'topojson-client'
import type { Feature, FeatureCollection, Point } from 'geojson'
import type { GeometryCollection, Topology } from 'topojson-specification'
import { Filters } from '@/components/Filters'
import { Legend } from '@/components/Legend'
import { MapView, type AreaStyle, type MapMode } from '@/components/MapView'
import { SidePanel } from '@/components/SidePanel'
import { Sources } from '@/components/Sources'
import { Button } from '@/components/ui/button'
import { Sheet, SheetClose, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { TooltipProvider } from '@/components/ui/tooltip'
import { adrByState, adrMapYears, adrYearFor } from '@/lib/adr'
import {
  districtValue, formatValue, loadData, metricUnit, offenderOptions, stateValue, yearsWithData,
  type DashboardData, type Filters as F,
} from '@/lib/data'
import { NO_DATA, RAMP_DARK, RAMP_LIGHT, colorFor, quantileBreaks } from '@/lib/scale'

const AUTHOR_ROLE = 'a concerned citizen'

interface Geo {
  states: FeatureCollection
  districts: FeatureCollection
  india: FeatureCollection
}

async function loadGeo(): Promise<Geo> {
  const base = import.meta.env.BASE_URL
  const [s, d, i] = await Promise.all(
    ['states', 'districts', 'india'].map((n) => fetch(`${base}data/${n}.topo.json`).then((r) => r.json() as Promise<Topology>)),
  )
  return {
    states: feature(s, s.objects.states as GeometryCollection) as FeatureCollection,
    districts: feature(d, d.objects.districts as GeometryCollection) as FeatureCollection,
    india: feature(i, i.objects.india as GeometryCollection) as FeatureCollection,
  }
}

function useTheme() {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    try {
      const saved = localStorage.getItem('theme')
      if (saved === 'light' || saved === 'dark') return saved
    } catch { /* storage unavailable */ }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])
  const toggle = () => {
    const next = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    try { localStorage.setItem('theme', next) } catch { /* ignore */ }
  }
  return { theme, toggle }
}

export default function App() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [geo, setGeo] = useState<Geo | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    Promise.all([loadData(), loadGeo()]).then(([d, g]) => { setData(d); setGeo(g) }).catch((e) => setError(String(e)))
  }, [])

  if (error) return <div className="grid h-full place-items-center p-6 text-sm">Could not load the dashboard data. {error}</div>
  if (!data || !geo) return <div className="grid h-full place-items-center text-sm text-muted-foreground">Loading NCRB data…</div>
  return <Dashboard data={data} geo={geo} />
}

function Dashboard({ data, geo }: { data: DashboardData; geo: Geo }) {
  const { theme, toggle } = useTheme()
  const [filters, setFiltersState] = useState<F>(() => ({ year: data.years[data.years.length - 1], cat: 'total', offender: 'all', metric: 'rate' }))
  const [mode, setMode] = useState<MapMode>('fill')
  const [showDistricts, setShowDistricts] = useState(false)
  const [playing, setPlaying] = useState(false)
  const [state, setState] = useState<string | null>(null)
  const [district, setDistrict] = useState<string | null>(null)

  const setFilters = useCallback((f: Partial<F>) => setFiltersState((old) => ({ ...old, ...f })), [])
  const isMobile = useIsMobile()
  const selectState = useCallback((s: string | null) => { setState(s); setDistrict(null) }, [])

  const offenders = useMemo(() => {
    const opts = offenderOptions(data)
    return data.adr.legislators_by_state?.length ? [...opts, 'legislators'] : opts
  }, [data])
  const legislators = filters.offender === 'legislators'
  // Offender relations exist only for rape, so an offender filter pins the crime type.
  const effective = useMemo<F>(
    () => (filters.offender !== 'all' && !legislators ? { ...filters, cat: 'rape' } : filters),
    [filters, legislators],
  )

  const stateNames = useMemo(() => geo.states.features.map((f) => String(f.properties?.name)).sort(), [geo])
  const districtMeta = useMemo(() => {
    const m: Record<string, { name: string; ost: string }> = {}
    for (const f of geo.districts.features) m[String(f.properties?.gid)] = { name: String(f.properties?.name), ost: String(f.properties?.ost) }
    return m
  }, [geo])
  const districtsOf = useCallback((s: string) => Object.keys(districtMeta).filter((g) => districtMeta[g].ost === s), [districtMeta])
  const districtName = useCallback((g: string) => `${districtMeta[g]?.name}, ${districtMeta[g]?.ost}`, [districtMeta])

  const stateYears = useMemo(() => (legislators ? [] : yearsWithData(data, effective, 'state')), [data, effective, legislators])
  const districtYears = useMemo(() => (legislators ? [] : yearsWithData(data, effective, 'district')), [data, effective, legislators])

  useEffect(() => {
    if (!legislators) return
    const ys = adrMapYears(data)
    if (ys.length && !ys.includes(filters.year)) setFilters({ year: ys[ys.length - 1] })
  }, [legislators]) // eslint-disable-line react-hooks/exhaustive-deps

  // Play: step through the years that have data for the current filter
  useEffect(() => {
    const ys = legislators ? adrMapYears(data) : stateYears
    if (!playing || !ys.length) return
    const t = setTimeout(() => setFilters({ year: ys.find((y) => y > filters.year) ?? ys[0] }), 1100)
    return () => clearTimeout(t)
  }, [playing, stateYears, filters.year, setFilters, legislators, data])

  // When the filter changes and the year has no data, jump to the nearest year that does.
  useEffect(() => {
    if (!stateYears.length || stateYears.includes(filters.year)) return
    const nearest = stateYears.reduce((a, b) => (Math.abs(b - filters.year) < Math.abs(a - filters.year) ? b : a))
    setFilters({ year: nearest })
  }, [stateYears]) // eslint-disable-line react-hooks/exhaustive-deps

  const ramp = theme === 'dark' ? RAMP_DARK : RAMP_LIGHT
  const noData = NO_DATA[theme]
  const unit = legislators ? 'MPs/MLAs' : metricUnit(filters.metric)
  const fmt = useCallback(
    (v: number | undefined) => (v === undefined ? 'No data' : `${legislators ? v : formatValue(v, filters.metric)} ${unit}`),
    [legislators, filters.metric, unit],
  )

  // States
  const adrYear = legislators ? adrYearFor(data, filters.year) : undefined
  const stateVals = useMemo(() => {
    const out: Record<string, number | undefined> = {}
    if (legislators) {
      const a = adrYear ? adrByState(data, adrYear) : {}
      for (const s of stateNames) out[s] = a[s]?.total ?? 0
    } else for (const s of stateNames) out[s] = stateValue(data, s, effective).value
    return out
  }, [data, stateNames, effective, legislators, adrYear])
  const stateBreaks = useMemo(() => quantileBreaks(defined(stateVals)), [stateVals])
  const stateStyles = useMemo(() => {
    const out: Record<string, AreaStyle> = {}
    for (const s of stateNames) out[s] = { color: colorFor(stateVals[s], stateBreaks, ramp, noData), label: fmt(stateVals[s]) }
    return out
  }, [stateNames, stateVals, stateBreaks, ramp, noData, fmt])

  // Districts: class breaks span all of India so colours compare across states
  const districtVals = useMemo(() => {
    const out: Record<string, number | undefined> = {}
    if (!legislators) for (const g of Object.keys(districtMeta)) out[g] = districtValue(data, g, effective).value
    return out
  }, [data, districtMeta, effective, legislators])
  const districtBreaks = useMemo(() => quantileBreaks(defined(districtVals)), [districtVals])
  const districtStyles = useMemo(() => {
    const out: Record<string, AreaStyle> = {}
    for (const g of Object.keys(districtMeta)) out[g] = { color: colorFor(districtVals[g], districtBreaks, ramp, noData), label: fmt(districtVals[g]) }
    return out
  }, [districtMeta, districtVals, districtBreaks, ramp, noData, fmt])

  const hasDistrictData = defined(districtVals).length > 0
  const districtLevel = hasDistrictData && (showDistricts || !!state)

  // Heatmap: weight district points where district data exists, otherwise state centres
  const heatPoints = useMemo<FeatureCollection>(() => {
    const vals = hasDistrictData ? districtVals : stateVals
    const coords = hasDistrictData ? data.points.districts : data.points.states
    const max = Math.max(...defined(vals), 1)
    const features: Feature<Point>[] = []
    for (const [id, v] of Object.entries(vals)) {
      if (v === undefined || !v || !coords[id]) continue
      features.push({ type: 'Feature', geometry: { type: 'Point', coordinates: coords[id] }, properties: { w: Math.sqrt(v / max) } })
    }
    return { type: 'FeatureCollection', features }
  }, [hasDistrictData, districtVals, stateVals, data.points])

  const stateLabels = useMemo<FeatureCollection>(() => ({
    type: 'FeatureCollection',
    features: Object.entries(data.points.states).map(([name, coordinates]) => ({
      type: 'Feature', geometry: { type: 'Point', coordinates }, properties: { name },
    })),
  }), [data.points.states])

  const legendTitle = legislators
    ? `MPs/MLAs with declared cases (ADR ${adrYear})`
    : `${effective.offender === 'all' ? data.cats[effective.cat]?.label : 'Rape, by offender'}, by ${districtLevel && mode === 'fill' ? 'district' : 'state'}`

  const detailsRef = useRef<HTMLElement>(null)
  const showDetails = () => detailsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  const current = district ? districtVals[district] : state ? stateVals[state] : undefined
  const placeName = district ? districtName(district).split(',')[0] : state

  const filtersPanel = (
    <Filters
      data={data}
      filters={filters}
      setFilters={setFilters}
      offenders={offenders}
      mode={mode}
      setMode={setMode}
      showDistricts={showDistricts}
      setShowDistricts={setShowDistricts}
      playing={playing}
      setPlaying={setPlaying}
      stateYears={stateYears}
      districtYears={districtYears}
    />
  )

  return (
    <TooltipProvider>
      <div className="flex h-full flex-col bg-background text-foreground">
        <div className="slogan-banner px-4 py-2 text-center sm:py-3" role="banner">
          <p className="slogan-text leading-tight font-black whitespace-nowrap uppercase">
            Educate <span aria-hidden className="opacity-60">·</span> Agitate <span aria-hidden className="opacity-60">·</span> Organise
          </p>
        </div>
        <header className="flex items-center justify-between gap-3 border-b px-4 py-2.5 sm:py-3">
          <div className="min-w-0">
            <h1 className="text-base font-semibold tracking-tight text-balance sm:truncate sm:text-lg">Crimes Against Women in India</h1>
            <p className="text-xs text-muted-foreground sm:truncate">
              Cases registered by police (NCRB), by state and district, 2001–2024 · By {AUTHOR_ROLE}
            </p>
          </div>
          <Button variant="ghost" size="icon" className="shrink-0" onClick={toggle} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}>
            {theme === 'dark' ? <Sun /> : <Moon />}
          </Button>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto lg:grid lg:grid-cols-[300px_minmax(0,1fr)_380px] lg:overflow-hidden">
          {isMobile ? (
            <MobileBar
              year={filters.year}
              years={legislators ? adrMapYears(data) : stateYears}
              label={legislators ? `ADR ${adrYear} report` : legendTitle.split(', by ')[0]}
              playing={playing}
              setPlaying={setPlaying}
              setYear={(y) => setFilters({ year: y })}
              filtersPanel={filtersPanel}
            />
          ) : (
            <aside className="overflow-y-auto border-r p-4" aria-label="Filters">
              {filtersPanel}
            </aside>
          )}

          <main className="relative h-[58svh] min-h-[340px] lg:h-auto">
            <MapView
              states={geo.states}
              districts={geo.districts}
              india={geo.india}
              stateLabels={stateLabels}
              theme={theme}
              mode={mode}
              cooperative={isMobile}
              showDistricts={showDistricts && hasDistrictData}
              selectedState={state}
              selectedDistrict={district}
              stateStyles={stateStyles}
              districtStyles={hasDistrictData ? districtStyles : {}}
              heatPoints={heatPoints}
              onSelectState={selectState}
              onSelectDistrict={setDistrict}
            />
            {state && !isMobile && (
              <Button size="sm" variant="secondary" className="absolute top-3 left-3 shadow" onClick={() => selectState(null)}>
                Back to India
              </Button>
            )}
            {state && isMobile && (
              <div className="absolute top-2 right-12 left-2 flex items-center gap-2 rounded-lg border bg-background/95 p-2 shadow-sm backdrop-blur">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{placeName}</p>
                  <p className="truncate text-xs text-muted-foreground tabular-nums">{fmt(current)}</p>
                </div>
                <Button size="sm" variant="outline" onClick={() => selectState(null)}>India</Button>
                <Button size="sm" onClick={showDetails}>Details</Button>
              </div>
            )}
            {isMobile && !state && (
              <p className="pointer-events-none absolute top-2 left-2 rounded-md bg-background/90 px-2 py-1 text-[11px] text-muted-foreground shadow-sm">
                Tap a state to see its districts
              </p>
            )}
            <div className="absolute right-2 bottom-7 left-2 rounded-lg border bg-background/90 p-2 shadow-sm backdrop-blur sm:right-auto sm:bottom-8 sm:left-3 sm:w-80 sm:p-3">
              <Legend
                title={legendTitle}
                breaks={districtLevel && mode === 'fill' ? districtBreaks : stateBreaks}
                ramp={ramp}
                metric={legislators ? 'count' : filters.metric}
                noData={noData}
                heat={mode === 'heat'}
                unit={legislators ? 'MPs/MLAs' : undefined}
                compact={isMobile}
              />
              {state && !hasDistrictData && !legislators && (
                <p className="mt-2 text-[11px] text-muted-foreground">No district data for this filter and year, so the whole state is shown.</p>
              )}
            </div>
          </main>

          <aside ref={detailsRef} className="scroll-mt-14 p-4 lg:overflow-y-auto lg:border-l" aria-label="Details">
            <SidePanel
              data={data}
              filters={effective}
              setFilters={setFilters}
              state={state}
              district={district}
              districtName={districtName}
              districtsOf={districtsOf}
              stateNames={stateNames}
              onSelectState={selectState}
              onSelectDistrict={setDistrict}
            />
            <footer className="mt-8 border-t pt-4 text-[11px] leading-relaxed text-muted-foreground">
              <p className="mb-2 text-xs text-foreground">
                Compiled by {AUTHOR_ROLE}.
              </p>
              <p className="mb-4">
                Figures are cases registered by police, so they reflect reporting and registration as well as crime.
                State boundaries are based on Survey of India maps. District boundaries are GADM (c. 2010); newer
                districts are counted in their parent district.
              </p>
              <Sources />
            </footer>
          </aside>
        </div>
      </div>
    </TooltipProvider>
  )
}

/** Phones and tablets: a sticky bar with the year controls and a button that opens all filters. */
function MobileBar(props: {
  year: number
  years: number[]
  label: string
  playing: boolean
  setPlaying: (v: boolean) => void
  setYear: (y: number) => void
  filtersPanel: React.ReactNode
}) {
  const i = props.years.indexOf(props.year)
  const prev = i > 0 ? props.years[i - 1] : undefined
  const next = i >= 0 && i < props.years.length - 1 ? props.years[i + 1] : undefined
  return (
    <div className="sticky top-0 z-20 flex items-center gap-2 border-b bg-background/95 px-3 py-2 backdrop-blur">
      <Button size="icon" variant="outline" aria-label={props.playing ? 'Pause year animation' : 'Play through years'} onClick={() => props.setPlaying(!props.playing)}>
        {props.playing ? <Pause /> : <Play />}
      </Button>
      <div className="flex items-center">
        <Button size="icon" variant="ghost" aria-label="Previous year" disabled={prev === undefined} onClick={() => prev !== undefined && props.setYear(prev)}>
          <ChevronLeft />
        </Button>
        <span className="w-12 text-center text-lg font-semibold tabular-nums">{props.year}</span>
        <Button size="icon" variant="ghost" aria-label="Next year" disabled={next === undefined} onClick={() => next !== undefined && props.setYear(next)}>
          <ChevronRight />
        </Button>
      </div>
      <Sheet>
        <SheetTrigger asChild>
          <Button variant="outline" className="ml-auto min-w-0 flex-1 justify-start gap-2" aria-label="Open filters">
            <SlidersHorizontal className="shrink-0" />
            <span className="truncate">{props.label}</span>
          </Button>
        </SheetTrigger>
        <SheetContent side="bottom" className="max-h-[85svh] overflow-y-auto rounded-t-2xl px-4 pb-[max(1.5rem,env(safe-area-inset-bottom))]">
          <SheetHeader className="px-0">
            <SheetTitle>Filters</SheetTitle>
            <SheetDescription>Changes apply to the map straight away.</SheetDescription>
          </SheetHeader>
          {props.filtersPanel}
          <SheetClose asChild>
            <Button className="mt-6 w-full">Show map</Button>
          </SheetClose>
        </SheetContent>
      </Sheet>
    </div>
  )
}

function useIsMobile(query = '(max-width: 1023px)') {
  const [match, setMatch] = useState(() => window.matchMedia(query).matches)
  useEffect(() => {
    const m = window.matchMedia(query)
    const on = () => setMatch(m.matches)
    m.addEventListener('change', on)
    return () => m.removeEventListener('change', on)
  }, [query])
  return match
}

const defined = (o: Record<string, number | undefined>) => Object.values(o).filter((v): v is number => v !== undefined)
