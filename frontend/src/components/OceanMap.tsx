import { MapPin, LocateFixed } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Circle,
  CircleMarker,
  MapContainer,
  Rectangle,
  TileLayer,
  Tooltip,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import type { LatLngBoundsExpression, LatLngExpression } from "leaflet";
import type { MapContext } from "../types/ocean";
import { formatCoordinates, formatRadius, viewportKey, type MapSelection } from "../utils/geo";

const VIEWPORT_OPTIONS = {
  paddingTopLeft: [28, 44] as [number, number],
  paddingBottomRight: [28, 28] as [number, number],
  maxZoom: 9,
};

function prefersReducedMotion(): boolean {
  return (
    typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches === true
  );
}

function selectionFromContext(context: MapContext): MapSelection {
  if (context.region) {
    return {
      kind: "region",
      label: context.label,
      bounds: {
        south: context.region.south,
        west: context.region.west,
        north: context.region.north,
        east: context.region.east,
      },
    };
  }
  return {
    kind: "point",
    label: context.label,
    latitude: context.marker.latitude,
    longitude: context.marker.longitude,
    radiusKm: context.radiusKm || 100,
  };
}

function fitSelection(map: L.Map, selection: MapSelection) {
  map.invalidateSize({ animate: false });
  const options = { ...VIEWPORT_OPTIONS, animate: !prefersReducedMotion(), duration: 0.6 };
  if (selection.kind === "region") {
    const { south, west, north, east } = selection.bounds;
    if (south < north && west < east) {
      map.fitBounds([[south, west], [north, east]] as LatLngBoundsExpression, options);
    }
    return;
  }
  const { latitude, longitude, radiusKm } = selection;
  if (![latitude, longitude, radiusKm].every(Number.isFinite)) return;
  const circleBounds = L.circle([latitude, longitude], { radius: radiusKm * 1000 }).getBounds();
  map.fitBounds(circleBounds, options);
}

function MapViewport({ selection, resetToken }: { selection: MapSelection; resetToken: number }) {
  const map = useMap();
  const key = viewportKey(selection);
  const animationFrame = useRef<number | null>(null);
  useEffect(() => {
    const container = map.getContainer();
    let lastSize = `${Math.round(container.clientWidth)}x${Math.round(container.clientHeight)}`;
    const scheduleFit = () => {
      if (animationFrame.current !== null) window.cancelAnimationFrame(animationFrame.current);
      animationFrame.current = window.requestAnimationFrame(() => {
        animationFrame.current = null;
        fitSelection(map, selection);
      });
    };
    scheduleFit();

    const onResize = (width: number, height: number) => {
      const nextSize = `${Math.round(width)}x${Math.round(height)}`;
      if (nextSize === lastSize) return;
      lastSize = nextSize;
      scheduleFit();
    };

    let observer: ResizeObserver | null = null;
    const windowResize = () => onResize(container.clientWidth, container.clientHeight);
    if (typeof ResizeObserver === "function") {
      observer = new ResizeObserver((entries) => {
        const entry = entries[0];
        if (entry) onResize(entry.contentRect.width, entry.contentRect.height);
      });
      observer.observe(container);
    } else {
      window.addEventListener("resize", windowResize);
    }
    return () => {
      observer?.disconnect();
      window.removeEventListener("resize", windowResize);
      if (animationFrame.current !== null) window.cancelAnimationFrame(animationFrame.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, key, resetToken]);
  return null;
}

export function OceanMap({ context }: { context: MapContext }) {
  const [tileError, setTileError] = useState(false);
  const [resetToken, setResetToken] = useState(0);
  const selection = useMemo(() => selectionFromContext(context), [context]);
  const center: LatLngExpression = [context.marker.latitude, context.marker.longitude];
  const regionBounds: LatLngBoundsExpression | undefined = context.region
    ? [[context.region.south, context.region.west], [context.region.north, context.region.east]]
    : undefined;

  const isRegion = selection.kind === "region";
  const coordinatePrecision = context.coordinatePrecision ?? 2;
  const selectionLabel = isRegion
    ? `Regional selection: ${context.label}`
    : `Point selection: ${context.label}`;
  const radiusLabel = isRegion ? "Regional selection" : `Search radius: ${formatRadius(selection.kind === "point" ? selection.radiusKm : 0)}`;
  const textEquivalent = isRegion
    ? `${context.label} regional selection, bounds ${context.region!.south.toFixed(1)}°–${context.region!.north.toFixed(1)}° latitude, ${context.region!.west.toFixed(1)}°–${context.region!.east.toFixed(1)}° longitude.`
    : `${context.label} at ${formatCoordinates(context.marker.latitude, context.marker.longitude, coordinatePrecision)}, ${radiusLabel.toLowerCase()}.`;

  const anchorRef = useRef<HTMLButtonElement>(null);

  return (
    <section className="map-card" aria-labelledby="location-title">
      <div className="panel-heading">
        <div><p className="section-kicker">Geographic context</p><h3 id="location-title">Interactive selection map</h3></div>
        <div className="map-heading-actions">
          <button
            type="button"
            ref={anchorRef}
            className="map-reset-button"
            onClick={() => setResetToken((token) => token + 1)}
          >
            <LocateFixed size={14} aria-hidden="true" /> Reset view
          </button>
          <span className="map-heading-icon"><MapPin size={16} aria-hidden="true" /></span>
        </div>
      </div>
      <div
        className="map-visual"
        role="region"
        aria-label={`Selection map. ${selectionLabel}. ${radiusLabel}.`}
      >
        <MapContainer center={center} zoom={5} minZoom={2} maxZoom={10} scrollWheelZoom={false}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            eventHandlers={{ tileerror: () => setTileError(true) }}
          />
          <MapViewport selection={selection} resetToken={resetToken} />
          {regionBounds && (
            <Rectangle
              bounds={regionBounds}
              pathOptions={{ color: "#2DD4C8", weight: 2, dashArray: "7 6", fillColor: "#2DD4C8", fillOpacity: 0.1 }}
            >
              <Tooltip sticky>{context.label} — regional selection</Tooltip>
            </Rectangle>
          )}
          {!context.region && (
            <Circle
              center={center}
              radius={(context.radiusKm || 100) * 1_000}
              pathOptions={{ color: "#2DD4C8", weight: 1, fillColor: "#2DD4C8", fillOpacity: 0.08 }}
            />
          )}
          <CircleMarker
            center={center}
            radius={isRegion ? 6 : 8}
            className="query-location-marker"
            pathOptions={{ color: "#2DD4C8", weight: 3, fillColor: "#2DD4C8", fillOpacity: 0.5 }}
          >
            <Tooltip direction="top" offset={[0, -9]} permanent>
              <strong>{context.label}</strong><br />
              {isRegion ? "Region centre" : formatCoordinates(context.marker.latitude, context.marker.longitude, coordinatePrecision)}
              <br />{radiusLabel}
            </Tooltip>
          </CircleMarker>
        </MapContainer>
        {tileError && <p className="map-network-note">Map tiles are unavailable; the selection geometry remains shown.</p>}
      </div>
      <div className="location-detail">
        <span className="mini-pin"><MapPin size={14} aria-hidden="true" /></span>
        <div>
          <strong>{context.label}</strong>
          <span>{isRegion ? "Regional selection" : `${formatCoordinates(context.marker.latitude, context.marker.longitude, coordinatePrecision)} • ${radiusLabel}`}</span>
        </div>
        <p>CartoDB / OpenStreetMap • selection geometry • not for navigation</p>
      </div>
      <p className="map-text-equivalent">{textEquivalent}</p>
    </section>
  );
}
