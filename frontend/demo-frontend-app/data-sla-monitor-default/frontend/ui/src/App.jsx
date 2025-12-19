import { useMemo, useState } from "react"
import SLATable from "./components/SLATable.jsx"
import DetailPanel from "./components/DetailPanel.jsx"
import { slaRows } from "./data/slaData.js"

function minutesBetween(isoA, isoB) {
  const a = new Date(isoA).getTime()
  const b = new Date(isoB).getTime()
  return Math.round((a - b) / 60000)
}

function computeStatus(row) {
  const delayMins = minutesBetween(row.lastRefreshUtc, row.expectedByUtc)
  const isLate = delayMins > 0
  const isAtRisk = !isLate && delayMins > -10
  const status = isLate ? "Late" : (isAtRisk ? "At risk" : "On time")

  let healthPct = 100
  if (status === "At risk") healthPct = 70
  if (status === "Late") healthPct = Math.max(10, 60 - Math.min(50, delayMins))

  return { status, delayMins, healthPct }
}

export default function App() {
  const [query, setQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState("All")
  const [selectedId, setSelectedId] = useState(null)

  const rows = useMemo(() => {
    return slaRows
      .map((r) => {
        const s = computeStatus(r)
        return { ...r, _status: s.status, _delayMins: s.delayMins, _healthPct: s.healthPct }
      })
      .filter((r) => {
        const q = query.trim().toLowerCase()
        const matchesQuery =
          !q ||
          r.dataset.toLowerCase().includes(q) ||
          r.pipeline.toLowerCase().includes(q) ||
          r.domain.toLowerCase().includes(q) ||
          r.owner.toLowerCase().includes(q)

        const matchesStatus = statusFilter === "All" || r._status === statusFilter
        return matchesQuery && matchesStatus
      })
      .sort((a, b) => {
        const rank = (s) => (s === "Late" ? 0 : s === "At risk" ? 1 : 2)
        return rank(a._status) - rank(b._status)
      })
  }, [query, statusFilter])

  const selectedRow = selectedId === null ? null : rows.find((_, idx) => idx == selectedId) ?? null

  const counts = useMemo(() => {
    const c = { "On time": 0, "At risk": 0, "Late": 0 }
    for (const r of slaRows.map(r => ({...r, _status: computeStatus(r).status}))) c[r._status]++
    return c
  }, [])

  return (
    <div className="page">
      <div className="top">
        <div>
          <div className="h1">Data SLA Monitor</div>
          <div className="sub">
            Lightweight operational dashboard for dataset refresh SLAs. Uses dummy business data — no external calls.
          </div>
        </div>

        <div className="kpis">
          <div className="kpi">
            <div className="kpiLabel muted">On time</div>
            <div className="kpiValue ok">{counts["On time"]}</div>
          </div>
          <div className="kpi">
            <div className="kpiLabel muted">At risk</div>
            <div className="kpiValue warn">{counts["At risk"]}</div>
          </div>
          <div className="kpi">
            <div className="kpiLabel muted">Late</div>
            <div className="kpiValue bad">{counts["Late"]}</div>
          </div>
        </div>
      </div>

      <div className="controls">
        <div className="control">
          <div className="label muted">Search</div>
          <input
            className="input"
            placeholder="Dataset, pipeline, domain, owner…"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setSelectedId(null) }}
          />
        </div>

        <div className="control">
          <div className="label muted">Status</div>
          <select
            className="select"
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setSelectedId(null) }}
          >
            <option>All</option>
            <option>On time</option>
            <option>At risk</option>
            <option>Late</option>
          </select>
        </div>

        <div className="control grow">
          <div className="label muted">Demo note</div>
          <div className="note">
            In App Framework default UI routes, static files are mounted at <span className="mono">/</span>.
            So assets resolve as <span className="mono">/assets/…</span>.
          </div>
        </div>
      </div>

      <div className="grid">
        <div className="card">
          <SLATable rows={rows} onSelect={(id) => setSelectedId(id)} selectedId={selectedId} />
        </div>
        <DetailPanel row={selectedRow} />
      </div>
    </div>
  )
}