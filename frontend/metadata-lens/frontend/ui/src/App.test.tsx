import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { App } from './App'
import * as api from './services/atlan-api'

vi.mock('./services/atlan-api')

describe('App', () => {
  describe('production mode (iframe)', () => {
    beforeEach(() => {
      vi.useFakeTimers()
      import.meta.env.VITE_DEV_MODE = ''
      vi.stubGlobal('parent', {
        postMessage: vi.fn(),
      })
    })

    afterEach(() => {
      vi.useRealTimers()
      vi.restoreAllMocks()
    })

    it('shows connecting state initially', () => {
      render(<App />)
      expect(screen.getByText('Connecting to Atlan')).toBeInTheDocument()
    })

    it('shows error state after handshake timeout', () => {
      render(<App />)

      act(() => {
        vi.advanceTimersByTime(10_000)
      })

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })

    it('fetches and displays attributes after authentication', async () => {
      vi.mocked(api.fetchEntityByGuid).mockResolvedValue({
        entity: {
          typeName: 'Table',
          guid: 'guid-1',
          status: 'ACTIVE',
          attributes: {
            name: 'test_table',
            qualifiedName: 'db.schema.test_table',
            description: null,
            columnCount: 10,
          },
        },
      })

      render(<App />)

      // Simulate handshake + auth
      act(() => {
        window.dispatchEvent(
          new MessageEvent('message', {
            data: { type: 'ATLAN_HANDSHAKE' },
            origin: 'https://atlan.com',
          })
        )
      })

      act(() => {
        window.dispatchEvent(
          new MessageEvent('message', {
            data: {
              type: 'ATLAN_AUTH_CONTEXT',
              payload: {
                token: 'test-token',
                user: { id: 'u1', username: 'testuser', email: 'test@atlan.com' },
                page: { route: '/asset', params: { id: 'guid-1' } },
                expiresAt: Date.now() + 3600000,
              },
            },
            origin: 'https://atlan.com',
          })
        )
      })

      await act(async () => {
        await vi.runAllTimersAsync()
      })

      expect(screen.getByText('Table')).toBeInTheDocument()
      expect(screen.getByText('test_table')).toBeInTheDocument()
      expect(screen.getByText('qualifiedName')).toBeInTheDocument()
    })

    it('shows logged out state after logout', () => {
      render(<App />)

      act(() => {
        window.dispatchEvent(
          new MessageEvent('message', {
            data: { type: 'ATLAN_HANDSHAKE' },
            origin: 'https://atlan.com',
          })
        )
      })

      act(() => {
        window.dispatchEvent(
          new MessageEvent('message', {
            data: {
              type: 'ATLAN_AUTH_CONTEXT',
              payload: {
                token: 'token',
                user: { id: 'u1', username: 'user', email: 'u@a.com' },
                page: { route: '/asset', params: { id: 'g1' } },
                expiresAt: Date.now() + 3600000,
              },
            },
            origin: 'https://atlan.com',
          })
        )
      })

      act(() => {
        window.dispatchEvent(
          new MessageEvent('message', {
            data: { type: 'ATLAN_LOGOUT' },
            origin: 'https://atlan.com',
          })
        )
      })

      expect(screen.getByText('Logged out')).toBeInTheDocument()
    })
  })

  describe('dev mode', () => {
    beforeEach(() => {
      import.meta.env.VITE_DEV_MODE = 'true'
      import.meta.env.VITE_ATLAN_API_TOKEN = 'dev-token'
      import.meta.env.VITE_ATLAN_ASSET_GUID = 'dev-asset-guid'
    })

    afterEach(() => {
      import.meta.env.VITE_DEV_MODE = ''
      import.meta.env.VITE_ATLAN_API_TOKEN = ''
      import.meta.env.VITE_ATLAN_ASSET_GUID = ''
      vi.restoreAllMocks()
    })

    it('shows dev banner and fetches metadata immediately', async () => {
      vi.mocked(api.fetchEntityByGuid).mockResolvedValue({
        entity: {
          typeName: 'Column',
          guid: 'dev-asset-guid',
          status: 'ACTIVE',
          attributes: { name: 'dev_column', dataType: 'VARCHAR' },
        },
      })

      const { findByText } = render(<App />)

      // Dev banner should be visible
      expect(screen.getByText(/Dev mode/)).toBeInTheDocument()
      expect(screen.getByText(/dev-asset-guid/)).toBeInTheDocument()

      // Should fetch metadata without any postMessage flow — use findBy to wait for async updates
      expect(await findByText('Column')).toBeInTheDocument()
      expect(await findByText('dev_column')).toBeInTheDocument()

      expect(api.fetchEntityByGuid).toHaveBeenCalledWith('dev-asset-guid', 'dev-token', '')
    })

    it('shows error when env vars are missing', () => {
      import.meta.env.VITE_ATLAN_API_TOKEN = ''

      render(<App />)

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
      expect(screen.getByText(/VITE_ATLAN_API_TOKEN/)).toBeInTheDocument()
    })
  })
})
