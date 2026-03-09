import { useAtlanAuth, isDevMode } from './hooks/use-atlan-auth'
import { useAssetMetadata } from './hooks/use-asset-metadata'
import { AttributesTable } from './components/attributes-table'
import { LoadingState } from './components/loading-state'

export function App() {
  const auth = useAtlanAuth()

  // In dev mode, Vite proxy forwards /api/meta/* to the Atlan instance.
  // In production (embedded iframe), relative URLs resolve against the same origin.
  const baseUrl = ''

  const token = auth.status === 'authenticated' ? auth.context.token : null
  const { attributes, totalCount, loading, error: metadataError, entityTypeName } =
    useAssetMetadata(auth.assetId, token, baseUrl)

  const authError = auth.status === 'error' ? auth.message : null
  const displayError = authError || metadataError

  const showContent =
    auth.status === 'authenticated' && !loading && !displayError

  return (
    <div className="app">
      {isDevMode() && (
        <div className="dev-banner">
          Dev mode — using token from .env.local | Asset: {auth.assetId}
        </div>
      )}

      <LoadingState
        authStatus={auth.status}
        metadataLoading={loading}
        error={displayError}
      />

      {showContent && (
        <AttributesTable
          attributes={attributes}
          totalCount={totalCount}
          entityTypeName={entityTypeName}
        />
      )}
    </div>
  )
}
