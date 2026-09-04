import { defineConfig } from 'vitepress';

export default defineConfig({
  lang: 'en-US',
  title: 'Kokoro Developer',
  description: 'Build with the Kokoro Product API.',
  cleanUrls: true,
  lastUpdated: false,
  srcExclude: ['reference/v1/generated/**'],
  themeConfig: {
    nav: [
      { text: 'Docs', link: '/introduction' },
      { text: 'API reference', link: '/reference/v1/' },
      { text: 'Changelog', link: '/changelog' },
    ],
    search: { provider: 'local' },
    sidebar: [
      {
        text: 'Start',
        items: [
          { text: 'Introduction', link: '/introduction' },
          { text: 'Quickstart', link: '/quickstart' },
          { text: 'Authentication', link: '/authentication' },
        ],
      },
      {
        text: 'API reference',
        items: [{ text: 'Kokoro API v1', link: '/reference/v1/' }],
      },
      { text: 'Changelog', link: '/changelog' },
    ],
    socialLinks: [
      { icon: 'github', link: 'https://github.com/LordFoxFairy/Kokoro' },
    ],
    footer: {
      message: 'Canonical contract owned by kokoro-bff.',
      copyright: 'Kokoro Developer API',
    },
  },
});
