import { useMemo } from "react";
import type { DqRule } from "../types/atlan";

interface Props {
  rules: DqRule[];
}

type StatusBucket = "passed" | "failed" | "delayed";

interface Stats {
  total: number;
  counts: Record<StatusBucket, number>;
}

function computeStats(rules: DqRule[]): Stats {
  const counts: Record<StatusBucket, number> = {
    passed: 0,
    failed: 0,
    delayed: 0,
  };
  let total = 0;
  for (const r of rules) {
    const entries = r.results || [];
    if (entries.length === 0) {
      // A rule with no executions still shows as one "delayed" row in the table.
      counts.delayed++;
      total++;
      continue;
    }
    for (const entry of entries) {
      const [, rawStatus = ""] = entry.split("|");
      const s = rawStatus.trim().toLowerCase();
      if (s === "passed") counts.passed++;
      else if (s === "failed") counts.failed++;
      else counts.delayed++;
      total++;
    }
  }
  return { total, counts };
}

interface StatItemProps {
  value: number;
  percent: number;
  label: string;
  variant: StatusBucket;
  icon: React.ReactNode;
}

function StatItem({ value, percent, label, variant, icon }: StatItemProps) {
  return (
    <div className="stat-item">
      <div className={`stat-item-icon stat-${variant}`}>{icon}</div>
      <div className="stat-item-text">
        <div className="stat-item-value-row">
          <span className="stat-item-value">{value}</span>
          <span className={`stat-item-pct stat-${variant}`}>{percent}%</span>
        </div>
        <div className="stat-item-label">{label}</div>
      </div>
    </div>
  );
}

export function StatsWidgets({ rules }: Props) {
  const stats = useMemo(() => computeStats(rules), [rules]);
  if (stats.total === 0) return null;

  const pct = (n: number) =>
    stats.total > 0 ? Math.round((n / stats.total) * 100) : 0;

  return (
    <div className="stats-card">
      <div className="stats-card-header">
        <h2 className="stats-card-title">Rule results</h2>
        <span className="stats-card-subtitle">
          {stats.total} execution{stats.total === 1 ? "" : "s"}
        </span>
      </div>
      <div className="stats-card-grid">
        <StatItem
          value={stats.counts.passed}
          percent={pct(stats.counts.passed)}
          label="Passed"
          variant="passed"
          icon={<CheckIcon />}
        />
        <StatItem
          value={stats.counts.failed}
          percent={pct(stats.counts.failed)}
          label="Failed"
          variant="failed"
          icon={<XIcon />}
        />
        <StatItem
          value={stats.counts.delayed}
          percent={pct(stats.counts.delayed)}
          label="Delayed"
          variant="delayed"
          icon={<ClockIcon />}
        />
      </div>
    </div>
  );
}

function CheckIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="1.6" />
      <path d="M6.5 10l2.5 2.5L13.5 8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function XIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="1.6" />
      <path d="M7 7l6 6M13 7l-6 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="1.6" />
      <path d="M10 5.5V10l3 2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
