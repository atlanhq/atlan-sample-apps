import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { DqRule, ViewMode } from "../types/atlan";

interface Props {
  rules: DqRule[];
  viewMode: ViewMode;
}

type StatusFilter = "all" | "pass" | "fail" | "na";
type ScopeFilter  = "all" | "table" | "column";

const PAGE_SIZE = 10;

/* ── Status helpers ──────────────────────────────────────────── */
function statusKey(rule: DqRule): StatusFilter {
  const s = rule.last_status?.toLowerCase() ?? "";
  if (s === "passed") return "pass";
  if (s === "failed") return "fail";
  return "na";
}

function StatusDot({ rule }: { rule: DqRule }) {
  const k = statusKey(rule);
  return <span className={`rule-status-dot ${k}`} />;
}

function StatusBadge({ rule }: { rule: DqRule }) {
  const s = rule.last_status;
  if (!s) return <span className="status-badge status-na">Not evaluated</span>;
  if (s.toLowerCase() === "passed") return <span className="status-badge status-passed">Passed</span>;
  return <span className="status-badge status-failed">Failed</span>;
}

/* ── Scope / "Added on" cell ─────────────────────────────────── */
function ScopeCell({ rule }: { rule: DqRule }) {
  if (rule.scope === "column" && rule.column_name) {
    return (
      <div className="scope-cell">
        <ColumnIcon />
        <span>{rule.column_name}</span>
      </div>
    );
  }
  return (
    <div className="scope-cell">
      <TableIcon />
      <span>Table level</span>
    </div>
  );
}

/* ── Main component ──────────────────────────────────────────── */
export function RulesTable({ rules, viewMode }: Props) {
  const isDP = viewMode === "data-product";

  /* counts for tab labels */
  const counts = useMemo(() => {
    let pass = 0, fail = 0, na = 0;
    for (const r of rules) {
      const k = statusKey(r);
      if (k === "pass") pass++;
      else if (k === "fail") fail++;
      else na++;
    }
    return { all: rules.length, pass, fail, na };
  }, [rules]);

  /* state */
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [scopeFilter,  setScopeFilter]  = useState<ScopeFilter>("all");
  const [search,       setSearch]       = useState("");
  const [selectedColumns, setSelectedColumns] = useState<Set<string>>(new Set());
  const [columnSearch, setColumnSearch] = useState("");
  const [columnDropdownOpen, setColumnDropdownOpen] = useState(false);
  const [selectedAssets,  setSelectedAssets]  = useState<Set<string>>(new Set());
  const [assetSearch,  setAssetSearch]  = useState("");
  const [assetDropdownOpen, setAssetDropdownOpen] = useState(false);
  const [visible, setVisible] = useState(PAGE_SIZE);

  const columnDropdownRef = useRef<HTMLDivElement>(null);
  const assetDropdownRef  = useRef<HTMLDivElement>(null);

  /* distinct column names & asset names */
  const availableColumns = useMemo(() => {
    const s = new Set<string>();
    for (const r of rules) {
      if (r.scope === "column" && r.column_name) s.add(r.column_name);
    }
    return [...s].sort();
  }, [rules]);

  const availableAssets = useMemo(() => {
    const s = new Set<string>();
    for (const r of rules) { if (r.source_asset_name) s.add(r.source_asset_name); }
    return [...s].sort();
  }, [rules]);

  const filteredColumns = useMemo(() => {
    if (!columnSearch.trim()) return availableColumns;
    const q = columnSearch.toLowerCase();
    return availableColumns.filter((c) => c.toLowerCase().includes(q));
  }, [availableColumns, columnSearch]);

  const filteredAssets = useMemo(() => {
    if (!assetSearch.trim()) return availableAssets;
    const q = assetSearch.toLowerCase();
    return availableAssets.filter((a) => a.toLowerCase().includes(q));
  }, [availableAssets, assetSearch]);

  /* outside-click handlers */
  const handleColumnOutside = useCallback((e: MouseEvent) => {
    if (columnDropdownRef.current && !columnDropdownRef.current.contains(e.target as Node)) {
      setColumnDropdownOpen(false); setColumnSearch("");
    }
  }, []);
  useEffect(() => {
    if (columnDropdownOpen) document.addEventListener("mousedown", handleColumnOutside);
    return () => document.removeEventListener("mousedown", handleColumnOutside);
  }, [columnDropdownOpen, handleColumnOutside]);

  const handleAssetOutside = useCallback((e: MouseEvent) => {
    if (assetDropdownRef.current && !assetDropdownRef.current.contains(e.target as Node)) {
      setAssetDropdownOpen(false); setAssetSearch("");
    }
  }, []);
  useEffect(() => {
    if (assetDropdownOpen) document.addEventListener("mousedown", handleAssetOutside);
    return () => document.removeEventListener("mousedown", handleAssetOutside);
  }, [assetDropdownOpen, handleAssetOutside]);

  /* filtered rows */
  const filteredRules = useMemo(() => {
    const q = search.trim().toLowerCase();
    return rules.filter((r) => {
      if (statusFilter !== "all" && statusKey(r) !== statusFilter) return false;
      if (scopeFilter  !== "all" && r.scope !== scopeFilter)  return false;
      if (q && !r.name.toLowerCase().includes(q) && !r.description.toLowerCase().includes(q)) return false;
      if (selectedColumns.size > 0 && r.scope === "column" && !selectedColumns.has(r.column_name)) return false;
      if (selectedColumns.size > 0 && r.scope === "table") return false;
      if (selectedAssets.size > 0 && !selectedAssets.has(r.source_asset_name)) return false;
      return true;
    });
  }, [rules, statusFilter, scopeFilter, search, selectedColumns, selectedAssets]);

  useEffect(() => { setVisible(PAGE_SIZE); }, [filteredRules]);

  const hasActiveFilters =
    statusFilter !== "all" || scopeFilter !== "all" || search !== "" ||
    selectedColumns.size > 0 || selectedAssets.size > 0;

  const clearAll = () => {
    setStatusFilter("all"); setScopeFilter("all"); setSearch("");
    setSelectedColumns(new Set()); setSelectedAssets(new Set());
  };

  if (!rules || rules.length === 0) {
    return (
      <div className="card">
        <div className="empty-state">No DQ rules linked to this asset.</div>
      </div>
    );
  }

  const shownRules = filteredRules.slice(0, visible);
  const hasMore    = visible < filteredRules.length;
  const remaining  = filteredRules.length - visible;
  const nextBatch  = Math.min(PAGE_SIZE, remaining);

  return (
    <div className="card">
      {/* ── Toolbar ── */}
      <div className="toolbar">
        {/* Status pill tabs */}
        <div className="status-tabs">
          {(["all", "pass", "fail", "na"] as StatusFilter[]).map((tab) => {
            const label = tab === "all" ? "All" : tab === "pass" ? "Passed" : tab === "fail" ? "Failed" : "Not evaluated";
            const count = counts[tab];
            return (
              <button
                key={tab}
                type="button"
                className={`status-tab ${tab} ${statusFilter === tab ? "active" : ""}`}
                onClick={() => setStatusFilter(tab)}
              >
                <span className="tab-dot" />
                {label}
                <span className="tab-count">{count}</span>
              </button>
            );
          })}
        </div>

        {/* Scope dropdown */}
        <ScopeSelect value={scopeFilter} onChange={setScopeFilter} />

        {/* DataProduct: asset filter */}
        {isDP && availableAssets.length > 0 && (
          <div className="filter-multiselect" ref={assetDropdownRef}>
            <button
              type="button"
              className={`multiselect-trigger ${assetDropdownOpen ? "multiselect-open" : ""}`}
              onClick={() => { setAssetDropdownOpen((v) => !v); if (assetDropdownOpen) setAssetSearch(""); }}
            >
              {selectedAssets.size > 0 ? (
                <>
                  <span className="multiselect-tags">{[...selectedAssets].join(", ")}</span>
                  <span className="multiselect-tag-clear" onClick={(e) => { e.stopPropagation(); setSelectedAssets(new Set()); }}>
                    <XIcon />
                  </span>
                </>
              ) : (<>Tables <ChevronIcon /></>)}
            </button>
            {assetDropdownOpen && (
              <div className="multiselect-dropdown">
                <div className="multiselect-search">
                  <SearchIcon />
                  <input type="text" placeholder="Search tables…" value={assetSearch} onChange={(e) => setAssetSearch(e.target.value)} autoFocus />
                </div>
                <div className="multiselect-actions">
                  <button type="button" onClick={() => setSelectedAssets(new Set(availableAssets))}>select all</button>
                  <button type="button" onClick={() => setSelectedAssets(new Set())}>clear</button>
                </div>
                <div className="multiselect-list">
                  {filteredAssets.length === 0
                    ? <div className="multiselect-empty">No tables match</div>
                    : filteredAssets.map((a) => (
                        <label key={a} className="multiselect-option">
                          <input type="checkbox" checked={selectedAssets.has(a)} onChange={() => {
                            setSelectedAssets((prev) => { const n = new Set(prev); n.has(a) ? n.delete(a) : n.add(a); return n; });
                          }} />
                          <span className="multiselect-option-label">{a}</span>
                        </label>
                      ))
                  }
                </div>
              </div>
            )}
          </div>
        )}

        {/* Column filter */}
        {availableColumns.length > 0 && (
          <div className="filter-multiselect" ref={columnDropdownRef}>
            <button
              type="button"
              className={`multiselect-trigger ${columnDropdownOpen ? "multiselect-open" : ""}`}
              onClick={() => { setColumnDropdownOpen((v) => !v); if (columnDropdownOpen) setColumnSearch(""); }}
            >
              {selectedColumns.size > 0 ? (
                <>
                  <span className="multiselect-tags">{[...selectedColumns].join(", ")}</span>
                  <span className="multiselect-tag-clear" onClick={(e) => { e.stopPropagation(); setSelectedColumns(new Set()); }}>
                    <XIcon />
                  </span>
                </>
              ) : (<>Columns <ChevronIcon /></>)}
            </button>
            {columnDropdownOpen && (
              <div className="multiselect-dropdown">
                <div className="multiselect-search">
                  <SearchIcon />
                  <input type="text" placeholder="Search columns…" value={columnSearch} onChange={(e) => setColumnSearch(e.target.value)} autoFocus />
                </div>
                <div className="multiselect-actions">
                  <button type="button" onClick={() => setSelectedColumns(new Set(availableColumns))}>select all</button>
                  <button type="button" onClick={() => setSelectedColumns(new Set())}>clear</button>
                </div>
                <div className="multiselect-list">
                  {filteredColumns.length === 0
                    ? <div className="multiselect-empty">No columns match</div>
                    : filteredColumns.map((col) => (
                        <label key={col} className="multiselect-option">
                          <input type="checkbox" checked={selectedColumns.has(col)} onChange={() => {
                            setSelectedColumns((prev) => { const n = new Set(prev); n.has(col) ? n.delete(col) : n.add(col); return n; });
                          }} />
                          <span className="multiselect-option-label">{col}</span>
                        </label>
                      ))
                  }
                </div>
              </div>
            )}
          </div>
        )}

        <div className="toolbar-spacer" />

        {/* Search */}
        <label className="filter-search">
          <SearchIcon />
          <input type="search" placeholder="Search rules…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </label>

        {hasActiveFilters && (
          <button type="button" className="filter-clear" onClick={clearAll}>Clear</button>
        )}
      </div>

      {/* ── Table ── */}
      <div className="table-wrapper">
        <table className="rules-table">
          <thead>
            <tr>
              <th>Rule</th>
              {isDP && <th>Asset</th>}
              <th>Added on</th>
              <th>Last run</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {shownRules.length === 0 ? (
              <tr>
                <td colSpan={isDP ? 5 : 4} className="empty-row">
                  No rules match the current filters.
                </td>
              </tr>
            ) : (
              shownRules.map((r) => (
                <tr key={r.guid}>
                  <td>
                    <div className="rule-name-cell">
                      <StatusDot rule={r} />
                      <span className="rule-name-text" title={r.name}>{r.name}</span>
                    </div>
                    {r.description && r.description !== r.name && (
                      <div style={{ fontSize: 12, color: "var(--gray-500)", marginTop: 2, marginLeft: 18, maxWidth: 320, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                        title={r.description}>{r.description}</div>
                    )}
                  </td>
                  {isDP && <td style={{ fontSize: 13, color: "var(--gray-700)" }}>{r.source_asset_name || "—"}</td>}
                  <td><ScopeCell rule={r} /></td>
                  <td className="date-cell">{r.last_execution_date || "—"}</td>
                  <td><StatusBadge rule={r} /></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {hasMore && (
        <div className="load-more-row">
          <button type="button" className="btn-load-more"
            onClick={() => setVisible((v) => Math.min(v + PAGE_SIZE, filteredRules.length))}>
            Load {nextBatch} more <ChevronIcon />
          </button>
          <span className="load-more-meta">{shownRules.length} of {filteredRules.length}</span>
        </div>
      )}
    </div>
  );
}

/* ── Scope dropdown ────────────────────────────────────────────── */
function ScopeSelect({ value, onChange }: { value: ScopeFilter; onChange: (v: ScopeFilter) => void }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const h = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, [open]);

  const opts: { id: ScopeFilter; label: string }[] = [
    { id: "all",    label: "All scopes" },
    { id: "table",  label: "Table" },
    { id: "column", label: "Column" },
  ];
  const label = opts.find((o) => o.id === value)?.label ?? "All scopes";

  return (
    <div className="single-select" ref={ref}>
      <button type="button" className={`single-select-trigger ${open ? "single-select-open" : ""}`} onClick={() => setOpen((v) => !v)}>
        <span>{label}</span>
        <ChevronIcon />
      </button>
      {open && (
        <div className="single-select-dropdown">
          {opts.map((o) => (
            <button key={o.id} type="button"
              className={`single-select-option ${o.id === value ? "single-select-active" : ""}`}
              onClick={() => { onChange(o.id); setOpen(false); }}>
              {o.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Icons ────────────────────────────────────────────────────── */
function SearchIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.4" />
      <path d="M10.5 10.5l3 3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
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

function XIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M3 3l6 6M9 3l-6 6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function TableIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" className="scope-icon">
      <rect x="1.5" y="2.5" width="13" height="11" rx="1.5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M1.5 6.5h13" stroke="currentColor" strokeWidth="1.3" />
      <path d="M6 6.5v7" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  );
}

function ColumnIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" className="scope-icon">
      <rect x="1.5" y="2.5" width="13" height="11" rx="1.5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M1.5 6.5h13" stroke="currentColor" strokeWidth="1.3" />
      <path d="M6 6.5v7" stroke="currentColor" strokeWidth="1.3" />
      <rect x="6" y="2.5" width="4.5" height="11" fill="currentColor" fillOpacity="0.08" />
    </svg>
  );
}
