export type AtlanMessageType =
  | "ATLAN_HANDSHAKE"
  | "IFRAME_READY"
  | "ATLAN_AUTH_CONTEXT"
  | "IFRAME_TOKEN_REQUEST"
  | "ATLAN_LOGOUT";

export interface AtlanUser {
  id: string;
  username: string;
  email: string;
  name: string;
}

export interface AtlanPage {
  route: string;
  params: Record<string, string>;
  query: Record<string, string>;
}

export interface AtlanAuthContext {
  token: string;
  expiresAt: number;
  user: AtlanUser;
  page: AtlanPage;
}

export interface AtlanMessage {
  type: AtlanMessageType;
  payload?: AtlanAuthContext | { appId: string };
}

export type AuthState = "connecting" | "authenticated" | "error" | "logged_out";

export interface AssetDetails {
  guid: string;
  name: string;
  qualified_name: string;
  type_name: string;
}

/** One execution entry parsed from Observability.Executions. */
export interface Execution {
  key: string;
  executionId: string;
  cutOffDate: string;
  executionDate: string;
}

/** One Observability CustomEntity linked via applicationQualifiedName. */
export interface ObservabilityAsset {
  guid: string;
  name: string;
  description: string;
  application_qualified_name: string;
  executions: Execution[];
}
