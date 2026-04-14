import { useEffect, useMemo, useState } from "react";
import type { DqRule } from "../types/atlan";

interface Props {
  rules: DqRule[];
}

interface ExecutionRow {
  key: string;
  ruleId: string | null;
  ruleName: string;
  description: string;
  executionDate: string;
  status: string;
}

type DatePreset = "all" | "today" | "yesterday" | "last7" | "last30";

const PAGE_SIZE = 7;

function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  const cls =
    normalized === "passed"
      ? "status-passed"
      : normalized === "failed"
      ? "status-failed"
      : "status-other";
  return <span className={`status-badge ${cls}`}>{status || "—"}</span>;
}

/** Flatten one-rule-many-executions into per-execution rows (newest first). */
function toExecutionRows(rules: DqRule[]): ExecutionRow[] {
  const rows: ExecutionRow[] = [];
  for (const rule of rules) {
    const entries = rule.results && rule.results.length > 0 ? rule.results : [];
    if (entries.length === 0) {
      rows.push({
        key: `${rule.guid}::empty`,
        ruleId: rule.id,
        ruleName: rule.name,
        description: rule.description || rule.name,
        executionDate: "",
        status: "",
      });
      continue;
    }
    for (let i = 0; i < entries.length; i++) {
      const [date = "", status = ""] = entries[i].split("|");
      rows.push({
        key: `${rule.guid}::${i}`,
        ruleId: rule.id,
        ruleName: rule.name,
        description: rule.description || rule.name,
        executionDate: date,
        status,
      });
    }
  }
  rows.sort((a, b) => b.executionDate.localeCompare(a.executionDate));
  return rows;
}

/** Current UTC date as YYYY-MM-DD. Execution timestamps in the dataset are UTC. */
function todayUtc(): string {
  return new Date().toISOString().slice(0, 10);
}

/** Shift a YYYY-MM-DD string by N days (negative = past). */
function shiftDate(dateStr: string, days: number): string {
  const d = new Date(dateStr + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

function matchesPreset(executionDate: string, preset: DatePreset): boolean {
  if (preset === "all") return true;
  if (!executionDate) return false;
  const datePart = executionDate.slice(0, 10); // "YYYY-MM-DD"
  const today = todayUtc();
  if (preset === "today") return datePart === today;
  if (preset === "yesterday") return datePart === shiftDate(today, -1);
  if (preset === "last7") {
    const from = shiftDate(today, -6); // 7-day window inclusive of today
    return datePart >= from && datePart <= today;
  }
  if (preset === "last30") {
    const from = shiftDate(today, -29);
    return datePart >= from && datePart <= today;
  }
  return true;
}

const DATE_PRESETS: { id: DatePreset; label: string }[] = [
  { id: "all", label: "All time" },
  { id: "today", label: "Today" },
  { id: "yesterday", label: "Yesterday" },
  { id: "last7", label: "Last 7 days" },
  { id: "last30", label: "Last 30 days" },
];

export function RulesTable({ rules }: Props) {
  const allRows = useMemo(() => toExecutionRows(rules), [rules]);

  const [search, setSearch] = useState("");
  const [datePreset, setDatePreset] = useState<DatePreset>("all");
  const [visible, setVisible] = useState(PAGE_SIZE);

  const filteredRows = useMemo(() => {
    const q = search.trim().toLowerCase();
    return allRows.filter((r) => {
      if (!matchesPreset(r.executionDate, datePreset)) return false;
      if (q && !r.description.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [allRows, search, datePreset]);

  // Reset pagination whenever filters/data change.
  useEffect(() => {
    setVisible(PAGE_SIZE);
  }, [filteredRows]);

  if (!rules || rules.length === 0) {
    return (
      <div className="card">
        <div className="empty-state">No DQ rules linked to this asset.</div>
      </div>
    );
  }

  const shownRows = filteredRows.slice(0, visible);
  const hasMore = visible < filteredRows.length;
  const remaining = filteredRows.length - visible;
  const nextBatch = Math.min(PAGE_SIZE, remaining);

  return (
    <div className="card">
      <div className="filters-row">
        <label className="filter-search">
          <SearchIcon />
          <input
            type="search"
            placeholder="Search by description…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>

        <div className="filter-date">
          <select
            value={datePreset}
            onChange={(e) => setDatePreset(e.target.value as DatePreset)}
          >
            {DATE_PRESETS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        {(search || datePreset !== "all") && (
          <button
            type="button"
            className="filter-clear"
            onClick={() => {
              setSearch("");
              setDatePreset("all");
            }}
          >
            Clear
          </button>
        )}
      </div>

      <div className="table-wrapper">
        <table className="rules-table">
          <thead>
            <tr>
              <th>Rule ID</th>
              <th>Rule description</th>
              <th>Execution date</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {shownRows.length === 0 ? (
              <tr>
                <td colSpan={4} className="empty-row">
                  No executions match the current filters.
                </td>
              </tr>
            ) : (
              shownRows.map((r) => (
                <tr key={r.key}>
                  <td className="mono">{r.ruleId || "—"}</td>
                  <td className="desc-cell" title={r.description}>
                    {r.description}
                  </td>
                  <td className="mono">{r.executionDate || "—"}</td>
                  <td>
                    <StatusBadge status={r.status} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {hasMore && (
        <div className="load-more-row">
          <button
            type="button"
            className="btn-load-more"
            onClick={() =>
              setVisible((v) => Math.min(v + PAGE_SIZE, filteredRows.length))
            }
          >
            Load {nextBatch} more
            <ChevronDownIcon />
          </button>
          <span className="load-more-meta">
            {shownRows.length} of {filteredRows.length}
          </span>
        </div>
      )}
    </div>
  );
}

function SearchIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M10.5 10.5l3 3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}

function ChevronDownIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2.5 4.5l3.5 3 3.5-3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
