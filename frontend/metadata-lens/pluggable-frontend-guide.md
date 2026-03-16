# Building Pluggable Frontend Apps for Atlan

A practical guide for developers building React (or other framework) frontend apps that render inside Atlan as iframe tabs. This covers deployment gotchas, SDK quirks, and infrastructure considerations not found in the standard SDK documentation.

---

## 1. SDK Gap: Asset Context from postMessage

The `@atlanhq/atlan-auth` SDK's `onReady` callback provides an `AuthContext` with `token`, `user`, `tenant`, and `mode`. It does **not** expose the `page` field from the parent's `ATLAN_AUTH_CONTEXT` postMessage — even though the parent sends it.

The `page` field contains the current route and params (e.g., the asset GUID when viewing an asset). The SDK parses the postMessage, extracts `token`, `user`, and `tenant`, and discards the rest.

**Workaround:** Register your own `message` event listener _before_ calling `atlan.init()` to capture the `page` data directly:

```typescript
const assetIdRef = useRef<string | null>(null)

useEffect(() => {
  // Capture page context that the SDK discards
  const handleMessage = (event: MessageEvent) => {
    const data = event.data ?? {}
    if (data.type === 'ATLAN_AUTH_CONTEXT') {
      const page = data.payload?.page ?? data.page
      assetIdRef.current = page?.params?.id ?? null
    }
  }
  window.addEventListener('message', handleMessage)

  const atlan = new AtlanAuth({
    origin,
    onReady: () => {
      // assetIdRef.current is populated by the time onReady fires
      const assetId = assetIdRef.current ?? getAssetIdFromUrl()
      // ...
    },
  })
  atlan.init()

  return () => window.removeEventListener('message', handleMessage)
}, [])
```

The postMessage listener fires synchronously before the SDK processes the same message and calls `onReady`, so `assetIdRef.current` is guaranteed to be set by the time you read it.

For standalone mode (Keycloak PKCE), there is no postMessage — use a URL query parameter (`?assetId=<GUID>`) as fallback.

---

## 2. API Calls: Same-Origin vs Cross-Origin Hosting

Where your app is hosted determines how API calls to the Atlan backend work.

### Same-origin (hosted on Atlan infrastructure)

When the app is served from the same domain as the Atlan tenant (e.g., `partner-apps.atlan.com` with Atlan's routing in front), the SDK's `api.get()` makes requests to the tenant origin directly. The browser treats these as same-origin requests — no CORS, no preflight. This is the simplest path.

```
iframe on: https://tenant.atlan.com/external-app/
API call:  https://tenant.atlan.com/api/meta/entity/guid/...
```

### Cross-origin (hosted on your own infrastructure)

When the app is on a separate domain (e.g., `your-app.company.com`), the SDK's `api.get()` still targets the tenant origin (`VITE_ATLAN_ORIGIN`). But now the browser sees a cross-origin request and sends a CORS preflight (`OPTIONS`). The Atlan API does not return `Access-Control-Allow-Origin` headers for arbitrary domains, so the request fails.

```
iframe on: https://your-app.company.com/
API call:  https://tenant.atlan.com/api/meta/...  --> CORS blocked
```

**Solution: Reverse proxy on your app server.** Route API calls through your own server, which proxies them to the Atlan tenant. The browser only talks to your origin — no CORS.

```
Browser  -->  your-app.company.com/api/meta/...  -->  tenant.atlan.com/api/meta/...
              (same-origin, no CORS)                  (server-to-server, no CORS)
```

When using a proxy, build the app **without** `VITE_ATLAN_ORIGIN` for the API base URL, or override the API calls to use a relative path instead of the SDK's `api.get()`. Keep `VITE_ATLAN_ORIGIN` set for the auth handshake — it's needed for postMessage origin validation.

A minimal FastAPI proxy example:

```python
@app.api_route("/api/meta/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(request: Request, path: str):
    url = f"{ATLAN_BASE_URL}/api/meta/{path}"
    if request.url.query:
        url += f"?{request.url.query}"
    headers = {}
    if "authorization" in request.headers:
        headers["Authorization"] = request.headers["authorization"]
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(request.method, url, headers=headers)
    return StreamingResponse(iter([resp.content]), status_code=resp.status_code,
        headers={"content-type": resp.headers.get("content-type", "application/json")})
```

The proxy must forward the `Authorization` header from the browser request. The SDK sets this header automatically via `api.get()`, and your proxy passes it through to the Atlan API.

---

## 3. Iframe URL: Trailing Slash Matters

When the Atlan frontend embeds your app, the iframe `src` URL must end with a **trailing slash**.

Without it, relative asset paths in your HTML resolve against the wrong directory:

| iframe src | `./assets/index.js` resolves to |
|---|---|
| `https://host.com/my-app/` | `https://host.com/my-app/assets/index.js` |
| `https://host.com/my-app` | `https://host.com/assets/index.js` |

The second case breaks because `my-app` is treated as a filename, not a directory. Ensure whoever configures the tab URL in the Atlan UI includes the trailing slash.

---

## 4. Vite Base Path Configuration

Set `base: './'` (relative) in `vite.config.ts` — not `base: '/'` (absolute):

```typescript
export default defineConfig({
  base: './',
  // ...
})
```

With `base: '/'`, the built HTML emits `src="/assets/index.js"` which resolves against the domain root. If the app is served under a subpath (e.g., `/metadata_lens/`), the browser requests `/assets/index.js` instead of `/metadata_lens/assets/index.js`.

With `base: './'`, asset paths are relative to the HTML document's URL, which works regardless of the deployment path.

### Template HTML

If your app framework serves a separate `templates/index.html` (distinct from the Vite-built `static/index.html`), ensure the template also uses relative paths:

```html
<!-- Correct -->
<link rel="stylesheet" href="./assets/index.css" />
<script type="module" src="./assets/index.js"></script>

<!-- Wrong — will break under subpaths -->
<link rel="stylesheet" href="/assets/index.css" />
<script type="module" src="/assets/index.js"></script>
```

---

## 5. Ingress Configuration (Kubernetes)

If using Kong ingress with `konghq.com/strip-path: "true"`:

- The ingress strips the path prefix before forwarding to your service
- Example: `/metadata_lens/assets/index.js` arrives at your server as `/assets/index.js`
- This works well **with relative asset paths** and a **trailing slash** on the iframe URL

Without strip-path, the full path reaches your server, but the server doesn't know about the prefix — requests 404 unless your server is configured to serve under that path.

**Recommended setup:** strip-path enabled + relative base (`./`) + trailing slash on iframe URL.

---

## 6. Cloudflare Considerations

If your app's domain routes through Cloudflare (DNS record set to "Proxied" / orange cloud):

### Challenge script injection

Cloudflare injects a bot-protection script into HTML responses. This script creates a hidden iframe and runs challenge code. In testing, this has been observed to **interfere with postMessage communication** between the parent Atlan page and your app iframe, causing the auth handshake to silently fail.

**Fix:** Set the DNS record to **DNS only** (gray cloud) for your app's domain. This removes Cloudflare from the request path entirely.

### Aggressive caching

Cloudflare caches static assets aggressively. When you redeploy, the old JS/CSS bundles may continue to be served. This is especially problematic because Vite's build output uses fixed filenames (`assets/index.js`) without content hashes.

Symptoms: you deploy new code, but the app behaves identically to the old version. Curl from the server returns the new code, but curl through Cloudflare returns the old code.

**Fixes:**
- Use DNS-only mode (no Cloudflare caching at all)
- Or purge the cache after each deploy (Dashboard > Caching > Purge Cache)
- Or add content hashes to filenames by removing the fixed `entryFileNames` in your Vite rollup config

### Port restrictions

Cloudflare only proxies traffic on standard ports. If your load balancer listens on a non-standard port (e.g., 8443), Cloudflare will return **HTTP 520** ("web server returned an unknown error"). Use port 443 for HTTPS when Cloudflare is in the path.

---

## 7. Response Headers for Iframe Embedding

Your app server must **not** send headers that block iframe embedding:

| Header | Requirement |
|---|---|
| `X-Frame-Options` | Must be `ALLOW-FROM https://tenant.atlan.com` or absent entirely. `SAMEORIGIN` or `DENY` will block the iframe. |
| `Content-Security-Policy` | If present, `frame-ancestors` must include the Atlan tenant origin: `frame-ancestors 'self' https://*.atlan.com` |
| `Content-Type` | Static assets must have correct MIME types. `text/html` for JS files causes silent module parse failures — the browser cannot execute HTML as JavaScript. |
| `Cache-Control` | Consider `no-cache` during development to avoid stale bundles. |

If using Cloudflare in proxied mode, Cloudflare may add `X-Frame-Options: SAMEORIGIN` automatically. This will block the iframe since the parent (Atlan tenant) and child (your domain) are different origins. Another reason to use DNS-only mode for cross-origin hosting.

---

## 8. GitHub Packages Authentication for `@atlanhq/atlan-auth`

The SDK is published on GitHub Packages, not the public npm registry.

### Local development

Create `.npmrc` in your project root:

```
@atlanhq:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=YOUR_GITHUB_PAT
```

The PAT needs `read:packages` scope. Do **not** commit the auth token line — add it to `.gitignore` or use an environment variable.

### Docker builds

Use BuildKit secrets to avoid baking the token into image layers:

```dockerfile
COPY package.json package-lock.json .npmrc ./
RUN --mount=type=secret,id=npm_token \
    NPM_TOKEN=$(cat /run/secrets/npm_token) \
    && echo "//npm.pkg.github.com/:_authToken=${NPM_TOKEN}" >> .npmrc \
    && npm ci \
    && sed -i '/_authToken/d' .npmrc
```

Pass the secret during build:

```bash
docker build --secret id=npm_token,env=GITHUB_TOKEN .
```

In CI (GitHub Actions):

```yaml
- uses: docker/build-push-action@v5
  with:
    secrets: |
      npm_token=${{ secrets.GITHUB_TOKEN }}
```

### Committable `.npmrc`

Only the registry line goes into version control:

```
@atlanhq:registry=https://npm.pkg.github.com
```

---

## 9. `keycloak-js` Peer Dependency

`@atlanhq/atlan-auth` requires `keycloak-js@^25.0.6` as a peer dependency. Install it alongside the SDK:

```bash
npm install @atlanhq/atlan-auth keycloak-js
```

Keycloak is used for standalone mode (PKCE flow). Even if your app only runs in embedded mode, the import is required at build time.

---

## 10. Hosting Architecture Decision Matrix

| Scenario | API calls | Auth handshake | CORS proxy needed | Cloudflare safe |
|---|---|---|---|---|
| Same-origin (Atlan infra) | Relative paths, same origin | postMessage | No | N/A |
| Cross-origin (your infra, Atlan-routable) | SDK `api.get()` to tenant | postMessage | No (if Atlan allows) | Must be DNS-only |
| Cross-origin (your infra, isolated) | Proxy through your server | postMessage | Yes | Must be DNS-only |
| Standalone (no iframe) | SDK `api.get()` to tenant | Keycloak PKCE | No (direct browser) | N/A |

---

## 11. Quick Debugging Checklist

If the iframe shows "Something went wrong" or hangs on "Connecting":

1. **Is the iframe loading at all?** Check Network tab for the HTML response. If 4xx/5xx, it's a routing/server issue.
2. **Are assets loading?** Check that `index.js` and `index.css` return correct content types (not HTML).
3. **Is Cloudflare injecting scripts?** View the HTML source — look for `challenge-platform` scripts. Switch to DNS-only.
4. **Is the postMessage handshake happening?** In the browser console (top frame): `window.addEventListener('message', e => console.log(e.origin, e.data))` — reload and watch for `ATLAN_HANDSHAKE` and `IFRAME_READY`.
5. **Is the iframe URL missing a trailing slash?** Check the iframe `src` attribute in Elements tab.
6. **Is `X-Frame-Options` blocking embedding?** Check the iframe's HTTP response headers in Network tab.
7. **Are API calls going to the wrong origin?** Check Network tab for the `/api/meta/` request URL. If it hits the iframe's domain instead of the tenant, you need a proxy or the SDK's origin config is wrong.
8. **Is the asset cached?** Curl the JS file URL and check if it contains your latest code. If not, purge cache or rename the file.
