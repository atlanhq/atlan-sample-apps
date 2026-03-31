import type { AssetRef } from '../types/atlan'

interface Props {
  asset: AssetRef
}

export function AssetHeader({ asset }: Props) {
  return (
    <div className="asset-header">
      <span className="asset-badge">{asset.typeName}</span>
      <div className="asset-header-text">
        <div className="asset-name">{asset.name}</div>
        <div className="asset-qn">{asset.qualifiedName}</div>
      </div>
    </div>
  )
}
