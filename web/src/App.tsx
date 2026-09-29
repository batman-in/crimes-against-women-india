import { Moon, Sun } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { feature } from 'topojson-client'
import type { Feature, FeatureCollection, Geometry, Point } from 'geojson'
import type { GeometryCollection, Topology } from 'topojson-specification'
import { BrandLockup, BrandMark, BrandTitle } from '@/components/Brand'
import { Filters } from '@/components/Filters'
import { Legend } from '@/components/Legend'
import { MapView, type AreaStyle, type MapMode } from '@/components/MapView'
import { SidePanel } from '@/components/SidePanel'
import { BackToIndia, CrimeChips, FiltersSheet, FitIndiaButton, MapControls, MobileFilterBar, SummaryCard, YearDock } from '@/components/mobile/MobileUI'
import { ShareFab } from '@/components/ShareMenu'
import { Sources } from '@/components/Sources'
import { VisitCount } from '@/components/VisitCount'
import { Button } from '@/components/ui/button'
import { TooltipProvider } from '@/components/ui/tooltip'
import { adrByState, adrMapYears, adrReports, adrYearFor } from '@/lib/adr'
import {
  OFFENDER_LABELS, districtValue, formatValue, loadData, metricUnit, nationalValue, offenderOptions, stateValue, yearsWithData,
  type DashboardData, type Filters as F,
} from '@/lib/data'
import { NO_DATA, RAMP_DARK, RAMP_LIGHT, colorFor, quantileBreaks } from '@/lib/scale'

const AUTHOR_ROLE = 'a concerned citizen'

interface Geo {
  states: FeatureCollection
  districts: FeatureCollection
  india: FeatureCollection
  indiaMask: Geometry // simplified India polygon: basemap labels outside it are hidden
}

async function loadGeo(): Promise<Geo> {
  const base = import.meta.env.BASE_URL
  const [s, d, i] = await Promise.all(
    ['states', 'districts', 'india'].map((n) => fetch(`${base}data/${n}.topo.json`).then((r) => r.json() as Promise<Topology>)),
  )
  const mask = await fetch(`${base}data/india_mask.json`).then((r) => r.json())
  return {
    indiaMask: (mask.type === 'GeometryCollection' ? mask.geometries[0] : mask.type === 'FeatureCollection' ? mask.features[0].geometry : mask) as Geometry,
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
  if (!data || !geo)
    return (
      <div className="grid h-full place-items-center text-sm text-muted-foreground">
        <div className="flex flex-col items-center gap-3">
          <BrandMark className="h-24 animate-pulse" />
          Loading NCRB data…
        </div>
      </div>
    )
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
  const [fitToken, setFitToken] = useState(0)
  const showIndia = useCallback(() => { setState(null); setDistrict(null); setFitToken((t) => t + 1) }, [])

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

  // Heatmap follows the same level as the filled map: state centres, or district centres when
  // districts are switched on (all of India) or a state is open (that state's districts only).
  const heatLevel: 'state' | 'district' = districtLevel ? 'district' : 'state'
  const heatPoints = useMemo<FeatureCollection>(() => {
    let vals: Record<string, number | undefined> = stateVals
    if (heatLevel === 'district') {
      vals = districtVals
      if (state && !showDistricts) {
        const inState = new Set(districtsOf(state))
        vals = Object.fromEntries(Object.entries(districtVals).filter(([g]) => inState.has(g)))
      }
    }
    const coords = heatLevel === 'district' ? data.points.districts : data.points.states
    const max = Math.max(...defined(vals), 1)
    const features: Feature<Point>[] = []
    for (const [id, v] of Object.entries(vals)) {
      if (v === undefined || !v || !coords[id]) continue
      features.push({ type: 'Feature', geometry: { type: 'Point', coordinates: coords[id] }, properties: { w: Math.sqrt(v / max) } })
    }
    return { type: 'FeatureCollection', features }
  }, [heatLevel, districtVals, stateVals, data.points, state, showDistricts, districtsOf])

  const stateLabels = useMemo<FeatureCollection>(() => ({
    type: 'FeatureCollection',
    features: Object.entries(data.points.states).map(([name, coordinates]) => ({
      type: 'Feature', geometry: { type: 'Point', coordinates }, properties: { name },
    })),
  }), [data.points.states])

  const legendTitle = legislators
    ? `MPs/MLAs with declared cases (ADR ${adrYear})`
    : `${effective.offender === 'all' ? data.cats[effective.cat]?.label : 'Rape, by offender'}, by ${districtLevel ? 'district' : 'state'}`

  useNetlifyBadgeInFooter(isMobile)

  const detailsRef = useRef<HTMLElement>(null)
  const showDetails = () => detailsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  const [sheetOpen, setSheetOpen] = useState(false)

  const filtersPanel = (variant: 'desktop' | 'mobile') => (
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
      variant={variant}
    />
  )

  const mapView = (
    <MapView
      states={geo.states}
      districts={geo.districts}
      india={geo.india}
      labelMask={geo.indiaMask}
      stateLabels={stateLabels}
      theme={theme}
      mode={mode}
      touch={isMobile}
      fitToken={fitToken}
      showDistricts={showDistricts && hasDistrictData}
      selectedState={state}
      selectedDistrict={district}
      stateStyles={stateStyles}
      districtStyles={hasDistrictData ? districtStyles : {}}
      heatPoints={heatPoints}
      heatLevel={heatLevel}
      onSelectState={selectState}
      onSelectDistrict={setDistrict}
    />
  )

  const legend = (
    <div
      className={
        isMobile
          ? 'map-glass absolute bottom-2 left-2 w-[60%] max-w-[230px] rounded-md px-2 py-1.5'
          : 'absolute right-2 bottom-7 left-2 rounded-lg border bg-background/90 p-2 shadow-sm backdrop-blur sm:right-auto sm:bottom-8 sm:left-3 sm:w-80 sm:p-3'
      }
    >
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
        <p className={isMobile ? 'mt-1 text-[9px] leading-tight opacity-75' : 'mt-2 text-[11px] text-muted-foreground'}>
          No district data for this filter and year, so the whole state is shown.
        </p>
      )}
    </div>
  )

  const details = (
    <>
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
        hideHeadline={isMobile}
      />
      <footer className="mt-8 border-t pt-4 text-[11px] leading-relaxed text-muted-foreground">
        <BrandLockup className="mb-3 h-28" />
        <p className="mb-2 text-xs text-foreground">
          Compiled by {AUTHOR_ROLE}.
        </p>
        <p className="mb-4">
          Figures are cases registered by police, so they reflect reporting and registration as well as crime.
          State boundaries are based on Survey of India maps. District boundaries are GADM (c. 2010); newer
          districts are counted in their parent district.
        </p>
        <Sources />
        <div id="netlify-badge-slot" />
      </footer>
    </>
  )

  const slogan = (
    <div className="slogan-banner px-4 py-2 text-center sm:py-3" role="banner">
      <p className="slogan-text leading-tight font-black whitespace-nowrap uppercase">
        Educate <span aria-hidden className="opacity-60">·</span> Agitate <span aria-hidden className="opacity-60">·</span> Organise
      </p>
    </div>
  )
  const themeButton = (
    <div className="flex shrink-0 items-center gap-0.5">
      <VisitCount />
      <Button variant="ghost" size="icon" className="shrink-0" onClick={toggle} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}>
        {theme === 'dark' ? <Sun /> : <Moon />}
      </Button>
    </div>
  )

  // Headline for the summary card and the share image: the selected place, this year vs the
  // previous year with data
  const valueAt = (fy: F) =>
    district ? districtValue(data, district, fy) : state ? stateValue(data, state, fy) : nationalValue(data, fy)
  const prevYear = [...stateYears].reverse().find((y) => y < filters.year)
  const now = valueAt(effective)
  const before = prevYear !== undefined ? valueAt({ ...effective, year: prevYear }) : undefined
  const change = now.value !== undefined && before?.value ? (now.value - before.value) / before.value : undefined
  const adrNow = legislators && adrYear ? adrByState(data, adrYear) : {}
  const adrTotal = legislators ? (adrReports(data).find((r) => r.year === adrYear)?.houses ?? []).reduce((t, h) => t + h.count, 0) : 0
  const what = effective.offender === 'all' ? data.cats[effective.cat]?.label : `Rape by ${OFFENDER_LABELS[effective.offender]?.toLowerCase() ?? effective.offender}`

  const place = district ? districtName(district) : state ?? 'India'
  const secondaryText = legislators
    ? 'Pending cases, not convictions'
    : filters.metric === 'rate'
      ? now.count !== undefined ? `${now.count.toLocaleString('en-IN')} cases` : undefined
      : now.rate !== undefined ? `${formatValue(now.rate, 'rate')} per lakh women` : undefined
  const shareValue = legislators ? String(state ? adrNow[state]?.total ?? 0 : adrTotal) : formatValue(now.value, filters.metric)
  const shareText = legislators
    ? `${place}: ${shareValue} sitting MPs/MLAs have declared cases of crimes against women (ADR ${adrYear ?? ''}). See the map on Project Durga:`
    : now.value !== undefined
      ? `${place}, ${filters.year}: ${shareValue} ${metricUnit(filters.metric)} (${what?.toLowerCase()}). See the map on Project Durga:`
      : `Crimes against women in ${place}, by state and district. See the map on Project Durga:`
  const shareFab = (
    <ShareFab
      shareText={shareText}
      fileName={`project-durga-${place}-${legislators ? `adr-${adrYear ?? ''}` : `${what ?? ''}-${filters.year}`}`}
      mobile={isMobile}
    />
  )

  if (isMobile) {
    const crumbs = [
      { label: 'India', onClick: state ? showIndia : undefined },
      ...(state ? [{ label: state, onClick: district ? () => setDistrict(null) : undefined }] : []),
      ...(district ? [{ label: districtName(district).split(',')[0] }] : []),
    ]
    const activeCount = filters.offender !== 'all' ? 1 : 0 // map style and districts are on the map itself
    const pill = filters.offender !== 'all'
      ? { label: legislators ? 'MPs/MLAs (ADR)' : OFFENDER_LABELS[filters.offender] ?? filters.offender, onClear: () => setFilters({ offender: 'all' }) }
      : undefined

    return (
      <TooltipProvider>
        <div className="m-ui flex h-full flex-col">
          {slogan}
          <header className="flex items-center justify-between gap-3 border-b border-[var(--m-border)] px-4 py-2">
            <div className="min-w-0">
              <BrandTitle size="sm" />
              <p className="sr-only">NCRB police records · 2001–2024</p>
            </div>
            {themeButton}
          </header>

          <div className="min-h-0 flex-1 overflow-y-auto pb-24">
            <MobileFilterBar
              chips={
                <CrimeChips
                  data={data}
                  cat={effective.cat}
                  setCat={(k) => setFilters({ cat: k })}
                  disabled={filters.offender !== 'all'}
                  onMore={() => setSheetOpen(true)}
                />
              }
              metric={filters.metric}
              setMetric={(m) => setFilters({ metric: m })}
              metricDisabled={legislators}
              activeCount={activeCount}
              onOpenFilters={() => setSheetOpen(true)}
              pill={pill}
            />

            {legislators ? (
              <SummaryCard
                crumbs={crumbs}
                subtitle={`Sitting MPs/MLAs with declared cases · ADR ${adrYear ?? ''}`}
                value={String(state ? adrNow[state]?.total ?? 0 : adrTotal)}
                unit="legislators"
                secondary="Pending cases, not convictions"
                onDetails={showDetails}
              />
            ) : (
              <SummaryCard
                crumbs={crumbs}
                subtitle={`${what} · ${filters.year}`}
                value={formatValue(now.value, filters.metric)}
                unit={now.value !== undefined ? metricUnit(filters.metric) : undefined}
                secondary={secondaryText}
                change={change}
                prevYear={prevYear}
                onDetails={showDetails}
                note={now.via ? `Reported for ${now.via} in this year.` : undefined}
              />
            )}

            <main className="relative h-[52svh] min-h-[320px] border-y border-[var(--m-border)]">
              {mapView}
              <div className="absolute top-2 left-2 flex flex-col items-start gap-1.5">
                {state && <BackToIndia onClick={showIndia} />}
                <MapControls
                  mode={mode}
                  setMode={setMode}
                  showDistricts={showDistricts}
                  setShowDistricts={setShowDistricts}
                  districtsAvailable={districtYears.length > 0}
                />
                {!state && (
                  <p className="map-glass pointer-events-none rounded-full px-2.5 py-0.5 text-[11px]">
                    Tap a state to see its districts
                  </p>
                )}
              </div>
              <div className="absolute top-[78px] right-[10px]">
                <FitIndiaButton onClick={showIndia} />
              </div>
              {legend}
            </main>

            <aside ref={detailsRef} className="scroll-mt-28 p-4" aria-label="Details">
              {details}
            </aside>
          </div>

          <YearDock
            years={stateYears}
            allYears={data.years}
            year={filters.year}
            setYear={(y) => setFilters({ year: y })}
            playing={playing}
            setPlaying={setPlaying}
            reportYears={legislators ? adrMapYears(data) : undefined}
          />
          <FiltersSheet open={sheetOpen} setOpen={setSheetOpen}>
            {filtersPanel('mobile')}
          </FiltersSheet>
          {shareFab}
        </div>
      </TooltipProvider>
    )
  }

  return (
    <TooltipProvider>
      <div className="flex h-full flex-col bg-background text-foreground">
        {slogan}
        <header className="flex items-center justify-between gap-3 border-b px-4 py-2">
          <div className="flex min-w-0 items-center gap-4">
            <BrandTitle />
            <p className="min-w-0 border-l pl-4 text-xs text-muted-foreground">
              Crimes against women in India: cases registered by police (NCRB), by state and district, 2001–2024 · By {AUTHOR_ROLE}
            </p>
          </div>
          {themeButton}
        </header>

        <div className="min-h-0 flex-1 lg:grid lg:grid-cols-[300px_minmax(0,1fr)_380px] lg:overflow-hidden">
          <aside className="overflow-y-auto border-r p-4" aria-label="Filters">
            {filtersPanel('desktop')}
          </aside>

          <main className="relative h-auto">
            {mapView}
            {state && (
              <Button size="sm" variant="secondary" className="absolute top-3 left-3 shadow" onClick={() => selectState(null)}>
                Back to India
              </Button>
            )}
            {legend}
          </main>

          <aside ref={detailsRef} className="p-4 lg:overflow-y-auto lg:border-l" aria-label="Details">
            {details}
          </aside>
        </div>
        {shareFab}
      </div>
    </TooltipProvider>
  )
}

/** Move Netlify's floating badge (added to <body> by the host) into the footer, so it covers nothing. */
function useNetlifyBadgeInFooter(layoutKey: unknown) {
  useEffect(() => {
    const move = () => {
      const badge = document.getElementById('nl-badge-frame')
      const slot = document.getElementById('netlify-badge-slot')
      if (badge && slot && badge.parentElement !== slot) slot.appendChild(badge)
    }
    move()
    const obs = new MutationObserver(move)
    obs.observe(document.body, { childList: true, subtree: true })
    return () => obs.disconnect()
  }, [layoutKey])
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
