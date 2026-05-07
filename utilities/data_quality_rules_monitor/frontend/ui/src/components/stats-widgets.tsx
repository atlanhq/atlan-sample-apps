import type { DqRule } from "../types/atlan";

interface Props {
  rules: DqRule[];
}

interface Counts {
  passed: number;
  failed: number;
  na: number;
  total: number;
  lastRun: string | null;
}

function getCounts(rules: DqRule[]): Counts {
  let passed = 0, failed = 0, na = 0;
  let lastRun: string | null = null;

  for (const r of rules) {
    const s = r.last_status?.toLowerCase() ?? "";
    if (s === "passed") passed++;
    else if (s === "failed") failed++;
    else na++;

    if (r.last_execution_date) {
      if (!lastRun || r.last_execution_date > lastRun) lastRun = r.last_execution_date;
    }
  }

  return { passed, failed, na, total: passed + failed + na, lastRun };
}

export function StatsWidgets({ rules }: Props) {
  if (rules.length === 0) return null;

  const { passed, failed, na, total, lastRun } = getCounts(rules);

  return (
    <div className="dq-header">
      {/* Top row: LAST RUN STATUS label + counts */}
      <div className="dq-header-top">
        <span className="dq-header-label">Last run status</span>

        <span className="dq-status-count pass">
          <span className="dot" />
          {passed} Passed
        </span>
        <span className="dq-header-sep">·</span>
        <span className="dq-status-count fail">
          <span className="dot" />
          {failed} Failed
        </span>
        <span className="dq-header-sep">·</span>
        <span className="dq-status-count na">
          <span className="dot" />
          {na} Not evaluated
        </span>
      </div>

      {/* Meta row */}
      <div className="dq-meta">
        <span className="dq-meta-item">
          <RulesIcon />
          {total} rule{total !== 1 ? "s" : ""}
        </span>
        {lastRun && (
          <>
            <span className="dq-meta-sep">·</span>
            <span className="dq-meta-item">
              <ClockIcon />
              Last run {lastRun}
            </span>
          </>
        )}
      </div>
    </div>
  );
}

function RulesIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ color: "var(--gray-400)" }}>
      <rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.4" />
      <path d="M5 6h6M5 8.5h4M5 11h5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ color: "var(--gray-400)" }}>
      <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.4" />
      <path d="M8 5v3.5l2 1.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
