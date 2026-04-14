import type { AssetDetails, DqRule } from "../types/atlan";

const CM_SET_NAME = "DQ";
const CM_ATTR_RESULTS = "Results";
const CM_ATTR_ID = "ID";

const headers = (token: string) => ({
  Authorization: `Bearer ${token}`,
  "Content-Type": "application/json",
});

export interface DqTypedef {
  bmId: string;
  resultsAttrId: string;
  idAttrId: string;
}

/**
 * Resolve the internal IDs for the DQ business-metadata set and its two attrs.
 * Custom-metadata values come back in the IndexSearch response only when you
 * request them by their internal IDs ("<bmId>.<attrId>"), so we need these
 * before we can pull CM values alongside regular attributes.
 */
export async function fetchDqTypedef(
  baseUrl: string,
  token: string
): Promise<DqTypedef> {
  const res = await fetch(
    `${baseUrl}/api/meta/types/typedefs?type=BUSINESS_METADATA`,
    { headers: headers(token) }
  );
  if (!res.ok) throw new Error(`Typedef fetch failed: ${res.status}`);
  const data = await res.json();
  const defs: any[] = data?.businessMetadataDefs || [];
  const dq = defs.find(
    (d) => d.displayName === CM_SET_NAME || d.name === CM_SET_NAME
  );
  if (!dq) throw new Error(`BM set '${CM_SET_NAME}' not found`);
  const attrs: any[] = dq.attributeDefs || [];
  const byDisplay = (n: string) =>
    attrs.find((a) => a.displayName === n || a.name === n);
  const results = byDisplay(CM_ATTR_RESULTS);
  const id = byDisplay(CM_ATTR_ID);
  if (!results || !id) {
    throw new Error(
      `BM '${CM_SET_NAME}' missing attribute '${CM_ATTR_RESULTS}' or '${CM_ATTR_ID}'`
    );
  }
  return { bmId: dq.name, resultsAttrId: results.name, idAttrId: id.name };
}

/** Fetch asset (GUID -> qualifiedName, name, typeName). */
export async function fetchAsset(
  baseUrl: string,
  token: string,
  assetGuid: string
): Promise<AssetDetails | null> {
  const body = {
    dsl: {
      from: 0,
      size: 1,
      query: { bool: { filter: [{ term: { __guid: assetGuid } }] } },
    },
    attributes: ["name", "qualifiedName"],
  };

  const res = await fetch(`${baseUrl}/api/meta/search/indexsearch`, {
    method: "POST",
    headers: headers(token),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Asset lookup failed: ${res.status}`);

  const data = await res.json();
  const entity = data?.entities?.[0];
  if (!entity) return null;

  return {
    guid: entity.guid || "",
    name: entity.attributes?.name || entity.displayText || "",
    qualified_name: entity.attributes?.qualifiedName || "",
    type_name: entity.typeName || "",
  };
}

/**
 * Fetch every CustomEntity whose `applicationQualifiedName` equals the asset
 * qualifiedName (table-level rules) or is prefixed by it + "/" (column-level rules).
 * Returns rules with DQ custom metadata parsed from the response attributes.
 */
export async function fetchDqRules(
  baseUrl: string,
  token: string,
  assetQualifiedName: string,
  dqTypedef: DqTypedef
): Promise<DqRule[]> {
  if (!assetQualifiedName) return [];

  const resultsKey = `${dqTypedef.bmId}.${dqTypedef.resultsAttrId}`;
  const idKey = `${dqTypedef.bmId}.${dqTypedef.idAttrId}`;

  const body = {
    dsl: {
      from: 0,
      size: 500,
      query: {
        bool: {
          filter: [
            { term: { "__typeName.keyword": "CustomEntity" } },
            // Table-level rules only: applicationQualifiedName matches the
            // asset's qualifiedName exactly (column-level rules — prefixed
            // with "<tableQn>/<column>" — are intentionally excluded).
            { term: { applicationQualifiedName: assetQualifiedName } },
          ],
        },
      },
      sort: [{ "name.keyword": { order: "asc" } }],
    },
    attributes: [
      "name",
      "description",
      "qualifiedName",
      "applicationQualifiedName",
      "assetUserDefinedType",
      "assetIcon",
      resultsKey,
      idKey,
    ],
  };

  const res = await fetch(`${baseUrl}/api/meta/search/indexsearch`, {
    method: "POST",
    headers: headers(token),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`DQ rules search failed: ${res.status}`);

  const data = await res.json();
  const entities = data?.entities || [];

  return entities.map((e: Record<string, any>) => {
    const attrs = e.attributes || {};
    const results: string[] = Array.isArray(attrs[resultsKey])
      ? attrs[resultsKey]
      : [];
    const id: string | null = attrs[idKey] ?? null;

    // Pick the latest execution by lexicographic sort of "YYYY-MM-DD HH:MM:SS.mmm|status".
    let lastExec: string | null = null;
    let lastStatus: string | null = null;
    if (results.length > 0) {
      const sorted = [...results].sort();
      const latest = sorted[sorted.length - 1];
      const [date, status] = latest.split("|");
      lastExec = date || null;
      lastStatus = status || null;
    }

    return {
      guid: e.guid || "",
      name: attrs.name || e.displayText || "",
      description: attrs.description || "",
      application_qualified_name: attrs.applicationQualifiedName || "",
      last_execution_date: lastExec,
      last_status: lastStatus,
      results,
      id,
    };
  });
}
