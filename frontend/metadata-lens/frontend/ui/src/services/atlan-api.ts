import type { EntityResponse } from '../types/atlan'

export async function fetchEntityByGuid(
  guid: string,
  token: string,
  baseUrl: string
): Promise<EntityResponse> {
  const url = `${baseUrl}/api/meta/entity/guid/${encodeURIComponent(guid)}?ignoreRelationships=true&minExtInfo=false`

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch entity: ${response.status} ${response.statusText}`)
  }

  return response.json()
}
