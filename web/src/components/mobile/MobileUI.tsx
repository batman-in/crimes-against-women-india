// Mobile (< 1024px) building blocks. Principles:
// - the main filters stay visible (crime chips, measure, year); rarer ones sit behind "Filters"
// - the answer comes first (summary card), the year control sits in the thumb zone (bottom dock)
// - purple marks everything you can act on; the red scale is reserved for the data itself
import { ArrowDownRight, ArrowLeft, ArrowUpRight, ChevronDown, ChevronLeft, ChevronRight, Maximize2, Pause, Play, SlidersHorizontal, X } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Slider } from '@/components/ui/slider'
import type { DashboardData, Metric } from '@/lib/data'

/** Most-used crime types, in order of how often people look for them. Everything else is under "More". */
export const QUICK_CATS = ['total', 'rape', 'cruelty', 'assault', 'insult', 'dowry', 'kidnap', 'pocso_girls']
const SHORT_LABEL: Record<string, string> = {
  total: 'All crimes',
  pocso_girls: 'Minor girls (POCSO)',
  kidnap: 'Kidnapping',
}

const chipBase =
  'inline-flex h-10 shrink-0 snap-start items-center gap-1.5 rounded-full border px-4 text-sm font-medium whitespace-nowrap transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--brand)] disabled:opacity-40'
const chipOff = 'border-[var(--m-border)] bg-[var(--m-surface)] text-[var(--m-ink)] active:bg-[var(--brand-soft)]'
const chipOn = 'border-transparent bg-[var(--brand)] text-[var(--brand-fg)] shadow-sm'

export function CrimeChips(props: {
  data: DashboardData
  cat: string
  setCat: (k: string) => void
  disabled?: boolean
  onMore: () => void
}) {
  const { data, cat } = props
  const quick = QUICK_CATS.filter((k) => data.coverage[k])
  // An active type picked from "More" shows first, so the current choice is always visible
  const chips = quick.includes(cat) || !data.cats[cat] ? quick : [cat, ...quick]
  const rowRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    rowRef.current?.querySelector<HTMLElement>('[aria-pressed="true"]')?.scrollIntoView({ block: 'nearest', inline: 'nearest' })
  }, [cat])
  return (
    <div className="relative">
      <div
        ref={rowRef}
        className="no-scrollbar -mx-3 flex snap-x gap-2 overflow-x-auto px-3 pb-0.5"
        role="toolbar"
        aria-label="Crime type"
      >
        {chips.map((k) => (
          <button
            key={k}
            type="button"
            aria-pressed={cat === k}
            disabled={props.disabled}
            onClick={() => props.setCat(k)}
            className={`${chipBase} ${cat === k ? chipOn : chipOff}`}
          >
            {SHORT_LABEL[k] ?? data.cats[k].label}
          </button>
        ))}
        <button type="button" onClick={props.onMore} disabled={props.disabled} className={`${chipBase} ${chipOff}`}>
          More types <ChevronDown className="size-4" />
        </button>
      </div>
      {/* fade hints that the row scrolls sideways */}
      <div aria-hidden className="pointer-events-none absolute inset-y-0 -right-3 w-8 bg-gradient-to-l from-[var(--m-bg)] to-transparent" />
    </div>
  )
}

export function MobileFilterBar(props: {
  chips: React.ReactNode
  metric: Metric
  setMetric: (m: Metric) => void
  metricDisabled?: boolean
  activeCount: number
  onOpenFilters: () => void
  pill?: { label: string; onClear: () => void }
}) {
  return (
    <div className="sticky top-0 z-20 flex flex-col gap-2 border-b border-[var(--m-border)] bg-[var(--m-bg)]/95 px-3 pt-2.5 pb-2.5 backdrop-blur">
      {props.chips}
      <div className="flex items-center gap-2">
        <div role="radiogroup" aria-label="Measure" className="flex h-10 rounded-full border border-[var(--m-border)] bg-[var(--m-surface)] p-0.5">
          {(['count', 'rate'] as Metric[]).map((m) => (
            <button
              key={m}
              type="button"
              role="radio"
              aria-checked={props.metric === m}
              disabled={props.metricDisabled}
              onClick={() => props.setMetric(m)}
              className={`rounded-full px-3.5 text-sm font-medium whitespace-nowrap transition-colors disabled:opacity-40 ${
                props.metric === m ? 'bg-[var(--brand)] text-[var(--brand-fg)]' : 'text-[var(--m-ink-soft)]'
              }`}
            >
              {m === 'count' ? 'Cases' : 'Rate / lakh'}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={props.onOpenFilters}
          className="ml-auto inline-flex h-10 shrink-0 items-center gap-2 rounded-full border border-[var(--brand)] px-4 text-sm font-semibold text-[var(--brand-ink)] active:bg-[var(--brand-soft)]"
        >
          <SlidersHorizontal className="size-4" />
          Filters
          {props.activeCount > 0 && (
            <span className="grid size-5 place-items-center rounded-full bg-[var(--brand)] text-[11px] text-[var(--brand-fg)] tabular-nums">
              {props.activeCount}
            </span>
          )}
        </button>
      </div>
      {props.pill && (
        <div className="flex items-center gap-2 rounded-2xl bg-[var(--brand-soft)] py-1 pr-1 pl-3 text-sm text-[var(--brand-ink)]">
          <span className="min-w-0 flex-1 truncate">
            <span className="font-medium">Showing:</span> {props.pill.label}
          </span>
          <button
            type="button"
            onClick={props.pill.onClear}
            aria-label={`Remove filter: ${props.pill.label}`}
            className="inline-flex h-9 shrink-0 items-center gap-1 rounded-full px-3 font-medium active:bg-[var(--brand)]/15"
          >
            <X className="size-4" /> Clear
          </button>
        </div>
      )}
    </div>
  )
}

export function SummaryCard(props: {
  crumbs: { label: string; onClick?: () => void }[]
  subtitle: string
  value: string
  unit?: string
  secondary?: string
  change?: number // fraction, e.g. -0.024
  prevYear?: number
  onDetails: () => void
  note?: string
}) {
  const up = props.change !== undefined && props.change > 0
  return (
    <section className="flex flex-col gap-1 px-4 pt-3 pb-3" aria-live="polite">
      <nav aria-label="Location" className="flex flex-wrap items-center gap-1 text-sm">
        {props.crumbs.map((c, i) => (
          <span key={c.label} className="flex items-center gap-1">
            {i > 0 && <ChevronRight className="size-3.5 text-[var(--m-ink-soft)]" />}
            {c.onClick ? (
              <button type="button" onClick={c.onClick} className="min-h-8 font-medium text-[var(--brand-ink)] underline decoration-[var(--brand)]/40 underline-offset-4">
                {c.label}
              </button>
            ) : (
              <span className="font-semibold text-[var(--m-ink)]">{c.label}</span>
            )}
          </span>
        ))}
      </nav>
      <p className="text-sm text-[var(--m-ink-soft)]">{props.subtitle}</p>
      <div className="flex items-end justify-between gap-3">
        <div className="min-w-0">
          <p className="flex flex-wrap items-baseline gap-x-2">
            <span className="text-4xl leading-none font-bold tracking-tight text-[var(--m-ink)] tabular-nums">{props.value}</span>
            {props.unit && <span className="text-sm text-[var(--m-ink-soft)]">{props.unit}</span>}
          </p>
          <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs">
            {props.change !== undefined && Number.isFinite(props.change) && (
              <span
                className={`inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 font-semibold tabular-nums ${
                  up ? 'bg-[var(--bad-soft)] text-[var(--bad)]' : 'bg-[var(--good-soft)] text-[var(--good)]'
                }`}
              >
                {up ? <ArrowUpRight className="size-3.5" /> : <ArrowDownRight className="size-3.5" />}
                {up ? '+' : ''}
                {(props.change * 100).toFixed(1)}% vs {props.prevYear}
              </span>
            )}
            {props.secondary && <span className="text-[var(--m-ink-soft)] tabular-nums">{props.secondary}</span>}
          </div>
        </div>
        <button
          type="button"
          onClick={props.onDetails}
          className="inline-flex h-10 shrink-0 items-center gap-1 rounded-full bg-[var(--brand-soft)] px-4 text-sm font-semibold text-[var(--brand-ink)] active:opacity-80"
        >
          Details <ChevronDown className="size-4" />
        </button>
      </div>
      {props.note && <p className="mt-1 text-xs text-[var(--m-ink-soft)]">{props.note}</p>}
    </section>
  )
}

/** Bottom dock in the thumb zone: play, step back/forward, the year, and a scrubber. */
export function YearDock(props: {
  years: number[] // years with data for the current filter
  allYears: number[]
  year: number
  setYear: (y: number) => void
  playing: boolean
  setPlaying: (v: boolean) => void
  reportYears?: number[] // ADR mode: discrete report years instead of a scrubber
}) {
  const ys = props.reportYears ?? props.years
  const i = ys.indexOf(props.year)
  const prev = i > 0 ? ys[i - 1] : undefined
  const next = i >= 0 && i < ys.length - 1 ? ys[i + 1] : undefined
  const iconBtn =
    'grid size-11 shrink-0 place-items-center rounded-full text-[var(--m-ink)] active:bg-[var(--brand-soft)] disabled:opacity-30'
  return (
    <div className="fixed inset-x-0 bottom-0 z-30 border-t border-[var(--m-border)] bg-[var(--m-bg)]/95 px-2 pt-1.5 pb-[max(0.5rem,env(safe-area-inset-bottom))] shadow-[0_-4px_16px_rgb(0_0_0/0.06)] backdrop-blur">
      <div className="mx-auto flex max-w-xl items-center gap-1">
        <button
          type="button"
          aria-label={props.playing ? 'Pause year animation' : 'Play through the years'}
          onClick={() => props.setPlaying(!props.playing)}
          className="grid size-11 shrink-0 place-items-center rounded-full bg-[var(--brand)] text-[var(--brand-fg)] shadow-sm active:opacity-90"
        >
          {props.playing ? <Pause className="size-5" /> : <Play className="size-5 translate-x-px" />}
        </button>
        {!props.reportYears && (
          <button type="button" aria-label="Previous year" disabled={prev === undefined} onClick={() => prev !== undefined && props.setYear(prev)} className={iconBtn}>
            <ChevronLeft className="size-5" />
          </button>
        )}
        <span className="w-14 text-center text-xl font-bold text-[var(--m-ink)] tabular-nums" aria-live="polite">{props.year}</span>
        {!props.reportYears && (
          <button type="button" aria-label="Next year" disabled={next === undefined} onClick={() => next !== undefined && props.setYear(next)} className={iconBtn}>
            <ChevronRight className="size-5" />
          </button>
        )}
        {props.reportYears ? (
          <div className="ml-1 flex min-w-0 flex-1 gap-1 overflow-x-auto no-scrollbar" role="radiogroup" aria-label="ADR report">
            {props.reportYears.map((y) => (
              <button
                key={y}
                type="button"
                role="radio"
                aria-checked={y === props.year}
                onClick={() => props.setYear(y)}
                className={`h-9 shrink-0 rounded-full px-3 text-sm font-medium tabular-nums ${
                  y === props.year ? 'bg-[var(--brand)] text-[var(--brand-fg)]' : 'border border-[var(--m-border)] text-[var(--m-ink)]'
                }`}
              >
                {y}
              </button>
            ))}
          </div>
        ) : (
          <div className="ml-2 min-w-0 flex-1 pr-2">
            <Slider
              min={props.allYears[0]}
              max={props.allYears[props.allYears.length - 1]}
              step={1}
              value={[props.year]}
              onValueChange={([y]) => props.setYear(y)}
              aria-label="Year"
              className="brand-slider py-3"
            />
            <div className="flex justify-between text-[10px] text-[var(--m-ink-soft)] tabular-nums">
              <span>{props.allYears[0]}</span>
              <span>{props.allYears[props.allYears.length - 1]}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export function FiltersSheet(props: { open: boolean; setOpen: (v: boolean) => void; children: React.ReactNode }) {
  return (
    <Sheet open={props.open} onOpenChange={props.setOpen}>
      <SheetContent side="bottom" className="m-ui max-h-[88svh] overflow-y-auto rounded-t-3xl border-0 bg-[var(--m-bg)] px-4 pb-[max(1.5rem,env(safe-area-inset-bottom))]">
        <div aria-hidden className="mx-auto mt-1 h-1.5 w-10 rounded-full bg-[var(--m-border)]" />
        <SheetHeader className="px-0">
          <SheetTitle>Filters</SheetTitle>
          <SheetDescription>Changes apply to the map straight away.</SheetDescription>
        </SheetHeader>
        {props.children}
        <button
          type="button"
          onClick={() => props.setOpen(false)}
          className="mt-6 h-12 w-full rounded-full bg-[var(--brand)] text-base font-semibold text-[var(--brand-fg)] shadow-sm active:opacity-90"
        >
          Show results
        </button>
      </SheetContent>
    </Sheet>
  )
}

/** On-map controls: how the map is drawn, and whether districts are shown across India. */
export function MapControls(props: {
  mode: 'fill' | 'heat'
  setMode: (m: 'fill' | 'heat') => void
  showDistricts: boolean
  setShowDistricts: (v: boolean) => void
  districtsAvailable: boolean
}) {
  const seg = (on: boolean) =>
    `h-8 rounded-full px-3 text-xs font-semibold whitespace-nowrap transition-colors ${
      on ? 'bg-[var(--brand)]/75 text-[var(--brand-fg)]' : 'text-[var(--m-ink)]'
    }`
  return (
    <div className="flex items-center gap-1.5">
      <div role="radiogroup" aria-label="Map style" className="map-glass flex rounded-full p-0.5">
        <button type="button" role="radio" aria-checked={props.mode === 'fill'} onClick={() => props.setMode('fill')} className={seg(props.mode === 'fill')}>
          Filled
        </button>
        <button type="button" role="radio" aria-checked={props.mode === 'heat'} onClick={() => props.setMode('heat')} className={seg(props.mode === 'heat')}>
          Heatmap
        </button>
      </div>
      <button
        type="button"
        aria-pressed={props.showDistricts}
        disabled={!props.districtsAvailable}
        onClick={() => props.setShowDistricts(!props.showDistricts)}
        title={props.districtsAvailable ? 'Show districts across India' : 'No district data for this filter'}
        className={`h-9 rounded-full px-3 text-xs font-semibold whitespace-nowrap transition-colors disabled:opacity-40 ${
          props.showDistricts ? 'map-glass-on' : 'map-glass text-[var(--m-ink)]'
        }`}
      >
        Districts
      </button>
    </div>
  )
}

/** Shown on the map while a state or district is open: one tap back to the whole country. */
export function BackToIndia(props: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={props.onClick}
      className="map-glass-on inline-flex h-9 items-center gap-1.5 rounded-full pr-3.5 pl-3 text-sm font-semibold active:opacity-90"
    >
      <ArrowLeft className="size-4" /> India
    </button>
  )
}

/** Sits under the zoom buttons: re-centres the map on all of India from wherever it was dragged. */
export function FitIndiaButton(props: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={props.onClick}
      aria-label="Show all of India"
      title="Show all of India"
      className="map-glass grid size-[29px] place-items-center rounded-[4px] text-[var(--m-ink)]"
    >
      <Maximize2 className="size-4" />
    </button>
  )
}
