import assert from "node:assert/strict";
import test from "node:test";

import { heatmapLabelIndexes, heatmapLayout } from "../src/utils/heatmap.ts";

test("uses every month label when a full-width heatmap has enough room", () => {
  const layout = heatmapLayout(1280, 12);

  assert.deepEqual(layout.labelIndexes, Array.from({ length: 12 }, (_, index) => index));
  assert.equal(layout.svgWidth, 1280);
  assert.ok(layout.plotLeft >= 110);
});

test("thins labels by pixel spacing in a narrow heatmap", () => {
  const layout = heatmapLayout(500, 12);

  assert.equal(layout.labelIndexes[0], 0);
  assert.equal(layout.labelIndexes.at(-1), 11);
  assert.ok(layout.labelIndexes.length < 12);
  for (let index = 1; index < layout.labelIndexes.length; index += 1) {
    const pixelGap = (layout.labelIndexes[index] - layout.labelIndexes[index - 1]) * layout.cellWidth;
    assert.ok(pixelGap >= 78);
  }
});

test("keeps long timelines scrollable and includes their final month", () => {
  const layout = heatmapLayout(1280, 120);

  assert.ok(layout.svgWidth > 4000);
  assert.equal(layout.labelIndexes[0], 0);
  assert.equal(layout.labelIndexes.at(-1), 119);
});

test("handles empty and single-month label sets", () => {
  assert.deepEqual(heatmapLabelIndexes(0, 2), []);
  assert.deepEqual(heatmapLabelIndexes(1, 2), [0]);
});
