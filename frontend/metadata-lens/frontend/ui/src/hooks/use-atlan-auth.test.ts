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

  it('extracts assetId from postMessage page.params.id', () => {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, search: '' },
      writable: true,
    })

    const { result } = renderHook(() => useAtlanAuth())

    // Simulate ATLAN_AUTH_CONTEXT postMessage arriving before onReady
    act(() => {
      window.dispatchEvent(
        new MessageEvent('message', {
          data: {
            type: 'ATLAN_AUTH_CONTEXT',
            payload: {
              token: 'test-token',
              user: { id: 'u1', username: 'testuser', email: 'test@atlan.com' },
              page: { route: '/assets', params: { id: 'postmessage-guid' } },
            },
          },
        })
      )
    })

    act(() => {
      const onReady = capturedOptions.onReady as () => void
      onReady()
    })

    expect(result.current.assetId).toBe('postmessage-guid')
  })

  it('prefers postMessage assetId over URL param', () => {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, search: '?assetId=url-guid' },
      writable: true,
    })

    const { result } = renderHook(() => useAtlanAuth())

    // postMessage arrives with a different asset ID
    act(() => {
      window.dispatchEvent(
        new MessageEvent('message', {
          data: {
            type: 'ATLAN_AUTH_CONTEXT',
            payload: {
              token: 'test-token',
              user: { id: 'u1', username: 'testuser', email: 'test@atlan.com' },
              page: { route: '/assets', params: { id: 'postmessage-guid' } },
            },
          },
        })
      )
    })

    act(() => {
      const onReady = capturedOptions.onReady as () => void
      onReady()
    })

    expect(result.current.assetId).toBe('postmessage-guid')
  })

  it('falls back to URL ?assetId= param when no postMessage page data', () => {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, search: '?assetId=url-asset-guid' },
      writable: true,
    })

    const { result } = renderHook(() => useAtlanAuth())

    act(() => {
      const onReady = capturedOptions.onReady as () => void
      onReady()
    })

    expect(result.current.assetId).toBe('url-asset-guid')
  })

  it('sets assetId to null when no postMessage and no URL param', () => {
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

  it('cleans up postMessage listener on unmount', () => {
    const removeSpy = vi.spyOn(window, 'removeEventListener')

    const { unmount } = renderHook(() => useAtlanAuth())
    unmount()

    const messageRemovals = removeSpy.mock.calls.filter(
      ([event]) => event === 'message'
    )
    expect(messageRemovals).toHaveLength(1)

    removeSpy.mockRestore()
  })
})
