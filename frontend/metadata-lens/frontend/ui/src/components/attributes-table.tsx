import { useMemo, useState } from 'react'
import type { AttributeEntry } from '../types/atlan'

interface AttributesTableProps {
  attributes: AttributeEntry[]
  totalCount: number
  entityTypeName: string | null
}

function formatValue(value: unknown): string {
  if (typeof value === 'string') {
    // Detect ISO timestamps
    if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(value)) {
      const date = new Date(value)
      if (!isNaN(date.getTime())) {
        return date.toLocaleString()
      }
    }
    return value
  }

  if (typeof value === 'number') {
    // Detect epoch milliseconds (13 digits, after year 2000)
    if (value > 946684800000 && value < 32503680000000) {
      return new Date(value).toLocaleString()
    }
    return value.toLocaleString()
  }

  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No'
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return '(empty list)'
    const items = value.map((item) =>
      typeof item === 'object' ? JSON.stringify(item) : String(item)
    )
    return items.join(', ')
  }

  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value, null, 2)
  }

  return String(value)
}

function isObjectValue(value: unknown): boolean {
  return (typeof value === 'object' && value !== null && !Array.isArray(value))
}

export function AttributesTable({ attributes, totalCount, entityTypeName }: AttributesTableProps) {
  const [searchQuery, setSearchQuery] = useState('')

  const filtered = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    if (!q) return attributes

    return attributes.filter((attr) => {
      const keyMatch = attr.key.toLowerCase().includes(q)
      const valStr = formatValue(attr.value).toLowerCase()
      const valMatch = valStr.includes(q)
      return keyMatch || valMatch
    })
  }, [attributes, searchQuery])

  if (attributes.length === 0) {
    return (
      <div className="state-container">
        <div className="state-title">No attributes found</div>
        <div className="state-message">This asset has no non-null attributes.</div>
      </div>
    )
  }

  return (
    <div className="attributes-panel">
      <div className="attributes-header">
        {entityTypeName && <span className="entity-type">{entityTypeName}</span>}
        <span className="attribute-count">
          {filtered.length === attributes.length
            ? `${attributes.length} of ${totalCount} attributes (non-null)`
            : `${filtered.length} matching of ${attributes.length} non-null`}
        </span>
      </div>

      <div className="search-bar">
        <input
          type="text"
          className="search-input"
          placeholder="Filter attributes by name or value..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <div className="table-container">
        <table className="attributes-table">
          <thead>
            <tr>
              <th className="col-name">Attribute</th>
              <th className="col-value">Value</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((attr) => (
              <tr key={attr.key}>
                <td className="col-name">{attr.key}</td>
                <td className="col-value">
                  {isObjectValue(attr.value) ? (
                    <pre className="json-value">{formatValue(attr.value)}</pre>
                  ) : (
                    formatValue(attr.value)
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filtered.length === 0 && searchQuery && (
        <div className="no-results">
          No attributes match &ldquo;{searchQuery}&rdquo;
        </div>
      )}
    </div>
  )
}
