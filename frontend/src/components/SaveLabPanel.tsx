import { useState, type JSX } from "react";

import { api, ApiError } from "../api/client";
import type { AnalysisReport } from "../types/api";

interface SaveLabPanelProps {
  readonly report: AnalysisReport;
}

/**
 * Optional control on the results page: persist the current score set behind a
 * password so it can be reopened later from "Previous scores".
 */
export function SaveLabPanel({ report }: SaveLabPanelProps): JSX.Element {
  const [label, setLabel] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [busy, setBusy] = useState<boolean>(false);
  const [saved, setSaved] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canSave = label.trim() !== "" && password.trim() !== "" && !busy;

  async function handleSave(): Promise<void> {
    setBusy(true);
    setError(null);
    setSaved(null);
    try {
      const summary = await api.saveLab({
        label: label.trim(),
        password,
        report,
      });
      setSaved(
        `Saved “${summary.label}”. Reopen it any time from “Previous scores” with this name and password.`,
      );
      setPassword("");
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError("That name is already taken. Choose a different lab name.");
      } else {
        setError(err instanceof ApiError ? err.message : "Failed to save scores");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <details className="panel save-lab">
      <summary>
        <span className="save-lab__title">Save these scores behind a password</span>
        <span className="muted"> (optional)</span>
      </summary>
      <p className="muted note">
        Stores this exact ranking so you can revisit it later without re-running the analysis.
        Pick a <strong>unique name</strong>; reopening it later needs that exact name plus the
        password, so no one else can stumble onto your scores.
      </p>
      <div className="save-lab__row">
        <label>
          Lab name
          <input
            type="text"
            value={label}
            placeholder="e.g. Lab 3, Week 12"
            onChange={(e) => setLabel(e.target.value)}
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            placeholder="Choose a password"
            autoComplete="new-password"
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
      </div>
      <button type="button" disabled={!canSave} onClick={() => void handleSave()}>
        {busy ? "Saving…" : "Save scores"}
      </button>
      {saved !== null && <p className="success">{saved}</p>}
      {error !== null && <p className="error">{error}</p>}
    </details>
  );
}
