import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// StaticFiles is mounted at "/" with directory="frontend/static"
// So assets resolve as "/assets/..."
export default defineConfig({
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
})