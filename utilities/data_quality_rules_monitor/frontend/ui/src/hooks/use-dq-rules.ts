import { useEffect, useState } from "react";
import type { AssetDetails, DqRule, ViewMode } from "../types/atlan";
import {
  fetchAsset,
  fetchDqRules,
  fetchDqTypedef,
  extractGuidsFromDsl,
  fetchMemberAssets,
  fetchDqRulesForMultipleAssets,
} from "../services/dq-api";

interface UseDqRulesReturn {
  asset: AssetDetails | null;
  viewMode: ViewMode;
  /** Member tables when in data-product mode. */
  memberAssets: AssetDetails[];
  rules: DqRule[];
  loading: boolean;
  error: string | null;
}

export function useDqRules(
  baseUrl: string,
  token: string,
  assetId: string
): UseDqRulesReturn {
  const [asset, setAsset] = useState<AssetDetails | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("table");
  const [memberAssets, setMemberAssets] = useState<AssetDetails[]>([]);
  const [rules, setRules] = useState<DqRule[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !assetId) return;
    let cancelled = false;

    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [a, td] = await Promise.all([
          fetchAsset(baseUrl, token, assetId),
          fetchDqTypedef(baseUrl, token),
        ]);
        if (cancelled) return;
        setAsset(a);
        if (!a) {
          setRules([]);
          return;
        }

        const isDataProduct = a.type_name === "DataProduct";
        setViewMode(isDataProduct ? "data-product" : "table");

        if (isDataProduct) {
          // DataProduct mode: get DSL → extract GUIDs → resolve member assets → batch-fetch rules.
          // fetchAsset already requests dataProductAssetsDSL; we need to re-fetch it
          // since AssetDetails doesn't carry it. Quick re-fetch with the attribute.
          const dpRes = await fetch(
            `${baseUrl}/api/meta/search/indexsearch`,
            {
              method: "POST",
              headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                dsl: {
                  from: 0,
                  size: 1,
                  query: { bool: { filter: [{ term: { __guid: assetId } }] } },
                },
                attributes: ["dataProductAssetsDSL"],
              }),
            }
          );
          if (!dpRes.ok) throw new Error(`DataProduct fetch failed: ${dpRes.status}`);
          const dpData = await dpRes.json();
          const dslStr =
            dpData?.entities?.[0]?.attributes?.dataProductAssetsDSL || "";
          const guids = extractGuidsFromDsl(dslStr);
          if (cancelled) return;

          if (guids.length === 0) {
            setMemberAssets([]);
            setRules([]);
            return;
          }

          const members = await fetchMemberAssets(baseUrl, token, guids);
          if (cancelled) return;
          // Filter to SQL-like assets (Tables, Views, etc.) that can have DQ rules.
          const sqlMembers = members.filter((m) =>
            ["Table", "View", "MaterialisedView"].includes(m.type_name)
          );
          setMemberAssets(sqlMembers);

          const rs = await fetchDqRulesForMultipleAssets(
            baseUrl,
            token,
            sqlMembers,
            td
          );
          if (cancelled) return;
          setRules(rs);
        } else {
          // Single-table mode.
          setMemberAssets([]);
          if (!a.qualified_name) {
            setRules([]);
            return;
          }
          const rs = await fetchDqRules(baseUrl, token, a.qualified_name, td);
          if (cancelled) return;
          setRules(rs);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load DQ rules");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [baseUrl, token, assetId]);

  return { asset, viewMode, memberAssets, rules, loading, error };
}
