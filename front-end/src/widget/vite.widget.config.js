import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import cssInjectedByJsPlugin from 'vite-plugin-css-injected-by-js';

export default defineConfig({
  plugins: [
    react(),
    cssInjectedByJsPlugin(), // This puts the CSS *inside* the JS file
  ],
  define: {
    'process.env.NODE_ENV': JSON.stringify('production')
  },
  build: {
    emptyOutDir: false, // Don't delete the dashboard build
    outDir: 'dist-widget', // Save to a separate folder
    lib: {
      entry: 'src/widget/main.jsx',
      name: 'eLankaChatAIWidget',
      fileName: 'widget',
      formats: ['iife'] // "Immediately Invoked Function Expression" (Self-contained script)
    },
    rollupOptions: {
      // Don't externalize React. Bundle it INSIDE the widget 
      // so it works on websites that don't have React.
      external: [], 
    }
  }
});