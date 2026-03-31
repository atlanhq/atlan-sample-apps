import { useEffect, useState } from 'react'
import { useAtlanAuth, isDevMode } from './hooks/use-atlan-auth'
import { useLineage } from './hooks/use-lineage'
import { fetchEntity } from './services/lineage-api'
import type { AssetRef } from './types/atlan'
import { AssetHeader } from './components/asset-header'
import { LineageForm } from './components/lineage-form'
import { LineageList } from './components/lineage-list'
import { LoadingState } from './components/loading-state'

// Asset types that support the lineage tab
const SUPPORTED_TYPES = ['Table', 'View', 'MaterialisedView']

export function App() {
  const auth = useAtlanAuth()
  const token = auth.status === 'authenticated' ? auth.context.token : null
  const userEmail =
    auth.status === 'authenticated'
      ? auth.context.user?.email || auth.context.user?.username || 'unknown'
      : 'unknown'

  const [currentAsset, setCurrentAsset] = useState<AssetRef | null>(null)
  const [assetError, setAssetError] = useState<string | null>(null)
  const [toast, setToast] = useState<{ msg: string; type: 'ok' | 'fail' | '' } | null>(null)

  // Load the current asset when auth + assetId are available
  useEffect(() => {
    if (!auth.assetId || !token) return
    let cancelled = false

    fetchEntity(auth.assetId, token)
      .then((asset) => { if (!cancelled) setCurrentAsset(asset) })
      .catch((err) => { if (!cancelled) setAssetError(err.message) })

    return () => { cancelled = true }
  }, [auth.assetId, token])

  const { entries, loading: lineageLoading, error: lineageError, create, remove } =
    useLineage(currentAsset, token)

  function showToast(msg: string, type: 'ok' | 'fail' | '' = '') {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }

  async function handleAdd(src: AssetRef, tgt: AssetRef) {
    await create(src, tgt, userEmail)
    showToast('Lineage connection created!', 'ok')
  }

  async function handleDelete(processGuid: string) {
    await remove(processGuid)
    showToast('Lineage deleted', 'ok')
  }

  const authError = auth.status === 'error' ? auth.message : null
  const displayError = authError || assetError

  // Show loading / error / session-ended states
  const isReady = auth.status === 'authenticated' && !displayError
  const isNavMode = isReady && !auth.assetId
  const isAssetMode =
    isReady &&
    !!auth.assetId &&
    !!currentAsset &&
    SUPPORTED_TYPES.includes(currentAsset.typeName)
  const isUnsupportedType =
    isReady && !!currentAsset && !SUPPORTED_TYPES.includes(currentAsset.typeName)

  return (
    <div className="app-root">
      {isDevMode() && (
        <div className="dev-banner">
          Dev mode — token from .env.local | Asset: {auth.assetId}
        </div>
      )}

      <LoadingState authStatus={auth.status} error={displayError} />

      {/* Nav-tab landing (no asset context) */}
      {isNavMode && (
        <div className="nav-mode">
          <div className="n-icon">🔗</div>
          <h2>Manual Lineage Builder</h2>
          <p>
            Open any <strong>Table</strong>, <strong>View</strong>, or{' '}
            <strong>Materialized View</strong> asset and switch to the{' '}
            <strong>Manual Lineage</strong> tab.
          </p>
        </div>
      )}

      {/* Unsupported asset type */}
      {isUnsupportedType && (
        <div className="nav-mode">
          <div className="n-icon">⚠️</div>
          <h2>{currentAsset!.typeName}</h2>
          <p>Manual lineage is only supported for Tables, Views, and Materialized Views.</p>
        </div>
      )}

      {/* Main app */}
      {isAssetMode && (
        <div className="app-shell">
          <AssetHeader asset={currentAsset!} />
          <div className="content">
            <div className="inner">
              <div className="section-label">Add Lineage Connection</div>
              <LineageForm
                currentAsset={currentAsset!}
                token={token!}
                onAdd={handleAdd}
              />

              <div className="section-label">
                Manual Lineage
                <span className="count-badge">{entries.length}</span>
              </div>
              <LineageList
                entries={entries}
                loading={lineageLoading}
                error={lineageError}
                onDelete={handleDelete}
              />
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className={`toast show ${toast.type}`}>{toast.msg}</div>
      )}
    </div>
  )
}
