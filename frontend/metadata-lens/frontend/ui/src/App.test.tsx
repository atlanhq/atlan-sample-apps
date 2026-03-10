import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { App } from './App'

// Capture the onReady/onError/onLogout callbacks from AtlanAuth constructor
let capturedOptions: Record<string, unknown> = {}
const mockInit = vi.fn().mockResolvedValue(undefined)
const mockGetToken = vi.fn().mockReturnValue('test-token')
const mockApiGet = vi.fn()

vi.mock('@atlanhq/atlan-auth', () => ({
  AtlanAuth: vi.fn().mockImplementation((options: Record<string, unknown>) => {
    capturedOptions = options
    return {
      init: mockInit,
      getToken: mockGetToken,
      api: { get: mockApiGet, post: vi.fn(), put: vi.fn(), delete: vi.fn() },
    }
  }),
}))

describe('App', () => {
  const originalLocation = window.location

  beforeEach(() => {
    vi.clearAllMocks()
    capturedOptions = {}
    mockApiGet.mockReset()
  })

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      writable: true,
    })
  })

  it('shows initializing state initially', () => {
    render(<App />)
    expect(screen.getByText('Connecting to Atlan')).toBeInTheDocument()
    expect(screen.getByText('Initializing authentication...')).toBeInTheDocument()
  })

  it('shows error state when onError fires', () => {
    render(<App />)

    act(() => {
      const onError = capturedOptions.onError as (error: Error) => void
      onError(new Error('Auth failed'))
    })

    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('Auth failed')).toBeInTheDocument()
  })

  it('shows logged out state', () => {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, search: '?assetId=g1' },
      writable: true,
    })

    render(<App />)

    // First authenticate
    mockApiGet.mockResolvedValue({
      data: { entity: { typeName: 'Table', guid: 'g1', status: 'ACTIVE', attributes: {} } },
      status: 200,
      headers: {},
    })

    act(() => {
      const onReady = capturedOptions.onReady as () => void
      onReady()
    })

    // Then logout
    act(() => {
      const onLogout = capturedOptions.onLogout as () => void
      onLogout()
    })

    expect(screen.getByText('Logged out')).toBeInTheDocument()
  })

  it('fetches and displays attributes after authentication', async () => {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, search: '?assetId=guid-1' },
      writable: true,
    })

    mockApiGet.mockResolvedValue({
      data: {
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
      },
      status: 200,
      headers: {},
    })

    render(<App />)

    act(() => {
      const onReady = capturedOptions.onReady as () => void
      onReady()
    })

    expect(await screen.findByText('Table')).toBeInTheDocument()
    expect(await screen.findByText('test_table')).toBeInTheDocument()
    expect(await screen.findByText('qualifiedName')).toBeInTheDocument()
  })

  it('does not show dev banner', () => {
    render(<App />)
    expect(screen.queryByText(/Dev mode/)).not.toBeInTheDocument()
  })
})
