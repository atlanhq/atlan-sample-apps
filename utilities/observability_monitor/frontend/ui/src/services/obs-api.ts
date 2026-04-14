import type { AssetDetails, Execution, ObservabilityAsset } from "../types/atlan";

const CM_SET_NAME = "Observability";
const CM_ATTR_EXECUTIONS = "Executions";

const headers = (token: string) => ({
  Authorization: `Bearer ${token}`,
  "Content-Type": "application/json",
});

export interface ObsTypedef {
  bmId: string;
  executionsAttrId: string;
}

export async function fetchObsTypedef(
  baseUrl: string,
  token: string
): Promise<ObsTypedef> {
  const res = await fetch(
    `${baseUrl}/api/meta/types/typedefs?type=BUSINESS_METADATA`,
    { headers: headers(token) }
  );
  if (!res.ok) throw new Error(`Typedef fetch failed: ${res.status}`);
  const data = await res.json();
  const defs: any[] = data?.businessMetadataDefs || [];
  const obs = defs.find(
    (d) => d.displayName === CM_SET_NAME || d.name === CM_SET_NAME
  );
  if (!obs) throw new Error(`BM set '${CM_SET_NAME}' not found`);
  const attrs: any[] = obs.attributeDefs || [];
  const execAttr = attrs.find(
    (a) => a.displayName === CM_ATTR_EXECUTIONS || a.name === CM_ATTR_EXECUTIONS
  );
  if (!execAttr) {
    throw new Error(`BM '${CM_SET_NAME}' missing attribute '${CM_ATTR_EXECUTIONS}'`);
  }
  return { bmId: obs.name, executionsAttrId: execAttr.name };
}

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
 * Fetch Observability CustomEntity assets linked to the given asset
 * via applicationQualifiedName (exact match).
 */
export async function fetchObservabilityAssets(
  baseUrl: string,
  token: string,
  assetQualifiedName: string,
  typedef: ObsTypedef
): Promise<ObservabilityAsset[]> {
  if (!assetQualifiedName) return [];

  const execKey = `${typedef.bmId}.${typedef.executionsAttrId}`;

  const body = {
    dsl: {
      from: 0,
      size: 500,
      query: {
        bool: {
          filter: [
            { term: { "__typeName.keyword": "CustomEntity" } },
            { term: { applicationQualifiedName: assetQualifiedName } },
            { term: { assetUserDefinedType: "Observability" } },
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
      execKey,
    ],
  };

  const res = await fetch(`${baseUrl}/api/meta/search/indexsearch`, {
    method: "POST",
    headers: headers(token),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Observability search failed: ${res.status}`);

  const data = await res.json();
  const entities: Record<string, any>[] = data?.entities || [];

  return entities.map((e) => {
    const attrs = e.attributes || {};
    const rawExecs: string[] = Array.isArray(attrs[execKey]) ? attrs[execKey] : [];

    const executions: Execution[] = rawExecs.map((entry, i) => {
      const parts = entry.split("|");
      return {
        key: `${e.guid}::${i}`,
        executionId: parts[0] || "",
        cutOffDate: parts[1] || "",
        executionDate: parts[2] || "",
      };
    });

    // Sort newest execution first.
    executions.sort((a, b) => b.executionDate.localeCompare(a.executionDate));

    return {
      guid: e.guid || "",
      name: attrs.name || e.displayText || "",
      description: attrs.description || "",
      application_qualified_name: attrs.applicationQualifiedName || "",
      executions,
    };
  });
}
