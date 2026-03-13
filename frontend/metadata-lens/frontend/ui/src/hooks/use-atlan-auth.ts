import { useState, useEffect, useRef } from 'react'
import { AtlanAuth } from '@atlanhq/atlan-auth'

export interface AtlanAuthState {
  status: 'initializing' | 'authenticated' | 'error' | 'logged_out'
  atlan: AtlanAuth | null
  token: string | null
  assetId: string | null
  error: string | null
}

function getAssetIdFromUrl(): string | null {
  return new URLSearchParams(window.location.search).get('assetId')
}

export function useAtlanAuth(): AtlanAuthState {
  const [state, setState] = useState<AtlanAuthState>({
    status: 'initializing',
    atlan: null,
    token: null,
    assetId: null,
    error: null,
  })
  const atlanRef = useRef<AtlanAuth | null>(null)
  const assetIdRef = useRef<string | null>(null)

  useEffect(() => {
    const origin = import.meta.env.VITE_ATLAN_ORIGIN || window.location.origin

    // Listen for ATLAN_AUTH_CONTEXT to extract page.params.id (asset GUID).
    // The SDK doesn't expose the page field, so we capture it directly.
    const handleMessage = (event: MessageEvent) => {
      const data = event.data ?? {}
      if (data.type === 'ATLAN_AUTH_CONTEXT') {
        const page = data.payload?.page ?? data.page
        assetIdRef.current = page?.params?.id ?? null
      }
    }
    window.addEventListener('message', handleMessage)

    const atlan = new AtlanAuth({
      origin,
      onReady: () => {
        const assetId = assetIdRef.current ?? getAssetIdFromUrl()
        setState({
          status: 'authenticated',
          atlan,
          token: atlan.getToken(),
          assetId,
          error: null,
        })
      },
      onError: (error) => {
        setState(prev => ({ ...prev, status: 'error', error: error.message ?? 'Authentication failed' }))
      },
      onTokenRefresh: (token) => {
        setState(prev => ({ ...prev, token }))
      },
      onLogout: () => {
        setState({ status: 'logged_out', atlan: null, token: null, assetId: null, error: null })
      },
    })
    atlanRef.current = atlan
    atlan.init().catch(() => {}) // errors handled by onError

    return () => {
      window.removeEventListener('message', handleMessage)
    }
  }, [])

  return state
}
