/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_DEV_MODE?: string;
  readonly VITE_ATLAN_API_TOKEN?: string;
  readonly VITE_ATLAN_ASSET_GUID?: string;
  readonly VITE_ATLAN_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
