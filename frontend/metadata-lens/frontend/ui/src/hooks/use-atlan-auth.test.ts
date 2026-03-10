import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useAtlanAuth } from './use-atlan-auth'

// Capture callback options passed to AtlanAuth constructor
let capturedOptions: Record<string, unknown> = {}
const mockInit = vi.fn().mockResolvedValue(undefined)
const mockGetToken = vi.fn().mockReturnValue('sdk-token')

vi.mock('@atlanhq/atlan-auth', () => ({
  AtlanAuth: vi.fn().mockImplementation((options: Record<string, unknown>) => {
    capturedOptions = options
    return {
      init: mockInit,
      getToken: mockGetToken,
      api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
    }
  }),
}))

describe('useAtlanAuth', () => {
  const originalLocation = window.location

  beforeEach(() => {
    vi.clearAllMocks()
    capturedOptions = {}
  })

  afterEach(() => {
    // Restore location if it was overridden
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      writable: true,
    })
  })

  it('starts in initializing state', () => {
    const { result } = renderHook(() => useAtlanAuth())

    expect(result.current.status).toBe('initializing')
    expect(result.current.atlan).toBeNull()
    expect(result.current.token).toBeNull()
    expect(result.current.assetId).toBeNull()
    expect(result.current.error).toBeNull()
  })

  it('calls AtlanAuth.init() on mount', () => {
    renderHook(() => useAtlanAuth())
    expect(mockInit).toHaveBeenCalledOnce()
  })

  it('transitions to authenticated when onReady fires', () => {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, search: '?assetId=asset-guid-123' },
      writable: true,
    })

    const { result } = renderHook(() => useAtlanAuth())

    act(() => {
      const onReady = capturedOptions.onReady as () => void
      onReady()
    })

    expect(result.current.status).toBe('authenticated')
    expect(result.current.atlan).not.toBeNull()
    expect(result.current.token).toBe('sdk-token')
    expect(result.current.assetId).toBe('asset-guid-123')
    expect(result.current.error).toBeNull()
  })

  it('extracts assetId from URL ?assetId= param', () => {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, search: '?assetId=my-asset-guid' },
      writable: true,
    })

    const { result } = renderHook(() => useAtlanAuth())

    act(() => {
      const onReady = capturedOptions.onReady as () => void
      onReady()
    })

    expect(result.current.assetId).toBe('my-asset-guid')
  })

  it('sets assetId to null when no URL param', () => {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, search: '' },
      writable: true,
    })

    const { result } = renderHook(() => useAtlanAuth())

    act(() => {
      const onReady = capturedOptions.onReady as () => void
      onReady()
    })

    expect(result.current.assetId).toBeNull()
  })

  it('handles onError callback', () => {
    const { result } = renderHook(() => useAtlanAuth())

    act(() => {
      const onError = capturedOptions.onError as (error: Error) => void
      onError(new Error('Auth failed'))
    })

    expect(result.current.status).toBe('error')
    expect(result.current.error).toBe('Auth failed')
  })

  it('handles onError with missing message', () => {
    const { result } = renderHook(() => useAtlanAuth())

    act(() => {
      const onError = capturedOptions.onError as (error: { message?: string }) => void
      onError({})
    })

    expect(result.current.status).toBe('error')
    expect(result.current.error).toBe('Authentication failed')
  })

  it('handles onLogout callback', () => {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, search: '?assetId=asset-1' },
      writable: true,
    })

    const { result } = renderHook(() => useAtlanAuth())

    // First authenticate
    act(() => {
      const onReady = capturedOptions.onReady as () => void
      onReady()
    })
    expect(result.current.status).toBe('authenticated')

    // Then logout
    act(() => {
      const onLogout = capturedOptions.onLogout as () => void
      onLogout()
    })

    expect(result.current.status).toBe('logged_out')
    expect(result.current.atlan).toBeNull()
    expect(result.current.token).toBeNull()
    expect(result.current.assetId).toBeNull()
    expect(result.current.error).toBeNull()
  })

  it('updates token on onTokenRefresh', () => {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, search: '?assetId=asset-1' },
      writable: true,
    })

    const { result } = renderHook(() => useAtlanAuth())

    // First authenticate
    act(() => {
      const onReady = capturedOptions.onReady as () => void
      onReady()
    })
    expect(result.current.token).toBe('sdk-token')

    // Refresh — onTokenRefresh receives new token string directly
    act(() => {
      const onTokenRefresh = capturedOptions.onTokenRefresh as (token: string) => void
      onTokenRefresh('refreshed-token')
    })

    expect(result.current.token).toBe('refreshed-token')
  })
})
