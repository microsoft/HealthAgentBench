import { defineConfig } from 'astro/config';

// Hosted on GitHub Pages with the custom domain medcli.gqin.me, so the site
// lives at the domain root (base '/'). The CNAME file in public/ pins the
// custom domain on every deploy.
export default defineConfig({
  site: 'https://medcli.gqin.me',
  base: '/',
});
