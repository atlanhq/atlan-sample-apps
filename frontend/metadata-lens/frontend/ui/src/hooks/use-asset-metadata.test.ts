import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useAssetMetadata } from './use-asset-metadata'
import type { EntityResponse } from '../types/atlan'
import * as api from '../services/atlan-api'

vi.mock('../services/atlan-api')

describe('useAssetMetadata', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('returns empty state when assetId is null', () => {
    const { result } = renderHook(() => useAssetMetadata(null, 'token', ''))

    expect(result.current.attributes).toEqual([])
    expect(result.current.totalCount).toBe(0)
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.entityTypeName).toBeNull()
  })

  it('returns empty state when token is null', () => {
    const { result } = renderHook(() => useAssetMetadata('guid-1', null, ''))

    expect(result.current.attributes).toEqual([])
    expect(result.current.loading).toBe(false)
  })

  it('fetches and returns sorted non-null attributes', async () => {
    vi.mocked(api.fetchEntityByGuid).mockResolvedValue({
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
    })

    const { result } = renderHook(() => useAssetMetadata('guid-1', 'token', ''))

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

  it('handles API errors gracefully', async () => {
    vi.mocked(api.fetchEntityByGuid).mockRejectedValue(new Error('Failed to fetch entity: 404 Not Found'))

    const { result } = renderHook(() => useAssetMetadata('bad-guid', 'token', ''))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.error).toBe('Failed to fetch entity: 404 Not Found')
    expect(result.current.attributes).toEqual([])
    expect(result.current.totalCount).toBe(0)
  })

  it('handles non-Error thrown values', async () => {
    vi.mocked(api.fetchEntityByGuid).mockRejectedValue('string error')

    const { result } = renderHook(() => useAssetMetadata('guid', 'token', ''))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.error).toBe('Failed to fetch asset metadata')
  })

  it('shows loading state while fetching', async () => {
    let resolvePromise: (value: EntityResponse) => void
    vi.mocked(api.fetchEntityByGuid).mockImplementation(
      () => new Promise<EntityResponse>((resolve) => { resolvePromise = resolve })
    )

    const { result } = renderHook(() => useAssetMetadata('guid-1', 'token', ''))

    await waitFor(() => {
      expect(result.current.loading).toBe(true)
    })

    resolvePromise!({
      entity: { typeName: 'Column', guid: 'guid-1', status: 'ACTIVE', attributes: {} },
    })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
  })

  it('handles entity with empty attributes', async () => {
    vi.mocked(api.fetchEntityByGuid).mockResolvedValue({
      entity: {
        typeName: 'Database',
        guid: 'guid-1',
        status: 'ACTIVE',
        attributes: {},
      },
    })

    const { result } = renderHook(() => useAssetMetadata('guid-1', 'token', ''))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.attributes).toEqual([])
    expect(result.current.totalCount).toBe(0)
  })

  it('refetches when assetId changes', async () => {
    vi.mocked(api.fetchEntityByGuid)
      .mockResolvedValueOnce({
        entity: { typeName: 'Table', guid: 'g1', status: 'ACTIVE', attributes: { name: 'table1' } },
      })
      .mockResolvedValueOnce({
        entity: { typeName: 'Column', guid: 'g2', status: 'ACTIVE', attributes: { name: 'col1' } },
      })

    const { result, rerender } = renderHook(
      ({ assetId }) => useAssetMetadata(assetId, 'token', ''),
      { initialProps: { assetId: 'g1' } }
    )

    await waitFor(() => {
      expect(result.current.entityTypeName).toBe('Table')
    })

    rerender({ assetId: 'g2' })

    await waitFor(() => {
      expect(result.current.entityTypeName).toBe('Column')
    })

    expect(api.fetchEntityByGuid).toHaveBeenCalledTimes(2)
  })
})
