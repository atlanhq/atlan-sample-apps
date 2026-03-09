import type { AuthState } from '../types/atlan'

interface LoadingStateProps {
  authStatus: AuthState['status']
  metadataLoading: boolean
  error: string | null
}

export function LoadingState({ authStatus, metadataLoading, error }: LoadingStateProps) {
  if (error) {
    return (
      <div className="state-container state-error">
        <div className="state-icon">!</div>
        <div className="state-title">Something went wrong</div>
        <div className="state-message">{error}</div>
      </div>
    )
  }

  if (authStatus === 'connecting') {
    return (
      <div className="state-container state-connecting">
        <div className="state-spinner" />
        <div className="state-title">Connecting to Atlan</div>
        <div className="state-message">Waiting for authentication handshake...</div>
      </div>
    )
  }

  if (authStatus === 'logged_out') {
    return (
      <div className="state-container state-logout">
        <div className="state-icon">&#x2192;</div>
        <div className="state-title">Logged out</div>
        <div className="state-message">Your session has ended. Please log in again.</div>
      </div>
    )
  }

  if (metadataLoading) {
    return (
      <div className="state-container state-loading">
        <div className="state-spinner" />
        <div className="state-title">Loading metadata</div>
        <div className="state-message">Fetching asset attributes...</div>
      </div>
    )
  }

  return null
}
