import { MapPin } from "lucide-react";
import { useEffect, useState } from "react";
import {
  Circle,
  CircleMarker,
  MapContainer,
  Rectangle,
  TileLayer,
  Tooltip,
  useMap,
} from "react-leaflet";
import type { LatLngExpression, LatLngBoundsExpression } from "leaflet";
import type { MapContext } from "../types/ocean";

function MapViewport({ context }: { context: MapContext }) {
  const map = useMap();
  useEffect(() => {
    if (context.region) {
      map.fitBounds([
        [context.region.south, context.region.west],
        [context.region.north, context.region.east],
      ], { padding: [20, 20], maxZoom: 5 });
      return;
    }
    map.flyTo([context.marker.latitude, context.marker.longitude], 6, { duration: 0.7 });
  }, [context, map]);
  return null;
}

export function OceanMap({ context }: { context: MapContext }) {
  const [tileError, setTileError] = useState(false);
  const center: LatLngExpression = [context.marker.latitude, context.marker.longitude];
  const bounds: LatLngBoundsExpression | undefined = context.region
    ? [[context.region.south, context.region.west], [context.region.north, context.region.east]]
    : undefined;

  return (
    <section className="map-card" aria-labelledby="location-title">
      <div className="panel-heading">
        <div><p className="section-kicker">Geographic context</p><h3 id="location-title">Interactive selection map</h3></div>
        <span className="map-heading-icon"><MapPin size={16} aria-hidden="true" /></span>
      </div>
      <div className="map-visual" aria-label={`Map for ${context.label}, ${context.coordinates}`}>
        <MapContainer center={center} zoom={5} minZoom={2} maxZoom={10} scrollWheelZoom>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            eventHandlers={{ tileerror: () => setTileError(true) }}
          />
          <MapViewport context={context} />
          {bounds && (
            <Rectangle
              bounds={bounds}
              pathOptions={{ color: "#2DD4C8", weight: 2, dashArray: "7 6", fillColor: "#2DD4C8", fillOpacity: 0.1 }}
            >
              <Tooltip sticky>{context.label} regional selection</Tooltip>
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
            radius={10}
            className="query-location-marker"
            pathOptions={{ color: "#2DD4C8", weight: 3, fillColor: "#2DD4C8", fillOpacity: 0.5 }}
          >
            <Tooltip direction="top" offset={[0, -9]} permanent>
              <strong>{context.label}</strong><br />{context.coordinates}
            </Tooltip>
          </CircleMarker>
        </MapContainer>
        {tileError && <p className="map-network-note">Map tiles are unavailable; the query coordinates remain shown.</p>}
      </div>
      <div className="location-detail">
        <span className="mini-pin"><MapPin size={14} aria-hidden="true" /></span>
        <div><strong>{context.label}</strong><span>{context.coordinates}</span></div>
        <p>CartoDB / OpenStreetMap • interactive • not for navigation</p>
      </div>
    </section>
  );
}
