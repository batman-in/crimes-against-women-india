import { Pause, Play } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectSeparator, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { adrMapYears } from '@/lib/adr'
import { OFFENDER_LABELS, describeYears, type DashboardData, type Filters as F, type Metric } from '@/lib/data'
import type { MapMode } from './MapView'

interface Props {
  data: DashboardData
  filters: F
  setFilters: (f: Partial<F>) => void
  offenders: string[]
  mode: MapMode
  setMode: (m: MapMode) => void
  showDistricts: boolean
  setShowDistricts: (v: boolean) => void
  playing: boolean
  setPlaying: (v: boolean) => void
  stateYears: number[]
  districtYears: number[]
  /** mobile: year and measure live in the bar/dock; crime types show as tappable chips */
  variant?: 'desktop' | 'mobile'
}

export function Filters(p: Props) {
  const { data, filters: f } = p
  const minY = data.years[0]
  const maxY = data.years[data.years.length - 1]
  const legislators = f.offender === 'legislators'
  const offenderMode = f.offender !== 'all' && !legislators
  const cat = data.cats[f.cat]


  const mobile = p.variant === 'mobile'

  return (
    <div className="flex flex-col gap-6">
      {mobile ? null : legislators ? (
        <section className="flex flex-col gap-3">
          <Label>ADR report</Label>
          <ToggleGroup
            type="single"
            variant="outline"
            value={String(adrMapYears(data).includes(f.year) ? f.year : '')}
            onValueChange={(v) => v && p.setFilters({ year: Number(v) })}
            className="w-full"
          >
            {adrMapYears(data).map((y) => (
              <ToggleGroupItem key={y} value={String(y)} className="flex-1 tabular-nums">{y}</ToggleGroupItem>
            ))}
          </ToggleGroup>
          <p className="text-xs text-muted-foreground">Reports with a state-wise breakdown. 2025 covers MLAs only (ADR's all-India sitting MLAs report). The 2023 report is only available as headline figures.</p>
        </section>
      ) : (
        <section className="flex flex-col gap-3">
          <div className="flex items-baseline justify-between">
            <Label htmlFor="year">Year</Label>
            <span className="text-2xl font-semibold tabular-nums">{f.year}</span>
          </div>
          <div className="flex items-center gap-3">
            <Button
              size="icon"
              variant="outline"
              aria-label={p.playing ? 'Pause year animation' : 'Play through years'}
              onClick={() => p.setPlaying(!p.playing)}
            >
              {p.playing ? <Pause /> : <Play />}
            </Button>
            <Slider
              id="year"
              min={minY}
              max={maxY}
              step={1}
              value={[f.year]}
              onValueChange={([y]) => p.setFilters({ year: y })}
              aria-label="Year"
            />
          </div>
          <YearStrip years={data.years} have={p.stateYears} districtHave={p.districtYears} current={f.year} onPick={(y) => p.setFilters({ year: y })} />
        </section>
      )}

      {mobile ? (
        <section className="order-3 flex flex-col gap-3" aria-label="All crime types">
          <p className="text-sm font-semibold">All crime types</p>
          {(offenderMode || legislators) && (
            <p className="text-xs text-muted-foreground">
              {legislators ? 'ADR counts all declared crimes against women together.' : 'Offender data covers rape cases only.'}
            </p>
          )}
          {Object.entries(data.catGroups).map(([group, keys]) => {
            const present = keys.filter((k) => data.coverage[k])
            if (!present.length) return null
            return (
              <div key={group} className="flex flex-col gap-1.5">
                <p className="text-xs font-medium text-[var(--m-ink-soft)] uppercase tracking-wide">{group}</p>
                <div className="flex flex-wrap gap-1.5">
                  {present.map((k) => {
                    const on = (offenderMode ? 'rape' : f.cat) === k
                    return (
                      <button
                        key={k}
                        type="button"
                        aria-pressed={on}
                        disabled={offenderMode || legislators}
                        onClick={() => p.setFilters({ cat: k })}
                        className={`min-h-10 rounded-full border px-3.5 py-2 text-left text-sm font-medium disabled:opacity-40 ${
                          on ? 'border-transparent bg-[var(--brand)] text-[var(--brand-fg)]' : 'border-[var(--m-border)] bg-[var(--m-surface)]'
                        }`}
                      >
                        {data.cats[k].label}
                      </button>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </section>
      ) : (
      <section className="flex flex-col gap-2">
        <Label htmlFor="cat">Crime type</Label>
        <Select value={offenderMode ? 'rape' : f.cat} onValueChange={(v) => p.setFilters({ cat: v })} disabled={offenderMode || legislators}>
          <SelectTrigger id="cat" className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent position="popper" className="max-h-96">
            {Object.entries(data.catGroups).map(([group, keys], i) => {
              const present = keys.filter((k) => data.coverage[k])
              if (!present.length) return null
              return (
                <SelectGroup key={group}>
                  {i > 0 && <SelectSeparator />}
                  <SelectLabel>{group}</SelectLabel>
                  {present.map((k) => (
                    <SelectItem key={k} value={k}>
                      {data.cats[k].label}
                    </SelectItem>
                  ))}
                </SelectGroup>
              )
            })}
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground">
          {legislators ? 'ADR counts all declared crimes against women together.' : offenderMode ? 'Offender data covers rape cases only.' : cat?.legal}
        </p>
      </section>
      )}

      <section className={`flex flex-col gap-2 ${mobile ? 'order-1' : ''}`}>
        <Label htmlFor="offender">Who committed it</Label>
        <Select value={f.offender} onValueChange={(v) => p.setFilters({ offender: v })}>
          <SelectTrigger id="offender" className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent position="popper">
            {p.offenders.map((k) => (
              <SelectItem key={k} value={k}>
                {k === 'legislators' ? 'Public representatives (MPs/MLAs)' : OFFENDER_LABELS[k] ?? k}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground">
          {f.offender === 'legislators'
            ? 'Sitting MPs/MLAs with declared pending cases (ADR analysis of affidavits). These are not convictions.'
            : f.offender === 'custodial'
              ? 'Rape committed while the victim was in police or other official custody.'
              : offenderMode
                ? "NCRB's record of the offender's relation to the rape victim. State level only."
                : 'NCRB records the offender relation only for rape.'}
        </p>
      </section>

      {!mobile && <section className="flex flex-col gap-2">
        <Label>Measure</Label>
        <ToggleGroup
          type="single"
          variant="outline"
          value={f.metric}
          onValueChange={(v) => v && p.setFilters({ metric: v as Metric })}
          disabled={f.offender === 'legislators'}
          className="w-full"
        >
          <ToggleGroupItem value="count" className="flex-1">Cases</ToggleGroupItem>
          <ToggleGroupItem value="rate" className="flex-1">Rate per lakh</ToggleGroupItem>
        </ToggleGroup>
      </section>}

      {!mobile && <section className="flex flex-col gap-3">
        <Label>Map style</Label>
        <ToggleGroup type="single" variant="outline" value={p.mode} onValueChange={(v) => v && p.setMode(v as MapMode)} className="w-full">
          <ToggleGroupItem value="fill" className="flex-1">Filled areas</ToggleGroupItem>
          <ToggleGroupItem value="heat" className="flex-1">Heatmap</ToggleGroupItem>
        </ToggleGroup>
        <div className="flex items-center justify-between gap-3">
          <Label htmlFor="districts" className="font-normal">Show districts across India</Label>
          <Switch id="districts" checked={p.showDistricts} onCheckedChange={p.setShowDistricts} disabled={!p.districtYears.length} />
        </div>
        <p className="text-xs text-muted-foreground">
          District data: {p.districtYears.length ? describeYears(p.districtYears) : 'not available for this filter'}.
          Select a state to open its districts.
        </p>
      </section>}
    </div>
  )
}

/** One tick per year: filled = state data, dot = district data too. */
function YearStrip(props: { years: number[]; have: number[]; districtHave: number[]; current: number; onPick: (y: number) => void }) {
  const have = new Set(props.have)
  const dist = new Set(props.districtHave)
  return (
    <div>
      <div className="flex gap-px" role="list" aria-label="Years with data">
        {props.years.map((y) => (
          <button
            key={y}
            type="button"
            role="listitem"
            title={`${y}: ${have.has(y) ? (dist.has(y) ? 'state and district data' : 'state data') : 'no data'}`}
            onClick={() => props.onPick(y)}
            className={`relative h-3 flex-1 rounded-[2px] focus-visible:outline-2 focus-visible:outline-ring ${
              have.has(y) ? 'bg-[var(--ramp-4)]' : 'bg-muted'
            } ${y === props.current ? 'ring-2 ring-foreground ring-offset-1 ring-offset-background' : ''}`}
          >
            {dist.has(y) && <span className="absolute inset-x-0 bottom-[-6px] mx-auto size-1 rounded-full bg-foreground/60" />}
          </button>
        ))}
      </div>
      <div className="mt-3 flex justify-between text-[11px] text-muted-foreground tabular-nums">
        <span>{props.years[0]}</span>
        <span>
          Data: {describeYears(props.have)}
        </span>
        <span>{props.years[props.years.length - 1]}</span>
      </div>
    </div>
  )
}
