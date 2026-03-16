import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Navbar } from '@/components/layout/navbar';
import { Footer } from '@/components/layout/footer';
import { AuthProvider } from './auth-provider';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: {
    default: 'ByggSjekk | nops.no',
    template: '%s | ByggSjekk – nops.no',
  },
  description:
    'ByggSjekk er Norges ledende digitale eiendomstjeneste for arkitekter og eiendomsaktører. ' +
    'Avdekk avvik, sjekk byggesaker, hent arealplaner og kjør AI-analyse – alt samlet på ett sted.',
  keywords: [
    'byggesak', 'eiendom', 'arealplan', 'avvik', 'dispensasjon',
    'matrikkel', 'kartverket', 'nops', 'arkitekt', 'bolig',
  ],
  robots: {
    index: true,
    follow: true,
  },
  manifest: '/manifest.json',
  openGraph: {
    title: 'ByggSjekk | nops.no',
    description: 'Norges smarteste eiendomsverktøy for arkitekter og eiendomsaktører.',
    siteName: 'nops.no',
    images: [{ url: '/og-image.svg', width: 1200, height: 630 }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'ByggSjekk | nops.no',
    description: 'Norges smarteste eiendomsverktøy for arkitekter og eiendomsaktører.',
    images: ['/og-image.svg'],
  },
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
