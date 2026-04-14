import type { AuthState } from "../types/atlan";

interface Props {
  authState: AuthState;
  error: string | null;
}

export function LoadingState({ authState, error }: Props) {
  if (authState === "error" || error) {
    return (
      <div className="loading-container">
        <div className="alert alert-error">{error || "Authentication error"}</div>
      </div>
    );
  }
  if (authState === "logged_out") {
    return (
      <div className="loading-container">
        <p>You have been logged out.</p>
      </div>
    );
  }
  return (
    <div className="loading-container">
      <div className="spinner" />
      <p>Connecting to Atlan…</p>
    </div>
  );
}
