import { useEffect, useState } from "react";
import type { AssetDetails, DqRule } from "../types/atlan";
import { fetchAsset, fetchDqRules, fetchDqTypedef } from "../services/dq-api";

interface UseDqRulesReturn {
  asset: AssetDetails | null;
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
        if (!a?.qualified_name) {
          setRules([]);
          return;
        }
        const rs = await fetchDqRules(baseUrl, token, a.qualified_name, td);
        if (cancelled) return;
        setRules(rs);
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

  return { asset, rules, loading, error };
}
