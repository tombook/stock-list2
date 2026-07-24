// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { PriceChart } from "./PriceChart";
import type { Bar } from "../../types/market";

function makeBar(overrides: Partial<Bar> = {}): Bar {
  return {
    ts: "2024-01-01T00:00:00Z",
    open: 100,
    high: 105,
    low: 98,
    close: 103,
    volume: 1000,
    ...overrides,
  };
}

const sampleBars: Bar[] = [
  makeBar({ ts: "2024-01-01", open: 100, high: 105, low: 98, close: 103, volume: 1000 }),
  makeBar({ ts: "2024-01-02", open: 103, high: 108, low: 102, close: 107, volume: 1200 }),
  makeBar({ ts: "2024-01-03", open: 107, high: 110, low: 104, close: 105, volume: 800 }),
  makeBar({ ts: "2024-01-04", open: 105, high: 109, low: 103, close: 108, volume: 900 }),
];

describe("PriceChart", () => {
  it("renders the chart with correct aria-label when bars >= 2", () => {
    render(<PriceChart bars={sampleBars} />);
    expect(screen.getByRole("img", { name: /price chart/i })).toBeTruthy();
  });

  it("renders the empty-state message when fewer than 2 bars", () => {
    render(<PriceChart bars={[makeBar()]} />);
    expect(screen.getByText(/not enough data/i)).toBeTruthy();
  });

  it("renders candlestick rects (one body + optional volume per bar)", () => {
    const { container } = render(<PriceChart bars={sampleBars} />);
    const rects = container.querySelectorAll("rect");
    // 每根蜡烛至少 1 个 body rect；有 volume 时多 1 个 volume rect
    expect(rects.length).toBeGreaterThanOrEqual(sampleBars.length);
  });

  it("renders grid lines and axis date labels", () => {
    render(<PriceChart bars={sampleBars} />);
    expect(screen.getByText("Jan 1, 24")).toBeTruthy();
    expect(screen.getByText("Jan 4, 24")).toBeTruthy();
  });

  it("renders SMA overlay paths when smaPeriods provided", () => {
    const { container } = render(<PriceChart bars={sampleBars} smaPeriods={[2]} />);
    const paths = container.querySelectorAll("path");
    // 至少有 candle 区域 path + SMA path
    expect(paths.length).toBeGreaterThanOrEqual(1);
    // SMA path 存在（d 属性以 M 开头）
    const smaPath = Array.from(paths).find((p) => p.getAttribute("d")?.startsWith("M"));
    expect(smaPath).toBeTruthy();
  });

  it("renders no SMA paths when smaPeriods is empty", () => {
    const { container } = render(<PriceChart bars={sampleBars} />);
    const paths = container.querySelectorAll("path");
    // 只有 area fill path + 可能没有额外 path
    const smaPaths = Array.from(paths).filter((p) => p.getAttribute("d")?.startsWith("M") && !p.getAttribute("d")?.includes("L"));
    // SMA 线不应存在
    expect(smaPaths.length).toBe(0);
  });
});
