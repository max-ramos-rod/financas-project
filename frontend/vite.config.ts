import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    host: true,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {

            if (id.includes('apexcharts') || id.includes('vue3-apexcharts')) {
              return 'apexcharts'
            }

            if (id.includes('vue-router')) return 'router'
            if (id.includes('pinia')) return 'pinia'
            if (id.includes('vue')) return 'vue'

            return 'vendor'
          }
        }
      }
    }
  }
})