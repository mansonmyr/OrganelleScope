import { describe, expect, it } from "vitest";
import { buildChannelMetrics, sampleTrace } from "../workers/analysisCore";

describe("physical profile coordinates", () => {
  it("recovers Gaussian FWHM across different sample intervals", () => {
    const channel = Float32Array.from({ length: 201 }, (_, x) => 100 * Math.exp(-.5 * ((x - 100) / 8) ** 2));
    for (const spacing of [.5, 1, 2]) {
      const trace = sampleTrace(channel, 201, 1, {
        start: { x: 0, y: 0 }, end: { x: 200, y: 0 }, sampleSpacingPx: spacing
      }, "Reference", "#fff");
      const result = buildChannelMetrics(trace, trace.distancesPx, trace.distancesPx.map(d => d * .1), "um");
      expect(result.peaks).toHaveLength(1);
      expect(result.peaks[0].fwhmPhysical).toBeCloseTo(2 * Math.sqrt(2 * Math.log(2)) * 8 * .1, 1);
      expect(result.peaks[0].leftCrossPhysical!).toBeLessThan(10);
      expect(result.peaks[0].rightCrossPhysical!).toBeGreaterThan(10);
    }
  });
});
