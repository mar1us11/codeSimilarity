import { useState, type JSX } from "react";

import { api, ApiError } from "../api/client";
import type { AnalysisReport } from "../types/api";
import { AnalysisReportView } from "./AnalysisReportView";

interface PreviousScoresModalProps {
  readonly onClose: () => void;
}

/**
 * Reopen a saved score set by typing its name + password. There is no browsable
 * list; you can only open a lab you already know the name and password for, so
 * one person's saved scores stay invisible to everyone else. The unlocked
 * report is rendered read-only (row drill-down is disabled because the original
 * submissions may no longer exist).
 */
export function PreviousScoresModal({ onClose }: PreviousScoresModalProps): JSX.Element {
  const [name, setName] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [unlocking, setUnlocking] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [openedName, setOpenedName] = useState<string>("");

  async function unlock(): Promise<void> {
    if (name.trim() === "" || password.trim() === "") {
      return;
    }
    setUnlocking(true);
    setError(null);
    try {
      const unlocked = await api.unlockLab(name.trim(), password);
      setReport(unlocked);
      setOpenedName(name.trim());
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setError("Incorrect name or password.");
      } else {
        setError(err instanceof ApiError ? err.message : "Could not unlock");
      }
    } finally {
      setUnlocking(false);
    }
  }

  function back(): void {
    setReport(null);
    setPassword("");
    setError(null);
  }

  return (
    <div className="modal" role="dialog" aria-modal="true">
      <div className="modal__backdrop" onClick={onClose} />
      <div className="modal__body panel code-modal">
        <div className="report__head">
          <h2>{report !== null ? openedName : "Open saved scores"}</h2>
          <div className="modal__head-actions">
            {report !== null && (
              <button type="button" className="secondary" onClick={back}>
                ← Open another
              </button>
            )}
            <button type="button" className="secondary" onClick={onClose}>
              Close
            </button>
          </div>
        </div>

        {/* --- Name + password prompt --------------------------------------- */}
        {report === null && (
          <div className="lab-unlock">
            <p className="muted">
              Enter the <strong>name</strong> and <strong>password</strong> you chose when these
              scores were saved.
            </p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void unlock();
              }}
            >
              <label>
                Lab name
                <input
                  type="text"
                  value={name}
                  autoFocus
                  placeholder="e.g. Lab 3, Group 2"
                  onChange={(e) => setName(e.target.value)}
                />
              </label>
              <label>
                Password
                <input
                  type="password"
                  value={password}
                  autoComplete="current-password"
                  onChange={(e) => setPassword(e.target.value)}
                />
              </label>
              {error !== null && <p className="error">{error}</p>}
              <button
                type="submit"
                disabled={unlocking || name.trim() === "" || password.trim() === ""}
              >
                {unlocking ? "Opening…" : "Open scores"}
              </button>
            </form>
          </div>
        )}

        {/* --- Unlocked report ---------------------------------------------- */}
        {report !== null && (
          <div className="lab-report">
            <AnalysisReportView report={report} running={false} onInspectPair={() => {}} />
          </div>
        )}
      </div>
    </div>
  );
}
