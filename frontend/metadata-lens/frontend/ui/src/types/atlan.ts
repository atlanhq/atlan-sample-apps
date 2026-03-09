export interface AuthContext {
  token: string
  user: AtlanUser
  page: AtlanPage
  expiresAt: number
}

export interface AtlanUser {
  id: string
  username: string
  email: string
}

export interface AtlanPage {
  route: string
  params: Record<string, string>
}

export interface AtlanEntity {
  typeName: string
  attributes: EntityAttributes
  guid: string
  status: string
}

export type EntityAttributes = Record<string, unknown>

export interface EntityResponse {
  entity: AtlanEntity
}

export type AttributeEntry = {
  key: string
  value: unknown
}

// Iframe postMessage event types
export type AtlanMessageType =
  | 'ATLAN_HANDSHAKE'
  | 'ATLAN_AUTH_CONTEXT'
  | 'ATLAN_LOGOUT'
  | 'ATLAN_TOKEN_REFRESH'

export type IframeMessageType =
  | 'IFRAME_READY'
  | 'IFRAME_TOKEN_REQUEST'

export interface AtlanMessage {
  type: AtlanMessageType
  payload?: AuthContext
}

export interface IframeMessage {
  type: IframeMessageType
}

export type AuthState =
  | { status: 'connecting' }
  | { status: 'authenticated'; context: AuthContext }
  | { status: 'error'; message: string }
  | { status: 'logged_out' }
