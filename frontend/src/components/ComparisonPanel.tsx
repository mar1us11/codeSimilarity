import type { JSX } from "react";

import type { ComparisonRead } from "../types/api";
import { formatPercent, riskColor, riskLevel } from "../util/score";
import { ScoreBar } from "./ScoreBar";

interface ComparisonPanelProps {
  readonly comparison: ComparisonRead | null;
  readonly loading: boolean;
  readonly subjectA?: string;
  readonly subjectB?: string;
  readonly onClose: () => void;
}

export function ComparisonPanel({
  comparison,
  loading,
  subjectA,
  subjectB,
  onClose,
}: ComparisonPanelProps): JSX.Element {
  return (
    <div className="modal" role="dialog" aria-modal="true">
      <div className="modal__backdrop" onClick={onClose} />
      <div className="modal__body panel">
        <div className="report__head">
          <h2>
            Pair detail
            {subjectA && subjectB ? (
              <span className="muted"> — {subjectA} vs {subjectB}</span>
            ) : null}
          </h2>
          <button type="button" className="secondary" onClick={onClose}>
            Close
          </button>
        </div>

        {loading || comparison === null ? (
          <div className="loading">
            <span className="spinner" aria-hidden />
            <span>Computing function-level alignment…</span>
          </div>
        ) : (
          <>
            <div className="overall" style={{ borderColor: riskColor(comparison.overall_score) }}>
              <div className="overall__score" style={{ color: riskColor(comparison.overall_score) }}>
                {formatPercent(comparison.overall_score)}
              </div>
              <div className={`badge badge--${riskLevel(comparison.overall_score)}`}>
                {riskLevel(comparison.overall_score)} similarity
              </div>
            </div>

            <div className="components">
              <ScoreBar label="Tree Edit Distance" score={comparison.ted_score} />
              <ScoreBar label="Winnowing / Jaccard" score={comparison.winnow_score} />
              <ScoreBar label="Call-graph structure" score={comparison.callgraph_score} />
            </div>

            <h3>Aligned functions ({comparison.matches.length})</h3>
            {comparison.matches.length === 0 ? (
              <p className="muted">No functions cleared the matching threshold.</p>
            ) : (
              <table className="match-table">
                <thead>
                  <tr>
                    <th>A fn #</th>
                    <th>B fn #</th>
                    <th>Combined</th>
                    <th>TED</th>
                    <th>Winnow</th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.matches.map((match) => (
                    <tr key={`${match.function_a_id}-${match.function_b_id}`}>
                      <td>{match.function_a_id}</td>
                      <td>{match.function_b_id}</td>
                      <td style={{ color: riskColor(match.similarity) }}>
                        {formatPercent(match.similarity)}
                      </td>
                      <td>{formatPercent(match.ted_similarity)}</td>
                      <td>{formatPercent(match.winnow_similarity)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </>
        )}
      </div>
    </div>
  );
}
