import { useAtlanAuth } from "./hooks/use-atlan-auth";
import { useObservability } from "./hooks/use-observability";
import { LoadingState } from "./components/loading-state";
import { ExecutionsTable } from "./components/executions-table";

export default function App() {
  const { authState, token, baseUrl, assetId, error: authError } =
    useAtlanAuth();

  const { executions, loading, error } = useObservability(baseUrl, token, assetId);

  if (authState !== "authenticated") {
    return <LoadingState authState={authState} error={authError} />;
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
        <p>Loading observability data…</p>
      </div>
    );
  }

  return (
    <div className="app">
      {error && <div className="alert alert-error">{error}</div>}
      <div className="stats-summary">
        <span className="stats-summary-count">{executions.length}</span>
        <span className="stats-summary-label">executions</span>
      </div>
      <ExecutionsTable executions={executions} />
    </div>
  );
}
