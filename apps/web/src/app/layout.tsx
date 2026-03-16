import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Navbar } from '@/components/layout/navbar';
import { Footer } from '@/components/layout/footer';
import { AuthProvider } from './auth-provider';
import { StructuredData } from '@/components/structured-data';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  metadataBase: new URL('https://nops.no'),
  title: {
    default: 'nops.no – Sjekk eiendommen din gratis | Eiendomsdata, avvik og AI-analyse',
    template: '%s | nops.no',
  },
  description:
    'Norges ledende plattform for digitale eiendomstjenester. Avviksdeteksjon, byggesøknad, 2D til 3D, energirådgivning, dispensasjon, ferdigattest og 20+ tjenester. Søk opp adressen gratis.',
  keywords: [
    'eiendomssjekk', 'avviksdeteksjon', 'byggesøknad', 'nops', 'nops.no',
    'eiendom', 'arealplan', 'reguleringsplan', 'dispensasjon', 'ferdigattest',
    'matrikkel', 'kartverket', 'arkitekt', 'bolig', 'tilbygg', 'påbygg',
    'bruksendring', 'situasjonsplan', 'nabovarsel', 'energimerke', 'energirådgivning',
    '2D til 3D', '3D-modell', 'visualisering', 'render', 'byggesak',
    'DOK-analyse', 'tomtedeling', 'mulighetsstudie', 'boligpris', 'verdiestimering',
    'Finn.no analyse', 'byggetegninger', 'godkjente tegninger',
  ],
  authors: [{ name: 'Konsepthus AS', url: 'https://nops.no' }],
  creator: 'Konsepthus AS',
  publisher: 'nops.no',
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    type: 'website',
    locale: 'nb_NO',
    title: 'nops.no – Sjekk eiendommen din gratis',
    description: 'Avviksdeteksjon, byggesøknad, 2D til 3D, energirådgivning og 20+ tjenester. Norges ledende eiendomsplattform.',
    siteName: 'nops.no',
    url: 'https://nops.no',
    images: [{ url: '/og-image.svg', width: 1200, height: 630, alt: 'nops.no – Norges smarteste eiendomsverktøy' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'nops.no – Sjekk eiendommen din gratis',
    description: 'Avviksdeteksjon, byggesøknad, 2D til 3D og 20+ tjenester for eiendom.',
    images: ['/og-image.svg'],
    creator: '@nopsno',
  },
  manifest: '/manifest.json',
  alternates: {
    canonical: 'https://nops.no',
  },
  verification: {
    google: 'PLACEHOLDER_GOOGLE_VERIFICATION',
  },
  category: 'technology',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="nb" className={inter.variable} suppressHydrationWarning>
      <body className="min-h-screen bg-background antialiased">
        <AuthProvider>
          <StructuredData />
          <Navbar />
          <main id="main-content" className="flex-1">
            {children}
          </main>
          <Footer />
        </AuthProvider>
      </body>
    </html>
  );
}
