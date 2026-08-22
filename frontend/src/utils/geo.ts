// Pure coordinate/radius formatting helpers for the selection map.
// The frontend renders the coordinates supplied by the accepted backend
// QueryParams; it never geocodes or reinterprets the user's text.

function normalizeZero(value: number): number {
  // Avoid rendering "-0.00".
  return Object.is(value, -0) || value === 0 ? 0 : value;
}

export function formatLatitude(latitude: number, decimals = 2): string {
  const normalized = normalizeZero(latitude);
  const hemisphere = normalized >= 0 ? "N" : "S";
  return `${Math.abs(normalized).toFixed(decimals)}°${hemisphere}`;
}

export function formatLongitude(longitude: number, decimals = 2): string {
  const normalized = normalizeZero(longitude);
  const hemisphere = normalized >= 0 ? "E" : "W";
  return `${Math.abs(normalized).toFixed(decimals)}°${hemisphere}`;
}

export function formatCoordinates(latitude: number, longitude: number, decimals = 2): string {
  return `${formatLatitude(latitude, decimals)}, ${formatLongitude(longitude, decimals)}`;
}

export function formatRadius(radiusKm: number): string {
  if (!Number.isFinite(radiusKm)) return "";
  if (radiusKm < 10) return `${radiusKm.toFixed(1)} km`;
  return `${Math.round(radiusKm)} km`;
}

export interface RegionBounds {
  south: number;
  west: number;
  north: number;
  east: number;
}

export type MapSelection =
  | { kind: "point"; label: string; latitude: number; longitude: number; radiusKm: number }
  | { kind: "region"; label: string; bounds: RegionBounds };

/** Stable key identifying the selection geometry, used to avoid refit loops. */
export function viewportKey(selection: MapSelection): string {
  if (selection.kind === "region") {
    const { south, west, north, east } = selection.bounds;
    return `region:${south},${west},${north},${east}`;
  }
  return `point:${selection.latitude},${selection.longitude},${selection.radiusKm}`;
}
