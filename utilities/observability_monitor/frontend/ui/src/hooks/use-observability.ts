import { useEffect, useState } from "react";
import type { AssetDetails, Execution } from "../types/atlan";
import {
  fetchAsset,
  fetchObservabilityAssets,
  fetchObsTypedef,
} from "../services/obs-api";

interface UseObservabilityReturn {
  asset: AssetDetails | null;
  executions: Execution[];
  loading: boolean;
  error: string | null;
}

export function useObservability(
  baseUrl: string,
  token: string,
  assetId: string
): UseObservabilityReturn {
  const [asset, setAsset] = useState<AssetDetails | null>(null);
  const [executions, setExecutions] = useState<Execution[]>([]);
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
          fetchObsTypedef(baseUrl, token),
        ]);
        if (cancelled) return;
        setAsset(a);
        if (!a?.qualified_name) {
          setExecutions([]);
          return;
        }
        const assets = await fetchObservabilityAssets(
          baseUrl,
          token,
          a.qualified_name,
          td
        );
        if (cancelled) return;
        // Flatten all executions from all Observability assets.
        const allExecs = assets.flatMap((oa) => oa.executions);
        allExecs.sort((a, b) => b.executionDate.localeCompare(a.executionDate));
        setExecutions(allExecs);
      } catch (e) {
        if (!cancelled) {
          setError(
            e instanceof Error ? e.message : "Failed to load observability data"
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [baseUrl, token, assetId]);

  return { asset, executions, loading, error };
}
