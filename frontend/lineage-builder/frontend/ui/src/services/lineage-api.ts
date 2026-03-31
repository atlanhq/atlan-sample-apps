import type { AssetRef, ProcessEntity, SearchHit } from '../types/atlan'

async function apiFetch<T>(
  method: string,
  path: string,
  token: string,
  body?: unknown
): Promise<T> {
  const res = await fetch(path, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: body != null ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`${method} ${path} → ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

// ── Fetch a single entity by GUID ────────────────────────────────────────────

export async function fetchEntity(guid: string, token: string): Promise<AssetRef> {
  const data = await apiFetch<{ entity: { guid: string; typeName: string; attributes: Record<string, unknown> } }>(
    'GET',
    `/api/meta/entity/guid/${encodeURIComponent(guid)}?minExtInfo=true`,
    token
  )
  const e = data.entity
  return {
    guid: e.guid,
    typeName: e.typeName,
    name: (e.attributes?.name as string) || (e.attributes?.displayName as string) || guid,
    qualifiedName: (e.attributes?.qualifiedName as string) || '',
  }
}

// ── Search assets by name ────────────────────────────────────────────────────

const SEARCHABLE_TYPES = ['Table', 'View', 'MaterialisedView', 'Column', 'Schema', 'Database']

export async function searchAssets(query: string, token: string): Promise<SearchHit[]> {
  const data = await apiFetch<{ entities?: SearchHit[] }>(
    'POST',
    '/api/meta/search/indexsearch',
    token,
    {
      dsl: {
        query: {
          bool: {
            must: [
              {
                bool: {
                  should: [
                    { match_phrase_prefix: { name: query } },
                    { wildcard: { 'name.keyword': { value: `*${query}*`, case_insensitive: true } } },
                  ],
                },
              },
            ],
            filter: [
              { term: { __state: 'ACTIVE' } },
              { terms: { '__typeName.keyword': SEARCHABLE_TYPES } },
            ],
          },
        },
        size: 12,
      },
      attributes: ['name', 'qualifiedName', 'typeName', 'connectionQualifiedName', 'databaseName', 'schemaName'],
    }
  )
  return data.entities || []
}

// ── Fetch lineage graph ───────────────────────────────────────────────────────

interface LineageGraphResponse {
  guidEntityMap: Record<string, { guid: string; typeName: string; attributes: Record<string, unknown> }>
}

export async function fetchLineageGraph(assetGuid: string, token: string): Promise<LineageGraphResponse> {
  return apiFetch<LineageGraphResponse>(
    'GET',
    `/api/meta/lineage/${encodeURIComponent(assetGuid)}?depth=1&direction=BOTH&hideProcess=false`,
    token
  )
}

// ── Fetch full process entity (lineage graph strips inputs/outputs) ───────────

export async function fetchProcessEntity(processGuid: string, token: string): Promise<ProcessEntity> {
  const data = await apiFetch<{ entity: ProcessEntity }>('GET', `/api/meta/entity/guid/${encodeURIComponent(processGuid)}`, token)
  return data.entity
}

// ── Batch resolve GUIDs → names via indexsearch ───────────────────────────────

export async function resolveGuids(
  guids: string[],
  token: string
): Promise<Record<string, SearchHit>> {
  if (!guids.length) return {}
  const data = await apiFetch<{ entities?: SearchHit[] }>(
    'POST',
    '/api/meta/search/indexsearch',
    token,
    {
      dsl: {
        query: { terms: { __guid: guids } },
        size: guids.length + 5,
      },
      attributes: ['name', 'qualifiedName'],
    }
  )
  const map: Record<string, SearchHit> = {}
  for (const e of data.entities || []) {
    map[e.guid] = e
  }
  return map
}

// ── Create a manual lineage Process asset ────────────────────────────────────

export async function createLineageProcess(
  src: AssetRef,
  tgt: AssetRef,
  token: string,
  createdByEmail: string
): Promise<void> {
  const id = crypto.randomUUID()
  await apiFetch<unknown>('POST', '/api/meta/entity/bulk', token, {
    entities: [
      {
        typeName: 'Process',
        attributes: {
          name: `manual-lineage-${id}`,
          qualifiedName: `manual/lineage/${src.guid}/${tgt.guid}/${id}`,
          inputs: [{ guid: src.guid, typeName: src.typeName }],
          outputs: [{ guid: tgt.guid, typeName: tgt.typeName }],
          connectorName: 'manual',
          userDescription: `Manual lineage created by ${createdByEmail} via Atlan UI`,
        },
      },
    ],
  })
}

// ── Soft-delete a Process asset ───────────────────────────────────────────────

export async function deleteProcess(processGuid: string, token: string): Promise<void> {
  await apiFetch<unknown>(
    'DELETE',
    `/api/meta/entity/guid/${encodeURIComponent(processGuid)}?deleteType=SOFT`,
    token
  )
}
