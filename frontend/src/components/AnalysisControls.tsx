import { useState, type JSX } from "react";

import type { AnalysisCapabilities, AnalysisRequest } from "../types/api";

interface AnalysisControlsProps {
  readonly submissionCount: number;
  readonly capabilities: AnalysisCapabilities | null;
  readonly running: boolean;
  readonly onRun: (request: AnalysisRequest) => void;
}

export function AnalysisControls({
  submissionCount,
  capabilities,
  running,
  onRun,
}: AnalysisControlsProps): JSX.Element {
  const defaultCount = capabilities?.default_reference_count ?? 5;
  const maxCount = capabilities?.max_reference_count ?? 15;
  const aiAvailable = capabilities?.ai_reference_available ?? false;

  const [useAi, setUseAi] = useState<boolean>(false);
  const [description, setDescription] = useState<string>("");
  const [count, setCount] = useState<number>(defaultCount);

  const descriptionMissing = useAi && description.trim() === "";
  const canRun =
    submissionCount >= 2 && !running && !(useAi && (!aiAvailable || descriptionMissing));

  function handleRun(): void {
    onRun({
      submission_ids: null,
      use_ai_reference: useAi,
      problem_description: useAi ? description.trim() : null,
      reference_count: count,
    });
  }

  return (
    <div className="panel">
      <h2>Run analysis</h2>
      <p className="muted">
        Every submission is compared against every other submission. Optionally compare each
        one against AI-generated reference solutions.
      </p>

      <label className="toggle">
        <input
          type="checkbox"
          checked={useAi}
          disabled={!aiAvailable}
          onChange={(e) => setUseAi(e.target.checked)}
        />
        <span>Compare against AI reference solutions</span>
      </label>
      {!aiAvailable && (
        <p className="muted note">
          AI references are unavailable — set <code>OPENAI_API_KEY</code> in the backend to
          enable this.
        </p>
      )}

      {useAi && (
        <div className="ai-options">
          <label>
            Assignment / problem description
            <textarea
              value={description}
              rows={5}
              placeholder="Describe the assignment the students were asked to solve…"
              onChange={(e) => setDescription(e.target.value)}
            />
          </label>
          {descriptionMissing && (
            <p className="error">A description is required to generate AI references.</p>
          )}
          <label>
            Number of reference solutions
            <input
              type="number"
              min={1}
              max={maxCount}
              value={count}
              onChange={(e) => {
                const next = Number.parseInt(e.target.value, 10);
                setCount(Number.isNaN(next) ? defaultCount : Math.min(Math.max(next, 1), maxCount));
              }}
            />
          </label>
          <span className="muted">Up to {maxCount}. Default {defaultCount}.</span>
        </div>
      )}

      <div className="compare-action">
        <button type="button" disabled={!canRun} onClick={handleRun}>
          {running ? "Analyzing cohort…" : "Run analysis"}
        </button>
        {submissionCount < 2 && (
          <span className="muted">Add at least two submissions to analyze.</span>
        )}
      </div>
    </div>
  );
}
