import { MapPin } from "lucide-react";
import indianOceanLandRaw from "../data/indianOceanLand.geojson?raw";
import type { MapContext } from "../types/ocean";

type Coordinate = [number, number];

interface LandFeatureCollection {
  features: Array<{
    properties: { name: string };
    geometry: { coordinates: Coordinate[][] };
  }>;
}

const WIDTH = 640;
const HEIGHT = 310;
const WEST = 25;
const EAST = 125;
const NORTH = 35;
const SOUTH = -45;

const project = ([longitude, latitude]: Coordinate) => ({
  x: ((longitude - WEST) / (EAST - WEST)) * WIDTH,
  y: ((NORTH - latitude) / (NORTH - SOUTH)) * HEIGHT,
});

const polygonPath = (ring: Coordinate[]) =>
  ring.map((coordinate, index) => {
    const { x, y } = project(coordinate);
    return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ") + " Z";

const longitudeLines = [40, 60, 80, 100, 120];
const latitudeLines = [20, 0, -20, -40];
const indianOceanLand = JSON.parse(indianOceanLandRaw) as LandFeatureCollection;

export function OceanMap({ context }: { context: MapContext }) {
  const marker = project([context.marker.longitude, context.marker.latitude]);
  const calloutOnLeft = marker.x > WIDTH * 0.7;
  const region = context.region ? {
    topLeft: project([context.region.west, context.region.north]),
    bottomRight: project([context.region.east, context.region.south]),
  } : null;

  return (
    <section className="map-card" aria-labelledby="location-title">
      <div className="panel-heading">
        <div><p className="section-kicker">Geographic context</p><h3 id="location-title">Indian Ocean region</h3></div>
        <span className="map-heading-icon"><MapPin size={16} aria-hidden="true" /></span>
      </div>
      <div className="map-visual">
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label={`${context.label}, ${context.coordinates}, highlighted on a regional map of the Indian Ocean`}>
          <title>{`${context.label} — ${context.coordinates}`}</title>
          <defs>
            <linearGradient id="ocean-depth" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#075A9C" />
              <stop offset="58%" stopColor="#076EAA" />
              <stop offset="100%" stopColor="#063B73" />
            </linearGradient>
            <linearGradient id="land-shore" x1="0" y1="0" x2="0.9" y2="1">
              <stop offset="0%" stopColor="#D8CAA7" />
              <stop offset="100%" stopColor="#7C9B86" />
            </linearGradient>
            <radialGradient id="lagoon-light" cx="62%" cy="36%" r="58%">
              <stop offset="0%" stopColor="#19BFC2" stopOpacity="0.32" />
              <stop offset="100%" stopColor="#19BFC2" stopOpacity="0" />
            </radialGradient>
            <filter id="map-shadow" x="-30%" y="-30%" width="160%" height="160%">
              <feDropShadow dx="0" dy="3" stdDeviation="4" floodColor="#052F5F" floodOpacity="0.3" />
            </filter>
          </defs>

          <rect width={WIDTH} height={HEIGHT} rx="18" fill="url(#ocean-depth)" />
          <rect width={WIDTH} height={HEIGHT} rx="18" fill="url(#lagoon-light)" />

          <g className="map-graticules" aria-hidden="true">
            {longitudeLines.map((longitude) => {
              const { x } = project([longitude, 0]);
              return <line key={`lon-${longitude}`} x1={x} x2={x} y1="0" y2={HEIGHT} />;
            })}
            {latitudeLines.map((latitude) => {
              const { y } = project([WEST, latitude]);
              return <line key={`lat-${latitude}`} x1="0" x2={WIDTH} y1={y} y2={y} />;
            })}
          </g>

          <g className="coast-glow" aria-hidden="true">
            {indianOceanLand.features.map((feature) => <path key={`glow-${feature.properties.name}`} d={polygonPath(feature.geometry.coordinates[0])} />)}
          </g>
          <g className="land-mass" filter="url(#map-shadow)">
            {indianOceanLand.features.map((feature) => <path key={feature.properties.name} d={polygonPath(feature.geometry.coordinates[0])}><title>{feature.properties.name}</title></path>)}
          </g>

          <g className="map-labels" aria-hidden="true">
            <text x="224" y="155">ARABIAN SEA</text>
            <text x="397" y="145">BAY OF BENGAL</text>
            <text x="326" y="246" className="primary-ocean-label">INDIAN OCEAN</text>
            <text x="296" y="68" className="land-label">INDIA</text>
          </g>

          {region && context.region && (
            <rect
              className={`map-region ${context.region.tone}`}
              key={`${context.label}-region`}
              x={region.topLeft.x}
              y={region.topLeft.y}
              width={region.bottomRight.x - region.topLeft.x}
              height={region.bottomRight.y - region.topLeft.y}
              rx="20"
            />
          )}

          <g className="map-marker-group" key={`${context.label}-marker`} transform={`translate(${marker.x} ${marker.y})`} tabIndex={0} role="button" aria-label={`Selected location: ${context.label}, ${context.coordinates}`}>
            <circle className="marker-pulse" r="15" />
            <circle className="marker-ring" r="8" />
            <circle className="marker-core" r="4" />
            <g className={`map-callout${calloutOnLeft ? " left" : ""}`} transform={`translate(${calloutOnLeft ? -160 : 15} -38)`}>
              <rect width="145" height="36" rx="8" />
              <text x="10" y="15">{context.label}</text>
              <text x="10" y="28" className="callout-coordinates">{context.coordinates}</text>
            </g>
          </g>

          <g className="coordinate-labels" aria-hidden="true">
            <text x="8" y={project([WEST, 20]).y - 5}>20°N</text>
            <text x="8" y={project([WEST, 0]).y - 5}>EQ</text>
            <text x={project([80, SOUTH]).x + 5} y={HEIGHT - 8}>80°E</text>
            <text x={project([100, SOUTH]).x + 5} y={HEIGHT - 8}>100°E</text>
          </g>
        </svg>
      </div>
      <div className="location-detail">
        <span className="mini-pin"><MapPin size={14} aria-hidden="true" /></span>
        <div><strong>{context.label}</strong><span>{context.coordinates}</span></div>
        <p>Regional overview • not for navigation</p>
      </div>
    </section>
  );
}
