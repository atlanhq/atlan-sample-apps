import type { AssetDetails, DqRule } from "../types/atlan";

const headers = (token: string) => ({
  Authorization: `Bearer ${token}`,
  "Content-Type": "application/json",
});

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
// Parse DQ rules from IndexSearch response entities.
// ---------------------------------------------------------------------------

function parseRules(
  entities: Record<string, any>[],
  assetQualifiedName: string,
  sourceAssetName: string
): DqRule[] {
  return entities.map((e) => {
    const attrs = e.attributes || {};

    const nativeResult: string | null = attrs.dqRuleLatestResult ?? null;
    const nativeDate: string | null = attrs.dqRuleLatestResultComputedAt ?? null;
    const lastStatus = nativeResult
      ? nativeResult === "PASS" ? "Passed" : "Failed"
      : null;
    const lastExec = nativeDate ? nativeDate.slice(0, 10) : null;

    const colQn: string = attrs.dqRuleBaseColumnQualifiedName || "";
    const datasetQn: string = attrs.dqRuleBaseDatasetQualifiedName || assetQualifiedName;
    const isColumn = colQn.startsWith(assetQualifiedName + "/");
    const columnName = isColumn ? colQn.slice(assetQualifiedName.length + 1) : "";
    const appQn = isColumn ? colQn : datasetQn;

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
    };
  });
}

// ---------------------------------------------------------------------------
// Single-table mode.
// ---------------------------------------------------------------------------

export async function fetchDqRules(
  baseUrl: string,
  token: string,
  assetQualifiedName: string
): Promise<DqRule[]> {
  if (!assetQualifiedName) return [];

  const body = {
    dsl: {
      from: 0,
      size: 500,
      query: {
        bool: {
          filter: [
            { term: { "__typeName.keyword": "DataQualityRule" } },
            { term: { dqRuleBaseDatasetQualifiedName: assetQualifiedName } },
          ],
        },
      },
      sort: [{ "name.keyword": { order: "asc" } }],
    },
    attributes: [
      "name",
      "description",
      "qualifiedName",
      "dqRuleBaseDatasetQualifiedName",
      "dqRuleBaseColumnQualifiedName",
      "dqRuleLatestResult",
      "dqRuleLatestResultComputedAt",
    ],
  };

  const res = await fetch(`${baseUrl}/api/meta/search/indexsearch`, {
    method: "POST",
    headers: headers(token),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`DQ rules search failed: ${res.status}`);

  const data = await res.json();
  const parts = assetQualifiedName.split("/");
  const tableName = parts[parts.length - 1] || "";
  return parseRules(data?.entities || [], assetQualifiedName, tableName);
}

// ---------------------------------------------------------------------------
// DataProduct mode.
// ---------------------------------------------------------------------------

/** Extract the __guid list from the DataProduct's stored DSL. */
export function extractGuidsFromDsl(dslString: string): string[] {
  try {
    const dsl = JSON.parse(dslString);
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

/** Fetch DQ rules for multiple tables in a single IndexSearch query. */
export async function fetchDqRulesForMultipleAssets(
  baseUrl: string,
  token: string,
  assets: AssetDetails[]
): Promise<DqRule[]> {
  if (assets.length === 0) return [];

  const datasetQns = assets.map((a) => a.qualified_name);

  const body = {
    dsl: {
      from: 0,
      size: 1000,
      query: {
        bool: {
          filter: [
            { term: { "__typeName.keyword": "DataQualityRule" } },
            { terms: { dqRuleBaseDatasetQualifiedName: datasetQns } },
          ],
        },
      },
      sort: [{ "name.keyword": { order: "asc" } }],
    },
    attributes: [
      "name",
      "description",
      "qualifiedName",
      "dqRuleBaseDatasetQualifiedName",
      "dqRuleBaseColumnQualifiedName",
      "dqRuleLatestResult",
      "dqRuleLatestResultComputedAt",
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
  const assetByQn = new Map(assets.map((a) => [a.qualified_name, a]));

  const rules: DqRule[] = [];
  for (const e of entities) {
    const attrs = e.attributes || {};
    const datasetQn: string = attrs.dqRuleBaseDatasetQualifiedName || "";
    const colQn: string = attrs.dqRuleBaseColumnQualifiedName || "";
    const parent = assetByQn.get(datasetQn);
    if (!parent) continue;

    const isColumn = !!colQn && colQn.startsWith(parent.qualified_name + "/");
    const columnName = isColumn ? colQn.slice(parent.qualified_name.length + 1) : "";
    const appQn = isColumn ? colQn : datasetQn;

    const nativeResult: string | null = attrs.dqRuleLatestResult ?? null;
    const nativeDate: string | null = attrs.dqRuleLatestResultComputedAt ?? null;

    rules.push({
      guid: e.guid || "",
      name: attrs.name || e.displayText || "",
      description: attrs.description || "",
      application_qualified_name: appQn,
      scope: isColumn ? "column" : "table",
      column_name: columnName,
      source_asset_name: parent.name,
      last_execution_date: nativeDate ? nativeDate.slice(0, 10) : null,
      last_status: nativeResult
        ? nativeResult === "PASS" ? "Passed" : "Failed"
        : null,
    });
  }
  return rules;
}
