import { useCallback, useEffect, useState, type JSX } from "react";

import { api, ApiError } from "./api/client";
import { AnalysisControls } from "./components/AnalysisControls";
import { AnalysisReportView } from "./components/AnalysisReportView";
import { ComparisonPanel } from "./components/ComparisonPanel";
import { PipelineOverview } from "./components/PipelineOverview";
import { PreviousScoresModal } from "./components/PreviousScoresModal";
import { SaveLabPanel } from "./components/SaveLabPanel";
import { SubmissionForm } from "./components/SubmissionForm";
import { SubmissionList } from "./components/SubmissionList";
import type {
  AnalysisCapabilities,
  AnalysisReport,
  AnalysisRequest,
  ComparisonRead,
  StudentPairResult,
  SubmissionSummary,
} from "./types/api";

interface PairDetail {
  readonly subjectA: string;
  readonly subjectB: string;
  readonly comparison: ComparisonRead | null;
}

type AppView = "submissions" | "similarity";

export function App(): JSX.Element {
  const [submissions, setSubmissions] = useState<readonly SubmissionSummary[]>([]);
  const [capabilities, setCapabilities] = useState<AnalysisCapabilities | null>(null);
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [running, setRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [pairDetail, setPairDetail] = useState<PairDetail | null>(null);
  const [view, setView] = useState<AppView>("submissions");
  const [showPrevious, setShowPrevious] = useState<boolean>(false);

  const refresh = useCallback(async (): Promise<void> => {
    try {
      setSubmissions(await api.listSubmissions());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load submissions");
    }
  }, []);

  useEffect(() => {
    void refresh();
    void api
      .analysisCapabilities()
      .then(setCapabilities)
      .catch(() => setCapabilities(null));
  }, [refresh]);

  const handleDelete = useCallback(
    async (id: number): Promise<void> => {
      try {
        await api.deleteSubmission(id);
        setReport(null);
        await refresh();
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to delete submission");
      }
    },
    [refresh],
  );

  async function runAnalysis(request: AnalysisRequest): Promise<void> {
    setRunning(true);
    setError(null);
    setView("similarity");
    try {
      setReport(await api.analyze(request));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Analysis failed");
    } finally {
      setRunning(false);
    }
  }

  async function inspectPair(pair: StudentPairResult): Promise<void> {
    setPairDetail({
      subjectA: pair.submission_a_name,
      subjectB: pair.submission_b_name,
      comparison: null,
    });
    try {
      const comparison = await api.compare({
        submission_a_id: pair.submission_a_id,
        submission_b_id: pair.submission_b_id,
        force: true,
      });
      setPairDetail({
        subjectA: pair.submission_a_name,
        subjectB: pair.submission_b_name,
        comparison,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load pair detail");
      setPairDetail(null);
    }
  }

  return (
    <div className="app">
      <header className="app__header">
        <div className="app__brand">
          <span className="app__logo" aria-hidden>
            <svg viewBox="0 0 24 24" fill="none" width="24" height="24">
              <path
                d="M12 2.5 4 6v5.5c0 4.6 3.2 8.4 8 9.5 4.8-1.1 8-4.9 8-9.5V6l-8-3.5Z"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinejoin="round"
              />
              <path
                d="m8.6 12 2.3 2.4 4.4-4.6"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          <div>
            <h1>CodeGuard</h1>
            <p>Structural plagiarism detection for C assignments.</p>
          </div>
        </div>
        <div className="app__actions">
          <button
            type="button"
            className="secondary previous-scores-btn"
            onClick={() => setShowPrevious(true)}
          >
            <span aria-hidden>🕘</span> Previous scores
          </button>
          <nav className="view-tabs" aria-label="Primary view">
            <button
              type="button"
              className={view === "submissions" ? "view-tabs__tab active" : "view-tabs__tab"}
              onClick={() => setView("submissions")}
            >
              Submissions
            </button>
            <button
              type="button"
              className={view === "similarity" ? "view-tabs__tab active" : "view-tabs__tab"}
              disabled={report === null && !running}
              onClick={() => setView("similarity")}
            >
              Similarities
            </button>
          </nav>
        </div>
      </header>

      {error !== null && (
        <div className="error banner">
          <span>{error}</span>
          <button type="button" className="link-danger" onClick={() => setError(null)}>
            dismiss
          </button>
        </div>
      )}

      {view === "submissions" ? (
        <div className="layout">
          <aside className="layout__sidebar">
            <SubmissionForm
              onCreated={() => {
                void refresh();
              }}
            />
            <SubmissionList
              submissions={submissions}
              onDelete={(id) => {
                void handleDelete(id);
              }}
            />
          </aside>

          <main className="layout__main">
            <PipelineOverview submissionCount={submissions.length} />
            <AnalysisControls
              submissionCount={submissions.length}
              capabilities={capabilities}
              running={running}
              onRun={(request) => {
                void runAnalysis(request);
              }}
            />
          </main>
        </div>
      ) : (
        <main className="results-page">
          <div className="results-toolbar panel">
            <div>
              <h2>Similarity workspace</h2>
              <p className="muted">
                {submissions.length} submissions in this assignment
                {report?.ai_reference_enabled
                  ? " · compared against AI reference solutions"
                  : ""}
                . To change the AI-reference choice, go back and run again.
              </p>
            </div>
            <button type="button" className="secondary" onClick={() => setView("submissions")}>
              Back to submissions
            </button>
          </div>
          {report !== null && !running && <SaveLabPanel report={report} />}
          <AnalysisReportView
            report={report}
            running={running}
            onInspectPair={(pair) => {
              void inspectPair(pair);
            }}
          />
        </main>
      )}

      {showPrevious && <PreviousScoresModal onClose={() => setShowPrevious(false)} />}

      {pairDetail !== null && (
        <ComparisonPanel
          comparison={pairDetail.comparison}
          loading={pairDetail.comparison === null}
          subjectA={pairDetail.subjectA}
          subjectB={pairDetail.subjectB}
          onClose={() => setPairDetail(null)}
        />
      )}
    </div>
  );
}
