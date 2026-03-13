import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useAtlanAuth } from './use-atlan-auth'

describe('useAtlanAuth', () => {
  describe('production mode (iframe handshake)', () => {
    beforeEach(() => {
      vi.useFakeTimers()
      // Ensure dev mode is off for production tests
      import.meta.env.VITE_DEV_MODE = ''
      vi.stubGlobal('parent', {
        postMessage: vi.fn(),
      })
    })

    afterEach(() => {
      vi.useRealTimers()
      vi.restoreAllMocks()
    })

    it('starts in connecting state', () => {
      const { result } = renderHook(() => useAtlanAuth())
      expect(result.current.status).toBe('connecting')
      expect(result.current.assetId).toBeNull()
    })

    it('responds to ATLAN_HANDSHAKE with IFRAME_READY', () => {
      renderHook(() => useAtlanAuth())

      act(() => {
        window.dispatchEvent(
          new MessageEvent('message', {
            data: { type: 'ATLAN_HANDSHAKE' },
            origin: 'https://atlan.com',
          })
        )
      })

      // When VITE_ATLAN_ORIGIN is not set, origin defaults to '*'
      expect(window.parent.postMessage).toHaveBeenCalledWith(
        { type: 'IFRAME_READY' },
        '*'
      )
    })

    it('handles ATLAN_AUTH_CONTEXT and extracts asset ID', () => {
      const { result } = renderHook(() => useAtlanAuth())

      act(() => {
        window.dispatchEvent(
          new MessageEvent('message', {
            data: {
              type: 'ATLAN_AUTH_CONTEXT',
              payload: {
                token: 'test-token',
                user: { id: 'u1', username: 'testuser', email: 'test@atlan.com' },
                page: { route: '/asset', params: { id: 'asset-guid-123' } },
                expiresAt: Date.now() + 3600000,
              },
            },
            origin: 'https://atlan.com',
          })
        )
      })

      expect(result.current.status).toBe('authenticated')
      expect(result.current.assetId).toBe('asset-guid-123')
      if (result.current.status === 'authenticated') {
        expect(result.current.context.token).toBe('test-token')
      }
    })

    it('sets error when auth context has no payload', () => {
      const { result } = renderHook(() => useAtlanAuth())

      act(() => {
        window.dispatchEvent(
          new MessageEvent('message', {
            data: { type: 'ATLAN_AUTH_CONTEXT' },
            origin: 'https://atlan.com',
          })
        )
      })

      expect(result.current.status).toBe('error')
      if (result.current.status === 'error') {
        expect(result.current.message).toContain('without payload')
      }
    })

    it('handles ATLAN_LOGOUT by clearing state', () => {
      const { result } = renderHook(() => useAtlanAuth())

      // First authenticate
      act(() => {
        window.dispatchEvent(
          new MessageEvent('message', {
            data: {
              type: 'ATLAN_AUTH_CONTEXT',
              payload: {
                token: 'test-token',
                user: { id: 'u1', username: 'testuser', email: 'test@atlan.com' },
                page: { route: '/asset', params: { id: 'asset-guid-123' } },
                expiresAt: Date.now() + 3600000,
              },
            },
            origin: 'https://atlan.com',
          })
        )
      })

      expect(result.current.status).toBe('authenticated')

      // Then logout
      act(() => {
        window.dispatchEvent(
          new MessageEvent('message', {
            data: { type: 'ATLAN_LOGOUT' },
            origin: 'https://atlan.com',
          })
        )
      })

      expect(result.current.status).toBe('logged_out')
      expect(result.current.assetId).toBeNull()
    })

    it('times out if no handshake received within 10 seconds', () => {
      const { result } = renderHook(() => useAtlanAuth())

      expect(result.current.status).toBe('connecting')

      act(() => {
        vi.advanceTimersByTime(10_000)
      })

      expect(result.current.status).toBe('error')
      if (result.current.status === 'error') {
        expect(result.current.message).toContain('timed out')
      }
    })

    it('clears handshake timeout after receiving handshake', () => {
      const { result } = renderHook(() => useAtlanAuth())

      act(() => {
        window.dispatchEvent(
          new MessageEvent('message', {
            data: { type: 'ATLAN_HANDSHAKE' },
            origin: 'https://atlan.com',
          })
        )
      })

      // Advance past timeout — should NOT switch to error
      act(() => {
        vi.advanceTimersByTime(10_000)
      })

      // Still connecting (not error) because handshake was received
      expect(result.current.status).toBe('connecting')
    })

    it('handles ATLAN_TOKEN_REFRESH', () => {
      const { result } = renderHook(() => useAtlanAuth())

      // First authenticate
      act(() => {
        window.dispatchEvent(
          new MessageEvent('message', {
            data: {
              type: 'ATLAN_AUTH_CONTEXT',
              payload: {
                token: 'old-token',
                user: { id: 'u1', username: 'testuser', email: 'test@atlan.com' },
                page: { route: '/asset', params: { id: 'guid-1' } },
                expiresAt: Date.now() + 3600000,
              },
            },
            origin: 'https://atlan.com',
          })
        )
      })

      // Refresh token
      act(() => {
        window.dispatchEvent(
          new MessageEvent('message', {
            data: {
              type: 'ATLAN_TOKEN_REFRESH',
              payload: {
                token: 'new-token',
                user: { id: 'u1', username: 'testuser', email: 'test@atlan.com' },
                page: { route: '/asset', params: { id: 'guid-1' } },
                expiresAt: Date.now() + 7200000,
              },
            },
            origin: 'https://atlan.com',
          })
        )
      })

      if (result.current.status === 'authenticated') {
        expect(result.current.context.token).toBe('new-token')
      }
    })

    it('schedules proactive token refresh 5 minutes before expiry', () => {
      renderHook(() => useAtlanAuth())

      const expiresAt = Date.now() + 10 * 60 * 1000 // 10 min from now

      act(() => {
        window.dispatchEvent(
          new MessageEvent('message', {
            data: {
              type: 'ATLAN_AUTH_CONTEXT',
              payload: {
                token: 'test-token',
                user: { id: 'u1', username: 'testuser', email: 'test@atlan.com' },
                page: { route: '/asset', params: { id: 'guid-1' } },
                expiresAt,
              },
            },
            origin: 'https://atlan.com',
          })
        )
      })

      // Advance to 5 minutes before expiry (5 min from now)
      act(() => {
        vi.advanceTimersByTime(5 * 60 * 1000)
      })

      // Should have sent a token refresh request
      expect(window.parent.postMessage).toHaveBeenCalledWith(
        { type: 'IFRAME_TOKEN_REQUEST' },
        '*'
      )
    })
  })

  describe('dev mode', () => {
    afterEach(() => {
      import.meta.env.VITE_DEV_MODE = ''
      import.meta.env.VITE_ATLAN_API_TOKEN = ''
      import.meta.env.VITE_ATLAN_ASSET_GUID = ''
    })

    it('immediately authenticates with env var token and GUID', () => {
      import.meta.env.VITE_DEV_MODE = 'true'
      import.meta.env.VITE_ATLAN_API_TOKEN = 'dev-token-abc'
      import.meta.env.VITE_ATLAN_ASSET_GUID = 'guid-from-env'

      const { result } = renderHook(() => useAtlanAuth())

      expect(result.current.status).toBe('authenticated')
      expect(result.current.assetId).toBe('guid-from-env')
      if (result.current.status === 'authenticated') {
        expect(result.current.context.token).toBe('dev-token-abc')
        expect(result.current.context.user.username).toBe('dev')
        expect(result.current.context.page.params.id).toBe('guid-from-env')
      }
    })

    it('returns error when token is missing', () => {
      import.meta.env.VITE_DEV_MODE = 'true'
      import.meta.env.VITE_ATLAN_API_TOKEN = ''
      import.meta.env.VITE_ATLAN_ASSET_GUID = 'some-guid'

      const { result } = renderHook(() => useAtlanAuth())

      expect(result.current.status).toBe('error')
      if (result.current.status === 'error') {
        expect(result.current.message).toContain('VITE_ATLAN_API_TOKEN')
      }
    })

    it('returns error when asset GUID is missing', () => {
      import.meta.env.VITE_DEV_MODE = 'true'
      import.meta.env.VITE_ATLAN_API_TOKEN = 'some-token'
      import.meta.env.VITE_ATLAN_ASSET_GUID = ''

      const { result } = renderHook(() => useAtlanAuth())

      expect(result.current.status).toBe('error')
      if (result.current.status === 'error') {
        expect(result.current.message).toContain('VITE_ATLAN_ASSET_GUID')
      }
    })

    it('does not set up postMessage listener in dev mode', () => {
      import.meta.env.VITE_DEV_MODE = 'true'
      import.meta.env.VITE_ATLAN_API_TOKEN = 'dev-token'
      import.meta.env.VITE_ATLAN_ASSET_GUID = 'dev-guid'

      const addEventSpy = vi.spyOn(window, 'addEventListener')

      renderHook(() => useAtlanAuth())

      const messageListeners = addEventSpy.mock.calls.filter(
        ([event]) => event === 'message'
      )
      expect(messageListeners).toHaveLength(0)

      addEventSpy.mockRestore()
    })
  })
})
