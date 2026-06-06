import { useMemo, useState, type JSX } from "react";

import type { AiReferenceSolution, AnalysisReport, StudentPairResult } from "../types/api";
import { formatPercent, riskColor, riskLevel } from "../util/score";

interface AnalysisReportViewProps {
  readonly report: AnalysisReport | null;
  readonly running: boolean;
  readonly onInspectPair: (pair: StudentPairResult) => void;
}

export function AnalysisReportView({
  report,
  running,
  onInspectPair,
}: AnalysisReportViewProps): JSX.Element {
  const [selectedReference, setSelectedReference] = useState<AiReferenceSolution | null>(null);
  const referenceByLabel = useMemo(
    () => new Map((report?.ai_references ?? []).map((ref) => [ref.label, ref])),
    [report],
  );

  if (running && report === null) {
    return (
      <div className="panel">
        <h2>Analysis</h2>
        <div className="loading">
          <span className="spinner" aria-hidden />
          <span>Comparing every submission pair…</span>
        </div>
      </div>
    );
  }

  if (report === null) {
    return (
      <div className="panel">
        <h2>Analysis</h2>
        <p className="muted">
          Configure and run an analysis to see student similarity, suspicious clusters and
          (optionally) similarity to AI reference solutions.
        </p>
      </div>
    );
  }

  const topPair = report.student_pairs[0] ?? null;

  return (
    <>
      <div className="report">
        <div className="panel">
          <div className="report__head">
            <h2>Similarity results</h2>
            {running && <span className="muted">refreshing…</span>}
          </div>

          <div className="stat-grid">
            <Stat label="Submissions" value={String(report.submission_count)} />
            <Stat label="Pairs compared" value={String(report.student_pairs.length)} />
            <Stat
              label="Highest similarity"
              value={formatPercent(report.highest_student_score)}
              color={riskColor(report.highest_student_score)}
            />
            <Stat label="Suspicious clusters" value={String(report.clusters.length)} />
          </div>

          {report.warnings.length > 0 && (
            <ul className="warnings">
              {report.warnings.map((w) => (
                <li key={w}>⚠️ {w}</li>
              ))}
            </ul>
          )}
        </div>

        {report.clusters.length > 0 && (
          <div className="panel">
            <h3>Suspicious clusters</h3>
            <p className="muted">
              Groups of submissions transitively linked by high structural similarity (found via
              DFS over the suspicion graph).
            </p>
            <div className="cluster-grid">
              {report.clusters.map((cluster, idx) => (
                <div
                  key={cluster.members.map((m) => m.submission_id).join("-")}
                  className="cluster-card"
                  style={{ borderColor: riskColor(cluster.average_similarity) }}
                >
                  <div className="cluster-card__head">
                    <strong>Cluster {idx + 1}</strong>
                    <span
                      className={`badge badge--${riskLevel(cluster.average_similarity)}`}
                    >
                      {formatPercent(cluster.average_similarity)} avg
                    </span>
                  </div>
                  <ul>
                    {cluster.members.map((m) => (
                      <li key={m.submission_id}>{m.name}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="panel">
          <h3>Student similarity — ranked highest to lowest</h3>
          {report.student_pairs.length === 0 ? (
            <p className="muted">No pairs to compare.</p>
          ) : (
            <table className="match-table pair-table">
              <thead>
                <tr>
                  <th className="rank-col">#</th>
                  <th>Submission A</th>
                  <th>Submission B</th>
                  <th>Overall</th>
                  <th>TED</th>
                  <th>Winnow</th>
                  <th>Call-graph</th>
                  <th>Fns</th>
                </tr>
              </thead>
              <tbody>
                {report.student_pairs.map((pair, idx) => (
                  <tr
                    key={`${pair.submission_a_id}-${pair.submission_b_id}`}
                    className="pair-row"
                    onClick={() => onInspectPair(pair)}
                    title="Inspect function-level matches"
                  >
                    <td className="rank-col">
                      <span className={`rank rank--${riskLevel(pair.overall_score)}`}>
                        {idx + 1}
                      </span>
                    </td>
                    <td>{pair.submission_a_name}</td>
                    <td>{pair.submission_b_name}</td>
                    <td>
                      <ScoreCell score={pair.overall_score} strong />
                    </td>
                    <td>{formatPercent(pair.ted_score)}</td>
                    <td>{formatPercent(pair.winnow_score)}</td>
                    <td>{formatPercent(pair.callgraph_score)}</td>
                    <td>{pair.aligned_function_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {topPair !== null && (
            <p className="muted hint">Tip: click a row to inspect aligned functions for that pair.</p>
          )}
        </div>

        {report.ai_reference_enabled && (
          <div className="panel">
            <h3>AI reference similarity</h3>
            <p className="muted">
              Every submission-to-reference comparison, sorted by highest similarity first.
              This is <em>not</em> a claim that the code is AI-generated.
            </p>

            {report.reference_results.length === 0 ? (
              <p className="muted">No reference comparisons were produced.</p>
            ) : (
              <table className="match-table">
                <thead>
                  <tr>
                    <th>Submission</th>
                    <th>AI reference</th>
                    <th>Overall</th>
                    <th>TED</th>
                    <th>Winnow</th>
                    <th>Call-graph</th>
                    <th>Code</th>
                  </tr>
                </thead>
                <tbody>
                  {report.reference_results.map((result) => {
                    const reference = referenceByLabel.get(result.reference_label);
                    return (
                      <tr key={`${result.submission_id}-${result.reference_label}`}>
                        <td>{result.submission_name}</td>
                        <td>{result.reference_label}</td>
                        <td>
                          <ScoreCell score={result.overall_score} strong />
                        </td>
                        <td>{formatPercent(result.ted_score)}</td>
                        <td>{formatPercent(result.winnow_score)}</td>
                        <td>{formatPercent(result.callgraph_score)}</td>
                        <td>
                          {reference ? (
                            <button
                              type="button"
                              className="link-button"
                              onClick={() => setSelectedReference(reference)}
                            >
                              view
                            </button>
                          ) : (
                            <span className="muted">n/a</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>

      {selectedReference !== null && (
        <ReferenceCodeModal
          reference={selectedReference}
          onClose={() => setSelectedReference(null)}
        />
      )}
    </>
  );
}

function Stat({
  label,
  value,
  color,
}: {
  readonly label: string;
  readonly value: string;
  readonly color?: string;
}): JSX.Element {
  return (
    <div className="stat">
      <span className="stat__value" style={color ? { color } : undefined}>
        {value}
      </span>
      <span className="stat__label">{label}</span>
    </div>
  );
}

function ScoreCell({ score, strong }: { readonly score: number; readonly strong?: boolean }): JSX.Element {
  const color = riskColor(score);
  return (
    <span className="score-cell">
      <span className="score-cell__bar" aria-hidden>
        <span style={{ width: `${Math.round(score * 100)}%`, backgroundColor: color }} />
      </span>
      <span style={{ color }} className={strong ? "score-cell__val strong" : "score-cell__val"}>
        {formatPercent(score)}
      </span>
    </span>
  );
}

function ReferenceCodeModal({
  reference,
  onClose,
}: {
  readonly reference: AiReferenceSolution;
  readonly onClose: () => void;
}): JSX.Element {
  return (
    <div className="modal" role="dialog" aria-modal="true">
      <div className="modal__backdrop" onClick={onClose} />
      <div className="modal__body panel code-modal">
        <div className="report__head">
          <h2>{reference.label}</h2>
          <button type="button" className="secondary" onClick={onClose}>
            Close
          </button>
        </div>
        <pre className="code-view">
          <code>{reference.source_code}</code>
        </pre>
      </div>
    </div>
  );
}
