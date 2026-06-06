/** Presentation helpers for similarity scores in [0, 1]. */

export function formatPercent(score: number): string {
  return `${(score * 100).toFixed(1)}%`;
}

export type RiskLevel = "high" | "medium" | "low";

export function riskLevel(score: number): RiskLevel {
  if (score >= 0.8) {
    return "high";
  }
  if (score >= 0.5) {
    return "medium";
  }
  return "low";
}

export function riskColor(score: number): string {
  switch (riskLevel(score)) {
    case "high":
      return "#dc2626";
    case "medium":
      return "#d97706";
    case "low":
      return "#16a34a";
  }
}
