import type { AuthState } from '../types/atlan'

interface Props {
  authStatus: AuthState['status']
  error: string | null
}

export function LoadingState({ authStatus, error }: Props) {
  if (error) {
    return (
      <div className="loading-screen">
        <div style={{ color: '#dc2626', fontSize: 12, textAlign: 'center', maxWidth: 280 }}>{error}</div>
      </div>
    )
  }

  if (authStatus === 'connecting') {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <span>Connecting to Atlan…</span>
      </div>
    )
  }

  if (authStatus === 'logged_out') {
    return (
      <div className="loading-screen">
        <span>Session ended</span>
      </div>
    )
  }

  return null
}
