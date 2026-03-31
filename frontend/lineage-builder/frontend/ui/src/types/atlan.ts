// ── Auth / postMessage types ─────────────────────────────────────────────────

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

export type AuthState =
  | { status: 'connecting' }
  | { status: 'authenticated'; context: AuthContext }
  | { status: 'error'; message: string }
  | { status: 'logged_out' }

export type AtlanMessageType =
  | 'ATLAN_HANDSHAKE'
  | 'ATLAN_AUTH_CONTEXT'
  | 'ATLAN_LOGOUT'
  | 'ATLAN_TOKEN_REFRESH'

export interface AtlanMessage {
  type: AtlanMessageType
  payload?: AuthContext
}

// ── Asset types ──────────────────────────────────────────────────────────────

export interface AssetRef {
  guid: string
  typeName: string
  name: string
  qualifiedName: string
}

export interface SearchHit {
  guid: string
  typeName: string
  attributes: {
    name?: string
    qualifiedName?: string
    connectionQualifiedName?: string
    databaseName?: string
    schemaName?: string
  }
}

// ── Lineage types ────────────────────────────────────────────────────────────

export interface ProcessEntity {
  guid: string
  typeName: 'Process'
  attributes: {
    name?: string
    qualifiedName?: string
    connectorName?: string
    inputs?: Array<{ guid: string; typeName: string }>
    outputs?: Array<{ guid: string; typeName: string }>
    createdBy?: string
    createTime?: number
    userDescription?: string
  }
}

export interface LineageEntry {
  processGuid: string
  srcName: string
  tgtName: string
  srcIsCurrent: boolean
  tgtIsCurrent: boolean
  createdBy: string
  createdAt: string
}

export type LineageRole = 'target' | 'source'
