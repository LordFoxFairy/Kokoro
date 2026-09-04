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
      {
        text: 'Core concepts',
        items: [
          { text: 'Projects', link: '/concepts/projects' },
          {
            text: 'Conversations and messages',
            link: '/concepts/conversations-messages',
          },
          { text: 'Asynchronous runs', link: '/concepts/asynchronous-runs' },
          { text: 'Lifecycle and status', link: '/concepts/lifecycle' },
          { text: 'AG-UI stream and replay', link: '/concepts/ag-ui' },
          { text: 'Files and artifacts', link: '/concepts/files-artifacts' },
          { text: 'Scheduled tasks', link: '/concepts/scheduled-tasks' },
        ],
      },
      {
        text: 'Guides',
        items: [
          { text: 'Create a run', link: '/guides/create-run' },
          { text: 'Follow up', link: '/guides/follow-up' },
          { text: 'Cancel a run', link: '/guides/cancel-run' },
          { text: 'Resume a run', link: '/guides/resume-run' },
          {
            text: 'Replay after disconnect',
            link: '/guides/replay-after-disconnect',
          },
          {
            text: 'Idempotent commands',
            link: '/guides/idempotent-commands',
          },
          { text: 'Cursor pagination', link: '/guides/cursor-pagination' },
          { text: 'Upload lifecycle', link: '/guides/upload-lifecycle' },
          { text: 'Webhooks', link: '/guides/webhooks' },
        ],
      },
      {
        text: 'Platform behavior',
        items: [
          { text: 'Responses and errors', link: '/platform/responses-errors' },
          { text: 'Request IDs', link: '/platform/request-ids' },
          { text: 'Idempotency', link: '/platform/idempotency' },
          {
            text: 'Rate limits and retries',
            link: '/platform/rate-limits-retries',
          },
          { text: 'UTC and RFC 3339', link: '/platform/time' },
          { text: 'Versioning', link: '/platform/versioning' },
          { text: 'Security', link: '/platform/security' },
        ],
      },
      {
        text: 'Release information',
        items: [
          { text: 'Changelog', link: '/changelog' },
          { text: 'Contract provenance', link: '/provenance' },
        ],
      },
    ],
    socialLinks: [
      { icon: 'github', link: 'https://github.com/LordFoxFairy/Kokoro' },
    ],
    footer: {
      message: 'Canonical contract owned by kokoro-bff.',
      copyright: 'Kokoro Developer API',
    },
    outline: { label: 'On this page', level: [2, 3] },
  },
});
