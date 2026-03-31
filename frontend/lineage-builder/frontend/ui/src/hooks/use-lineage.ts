import { useCallback, useEffect, useState } from 'react'
import type { AssetRef, LineageEntry, ProcessEntity } from '../types/atlan'
import {
  fetchLineageGraph,
  fetchProcessEntity,
  resolveGuids,
  createLineageProcess,
  deleteProcess,
} from '../services/lineage-api'

interface UseLineageResult {
  entries: LineageEntry[]
  loading: boolean
  error: string | null
  reload: () => void
  create: (src: AssetRef, tgt: AssetRef, createdByEmail: string) => Promise<void>
  remove: (processGuid: string) => Promise<void>
}

function formatDate(ts: number | undefined): string {
  if (!ts) return ''
  return new Date(ts).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function resolveName(guid: string, entityMap: Record<string, { attributes?: { name?: string; qualifiedName?: string } }>): string {
  const e = entityMap[guid]
  return e?.attributes?.name || e?.attributes?.qualifiedName || guid
}

export function useLineage(currentAsset: AssetRef | null, token: string | null): UseLineageResult {
  const [entries, setEntries] = useState<LineageEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)

  const reload = useCallback(() => setTick((t) => t + 1), [])

  useEffect(() => {
    if (!currentAsset || !token) {
      setEntries([])
      return
    }

    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)

      try {
        const graph = await fetchLineageGraph(currentAsset!.guid, token!)
        const entityMap = graph.guidEntityMap || {}

        // Find manual Process assets in the graph
        const processes = Object.values(entityMap).filter(
          (e) =>
            e.typeName === 'Process' &&
            (String(e.attributes?.qualifiedName || '').startsWith('manual/lineage/') ||
              e.attributes?.connectorName === 'manual')
        )

        if (cancelled) return

        if (!processes.length) {
          setEntries([])
          setLoading(false)
          return
        }

        // Lineage graph strips inputs/outputs — fetch each process fully
        const fullProcesses = await Promise.all(
          processes.map((p) =>
            fetchProcessEntity(p.guid, token!).catch(() => p as unknown as ProcessEntity)
          )
        )

        if (cancelled) return

        // Seed local map with currentAsset
        const nameMap: Record<string, { attributes?: { name?: string; qualifiedName?: string } }> = {
          [currentAsset!.guid]: { attributes: { name: currentAsset!.name } },
        }

        // Collect GUIDs not in entityMap
        const missingGuids = new Set<string>()
        fullProcesses.forEach((p) => {
          ;(p.attributes?.inputs || []).forEach((i) => {
            if (!entityMap[i.guid]) missingGuids.add(i.guid)
          })
          ;(p.attributes?.outputs || []).forEach((o) => {
            if (!entityMap[o.guid]) missingGuids.add(o.guid)
          })
        })

        // Batch-fetch missing
        const resolved = await resolveGuids([...missingGuids], token!).catch(() => ({}))
        Object.assign(nameMap, entityMap, resolved)

        const built: LineageEntry[] = fullProcesses.map((p) => {
          const inputGuids = (p.attributes?.inputs || []).map((i) => i.guid)
          const outputGuids = (p.attributes?.outputs || []).map((o) => o.guid)

          return {
            processGuid: p.guid,
            srcName: inputGuids.map((g) => resolveName(g, nameMap)).join(', ') || '?',
            tgtName: outputGuids.map((g) => resolveName(g, nameMap)).join(', ') || '?',
            srcIsCurrent: inputGuids.includes(currentAsset!.guid),
            tgtIsCurrent: outputGuids.includes(currentAsset!.guid),
            createdBy: p.attributes?.createdBy || '',
            createdAt: formatDate(p.attributes?.createTime),
          }
        })

        if (!cancelled) setEntries(built)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load lineage')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => { cancelled = true }
  }, [currentAsset, token, tick])

  const create = useCallback(
    async (src: AssetRef, tgt: AssetRef, createdByEmail: string) => {
      await createLineageProcess(src, tgt, token!, createdByEmail)
      reload()
    },
    [token, reload]
  )

  const remove = useCallback(
    async (processGuid: string) => {
      await deleteProcess(processGuid, token!)
      reload()
    },
    [token, reload]
  )

  return { entries, loading, error, reload, create, remove }
}
