/**
 * Per-browser-tab "workspace" identity.
 *
 * There are no user accounts. Each tab gets a random token kept in
 * `sessionStorage`, which the API client sends on every request so submissions
 * are private to that tab. Because `sessionStorage` is cleared when the tab is
 * closed, reopening the app starts from an empty submissions list.
 */

const STORAGE_KEY = "codeguard.workspace";

function randomToken(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  // Fallback for environments without crypto.randomUUID.
  return `ws-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

/** Return this tab's workspace token, creating and persisting one on first use. */
export function getWorkspaceId(): string {
  let token = sessionStorage.getItem(STORAGE_KEY);
  if (token === null || token === "") {
    token = randomToken();
    sessionStorage.setItem(STORAGE_KEY, token);
  }
  return token;
}
