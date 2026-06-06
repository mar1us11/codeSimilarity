import type { JSX } from "react";

import type { SubmissionSummary } from "../types/api";

interface SubmissionListProps {
  readonly submissions: readonly SubmissionSummary[];
  readonly onDelete: (id: number) => void;
}

export function SubmissionList({ submissions, onDelete }: SubmissionListProps): JSX.Element {
  return (
    <div className="panel">
      <div className="report__head">
        <h2>Submissions</h2>
        <span className="count-pill">{submissions.length}</span>
      </div>

      {submissions.length === 0 ? (
        <p className="muted">No submissions yet. Add one to begin.</p>
      ) : (
        <table className="submission-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Fns</th>
              <th>AST</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {submissions.map((submission) => (
              <tr key={submission.id}>
                <td>
                  <span className="submission-name">{submission.name}</span>
                  <span className="muted"> · {submission.filename}</span>
                </td>
                <td>{submission.function_count}</td>
                <td>{submission.ast_node_count}</td>
                <td>
                  <button
                    type="button"
                    className="link-danger"
                    onClick={() => onDelete(submission.id)}
                  >
                    delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
