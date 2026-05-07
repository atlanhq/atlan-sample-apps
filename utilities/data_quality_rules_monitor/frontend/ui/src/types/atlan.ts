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

export type RuleScope = "table" | "column";

/** One DQ rule = one DataQualityRule asset. */
export interface DqRule {
  guid: string;
  name: string;
  description: string;
  /** dq_rule_base_column_qualified_name for column rules, dq_rule_base_dataset_qualified_name for table rules. */
  application_qualified_name: string;
  /** "table" or "column" — derived from dq_rule_base_column_qualified_name presence. */
  scope: RuleScope;
  /** Column name if scope is "column", empty string otherwise. */
  column_name: string;
  /** When in DataProduct mode, the member table this rule belongs to. */
  source_asset_name: string;
  /** Last execution date from DQ.Results history, or dq_rule_latest_result_computed_at. */
  last_execution_date: string | null;
  /** Last status from dq_rule_latest_result (PASS → "Passed", FAIL → "Failed"). */
  last_status: string | null;
}

/** View mode: single table vs data product (aggregated across member tables). */
export type ViewMode = "table" | "data-product";
