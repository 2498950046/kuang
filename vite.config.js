import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  // 配置 vue 插件，告诉编译器 `model-viewer` 是原生自定义元素
  plugins: [
    vue({
      template: {
        compilerOptions: {
          isCustomElement: (tag) => tag === 'model-viewer',
        },
      },
    }),
  ],
  define: {
    global: 'globalThis'
  },
  optimizeDeps: {
    exclude: ['neovis.js']
  },
  server: {
    host: '0.0.0.0',
    fs: {
      allow: ['..']
    },
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false
      },
      '/ai': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false
      },
      '/mineral': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false
      },
    }
  },
  build: {
    rollupOptions: {
      external: ['neovis.js'],
      // 新增：处理CommonJS模块
      output: {
        globals: {
          'neovis.js': 'NeoVis'
        }
      }
    }
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})