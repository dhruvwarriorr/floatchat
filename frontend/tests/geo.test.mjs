import assert from "node:assert/strict";
import test from "node:test";

import {
  formatCoordinates,
  formatLatitude,
  formatLongitude,
  formatRadius,
  viewportKey,
} from "../src/utils/geo.ts";

test("formats named and explicit Indian Ocean coordinates without negative zero", () => {
  assert.equal(formatCoordinates(19, 72.8), "19.00°N, 72.80°E");
  assert.equal(formatCoordinates(15.49, 73.83), "15.49°N, 73.83°E");
  assert.equal(formatCoordinates(-4.62, 55.45), "4.62°S, 55.45°E");
  assert.equal(formatCoordinates(10.1234, 70.5, 4), "10.1234°N, 70.5000°E");
  assert.equal(formatLatitude(-0), "0.00°N");
  assert.equal(formatLongitude(-0), "0.00°E");
});

test("formats the full supported radius range consistently", () => {
  assert.equal(formatRadius(1), "1.0 km");
  assert.equal(formatRadius(5.25), "5.3 km");
  assert.equal(formatRadius(10), "10 km");
  assert.equal(formatRadius(50), "50 km");
  assert.equal(formatRadius(100), "100 km");
  assert.equal(formatRadius(500), "500 km");
  assert.equal(formatRadius(2000), "2000 km");
});

test("viewport keys change only when selection geometry changes", () => {
  const point = { kind: "point", label: "Goa", latitude: 15.49, longitude: 73.83, radiusKm: 100 };
  assert.equal(viewportKey(point), "point:15.49,73.83,100");
  assert.equal(
    viewportKey({ ...point, label: "Goa coast" }),
    viewportKey(point),
  );
  assert.notEqual(viewportKey({ ...point, radiusKm: 50 }), viewportKey(point));
  assert.equal(
    viewportKey({ kind: "region", label: "Bay", bounds: { south: 5, west: 80, north: 22, east: 100 } }),
    "region:5,80,22,100",
  );
});
