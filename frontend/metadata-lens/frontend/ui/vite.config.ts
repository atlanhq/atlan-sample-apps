import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// StaticFiles is mounted at "/" with directory="frontend/static"
// So assets resolve as "/assets/..."
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
    base: '/',
    build: {
      outDir: '../static',
      emptyOutDir: true,
      assetsDir: 'assets',
      rollupOptions: {
        output: {
          entryFileNames: 'assets/index.js',
          chunkFileNames: 'assets/chunk-[name].js',
          assetFileNames: (assetInfo) => {
            if (assetInfo.name && assetInfo.name.endsWith('.css')) return 'assets/index.css'
            return 'assets/[name][extname]'
          },
        },
      },
    },
    server: {
      // Proxy API calls to the Atlan instance during local development.
      // This avoids CORS issues since the browser sees requests going to localhost.
      proxy: env.VITE_ATLAN_BASE_URL
        ? {
            '/api/meta': {
              target: env.VITE_ATLAN_BASE_URL,
              changeOrigin: true,
              secure: true,
            },
          }
        : undefined,
    },
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: './src/test-setup.ts',
      css: true,
    },
  }
})
