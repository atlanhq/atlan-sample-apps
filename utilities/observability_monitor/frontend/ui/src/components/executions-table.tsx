import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Execution } from "../types/atlan";

interface Props {
  executions: Execution[];
}

type DatePreset = "all" | "today" | "yesterday" | "last7" | "last30";

const PAGE_SIZE = 7;

function todayUtc(): string {
  return new Date().toISOString().slice(0, 10);
}

function shiftDate(dateStr: string, days: number): string {
  const d = new Date(dateStr + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

function matchesPreset(dateValue: string, preset: DatePreset): boolean {
  if (preset === "all") return true;
  if (!dateValue) return false;
  const datePart = dateValue.slice(0, 10);
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
              onClick={() => { onChange(o.id); setOpen(false); }}
            >
              {o.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

const MONTH_NAMES = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];
const DAY_LABELS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

function CalendarPicker({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Parse selected date or default to today for initial view.
  const selected = value !== "all" ? value : "";
  const initDate = selected ? new Date(selected + "T00:00:00") : new Date();
  const [viewYear, setViewYear] = useState(initDate.getFullYear());
  const [viewMonth, setViewMonth] = useState(initDate.getMonth());

  const handleOutside = useCallback((e: MouseEvent) => {
    if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
  }, []);

  useEffect(() => {
    if (open) document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, [open, handleOutside]);

  // Build the day grid for the current view month.
  const days = useMemo(() => {
    const first = new Date(viewYear, viewMonth, 1);
    const startDay = first.getDay(); // 0=Sun
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
    const cells: (number | null)[] = [];
    for (let i = 0; i < startDay; i++) cells.push(null);
    for (let d = 1; d <= daysInMonth; d++) cells.push(d);
    return cells;
  }, [viewYear, viewMonth]);

  const prevMonth = () => {
    if (viewMonth === 0) { setViewMonth(11); setViewYear((y) => y - 1); }
    else setViewMonth((m) => m - 1);
  };
  const nextMonth = () => {
    if (viewMonth === 11) { setViewMonth(0); setViewYear((y) => y + 1); }
    else setViewMonth((m) => m + 1);
  };

  const pad = (n: number) => String(n).padStart(2, "0");
  const formatDate = (day: number) =>
    `${viewYear}-${pad(viewMonth + 1)}-${pad(day)}`;

  const activeLabel = value === "all" ? "Cut-off date" : value;

  return (
    <div className="single-select" ref={ref}>
      <button
        type="button"
        className={`single-select-trigger ${open ? "single-select-open" : ""}`}
        onClick={() => setOpen((v) => !v)}
      >
        <CalendarIcon />
        <span>{activeLabel}</span>
        {value !== "all" ? (
          <span
            className="cal-clear"
            onClick={(e) => { e.stopPropagation(); onChange("all"); }}
          >
            <XSmallIcon />
          </span>
        ) : (
          <ChevronDownIcon />
        )}
      </button>
      {open && (
        <div className="cal-dropdown">
          <div className="cal-header">
            <button type="button" className="cal-nav" onClick={prevMonth}>
              <ChevronLeftIcon />
            </button>
            <span className="cal-title">
              {MONTH_NAMES[viewMonth]} {viewYear}
            </span>
            <button type="button" className="cal-nav" onClick={nextMonth}>
              <ChevronRightIcon />
            </button>
          </div>
          <div className="cal-grid">
            {DAY_LABELS.map((d) => (
              <div key={d} className="cal-day-label">{d}</div>
            ))}
            {days.map((day, i) =>
              day === null ? (
                <div key={`e${i}`} className="cal-cell" />
              ) : (
                <button
                  key={day}
                  type="button"
                  className={`cal-cell cal-day ${formatDate(day) === selected ? "cal-selected" : ""}`}
                  onClick={() => { onChange(formatDate(day)); setOpen(false); }}
                >
                  {day}
                </button>
              )
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export function ExecutionsTable({ executions }: Props) {
  const [search, setSearch] = useState("");
  const [execDatePreset, setExecDatePreset] = useState<DatePreset>("all");
  const [cutOffDate, setCutOffDate] = useState("all");
  const [visible, setVisible] = useState(PAGE_SIZE);

  const filteredRows = useMemo(() => {
    const q = search.trim().toLowerCase();
    return executions.filter((e) => {
      if (!matchesPreset(e.executionDate, execDatePreset)) return false;
      if (cutOffDate !== "all" && e.cutOffDate !== cutOffDate) return false;
      if (q && !e.executionId.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [executions, search, execDatePreset, cutOffDate]);

  useEffect(() => {
    setVisible(PAGE_SIZE);
  }, [filteredRows]);

  const hasActiveFilters =
    search !== "" || execDatePreset !== "all" || cutOffDate !== "all";

  const clearAll = () => {
    setSearch("");
    setExecDatePreset("all");
    setCutOffDate("all");
  };

  if (executions.length === 0) {
    return (
      <div className="card">
        <div className="empty-state">No observability executions found.</div>
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
            placeholder="Search by execution ID…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>

        <SingleSelect value={execDatePreset} options={DATE_PRESETS} onChange={setExecDatePreset} />

        <CalendarPicker value={cutOffDate} onChange={setCutOffDate} />

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
              <th>Execution ID</th>
              <th>Cut-off date</th>
              <th>Execution date</th>
            </tr>
          </thead>
          <tbody>
            {shownRows.length === 0 ? (
              <tr>
                <td colSpan={3} className="empty-row">
                  No executions match the current filters.
                </td>
              </tr>
            ) : (
              shownRows.map((e) => (
                <tr key={e.key}>
                  <td className="mono">{e.executionId || "—"}</td>
                  <td className="mono">{e.cutOffDate || "—"}</td>
                  <td className="mono">{e.executionDate || "—"}</td>
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

function ChevronLeftIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M10 3l-5 5 5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ChevronRightIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M6 3l5 5-5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function CalendarIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="2" y="3" width="12" height="11" rx="1.5" stroke="currentColor" strokeWidth="1.2" />
      <path d="M2 6.5h12" stroke="currentColor" strokeWidth="1.2" />
      <path d="M5.5 1.5v3M10.5 1.5v3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
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
