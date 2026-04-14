import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { DqRule } from "../types/atlan";

interface Props {
  rules: DqRule[];
}

type StatusBucket = "passed" | "failed" | "delayed";

interface BucketCounts {
  passed: number;
  failed: number;
  delayed: number;
  total: number;
}

function countExecutions(rules: DqRule[]): BucketCounts {
  const c: BucketCounts = { passed: 0, failed: 0, delayed: 0, total: 0 };
  for (const r of rules) {
    const entries = r.results || [];
    if (entries.length === 0) {
      c.delayed++;
      c.total++;
      continue;
    }
    for (const entry of entries) {
      const [, rawStatus = ""] = entry.split("|");
      const s = rawStatus.trim().toLowerCase();
      if (s === "passed") c.passed++;
      else if (s === "failed") c.failed++;
      else c.delayed++;
      c.total++;
    }
  }
  return c;
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

type StatsScope = "all" | "table" | "column";

const STATS_SCOPE_OPTIONS: { id: StatsScope; label: string }[] = [
  { id: "all", label: "All" },
  { id: "table", label: "Table" },
  { id: "column", label: "Column" },
];

export function StatsWidgets({ rules }: Props) {
  const [scope, setScope] = useState<StatsScope>("all");

  const counts = useMemo(() => {
    const filtered =
      scope === "all"
        ? rules
        : rules.filter((r) => r.scope === scope);
    return countExecutions(filtered);
  }, [rules, scope]);

  if (countExecutions(rules).total === 0) return null;

  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const handleOutside = useCallback((e: MouseEvent) => {
    if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node))
      setOpen(false);
  }, []);

  useEffect(() => {
    if (open) document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, [open, handleOutside]);

  const activeLabel = STATS_SCOPE_OPTIONS.find((o) => o.id === scope)?.label;

  return (
    <div className="stats-card">
      <div className="stats-card-header">
        <h2 className="stats-card-title">Rule results</h2>
        <div className="stats-scope-pill" ref={dropdownRef}>
          <button
            type="button"
            className={`stats-scope-pill-btn ${open ? "stats-scope-pill-open" : ""}`}
            onClick={() => setOpen((v) => !v)}
          >
            {activeLabel}
            <ChevronIcon />
          </button>
          {open && (
            <div className="stats-scope-dropdown">
              {STATS_SCOPE_OPTIONS.map((o) => (
                <button
                  key={o.id}
                  type="button"
                  className={`stats-scope-option ${o.id === scope ? "stats-scope-option-active" : ""}`}
                  onClick={() => { setScope(o.id); setOpen(false); }}
                >
                  {o.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
      <div className="stats-card-grid">
        <StatItem value={counts.passed} percent={counts.total > 0 ? Math.round((counts.passed / counts.total) * 100) : 0} label="Passed" variant="passed" icon={<CheckIcon />} />
        <StatItem value={counts.failed} percent={counts.total > 0 ? Math.round((counts.failed / counts.total) * 100) : 0} label="Failed" variant="failed" icon={<XIcon />} />
        <StatItem value={counts.delayed} percent={counts.total > 0 ? Math.round((counts.delayed / counts.total) * 100) : 0} label="Delayed" variant="delayed" icon={<ClockIcon />} />
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

function ChevronIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2.5 4.5l3.5 3 3.5-3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
