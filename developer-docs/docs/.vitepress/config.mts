import { existsSync, readFileSync } from 'node:fs';

import { defineConfig } from 'vitepress';

interface ReferenceItem {
  readonly link: string;
  readonly text: string;
}

function isReferenceItem(value: unknown): value is ReferenceItem {
  if (value === null || typeof value !== 'object') return false;
  if (!('link' in value) || !('text' in value)) return false;
  return typeof value.link === 'string' && typeof value.text === 'string';
}

function loadReferenceItems(): ReferenceItem[] {
  const manifestUrl = new URL(
    '../reference/v1/generated/manifest.json',
    import.meta.url,
  );
  if (!existsSync(manifestUrl)) return [];
  const parsed: unknown = JSON.parse(readFileSync(manifestUrl, 'utf8'));
  if (parsed === null || typeof parsed !== 'object' || !('items' in parsed)) {
    throw new Error('Generated reference manifest has no items');
  }
  if (!Array.isArray(parsed.items) || !parsed.items.every(isReferenceItem)) {
    throw new Error('Generated reference manifest contains invalid items');
  }
  return parsed.items;
}

const referenceItems = loadReferenceItems();

export default defineConfig({
  lang: 'en-US',
  title: 'Kokoro Developer',
  description: 'Build with the Kokoro Product API.',
  cleanUrls: true,
  lastUpdated: false,
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
        items: [
          { text: 'Kokoro API v1', link: '/reference/v1/' },
          ...referenceItems,
        ],
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
