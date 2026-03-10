import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useAssetMetadata } from './use-asset-metadata'
import type { EntityResponse } from '../types/atlan'
import type { AtlanAuth } from '@atlanhq/atlan-auth'

function createMockAtlan(apiGet: ReturnType<typeof vi.fn>): AtlanAuth {
  return {
    api: {
      get: apiGet,
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    },
  } as unknown as AtlanAuth
}

describe('useAssetMetadata', () => {
  let mockApiGet: ReturnType<typeof vi.fn>
  let mockAtlan: AtlanAuth

  beforeEach(() => {
    vi.restoreAllMocks()
    mockApiGet = vi.fn()
    mockAtlan = createMockAtlan(mockApiGet)
  })

  it('returns empty state when assetId is null', () => {
    const { result } = renderHook(() => useAssetMetadata(null, mockAtlan))

    expect(result.current.attributes).toEqual([])
    expect(result.current.totalCount).toBe(0)
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.entityTypeName).toBeNull()
  })

  it('returns empty state when atlan is null', () => {
    const { result } = renderHook(() => useAssetMetadata('guid-1', null))

    expect(result.current.attributes).toEqual([])
    expect(result.current.loading).toBe(false)
  })

  it('fetches and returns sorted non-null attributes', async () => {
    mockApiGet.mockResolvedValue({
      data: {
        entity: {
          typeName: 'Table',
          guid: 'guid-1',
          status: 'ACTIVE',
          attributes: {
            name: 'my_table',
            description: null,
            qualifiedName: 'db.schema.my_table',
            createTime: 1700000000000,
            ownerUsers: undefined,
            columnCount: 5,
          },
        },
      },
      status: 200,
      headers: {},
    })

    const { result } = renderHook(() => useAssetMetadata('guid-1', mockAtlan))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.entityTypeName).toBe('Table')
    expect(result.current.totalCount).toBe(6)
    // Non-null: name, qualifiedName, createTime, columnCount = 4
    expect(result.current.attributes).toHaveLength(4)
    // Should be sorted alphabetically
    expect(result.current.attributes[0].key).toBe('columnCount')
    expect(result.current.attributes[1].key).toBe('createTime')
    expect(result.current.attributes[2].key).toBe('name')
    expect(result.current.attributes[3].key).toBe('qualifiedName')
  })

  it('calls api.get with correct URL', async () => {
    mockApiGet.mockResolvedValue({
      data: {
        entity: { typeName: 'Table', guid: 'guid-1', status: 'ACTIVE', attributes: {} },
      },
      status: 200,
      headers: {},
    })

    renderHook(() => useAssetMetadata('guid-1', mockAtlan))

    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledOnce()
    })

    expect(mockApiGet).toHaveBeenCalledWith(
      '/api/meta/entity/guid/guid-1?ignoreRelationships=true&minExtInfo=false'
    )
  })

  it('handles API errors gracefully', async () => {
    mockApiGet.mockRejectedValue(new Error('Failed to fetch entity: 404 Not Found'))

    const { result } = renderHook(() => useAssetMetadata('bad-guid', mockAtlan))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.error).toBe('Failed to fetch entity: 404 Not Found')
    expect(result.current.attributes).toEqual([])
    expect(result.current.totalCount).toBe(0)
  })

  it('handles non-Error thrown values', async () => {
    mockApiGet.mockRejectedValue('string error')

    const { result } = renderHook(() => useAssetMetadata('guid', mockAtlan))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.error).toBe('Failed to fetch asset metadata')
  })

  it('shows loading state while fetching', async () => {
    let resolvePromise: (value: { data: EntityResponse; status: number; headers: Record<string, string> }) => void
    mockApiGet.mockImplementation(
      () => new Promise((resolve) => { resolvePromise = resolve })
    )

    const { result } = renderHook(() => useAssetMetadata('guid-1', mockAtlan))

    await waitFor(() => {
      expect(result.current.loading).toBe(true)
    })

    resolvePromise!({
      data: { entity: { typeName: 'Column', guid: 'guid-1', status: 'ACTIVE', attributes: {} } },
      status: 200,
      headers: {},
    })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
  })

  it('handles entity with empty attributes', async () => {
    mockApiGet.mockResolvedValue({
      data: {
        entity: {
          typeName: 'Database',
          guid: 'guid-1',
          status: 'ACTIVE',
          attributes: {},
        },
      },
      status: 200,
      headers: {},
    })

    const { result } = renderHook(() => useAssetMetadata('guid-1', mockAtlan))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.attributes).toEqual([])
    expect(result.current.totalCount).toBe(0)
  })

  it('refetches when assetId changes', async () => {
    mockApiGet
      .mockResolvedValueOnce({
        data: { entity: { typeName: 'Table', guid: 'g1', status: 'ACTIVE', attributes: { name: 'table1' } } },
        status: 200,
        headers: {},
      })
      .mockResolvedValueOnce({
        data: { entity: { typeName: 'Column', guid: 'g2', status: 'ACTIVE', attributes: { name: 'col1' } } },
        status: 200,
        headers: {},
      })

    const { result, rerender } = renderHook(
      ({ assetId }) => useAssetMetadata(assetId, mockAtlan),
      { initialProps: { assetId: 'g1' } }
    )

    await waitFor(() => {
      expect(result.current.entityTypeName).toBe('Table')
    })

    rerender({ assetId: 'g2' })

    await waitFor(() => {
      expect(result.current.entityTypeName).toBe('Column')
    })

    expect(mockApiGet).toHaveBeenCalledTimes(2)
  })
})
