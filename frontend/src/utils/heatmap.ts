export interface HeatmapLayout {
  cellWidth: number;
  labelIndexes: number[];
  plotLeft: number;
  plotWidth: number;
  svgWidth: number;
}

const LEFT_GUTTER = 118;
const RIGHT_GUTTER = 20;
const MIN_CELL_WIDTH = 34;
const MIN_LABEL_GAP = 78;

export function heatmapLabelIndexes(monthCount: number, stride: number): number[] {
  if (monthCount <= 0) return [];
  if (monthCount === 1) return [0];

  const safeStride = Math.max(1, Math.floor(stride));
  const indexes = Array.from(
    { length: Math.ceil(monthCount / safeStride) },
    (_, index) => index * safeStride,
  ).filter((index) => index < monthCount);
  const lastIndex = monthCount - 1;

  if (indexes.at(-1) !== lastIndex) {
    if (indexes.length > 1 && lastIndex - indexes.at(-1)! < safeStride) {
      indexes.pop();
    }
    indexes.push(lastIndex);
  }
  return indexes;
}

export function heatmapLayout(containerWidth: number, monthCount: number): HeatmapLayout {
  const safeWidth = Math.max(320, Math.floor(containerWidth));
  const safeMonthCount = Math.max(1, monthCount);
  const availablePlotWidth = Math.max(1, safeWidth - LEFT_GUTTER - RIGHT_GUTTER);
  const cellWidth = Math.max(MIN_CELL_WIDTH, availablePlotWidth / safeMonthCount);
  const plotWidth = safeMonthCount * cellWidth;
  const labelStride = Math.max(1, Math.ceil(MIN_LABEL_GAP / cellWidth));

  return {
    cellWidth,
    labelIndexes: heatmapLabelIndexes(monthCount, labelStride),
    plotLeft: LEFT_GUTTER,
    plotWidth,
    svgWidth: Math.ceil(LEFT_GUTTER + plotWidth + RIGHT_GUTTER),
  };
}
