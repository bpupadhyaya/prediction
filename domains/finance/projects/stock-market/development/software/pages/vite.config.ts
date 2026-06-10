import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  base: '/prediction/stock-prediction/',
  plugins: [svelte()],
  build: {
    outDir: 'dist',
    target: 'es2022',
  },
  server: {
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'require-corp',
    },
  },
  optimizeDeps: {
    exclude: ['@mlc-ai/web-llm', 'onnxruntime-web'],
  },
});
