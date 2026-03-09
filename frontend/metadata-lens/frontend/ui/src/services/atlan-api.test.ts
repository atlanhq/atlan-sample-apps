import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fetchEntityByGuid } from './atlan-api'

describe('fetchEntityByGuid', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('fetches entity with correct URL and headers', async () => {
    const mockEntity = {
      entity: {
        typeName: 'Table',
        guid: 'abc-123',
        status: 'ACTIVE',
        attributes: { name: 'my_table' },
      },
    }

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockEntity),
    }))

    const result = await fetchEntityByGuid('abc-123', 'my-token', 'https://tenant.atlan.com')

    expect(fetch).toHaveBeenCalledWith(
      'https://tenant.atlan.com/api/meta/entity/guid/abc-123?ignoreRelationships=true&minExtInfo=false',
      {
        method: 'GET',
        headers: {
          Authorization: 'Bearer my-token',
          'Content-Type': 'application/json',
        },
      }
    )

    expect(result).toEqual(mockEntity)
  })

  it('encodes special characters in guid', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ entity: {} }),
    }))

    await fetchEntityByGuid('guid/with spaces', 'token', 'https://example.com')

    const calledUrl = (fetch as ReturnType<typeof vi.fn>).mock.calls[0][0] as string
    expect(calledUrl).toContain('guid%2Fwith%20spaces')
  })

  it('throws on non-ok response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    }))

    await expect(fetchEntityByGuid('bad-id', 'token', 'https://example.com'))
      .rejects.toThrow('Failed to fetch entity: 404 Not Found')
  })

  it('throws on network error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Network error')))

    await expect(fetchEntityByGuid('id', 'token', 'https://example.com'))
      .rejects.toThrow('Network error')
  })

  it('uses empty baseUrl for relative requests', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ entity: {} }),
    }))

    await fetchEntityByGuid('guid-1', 'token', '')

    const calledUrl = (fetch as ReturnType<typeof vi.fn>).mock.calls[0][0] as string
    expect(calledUrl).toBe('/api/meta/entity/guid/guid-1?ignoreRelationships=true&minExtInfo=false')
  })
})
