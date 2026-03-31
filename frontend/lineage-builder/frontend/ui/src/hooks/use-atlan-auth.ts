import { useCallback, useEffect, useRef, useState } from 'react'
import type { AuthContext, AuthState, AtlanMessage } from '../types/atlan'

const HANDSHAKE_TIMEOUT_MS = 10_000
const TOKEN_REFRESH_BUFFER_MS = 5 * 60 * 1000

export function isDevMode(): boolean {
  return import.meta.env.VITE_DEV_MODE === 'true'
}

function getAllowedOrigin(): string {
  return import.meta.env.VITE_ATLAN_ORIGIN || '*'
}

function buildDevAuthContext(): AuthContext {
  return {
    token: import.meta.env.VITE_ATLAN_API_TOKEN || '',
    user: { id: 'dev-user', username: 'dev', email: 'dev@localhost' },
    page: {
      route: '/assets',
      params: { id: import.meta.env.VITE_ATLAN_ASSET_GUID || '' },
    },
    expiresAt: Date.now() + 24 * 60 * 60 * 1000,
  }
}

export function useAtlanAuth(): AuthState & { assetId: string | null } {
  const devMode = isDevMode()

  const [authState, setAuthState] = useState<AuthState>(() => {
    if (devMode) {
      const context = buildDevAuthContext()
      if (!context.token || !context.page.params.id) {
        return {
          status: 'error',
          message:
            'Dev mode: VITE_ATLAN_API_TOKEN and VITE_ATLAN_ASSET_GUID must be set in .env.local',
        }
      }
      return { status: 'authenticated', context }
    }
    return { status: 'connecting' }
  })

  const [assetId, setAssetId] = useState<string | null>(() => {
    if (devMode) return import.meta.env.VITE_ATLAN_ASSET_GUID || null
    return null
  })

  const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const handshakeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const scheduleTokenRefresh = useCallback((expiresAt: number) => {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
    const delay = Math.max(0, expiresAt - TOKEN_REFRESH_BUFFER_MS - Date.now())
    refreshTimerRef.current = setTimeout(() => {
      const origin = getAllowedOrigin()
      window.parent.postMessage({ type: 'IFRAME_TOKEN_REQUEST' }, origin === '*' ? '*' : origin)
    }, delay)
  }, [])

  useEffect(() => {
    if (devMode) return

    const allowedOrigin = getAllowedOrigin()

    const handleMessage = (event: MessageEvent<AtlanMessage>) => {
      if (allowedOrigin !== '*' && event.origin !== allowedOrigin) return
      const { type, payload } = event.data ?? {}

      switch (type) {
        case 'ATLAN_HANDSHAKE': {
          if (handshakeTimerRef.current) {
            clearTimeout(handshakeTimerRef.current)
            handshakeTimerRef.current = null
          }
          const targetOrigin = allowedOrigin === '*' ? '*' : event.origin
          window.parent.postMessage({ type: 'IFRAME_READY' }, targetOrigin)
          break
        }
        case 'ATLAN_AUTH_CONTEXT': {
          if (!payload) {
            setAuthState({ status: 'error', message: 'Auth context received without payload' })
            return
          }
          setAuthState({ status: 'authenticated', context: payload })
          setAssetId(payload.page?.params?.id ?? null)
          if (payload.expiresAt) scheduleTokenRefresh(payload.expiresAt)
          break
        }
        case 'ATLAN_TOKEN_REFRESH': {
          if (!payload) return
          setAuthState({ status: 'authenticated', context: payload })
          if (payload.expiresAt) scheduleTokenRefresh(payload.expiresAt)
          break
        }
        case 'ATLAN_LOGOUT': {
          setAuthState({ status: 'logged_out' })
          setAssetId(null)
          if (refreshTimerRef.current) {
            clearTimeout(refreshTimerRef.current)
            refreshTimerRef.current = null
          }
          break
        }
      }
    }

    window.addEventListener('message', handleMessage)

    handshakeTimerRef.current = setTimeout(() => {
      setAuthState((prev) =>
        prev.status === 'connecting'
          ? { status: 'error', message: 'Handshake timed out — is the app embedded in Atlan?' }
          : prev
      )
    }, HANDSHAKE_TIMEOUT_MS)

    return () => {
      window.removeEventListener('message', handleMessage)
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
      if (handshakeTimerRef.current) clearTimeout(handshakeTimerRef.current)
    }
  }, [devMode, scheduleTokenRefresh])

  return { ...authState, assetId }
}
