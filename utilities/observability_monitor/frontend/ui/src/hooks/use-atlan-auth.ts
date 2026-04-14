import { useState, useEffect, useCallback, useRef } from "react";
import type { AtlanAuthContext, AuthState, AtlanMessage } from "../types/atlan";

const DEV_MODE = import.meta.env.VITE_DEV_MODE === "true";
const DEV_TOKEN = import.meta.env.VITE_ATLAN_API_TOKEN || "";
const DEV_ASSET_GUID = import.meta.env.VITE_ATLAN_ASSET_GUID || "";
// In dev, leave baseUrl empty so requests hit Vite's /api/meta proxy.
const DEV_BASE_URL = "";

interface UseAtlanAuthReturn {
  authState: AuthState;
  token: string;
  baseUrl: string;
  assetId: string;
  userEmail: string;
  error: string | null;
}

export function useAtlanAuth(): UseAtlanAuthReturn {
  const [authState, setAuthState] = useState<AuthState>(
    DEV_MODE ? "authenticated" : "connecting"
  );
  const [token, setToken] = useState(DEV_MODE ? DEV_TOKEN : "");
  const [baseUrl, setBaseUrl] = useState(DEV_MODE ? DEV_BASE_URL : "");
  const [assetId, setAssetId] = useState(DEV_MODE ? DEV_ASSET_GUID : "");
  const [userEmail, setUserEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const refreshTimer = useRef<ReturnType<typeof setTimeout>>();

  const scheduleTokenRefresh = useCallback((expiresAt: number) => {
    if (refreshTimer.current) clearTimeout(refreshTimer.current);
    const refreshIn = Math.max(0, expiresAt - Date.now() - 5 * 60 * 1000);
    refreshTimer.current = setTimeout(() => {
      window.parent.postMessage({ type: "IFRAME_TOKEN_REQUEST" }, "*");
    }, refreshIn);
  }, []);

  useEffect(() => {
    if (DEV_MODE) return;

    const handleMessage = (event: MessageEvent<AtlanMessage>) => {
      const { type, payload } = event.data || {};
      switch (type) {
        case "ATLAN_HANDSHAKE":
          window.parent.postMessage({ type: "IFRAME_READY" }, event.origin);
          break;
        case "ATLAN_AUTH_CONTEXT": {
          const ctx = payload as AtlanAuthContext;
          setToken(ctx.token || DEV_TOKEN);
          setBaseUrl(ctx.token ? event.origin : "");
          setAssetId(ctx.page?.params?.id || DEV_ASSET_GUID);
          setUserEmail(ctx.user?.email || "");
          setAuthState("authenticated");
          setError(null);
          if (ctx.token) scheduleTokenRefresh(ctx.expiresAt);
          break;
        }
        case "ATLAN_LOGOUT":
          setToken("");
          setAuthState("logged_out");
          if (refreshTimer.current) clearTimeout(refreshTimer.current);
          break;
      }
    };

    window.addEventListener("message", handleMessage);

    const timeout = setTimeout(() => {
      if (authState === "connecting") {
        setError("Timed out waiting for Atlan authentication");
        setAuthState("error");
      }
    }, 10000);

    return () => {
      window.removeEventListener("message", handleMessage);
      clearTimeout(timeout);
      if (refreshTimer.current) clearTimeout(refreshTimer.current);
    };
  }, [authState, scheduleTokenRefresh]);

  return { authState, token, baseUrl, assetId, userEmail, error };
}
