import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  base: '/prediction/stock-prediction/',
  plugins: [svelte()],
  build: {
    outDir: 'dist',
    target: 'es2022',
  },
});
