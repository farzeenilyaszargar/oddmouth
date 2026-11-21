import type { MetadataRoute } from 'next';
import { indexable, siteUrl } from './lib/site';

export const dynamic = 'force-static';
export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: '*', ...(indexable ? { allow: '/' } : { disallow: '/' }) },
    ...(indexable && siteUrl ? { sitemap: new URL('/sitemap.xml', siteUrl).href } : {}),
  };
}
