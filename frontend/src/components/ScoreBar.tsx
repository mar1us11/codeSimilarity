import type { JSX } from "react";

import { formatPercent, riskColor } from "../util/score";

interface ScoreBarProps {
  readonly label: string;
  readonly score: number;
}

export function ScoreBar({ label, score }: ScoreBarProps): JSX.Element {
  const color = riskColor(score);
  return (
    <div className="score-bar">
      <div className="score-bar__header">
        <span>{label}</span>
        <strong style={{ color }}>{formatPercent(score)}</strong>
      </div>
      <div className="score-bar__track">
        <div
          className="score-bar__fill"
          style={{ width: `${Math.round(score * 100)}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
