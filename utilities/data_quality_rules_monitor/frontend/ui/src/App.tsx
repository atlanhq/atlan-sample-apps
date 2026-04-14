import { useAtlanAuth } from "./hooks/use-atlan-auth";
import { useDqRules } from "./hooks/use-dq-rules";
import { LoadingState } from "./components/loading-state";
import { RulesTable } from "./components/rules-table";
import { StatsWidgets } from "./components/stats-widgets";

export default function App() {
  const { authState, token, baseUrl, assetId, error: authError } =
    useAtlanAuth();

  const { rules, viewMode, loading, error } = useDqRules(baseUrl, token, assetId);

  if (authState !== "authenticated") {
    return <LoadingState authState={authState} error={authError} />;
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
        <p>Loading data quality rules…</p>
      </div>
    );
  }

  return (
    <div className="app">
      {error && <div className="alert alert-error">{error}</div>}
      <StatsWidgets rules={rules} />
      <RulesTable rules={rules} viewMode={viewMode} />
    </div>
  );
}
