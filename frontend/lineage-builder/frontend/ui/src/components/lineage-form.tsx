import { useState } from 'react'
import type { AssetRef, LineageRole } from '../types/atlan'
import { AssetSearch } from './asset-search'

interface Props {
  currentAsset: AssetRef
  token: string
  onAdd: (src: AssetRef, tgt: AssetRef) => Promise<void>
}

export function LineageForm({ currentAsset, token, onAdd }: Props) {
  const [role, setRole] = useState<LineageRole>('target')
  const [otherAsset, setOtherAsset] = useState<AssetRef | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function switchRole(r: LineageRole) {
    setRole(r)
    setOtherAsset(null)
    setError(null)
  }

  async function handleAdd() {
    if (!otherAsset) {
      setError(`Select a ${role === 'target' ? 'source' : 'target'} asset first`)
      return
    }
    setError(null)
    setSaving(true)
    try {
      const [src, tgt] =
        role === 'target'
          ? [otherAsset, currentAsset]   // upstream: other → current
          : [currentAsset, otherAsset]   // downstream: current → other
      await onAdd(src, tgt)
      setOtherAsset(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create lineage')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="form-card">
      {/* Role toggle */}
      <div style={{ marginBottom: 10 }}>
        <div className="role-toggle">
          <button
            className={`role-btn${role === 'target' ? ' active' : ''}`}
            onClick={() => switchRole('target')}
          >
            ← Upstream source
          </button>
          <button
            className={`role-btn${role === 'source' ? ' active' : ''}`}
            onClick={() => switchRole('source')}
          >
            Downstream target →
          </button>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="form-cols">
        {role === 'target' ? (
          <>
            <div className="form-col">
              <label>Source</label>
              <AssetSearch
                token={token}
                selected={otherAsset}
                onSelect={setOtherAsset}
                onClear={() => setOtherAsset(null)}
              />
            </div>
            <div className="form-arrow">→</div>
            <div className="form-col">
              <label>Target (this asset)</label>
              <CurrentPill asset={currentAsset} />
            </div>
          </>
        ) : (
          <>
            <div className="form-col">
              <label>Source (this asset)</label>
              <CurrentPill asset={currentAsset} />
            </div>
            <div className="form-arrow">→</div>
            <div className="form-col">
              <label>Target</label>
              <AssetSearch
                token={token}
                selected={otherAsset}
                onSelect={setOtherAsset}
                onClear={() => setOtherAsset(null)}
              />
            </div>
          </>
        )}
      </div>

      {error && (
        <div style={{ color: '#dc2626', fontSize: 11, marginTop: 6 }}>{error}</div>
      )}

      <button className="btn-primary" onClick={handleAdd} disabled={saving}>
        {saving ? 'Creating…' : '+ Add Lineage Connection'}
      </button>
    </div>
  )
}

function CurrentPill({ asset }: { asset: AssetRef }) {
  return (
    <div className="current-pill">
      <span className="type-tag">{asset.typeName}</span>
      <span>{asset.name}</span>
    </div>
  )
}
