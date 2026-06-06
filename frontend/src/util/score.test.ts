import { describe, expect, it } from "vitest";

import { formatPercent, riskLevel } from "./score";

describe("score helpers", () => {
  it("formats a fraction as a percentage", () => {
    expect(formatPercent(0.8123)).toBe("81.2%");
    expect(formatPercent(1)).toBe("100.0%");
  });

  it("classifies risk by threshold", () => {
    expect(riskLevel(0.95)).toBe("high");
    expect(riskLevel(0.6)).toBe("medium");
    expect(riskLevel(0.2)).toBe("low");
  });
});
