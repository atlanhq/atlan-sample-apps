import { useState } from 'react'
import type { LineageEntry } from '../types/atlan'

interface Props {
  entries: LineageEntry[]
  loading: boolean
  error: string | null
  onDelete: (processGuid: string) => Promise<void>
}

export function LineageList({ entries, loading, error, onDelete }: Props) {
  if (loading) {
    return <div style={{ color: '#9ca3af', fontSize: 11, padding: 8 }}>Loading…</div>
  }

  if (error) {
    return <div style={{ color: '#dc2626', fontSize: 12, padding: 8 }}>{error}</div>
  }

  if (!entries.length) {
    return (
      <div className="empty-state">
        <div className="e-icon">🔗</div>
        <p>No manual lineage connections yet.<br />Use the form above to add one.</p>
      </div>
    )
  }

  return (
    <div>
      {entries.map((entry) => (
        <LineageEntryRow key={entry.processGuid} entry={entry} onDelete={onDelete} />
      ))}
    </div>
  )
}

function LineageEntryRow({
  entry,
  onDelete,
}: {
  entry: LineageEntry
  onDelete: (guid: string) => Promise<void>
}) {
  const [confirming, setConfirming] = useState(false)
  const [deleting, setDeleting] = useState(false)

  async function handleConfirm() {
    setDeleting(true)
    try {
      await onDelete(entry.processGuid)
    } catch {
      setDeleting(false)
      setConfirming(false)
    }
  }

  const meta = [entry.createdBy, entry.createdAt].filter(Boolean).join(' · ')

  return (
    <div className="lineage-entry">
      <div className="flow-row">
        <span className={`asset-chip${entry.srcIsCurrent ? ' this-asset' : ''}`}>
          {entry.srcName}
        </span>
        <span className="flow-arrow">→</span>
        <span className={`asset-chip${entry.tgtIsCurrent ? ' this-asset' : ''}`}>
          {entry.tgtName}
        </span>
      </div>
      <div className="entry-footer">
        <span className="entry-meta">{meta}</span>
        <div className="del-actions">
          {deleting ? (
            <span style={{ fontSize: 11, color: '#9ca3af' }}>Deleting…</span>
          ) : confirming ? (
            <>
              <button className="btn-cancel" onClick={() => setConfirming(false)}>Cancel</button>
              <button className="btn-confirm" onClick={handleConfirm}>Confirm delete</button>
            </>
          ) : (
            <button className="btn-del" onClick={() => setConfirming(true)}>Delete</button>
          )}
        </div>
      </div>
    </div>
  )
}
