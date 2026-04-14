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
    attributes: ["name", "qualifiedName", "dataProductAssetsDSL"],
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

// ---------------------------------------------------------------------------
// Helpers to parse DQ rules from IndexSearch response entities.
// ---------------------------------------------------------------------------

function parseRules(
  entities: Record<string, any>[],
  resultsKey: string,
  idKey: string,
  assetQualifiedName: string,
  sourceAssetName: string
): DqRule[] {
  return entities.map((e) => {
    const attrs = e.attributes || {};
    const results: string[] = Array.isArray(attrs[resultsKey])
      ? attrs[resultsKey]
      : [];
    const id: string | null = attrs[idKey] ?? null;

    let lastExec: string | null = null;
    let lastStatus: string | null = null;
    if (results.length > 0) {
      const sorted = [...results].sort();
      const latest = sorted[sorted.length - 1];
      const [date, status] = latest.split("|");
      lastExec = date || null;
      lastStatus = status || null;
    }

    const appQn: string = attrs.applicationQualifiedName || "";
    const isColumn = appQn.startsWith(assetQualifiedName + "/");
    const columnName = isColumn
      ? appQn.slice(assetQualifiedName.length + 1)
      : "";

    return {
      guid: e.guid || "",
      name: attrs.name || e.displayText || "",
      description: attrs.description || "",
      application_qualified_name: appQn,
      scope: isColumn ? ("column" as const) : ("table" as const),
      column_name: columnName,
      source_asset_name: sourceAssetName,
      last_execution_date: lastExec,
      last_status: lastStatus,
      results,
      id,
    };
  });
}

// ---------------------------------------------------------------------------
// Single-table mode: fetch DQ rules for one asset.
// ---------------------------------------------------------------------------

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
            {
              bool: {
                should: [
                  { term: { applicationQualifiedName: assetQualifiedName } },
                  {
                    prefix: {
                      applicationQualifiedName: assetQualifiedName + "/",
                    },
                  },
                ],
                minimum_should_match: 1,
              },
            },
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
  // Extract simple table name from qualified name for source_asset_name.
  const parts = assetQualifiedName.split("/");
  const tableName = parts[parts.length - 1] || "";
  return parseRules(data?.entities || [], resultsKey, idKey, assetQualifiedName, tableName);
}

// ---------------------------------------------------------------------------
// DataProduct mode: extract member GUIDs from DSL, resolve to tables, fetch
// DQ rules across all of them in a single batched query.
// ---------------------------------------------------------------------------

/** Extract the __guid list from the DataProduct's stored DSL. */
export function extractGuidsFromDsl(dslString: string): string[] {
  try {
    const dsl = JSON.parse(dslString);
    // Walk: query.dsl.query.bool.filter.bool.must[0].bool.filter.terms.__guid
    const must =
      dsl?.query?.dsl?.query?.bool?.filter?.bool?.must ||
      dsl?.query?.bool?.filter?.bool?.must ||
      [];
    for (const clause of must) {
      const guids =
        clause?.bool?.filter?.terms?.__guid ||
        clause?.terms?.__guid;
      if (Array.isArray(guids) && guids.length > 0) return guids;
    }
  } catch {
    // ignore parse errors
  }
  return [];
}

/** Fetch member assets (Tables/Views) by their GUIDs. */
export async function fetchMemberAssets(
  baseUrl: string,
  token: string,
  guids: string[]
): Promise<AssetDetails[]> {
  if (guids.length === 0) return [];

  const body = {
    dsl: {
      from: 0,
      size: guids.length,
      query: {
        bool: {
          filter: [
            { terms: { __guid: guids } },
            { term: { __state: "ACTIVE" } },
          ],
        },
      },
    },
    attributes: ["name", "qualifiedName"],
  };

  const res = await fetch(`${baseUrl}/api/meta/search/indexsearch`, {
    method: "POST",
    headers: headers(token),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Member asset fetch failed: ${res.status}`);

  const data = await res.json();
  return (data?.entities || []).map((e: Record<string, any>) => ({
    guid: e.guid || "",
    name: e.attributes?.name || e.displayText || "",
    qualified_name: e.attributes?.qualifiedName || "",
    type_name: e.typeName || "",
  }));
}

/**
 * Fetch DQ rules for multiple tables in a single IndexSearch query.
 * Builds a `should` with one term + prefix per table qualifiedName.
 */
export async function fetchDqRulesForMultipleAssets(
  baseUrl: string,
  token: string,
  assets: AssetDetails[],
  dqTypedef: DqTypedef
): Promise<DqRule[]> {
  if (assets.length === 0) return [];

  const resultsKey = `${dqTypedef.bmId}.${dqTypedef.resultsAttrId}`;
  const idKey = `${dqTypedef.bmId}.${dqTypedef.idAttrId}`;

  // Build one should clause per asset (exact + prefix).
  const shouldClauses: object[] = [];
  for (const a of assets) {
    shouldClauses.push({ term: { applicationQualifiedName: a.qualified_name } });
    shouldClauses.push({
      prefix: { applicationQualifiedName: a.qualified_name + "/" },
    });
  }

  const body = {
    dsl: {
      from: 0,
      size: 1000,
      query: {
        bool: {
          filter: [
            { term: { "__typeName.keyword": "CustomEntity" } },
            { bool: { should: shouldClauses, minimum_should_match: 1 } },
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
  const entities: Record<string, any>[] = data?.entities || [];

  // For each entity, figure out which member asset it belongs to.
  // Sort assets by QN length descending so longer (more specific) matches win.
  const sortedAssets = [...assets].sort(
    (a, b) => b.qualified_name.length - a.qualified_name.length
  );

  const rules: DqRule[] = [];
  for (const e of entities) {
    const appQn: string = e.attributes?.applicationQualifiedName || "";
    // Find the matching parent asset.
    const parent = sortedAssets.find(
      (a) =>
        appQn === a.qualified_name ||
        appQn.startsWith(a.qualified_name + "/")
    );
    if (!parent) continue;

    const isColumn = appQn.startsWith(parent.qualified_name + "/");
    const columnName = isColumn
      ? appQn.slice(parent.qualified_name.length + 1)
      : "";

    const attrs = e.attributes || {};
    const results: string[] = Array.isArray(attrs[resultsKey])
      ? attrs[resultsKey]
      : [];
    const id: string | null = attrs[idKey] ?? null;

    let lastExec: string | null = null;
    let lastStatus: string | null = null;
    if (results.length > 0) {
      const sorted = [...results].sort();
      const latest = sorted[sorted.length - 1];
      const [date, status] = latest.split("|");
      lastExec = date || null;
      lastStatus = status || null;
    }

    rules.push({
      guid: e.guid || "",
      name: attrs.name || e.displayText || "",
      description: attrs.description || "",
      application_qualified_name: appQn,
      scope: isColumn ? "column" : "table",
      column_name: columnName,
      source_asset_name: parent.name,
      last_execution_date: lastExec,
      last_status: lastStatus,
      results,
      id,
    });
  }
  return rules;
}
