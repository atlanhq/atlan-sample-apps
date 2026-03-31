import { useEffect, useRef, useState } from 'react'
import type { AssetRef, SearchHit } from '../types/atlan'
import { searchAssets } from '../services/lineage-api'

interface Props {
  token: string
  selected: AssetRef | null
  onSelect: (asset: AssetRef) => void
  onClear: () => void
  placeholder?: string
}

export function AssetSearch({ token, selected, onSelect, onClear, placeholder = 'Search asset…' }: Props) {
  const [query, setQuery] = useState('')
  const [hits, setHits] = useState<SearchHit[]>([])
  const [open, setOpen] = useState(false)
  const [searching, setSearching] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (query.length < 2) {
      setOpen(false)
      setHits([])
      return
    }
    setSearching(true)
    setOpen(true)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      try {
        const results = await searchAssets(query, token)
        setHits(results)
      } catch {
        setHits([])
      } finally {
        setSearching(false)
      }
    }, 300)
  }, [query, token])

  function pick(hit: SearchHit) {
    onSelect({
      guid: hit.guid,
      typeName: hit.typeName,
      name: hit.attributes?.name || hit.guid,
      qualifiedName: hit.attributes?.qualifiedName || '',
    })
    setQuery('')
    setOpen(false)
  }

  if (selected) {
    return (
      <div className="selected-pill">
        <span className="s-type">{selected.typeName}</span>
        <span className="s-name">{selected.name}</span>
        <span className="s-clear" onClick={onClear}>✕</span>
      </div>
    )
  }

  return (
    <div className="search-wrap">
      <input
        type="text"
        className="search-input"
        placeholder={placeholder}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onBlur={() => setTimeout(() => setOpen(false), 160)}
        autoComplete="off"
      />
      {open && (
        <div className="dropdown open">
          {searching && <div className="dd-msg">Searching…</div>}
          {!searching && hits.length === 0 && <div className="dd-msg">No assets found</div>}
          {!searching && hits.map((hit) => {
            const name = hit.attributes?.name || hit.guid
            const qn = hit.attributes?.qualifiedName || ''
            return (
              <div key={hit.guid} className="dd-item" onMouseDown={() => pick(hit)}>
                <div className="dd-name">{name}</div>
                <div className="dd-meta">
                  <span className="dd-type">{hit.typeName}</span>
                  {qn}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
