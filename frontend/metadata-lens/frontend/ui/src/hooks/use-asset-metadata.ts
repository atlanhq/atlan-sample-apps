import { useEffect, useState } from 'react'
import type { AttributeEntry } from '../types/atlan'
import { fetchEntityByGuid } from '../services/atlan-api'

interface UseAssetMetadataResult {
  attributes: AttributeEntry[]
  totalCount: number
  loading: boolean
  error: string | null
  entityTypeName: string | null
}

function isNonNull(value: unknown): boolean {
  return value !== null && value !== undefined
}

function extractAttributes(attrs: Record<string, unknown>): AttributeEntry[] {
  return Object.entries(attrs)
    .filter(([, value]) => isNonNull(value))
    .map(([key, value]) => ({ key, value }))
    .sort((a, b) => a.key.localeCompare(b.key))
}

export function useAssetMetadata(
  assetId: string | null,
  token: string | null,
  baseUrl: string
): UseAssetMetadataResult {
  const [attributes, setAttributes] = useState<AttributeEntry[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [entityTypeName, setEntityTypeName] = useState<string | null>(null)

  useEffect(() => {
    if (!assetId || !token) {
      setAttributes([])
      setTotalCount(0)
      setError(null)
      setEntityTypeName(null)
      return
    }

    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)

      try {
        const response = await fetchEntityByGuid(assetId!, token!, baseUrl)
        if (cancelled) return

        const entity = response.entity
        setEntityTypeName(entity.typeName)

        const allAttrs = entity.attributes ?? {}
        const totalEntries = Object.keys(allAttrs).length
        setTotalCount(totalEntries)

        const nonNullAttrs = extractAttributes(allAttrs)
        setAttributes(nonNullAttrs)
      } catch (err) {
        if (cancelled) return
        const message = err instanceof Error ? err.message : 'Failed to fetch asset metadata'
        setError(message)
        setAttributes([])
        setTotalCount(0)
        setEntityTypeName(null)
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    load()

    return () => {
      cancelled = true
    }
  }, [assetId, token, baseUrl])

  return { attributes, totalCount, loading, error, entityTypeName }
}
