import { useAtlanAuth } from './hooks/use-atlan-auth'
import { useAssetMetadata } from './hooks/use-asset-metadata'
import { AttributesTable } from './components/attributes-table'
import { LoadingState } from './components/loading-state'

export function App() {
  const { status, atlan, assetId, error: authError } = useAtlanAuth()
  const { attributes, totalCount, loading, error: metadataError, entityTypeName } =
    useAssetMetadata(assetId, atlan)

  const displayError = authError || metadataError
  const showContent = status === 'authenticated' && !loading && !displayError

  return (
    <div className="app">
      <LoadingState
        authStatus={status}
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
