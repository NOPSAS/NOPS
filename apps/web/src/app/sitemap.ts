import type { MetadataRoute } from 'next';

export default function sitemap(): MetadataRoute.Sitemap {
  const base = 'https://nops.no';
  const now = new Date().toISOString();

  const pages = [
    { path: '/', priority: 1.0, freq: 'daily' },
    { path: '/landing', priority: 0.95, freq: 'weekly' },
    { path: '/property', priority: 0.95, freq: 'daily' },
    { path: '/pricing', priority: 0.8, freq: 'weekly' },
    { path: '/tjenester', priority: 0.9, freq: 'weekly' },
    { path: '/visualisering', priority: 0.85, freq: 'weekly' },
    { path: '/utbygging', priority: 0.8, freq: 'weekly' },
    { path: '/investering', priority: 0.8, freq: 'weekly' },
    { path: '/romplanlegger', priority: 0.7, freq: 'weekly' },
    { path: '/tomter', priority: 0.85, freq: 'weekly' },
    { path: '/finn-analyse', priority: 0.85, freq: 'weekly' },
    { path: '/dokumenter', priority: 0.85, freq: 'weekly' },
    { path: '/juridisk', priority: 0.8, freq: 'weekly' },
    { path: '/pakke', priority: 0.8, freq: 'weekly' },
    { path: '/nyheter', priority: 0.75, freq: 'daily' },
    { path: '/dispensasjon', priority: 0.8, freq: 'weekly' },
    { path: '/ferdigattest', priority: 0.8, freq: 'weekly' },
    { path: '/naboklage', priority: 0.8, freq: 'weekly' },
    { path: '/situasjonsplan', priority: 0.8, freq: 'weekly' },
    { path: '/energi', priority: 0.8, freq: 'weekly' },
    { path: '/personvern', priority: 0.3, freq: 'yearly' },
    { path: '/vilkar', priority: 0.3, freq: 'yearly' },
    { path: '/kontakt', priority: 0.5, freq: 'yearly' },
    { path: '/register', priority: 0.6, freq: 'monthly' },
    { path: '/login', priority: 0.4, freq: 'monthly' },
  ];

  return pages.map(({ path, priority, freq }) => ({
    url: `${base}${path}`,
    lastModified: now,
    changeFrequency: freq as 'daily' | 'weekly' | 'monthly' | 'yearly',
    priority,
  }));
}
