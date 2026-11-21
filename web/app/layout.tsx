import type { Metadata } from 'next';
import { indexable, siteDescription, siteTitle, siteUrl } from './lib/site';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: siteUrl ?? new URL('http://localhost:3000'),
  title: siteTitle,
  description: siteDescription,
  applicationName: 'Oddmouth',
  ...(siteUrl ? { alternates: { canonical: siteUrl.href } } : {}),
  robots: { index: indexable, follow: indexable },
  icons: { icon: '/icon.svg' },
  openGraph: {
    type: 'website', locale: 'en_US', siteName: 'Oddmouth',
    title: siteTitle, description: siteDescription,
    ...(siteUrl ? { url: siteUrl.href } : {}),
    images: [{ url: '/social-card.png', width: 1200, height: 630, alt: 'Oddmouth text-to-speech demo. Listen to a voice sample and download the audio.' }],
  },
  twitter: {
    card: 'summary_large_image', title: siteTitle, description: siteDescription,
    images: ['/social-card.png'],
  },
};

const structuredData = {
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  name: 'Oddmouth',
  description: siteDescription,
  inLanguage: 'en',
  ...(siteUrl ? { url: siteUrl.href } : {}),
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData).replace(/</g, '\\u003c') }} />
    {children}
  </body></html>;
}
