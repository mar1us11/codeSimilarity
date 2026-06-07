import type { JSX } from "react";

interface PipelineOverviewProps {
  readonly submissionCount: number;
}

interface Stage {
  readonly track: string;
  readonly steps: readonly string[];
  readonly out: string;
}

const STAGES: readonly Stage[] = [
  {
    track: "Structure",
    steps: ["Tree-sitter", "AST", "Normalize", "Tree Edit Distance"],
    out: "AST similarity",
  },
  {
    track: "Fingerprints",
    steps: ["Tokens", "Winnowing", "Fingerprints", "Jaccard"],
    out: "Fingerprint similarity",
  },
  {
    track: "Alignment",
    steps: ["Function matching", "Hopcroft–Karp"],
    out: "Submission similarity",
  },
  {
    track: "Clusters",
    steps: ["Submission graph", "DFS / BFS"],
    out: "Plagiarism clusters",
  },
];

export function PipelineOverview({ submissionCount }: PipelineOverviewProps): JSX.Element {
  return (
    <div className="panel pipeline">
      <h2>How CodeGuard scores a cohort</h2>
      <p className="muted">
        Add every student submission on the left, then run the analysis below to compare{" "}
        <em>every</em> pair structurally, not by text. Each track below runs on every comparison
        and is fused into one explainable score.
      </p>

      <div className="pipeline__tracks">
        {STAGES.map((stage) => (
          <div className="pipeline__track" key={stage.track}>
            <span className="pipeline__track-label">{stage.track}</span>
            <div className="pipeline__flow">
              {stage.steps.map((step) => (
                <span className="pipeline__step" key={step}>
                  {step}
                </span>
              ))}
              <span className="pipeline__out">{stage.out}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="pipeline__fusion">
        <span className="pipeline__weight">
          <strong>50%</strong> Tree Edit Distance
        </span>
        <span className="pipeline__weight">
          <strong>35%</strong> Winnowing / Jaccard
        </span>
        <span className="pipeline__weight">
          <strong>15%</strong> Call-graph
        </span>
      </div>

      <p className="muted pipeline__count">
        {submissionCount < 2
          ? "Add at least two submissions to analyze."
          : `${submissionCount} submissions · ${
              (submissionCount * (submissionCount - 1)) / 2
            } pairs to compare`}
      </p>
    </div>
  );
}
