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

/** One DQ rule = one CustomEntity asset linked via applicationQualifiedName. */
export interface DqRule {
  guid: string;
  name: string;
  description: string;
  application_qualified_name: string;
  /** Last execution date parsed from DQ.Results (latest element). */
  last_execution_date: string | null;
  /** Last status parsed from DQ.Results (Passed / Failed / etc.). */
  last_status: string | null;
  /** Raw DQ.Results array (each entry is "execution_date|status"). */
  results: string[];
  /** gf_uuaa_id, pushed as DQ.ID. */
  id: string | null;
}
