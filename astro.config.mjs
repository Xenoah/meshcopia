import { defineConfig } from 'astro/config';
export default defineConfig({
  site: process.env.PUBLIC_SITE || 'https://xenoah.github.io',
  base: process.env.PUBLIC_BASE_PATH ?? '/meshcopia',
  output: 'static',
  trailingSlash: 'always',
});
