import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { DqRule, RuleScope, ViewMode } from "../types/atlan";

interface Props {
  rules: DqRule[];
  viewMode: ViewMode;
}

interface ExecutionRow {
  key: string;
  ruleId: string | null;
  sourceAssetName: string;
  scope: RuleScope;
  columnName: string;
  description: string;
  executionDate: string;
  status: string;
}

type DatePreset = "all" | "today" | "yesterday" | "last7" | "last30";
type ScopeFilter = "all" | "table" | "column";

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

function ScopeBadge({ scope }: { scope: RuleScope }) {
  return (
    <span className={`scope-badge scope-${scope}`}>
      {scope === "table" ? "Table" : "Column"}
    </span>
  );
}

function toExecutionRows(rules: DqRule[]): ExecutionRow[] {
  const rows: ExecutionRow[] = [];
  for (const rule of rules) {
    const entries = rule.results && rule.results.length > 0 ? rule.results : [];
    if (entries.length === 0) {
      rows.push({
        key: `${rule.guid}::empty`,
        ruleId: rule.id,
        sourceAssetName: rule.source_asset_name,
        scope: rule.scope,
        columnName: rule.column_name,
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
        sourceAssetName: rule.source_asset_name,
        scope: rule.scope,
        columnName: rule.column_name,
        description: rule.description || rule.name,
        executionDate: date,
        status,
      });
    }
  }
  rows.sort((a, b) => b.executionDate.localeCompare(a.executionDate));
  return rows;
}

function todayUtc(): string {
  return new Date().toISOString().slice(0, 10);
}

function shiftDate(dateStr: string, days: number): string {
  const d = new Date(dateStr + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

function matchesPreset(executionDate: string, preset: DatePreset): boolean {
  if (preset === "all") return true;
  if (!executionDate) return false;
  const datePart = executionDate.slice(0, 10);
  const today = todayUtc();
  if (preset === "today") return datePart === today;
  if (preset === "yesterday") return datePart === shiftDate(today, -1);
  if (preset === "last7") return datePart >= shiftDate(today, -6) && datePart <= today;
  if (preset === "last30") return datePart >= shiftDate(today, -29) && datePart <= today;
  return true;
}

const DATE_PRESETS: { id: DatePreset; label: string }[] = [
  { id: "all", label: "All time" },
  { id: "today", label: "Today" },
  { id: "yesterday", label: "Yesterday" },
  { id: "last7", label: "Last 7 days" },
  { id: "last30", label: "Last 30 days" },
];

const SCOPE_OPTIONS: { id: ScopeFilter; label: string }[] = [
  { id: "all", label: "All scopes" },
  { id: "table", label: "Table" },
  { id: "column", label: "Column" },
];

export function RulesTable({ rules, viewMode }: Props) {
  const isDP = viewMode === "data-product";
  const allRows = useMemo(() => toExecutionRows(rules), [rules]);

  // State declarations first (before memos that depend on them).
  const [search, setSearch] = useState("");
  const [datePreset, setDatePreset] = useState<DatePreset>("all");
  const [scopeFilter, setScopeFilter] = useState<ScopeFilter>("all");
  const [selectedColumns, setSelectedColumns] = useState<Set<string>>(new Set());
  const [columnSearch, setColumnSearch] = useState("");
  const [columnDropdownOpen, setColumnDropdownOpen] = useState(false);
  const [selectedAssets, setSelectedAssets] = useState<Set<string>>(new Set());
  const [assetSearch, setAssetSearch] = useState("");
  const [assetDropdownOpen, setAssetDropdownOpen] = useState(false);
  const [visible, setVisible] = useState(PAGE_SIZE);
  const columnDropdownRef = useRef<HTMLDivElement>(null);
  const assetDropdownRef = useRef<HTMLDivElement>(null);

  // Distinct source asset names (DataProduct mode).
  const availableAssets = useMemo(() => {
    const set = new Set<string>();
    for (const r of rules) {
      if (r.source_asset_name) set.add(r.source_asset_name);
    }
    return [...set].sort();
  }, [rules]);

  // Distinct column names — filtered by selected tables in DP mode.
  const availableColumns = useMemo(() => {
    const set = new Set<string>();
    for (const r of rules) {
      if (r.scope !== "column" || !r.column_name) continue;
      if (selectedAssets.size > 0 && !selectedAssets.has(r.source_asset_name)) continue;
      set.add(r.column_name);
    }
    return [...set].sort();
  }, [rules, selectedAssets]);

  const filteredAssets = useMemo(() => {
    if (!assetSearch.trim()) return availableAssets;
    const q = assetSearch.trim().toLowerCase();
    return availableAssets.filter((a) => a.toLowerCase().includes(q));
  }, [availableAssets, assetSearch]);

  const toggleAsset = (name: string) => {
    setSelectedAssets((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name); else next.add(name);
      return next;
    });
    // Clear column selection when table filter changes — columns depend on tables.
    setSelectedColumns(new Set());
  };

  // Close asset dropdown on outside click.
  const handleAssetOutside = useCallback((e: MouseEvent) => {
    if (assetDropdownRef.current && !assetDropdownRef.current.contains(e.target as Node)) {
      setAssetDropdownOpen(false);
      setAssetSearch("");
    }
  }, []);

  useEffect(() => {
    if (assetDropdownOpen) document.addEventListener("mousedown", handleAssetOutside);
    return () => document.removeEventListener("mousedown", handleAssetOutside);
  }, [assetDropdownOpen, handleAssetOutside]);

  const filteredColumns = useMemo(() => {
    if (!columnSearch.trim()) return availableColumns;
    const q = columnSearch.trim().toLowerCase();
    return availableColumns.filter((c) => c.toLowerCase().includes(q));
  }, [availableColumns, columnSearch]);

  // Close dropdown on outside click.
  const handleOutsideClick = useCallback((e: MouseEvent) => {
    if (columnDropdownRef.current && !columnDropdownRef.current.contains(e.target as Node)) {
      setColumnDropdownOpen(false);
      setColumnSearch("");
    }
  }, []);

  useEffect(() => {
    if (columnDropdownOpen) {
      document.addEventListener("mousedown", handleOutsideClick);
    }
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, [columnDropdownOpen, handleOutsideClick]);

  const filteredRows = useMemo(() => {
    const q = search.trim().toLowerCase();
    return allRows.filter((r) => {
      if (!matchesPreset(r.executionDate, datePreset)) return false;
      if (q && !r.description.toLowerCase().includes(q)) return false;
      if (scopeFilter !== "all" && r.scope !== scopeFilter) return false;
      if (selectedColumns.size > 0 && r.scope === "column" && !selectedColumns.has(r.columnName)) return false;
      if (selectedColumns.size > 0 && r.scope === "table") return false;
      if (selectedAssets.size > 0 && !selectedAssets.has(r.sourceAssetName)) return false;
      return true;
    });
  }, [allRows, search, datePreset, scopeFilter, selectedColumns, selectedAssets]);

  useEffect(() => {
    setVisible(PAGE_SIZE);
  }, [filteredRows]);

  const toggleColumn = (col: string) => {
    setSelectedColumns((prev) => {
      const next = new Set(prev);
      if (next.has(col)) next.delete(col);
      else next.add(col);
      return next;
    });
  };

  const hasActiveFilters =
    search !== "" ||
    datePreset !== "all" ||
    scopeFilter !== "all" ||
    selectedColumns.size > 0 ||
    selectedAssets.size > 0;

  const clearAll = () => {
    setSearch("");
    setDatePreset("all");
    setScopeFilter("all");
    setSelectedColumns(new Set());
    setSelectedAssets(new Set());
  };

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

        <SingleSelect value={scopeFilter} options={SCOPE_OPTIONS} onChange={setScopeFilter} />

        {isDP && availableAssets.length > 0 && (
          <div className="filter-multiselect" ref={assetDropdownRef}>
            <button
              type="button"
              className={`multiselect-trigger ${assetDropdownOpen ? "multiselect-open" : ""}`}
              onClick={() => {
                setAssetDropdownOpen((v) => !v);
                if (assetDropdownOpen) setAssetSearch("");
              }}
            >
              {selectedAssets.size > 0 ? (
                <>
                  <span className="multiselect-tags">
                    {[...selectedAssets].join(", ")}
                  </span>
                  <span
                    className="multiselect-tag-clear"
                    onClick={(e) => { e.stopPropagation(); setSelectedAssets(new Set()); }}
                  >
                    <XSmallIcon />
                  </span>
                </>
              ) : (
                <>All tables <ChevronDownIcon /></>
              )}
            </button>
            {assetDropdownOpen && (
              <div className="multiselect-dropdown">
                <div className="multiselect-search">
                  <SearchIcon />
                  <input
                    type="text"
                    placeholder="Search tables…"
                    value={assetSearch}
                    onChange={(e) => setAssetSearch(e.target.value)}
                    autoFocus
                  />
                </div>
                <div className="multiselect-actions">
                  <button type="button" onClick={() => setSelectedAssets(new Set(availableAssets))}>select all</button>
                  <button type="button" onClick={() => setSelectedAssets(new Set())}>clear</button>
                </div>
                <div className="multiselect-list">
                  {filteredAssets.length === 0 ? (
                    <div className="multiselect-empty">No tables match</div>
                  ) : (
                    filteredAssets.map((a) => (
                      <label key={a} className="multiselect-option">
                        <input type="checkbox" checked={selectedAssets.has(a)} onChange={() => toggleAsset(a)} />
                        <span className="multiselect-option-label">{a}</span>
                      </label>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {availableColumns.length > 0 && (
          <div className="filter-multiselect" ref={columnDropdownRef}>
            <button
              type="button"
              className={`multiselect-trigger ${columnDropdownOpen ? "multiselect-open" : ""}`}
              onClick={() => {
                setColumnDropdownOpen((v) => !v);
                if (columnDropdownOpen) setColumnSearch("");
              }}
            >
              {selectedColumns.size > 0 ? (
                <>
                  <span className="multiselect-tags">
                    {[...selectedColumns].join(", ")}
                  </span>
                  <span
                    className="multiselect-tag-clear"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedColumns(new Set());
                    }}
                  >
                    <XSmallIcon />
                  </span>
                </>
              ) : (
                <>
                  All columns
                  <ChevronDownIcon />
                </>
              )}
            </button>
            {columnDropdownOpen && (
              <div className="multiselect-dropdown">
                <div className="multiselect-search">
                  <SearchIcon />
                  <input
                    type="text"
                    placeholder="Search columns…"
                    value={columnSearch}
                    onChange={(e) => setColumnSearch(e.target.value)}
                    autoFocus
                  />
                </div>
                <div className="multiselect-actions">
                  <button
                    type="button"
                    onClick={() => setSelectedColumns(new Set(availableColumns))}
                  >
                    select all
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedColumns(new Set())}
                  >
                    clear
                  </button>
                </div>
                <div className="multiselect-list">
                  {filteredColumns.length === 0 ? (
                    <div className="multiselect-empty">No columns match</div>
                  ) : (
                    filteredColumns.map((col) => (
                      <label key={col} className="multiselect-option">
                        <input
                          type="checkbox"
                          checked={selectedColumns.has(col)}
                          onChange={() => toggleColumn(col)}
                        />
                        <span className="multiselect-option-label">{col}</span>
                      </label>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        <SingleSelect value={datePreset} options={DATE_PRESETS} onChange={setDatePreset} />

        {hasActiveFilters && (
          <button type="button" className="filter-clear" onClick={clearAll}>
            Clear
          </button>
        )}
      </div>

      <div className="table-wrapper">
        <table className="rules-table">
          <thead>
            <tr>
              <th>Rule ID</th>
              {isDP && <th>Asset</th>}
              <th>Scope</th>
              <th>Rule description</th>
              <th>Execution date</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {shownRows.length === 0 ? (
              <tr>
                <td colSpan={isDP ? 6 : 5} className="empty-row">
                  No executions match the current filters.
                </td>
              </tr>
            ) : (
              shownRows.map((r) => (
                <tr key={r.key}>
                  <td className="mono">{r.ruleId || "—"}</td>
                  {isDP && <td className="mono">{r.sourceAssetName || "—"}</td>}
                  <td>
                    <ScopeBadge scope={r.scope} />
                    {r.columnName && (
                      <span className="column-name">{r.columnName}</span>
                    )}
                  </td>
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

/* ---- Reusable single-select dropdown (Atlan Source picker style) ---- */

function SingleSelect<T extends string>({
  value,
  options,
  onChange,
}: {
  value: T;
  options: { id: T; label: string }[];
  onChange: (v: T) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const selected = options.find((o) => o.id === value);

  return (
    <div className="single-select" ref={ref}>
      <button
        type="button"
        className={`single-select-trigger ${open ? "single-select-open" : ""}`}
        onClick={() => setOpen((v) => !v)}
      >
        <span>{selected?.label || value}</span>
        <ChevronDownIcon />
      </button>
      {open && (
        <div className="single-select-dropdown">
          {options.map((o) => (
            <button
              key={o.id}
              type="button"
              className={`single-select-option ${o.id === value ? "single-select-active" : ""}`}
              onClick={() => {
                onChange(o.id);
                setOpen(false);
              }}
            >
              {o.label}
            </button>
          ))}
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

function XSmallIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M3 3l6 6M9 3l-6 6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}
