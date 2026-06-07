import {
  useRef,
  useState,
  type ChangeEvent,
  type DragEvent,
  type FormEvent,
  type JSX,
} from "react";

import { api, ApiError } from "../api/client";
import type { SubmissionRead } from "../types/api";

interface SubmissionFormProps {
  readonly onCreated: (submission: SubmissionRead) => void;
}

type Mode = "upload" | "paste";

const SAMPLE = `int add(int a, int b) {
    int result = a + b;
    return result;
}

int run(void) {
    return add(2, 3);
}
`;

const ALLOWED = [".c", ".h"];

function hasAllowedExtension(filename: string): boolean {
  return ALLOWED.some((ext) => filename.toLowerCase().endsWith(ext));
}

/** Derive a stored filename from a student name (the model still needs one). */
function deriveFilename(studentName: string): string {
  const slug = studentName
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
  return slug === "" ? "submission.c" : `${slug}.c`;
}

export function SubmissionForm({ onCreated }: SubmissionFormProps): JSX.Element {
  const [mode, setMode] = useState<Mode>("upload");

  // Student name applies to both modes.
  const [name, setName] = useState<string>("");
  const [source, setSource] = useState<string>(SAMPLE);

  // Upload-mode state: files are staged on selection and only sent on submit.
  const [stagedFiles, setStagedFiles] = useState<readonly File[]>([]);

  // Shared state
  const [busy, setBusy] = useState<boolean>(false);
  const [dragging, setDragging] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (mode === "upload") {
      await uploadStaged();
    } else {
      await submitPaste();
    }
  }

  async function submitPaste(): Promise<void> {
    const studentName = name.trim();
    if (studentName === "") {
      setError("Student name is required.");
      return;
    }
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const created = await api.createSubmission({
        name: studentName,
        filename: deriveFilename(studentName),
        source_code: source,
      });
      onCreated(created);
      setNotice(`Stored "${created.name}" (${created.functions.length} function(s)).`);
      setName("");
      setSource(SAMPLE);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create submission");
    } finally {
      setBusy(false);
    }
  }

  async function uploadStaged(): Promise<void> {
    const files = stagedFiles;
    if (files.length === 0) {
      setError("Choose a .c / .h file first.");
      return;
    }
    const trimmedName = name.trim();
    if (files.length === 1 && trimmedName === "") {
      setError("Student name is required.");
      return;
    }

    setBusy(true);
    setError(null);
    setNotice(null);
    const stored: string[] = [];
    const failed: string[] = [];
    for (const file of files) {
      // A single file is one student, so use the typed name. With several
      // files at once we can't tell them apart, so fall back to each filename.
      const studentName = files.length === 1 && trimmedName !== "" ? trimmedName : file.name;
      try {
        const created = await api.uploadSubmission(file, studentName);
        onCreated(created);
        stored.push(created.name);
      } catch (err) {
        failed.push(`${file.name}: ${err instanceof ApiError ? err.message : "upload failed"}`);
      }
    }
    if (stored.length > 0) {
      setName("");
      setStagedFiles([]);
      setNotice(`Uploaded ${stored.length} file(s): ${stored.join(", ")}`);
    }
    if (failed.length > 0) {
      setError(failed.join(" • "));
    }
    setBusy(false);
  }

  /** Validate and stage the chosen files; nothing is sent until "Analyze & store". */
  function stageFiles(files: readonly File[]): void {
    if (files.length === 0) {
      return;
    }
    const invalid = files.filter((f) => !hasAllowedExtension(f.name));
    if (invalid.length > 0) {
      setError(`Only .c / .h files are allowed: ${invalid.map((f) => f.name).join(", ")}`);
      return;
    }
    setError(null);
    setNotice(null);
    setStagedFiles(files);
  }

  function handleFiles(event: ChangeEvent<HTMLInputElement>): void {
    const files = Array.from(event.target.files ?? []);
    event.target.value = ""; // allow re-selecting the same file
    stageFiles(files);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>): void {
    event.preventDefault();
    setDragging(false);
    if (busy) {
      return;
    }
    stageFiles(Array.from(event.dataTransfer.files ?? []));
  }

  function switchMode(next: Mode): void {
    if (next === mode) {
      return;
    }
    setMode(next);
    setStagedFiles([]);
    setError(null);
    setNotice(null);
  }

  return (
    <form className="panel" onSubmit={handleSubmit}>
      <h2>Add submission</h2>

      <div className="mode-switch" role="tablist" aria-label="Submission input method">
        <button
          type="button"
          role="tab"
          aria-selected={mode === "upload"}
          className={mode === "upload" ? "mode-switch__btn active" : "mode-switch__btn"}
          disabled={busy}
          onClick={() => switchMode("upload")}
        >
          Upload file
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === "paste"}
          className={mode === "paste" ? "mode-switch__btn active" : "mode-switch__btn"}
          disabled={busy}
          onClick={() => switchMode("paste")}
        >
          Paste source
        </button>
      </div>
      <p className="muted note">
        Use <strong>one or the other</strong>: upload <code>.c</code>/<code>.h</code> file(s),{" "}
        or paste a single source by hand.
      </p>

      {mode === "upload" ? (
        <>
          <label>
            Student name
            <input
              type="text"
              value={name}
              placeholder="e.g. Student 1"
              disabled={busy}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          <div
            className={dragging ? "dropzone dropzone--active" : "dropzone"}
            onClick={() => {
              if (!busy) {
                fileInput.current?.click();
              }
            }}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
          >
            <span className="dropzone__icon" aria-hidden>
              <svg viewBox="0 0 24 24" width="26" height="26" fill="none">
                <path
                  d="M12 16V4m0 0L8 8m4-4 4 4"
                  stroke="currentColor"
                  strokeWidth="1.7"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"
                  stroke="currentColor"
                  strokeWidth="1.7"
                  strokeLinecap="round"
                />
              </svg>
            </span>
            <strong>{stagedFiles.length > 0 ? "Choose different files" : "Drop .c / .h files here"}</strong>
            <span className="dropzone__hint">
              or click to browse. Drop several files to add one student per filename
            </span>
            <input
              ref={fileInput}
              type="file"
              accept=".c,.h,text/x-c"
              multiple
              hidden
              onChange={handleFiles}
            />
          </div>
          {stagedFiles.length > 0 && (
            <div className="staged-files">
              <span className="muted">
                {stagedFiles.length === 1
                  ? `Selected: ${stagedFiles[0]?.name ?? ""}`
                  : `${stagedFiles.length} files selected (one student per filename): ${stagedFiles
                      .map((f) => f.name)
                      .join(", ")}`}
              </span>
              <button
                type="button"
                className="link-danger"
                disabled={busy}
                onClick={() => setStagedFiles([])}
              >
                clear
              </button>
            </div>
          )}
        </>
      ) : (
        <>
          <label>
            Student name
            <input
              type="text"
              value={name}
              placeholder="e.g. Student 1"
              disabled={busy}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          <label>
            C source
            <textarea
              value={source}
              spellCheck={false}
              rows={12}
              onChange={(e) => setSource(e.target.value)}
            />
          </label>
        </>
      )}

      {error !== null && <p className="error">{error}</p>}
      {notice !== null && <p className="success">{notice}</p>}

      <button
        type="submit"
        disabled={
          busy ||
          (mode === "paste"
            ? source.trim() === "" || name.trim() === ""
            : stagedFiles.length === 0 || (stagedFiles.length === 1 && name.trim() === ""))
        }
      >
        {busy ? "Analyzing…" : "Analyze & store"}
      </button>
    </form>
  );
}
