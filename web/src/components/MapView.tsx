import * as maplibregl from 'maplibre-gl'
import type { GeoJSONSource, MapGeoJSONFeature } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
// Bundle the worker (and the shared chunk it imports) so production builds can find it
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import { useEffect, useRef } from 'react'
import type { FeatureCollection, Geometry } from 'geojson'

export type MapMode = 'fill' | 'heat'

export interface AreaStyle {
  color: string
  label: string // tooltip value text
}

interface Props {
  states: FeatureCollection
  districts: FeatureCollection
  india: FeatureCollection // national boundary as depicted by the Government of India
  stateLabels: FeatureCollection // Point features with property name
  labelMask?: Geometry // only basemap labels inside this polygon (India) are drawn
  theme: 'light' | 'dark'
  mode: MapMode
  touch?: boolean // phone/tablet layout: no hover labels (the summary card shows the value)
  fitToken?: number // bump to re-fit the view (e.g. a 'show all of India' button)
  showDistricts: boolean // districts drawn for the whole country or the selected state
  selectedState: string | null
  selectedDistrict: string | null
  stateStyles: Record<string, AreaStyle>
  districtStyles: Record<string, AreaStyle>
  heatPoints: FeatureCollection // Point features with property w in 0..1
  heatLevel?: 'state' | 'district' // wider spots for ~36 states, tighter for ~600 districts
  onSelectState: (name: string | null) => void
  onSelectDistrict: (gid: string | null) => void
}

maplibregl.setWorkerUrl(workerUrl)

const STYLES = {
  light: 'https://tiles.openfreemap.org/styles/positron',
  dark: 'https://tiles.openfreemap.org/styles/dark',
}
const INDIA: [[number, number], [number, number]] = [[67.5, 6], [98.5, 37.5]]
const LINE = { light: '#4b4a46', dark: '#c9c8c0' } // selection outline
const OUTLINE = { light: '#ffffff', dark: '#ffffff' } // national boundary
const OUTLINE_EDGE = { light: '#3a3936', dark: '#0d0d0c' } // thin dark edge so the white line reads on light ground
const GAP = { light: '#ffffff', dark: '#1a1a19' } // surface-coloured borders between areas
const HEAT_RAMP = [
  'interpolate', ['linear'], ['heatmap-density'],
  0, 'rgba(235,104,52,0)', 0.15, 'rgba(252,196,120,0.55)', 0.35, '#f59e4c',
  0.6, '#eb6834', 0.8, '#d0412a', 1, '#8f1d1d',
] as const

function bboxOf(g: Geometry): [[number, number], [number, number]] {
  let minX = 180, minY = 90, maxX = -180, maxY = -90
  const walk = (c: unknown): void => {
    if (typeof (c as number[])[0] === 'number') {
      const [x, y] = c as number[]
      if (x < minX) minX = x
      if (x > maxX) maxX = x
      if (y < minY) minY = y
      if (y > maxY) maxY = y
    } else (c as unknown[]).forEach(walk)
  }
  if ('coordinates' in g) walk(g.coordinates)
  return [[minX, minY], [maxX, maxY]]
}

export function MapView(props: Props) {
  const container = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const latest = useRef(props)
  latest.current = props
  const ready = useRef(false)

  // Create the map once; (re)add our layers whenever a basemap style loads.
  useEffect(() => {
    const map = new maplibregl.Map({
      container: container.current!,
      style: STYLES[latest.current.theme],
      bounds: INDIA,
      fitBoundsOptions: { padding: 16 },
      minZoom: 3,
      maxZoom: 11,
      attributionControl: { compact: true },
      dragRotate: false,
      dragPan: true,
      touchZoomRotate: true,
      doubleClickZoom: true,
      pitchWithRotate: false,
    })
    map.touchZoomRotate.disableRotation()
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
    mapRef.current = map
    map.on('error', (e) => console.error('map error:', e.error?.message ?? e))

    const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 12, className: 'area-popup' })

    map.on('load', () => {
      // Phones: start with the credit collapsed to its (i) button so it doesn't cover the map
      if (latest.current.touch) map.getContainer().querySelector('.maplibregl-ctrl-attrib')?.classList.remove('maplibregl-compact-show')
    })
    map.on('style.load', () => {
      addLayers(map)
      ready.current = true
      applyAll(map, latest.current)
    })

    const hover = (layer: 'state-fill' | 'district-fill') => (e: maplibregl.MapLayerMouseEvent) => {
      const f = e.features?.[0] as MapGeoJSONFeature | undefined
      if (!f || latest.current.touch) return // touch layouts show a summary card instead
      map.getCanvas().style.cursor = 'pointer'
      const p = latest.current
      const isState = layer === 'state-fill'
      const id = String(isState ? f.properties.name : f.properties.gid)
      const style = isState ? p.stateStyles[id] : p.districtStyles[id]
      const title = isState ? id : `${f.properties.name}, ${f.properties.ost}`
      popup
        .setLngLat(e.lngLat)
        .setHTML(`<div class="font-medium">${escapeHtml(title)}</div><div>${escapeHtml(style?.label ?? 'No data')}</div>`)
        .addTo(map)
    }
    const leave = () => {
      map.getCanvas().style.cursor = ''
      popup.remove()
    }
    map.on('mousemove', 'state-fill', hover('state-fill'))
    map.on('mousemove', 'district-fill', hover('district-fill'))
    map.on('mouseleave', 'state-fill', leave)
    map.on('mouseleave', 'district-fill', leave)

    map.on('click', (e) => {
      const p = latest.current
      const hits = map.queryRenderedFeatures(e.point, { layers: ['district-fill', 'state-hit'].filter((l) => map.getLayer(l)) })
      const d = hits.find((h) => h.layer.id === 'district-fill')
      const s = hits.find((h) => h.layer.id === 'state-hit')
      if (d && (p.showDistricts || p.selectedState)) {
        const ost = String(d.properties.ost)
        if (p.selectedState !== ost) p.onSelectState(ost)
        p.onSelectDistrict(String(d.properties.gid))
      } else if (s) {
        p.onSelectState(String(s.properties.name))
      }
    })

    return () => {
      ready.current = false
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Basemap theme
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    ready.current = false
    map.setStyle(STYLES[props.theme])
  }, [props.theme])

  // Data, filters and selection
  useEffect(() => {
    const map = mapRef.current
    if (map && ready.current) applyAll(map, props)
  })

  // Zoom to the selected state / district, or back out to India
  const { selectedState, selectedDistrict, states, districts, fitToken } = props
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const feat = selectedDistrict
      ? districts.features.find((f) => String(f.properties?.gid) === selectedDistrict)
      : selectedState
        ? states.features.find((f) => f.properties?.name === selectedState)
        : null
    const bounds = feat ? bboxOf(feat.geometry) : INDIA
    map.fitBounds(bounds, { padding: 40, duration: 700, maxZoom: selectedDistrict ? 8 : 7.5 })
  }, [selectedState, selectedDistrict, states, districts, fitToken])

  // maplibre sets position:relative on its container, so the absolute box is a wrapper
  return (
    <div className="absolute inset-0">
      <div ref={container} className="h-full w-full" role="region" aria-label="Map of India" />
    </div>
  )

  function addLayers(map: maplibregl.Map) {
    const p = latest.current
    // Hide the basemap's own borders and region (admin-1) labels: the official boundaries and
    // state names below replace them, so disputed areas are shown as India depicts them.
    let labelFont: string[] | undefined
    for (const l of map.getStyle().layers ?? []) {
      if ('source-layer' in l && l['source-layer'] === 'boundary') map.setLayoutProperty(l.id, 'visibility', 'none')
      if (l.type === 'symbol' && /(^|_)state($|_)/.test(l.id)) map.setLayoutProperty(l.id, 'visibility', 'none')
      if (!labelFont && l.type === 'symbol' && l.layout && 'text-font' in l.layout) labelFont = l.layout['text-font'] as string[]
    }
    // Names of places outside India are not shown: every basemap label layer keeps only
    // features that lie within the official outline. A layer that can't take the filter is hidden.
    if (p.labelMask) {
      for (const l of map.getStyle().layers ?? []) {
        if (l.type !== 'symbol' || map.getLayoutProperty(l.id, 'visibility') === 'none') continue
        const within = ['within', p.labelMask] as unknown as maplibregl.FilterSpecification
        const prev = map.getFilter(l.id)
        try {
          map.setFilter(l.id, prev ? (['all', prev, within] as unknown as maplibregl.FilterSpecification) : within)
        } catch {
          map.setLayoutProperty(l.id, 'visibility', 'none')
        }
      }
    }
    const firstSymbol = map.getStyle().layers?.find((l) => l.type === 'symbol')?.id
    map.addSource('states', { type: 'geojson', data: p.states, promoteId: 'name' })
    map.addSource('districts', { type: 'geojson', data: p.districts, promoteId: 'gid' })
    map.addSource('heat', { type: 'geojson', data: p.heatPoints })
    const line = LINE[p.theme]

    map.addLayer({
      id: 'district-fill', type: 'fill', source: 'districts',
      paint: { 'fill-color': ['coalesce', ['feature-state', 'color'], 'rgba(0,0,0,0)'], 'fill-opacity': 0.85 },
    }, firstSymbol)
    map.addLayer({
      id: 'district-line', type: 'line', source: 'districts',
      paint: { 'line-color': GAP[p.theme], 'line-opacity': 0.9, 'line-width': ['interpolate', ['linear'], ['zoom'], 4, 0.3, 8, 1] },
    }, firstSymbol)
    map.addLayer({
      id: 'state-fill', type: 'fill', source: 'states',
      paint: { 'fill-color': ['coalesce', ['feature-state', 'color'], 'rgba(0,0,0,0)'], 'fill-opacity': 0.85 },
    }, firstSymbol)
    // Invisible layer that keeps whole states clickable when their fill is hidden
    map.addLayer({ id: 'state-hit', type: 'fill', source: 'states', paint: { 'fill-color': '#000', 'fill-opacity': 0 } }, firstSymbol)
    map.addLayer({
      id: 'heat', type: 'heatmap', source: 'heat',
      paint: {
        'heatmap-weight': ['get', 'w'],
        'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 3, 0.9, 8, 2],
        'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 3, 16, 5, 34, 8, 70, 11, 120],
        'heatmap-color': HEAT_RAMP as unknown as maplibregl.ExpressionSpecification,
        'heatmap-opacity': 0.85,
      },
    }, firstSymbol)
    map.addLayer({
      id: 'state-line', type: 'line', source: 'states',
      paint: { 'line-color': GAP[p.theme], 'line-width': ['interpolate', ['linear'], ['zoom'], 3, 0.9, 7, 2] },
    }, firstSymbol)
    // National boundary: a bold continuous line with a thin halo so it reads over any fill
    map.addSource('india', { type: 'geojson', data: p.india })
    map.addLayer({
      id: 'india-outline-halo', type: 'line', source: 'india',
      layout: { 'line-join': 'round', 'line-cap': 'round' },
      paint: { 'line-color': OUTLINE_EDGE[p.theme], 'line-opacity': 0.55, 'line-width': ['interpolate', ['linear'], ['zoom'], 3, 3, 6, 4, 9, 5.2] },
    }, firstSymbol)
    map.addLayer({
      id: 'india-outline', type: 'line', source: 'india',
      layout: { 'line-join': 'round', 'line-cap': 'round' },
      paint: { 'line-color': OUTLINE[p.theme], 'line-width': ['interpolate', ['linear'], ['zoom'], 3, 1.8, 6, 2.5, 9, 3.2] },
    }, firstSymbol)
    map.addSource('state-labels', { type: 'geojson', data: p.stateLabels })
    map.addLayer({
      id: 'state-labels', type: 'symbol', source: 'state-labels', minzoom: 4,
      layout: {
        'text-field': ['get', 'name'], 'text-font': labelFont ?? ['Noto Sans Regular'],
        'text-size': ['interpolate', ['linear'], ['zoom'], 4, 10, 7, 13], 'text-transform': 'uppercase',
        'text-letter-spacing': 0.08, 'text-max-width': 8,
      },
      paint: { 'text-color': LINE[p.theme], 'text-opacity': 0.85, 'text-halo-color': GAP[p.theme], 'text-halo-width': 1.4 },
    })
    map.addLayer({
      id: 'selected-line', type: 'line', source: 'states',
      filter: ['==', ['get', 'name'], ''],
      paint: { 'line-color': line, 'line-width': 2.6 },
    }, firstSymbol)
    map.addLayer({
      id: 'selected-district-line', type: 'line', source: 'districts',
      filter: ['==', ['get', 'gid'], -1],
      paint: { 'line-color': line, 'line-width': 2.4 },
    }, firstSymbol)
  }
}

function applyAll(map: maplibregl.Map, p: Props) {
  if (!map.getSource('states')) return
  for (const f of p.states.features) {
    const id = String(f.properties?.name)
    map.setFeatureState({ source: 'states', id }, { color: p.stateStyles[id]?.color ?? null })
  }
  for (const f of p.districts.features) {
    const id = String(f.properties?.gid)
    map.setFeatureState({ source: 'districts', id }, { color: p.districtStyles[id]?.color ?? null })
  }
  ;(map.getSource('heat') as GeoJSONSource).setData(p.heatPoints)
  map.setPaintProperty('heat', 'heatmap-radius', p.heatLevel === 'district'
    ? ['interpolate', ['linear'], ['zoom'], 3, 12, 5, 26, 6, 44, 7, 62, 9, 96, 11, 140]
    : ['interpolate', ['linear'], ['zoom'], 3, 44, 5, 80, 7, 140, 9, 220])
  map.setPaintProperty('heat', 'heatmap-intensity', p.heatLevel === 'district'
    ? ['interpolate', ['linear'], ['zoom'], 3, 1.3, 6, 2.2, 9, 2.8]
    : ['interpolate', ['linear'], ['zoom'], 3, 1.8, 6, 2.4, 9, 3])

  const heat = p.mode === 'heat'
  const sel = p.selectedState
  const districtsOn = !heat && (p.showDistricts || !!sel)
  map.setLayoutProperty('heat', 'visibility', heat ? 'visible' : 'none')
  map.setLayoutProperty('district-fill', 'visibility', districtsOn ? 'visible' : 'none')
  map.setLayoutProperty('district-line', 'visibility', districtsOn || (heat && sel) ? 'visible' : 'none')
  map.setFilter('district-fill', sel && !p.showDistricts ? ['==', ['get', 'ost'], sel] : null)
  map.setFilter('district-line', sel && !p.showDistricts ? ['==', ['get', 'ost'], sel] : null)
  map.setLayoutProperty('state-fill', 'visibility', heat ? 'none' : 'visible')
  // Country view: states filled. State view: the selected state shows its districts, others fade.
  map.setPaintProperty('state-fill', 'fill-opacity',
    districtsOn && p.showDistricts ? 0 : sel ? ['case', ['==', ['get', 'name'], sel], 0, 0.35] : 0.85)
  map.setFilter('selected-line', ['==', ['get', 'name'], sel ?? ''])
  map.setFilter('selected-district-line', ['==', ['get', 'gid'], p.selectedDistrict ? Number(p.selectedDistrict) : -1])
}

function escapeHtml(s: string) {
  return s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!)
}
