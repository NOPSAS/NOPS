'use client';

import Link from 'next/link';
import { Building2 } from 'lucide-react';

const tjenester = [
  { navn: 'Eiendomssok', href: '/property' },
  { navn: 'Visualisering', href: '/visualisering' },
  { navn: 'Utbygging', href: '/utbygging' },
  { navn: 'Investering', href: '/investering' },
  { navn: 'Romplanlegger', href: '/romplanlegger' },
  { navn: 'Komplett pakke', href: '/pakke' },
  { navn: 'Alle tjenester', href: '/tjenester' },
];

const okosystem = [
  { navn: 'nops.no', href: 'https://www.nops.no' },
  { navn: 'situasjonsplan.no', href: 'https://www.situasjonsplan.no' },
  { navn: 'dispensasjonen.no', href: 'https://www.dispensasjonen.no' },
  { navn: 'naboklagen.no', href: 'https://www.naboklagen.no' },
  { navn: 'ferdigattesten.no', href: 'https://www.ferdigattesten.no' },
  { navn: 'minni.no', href: 'https://www.minni.no' },
];

const omOss = [
  { navn: 'Priser', href: '/pricing' },
  { navn: 'Nyheter', href: '/nyheter' },
  { navn: 'Kontakt', href: '/kontakt' },
  { navn: 'Personvern', href: '/personvern' },
  { navn: 'Vilkar', href: '/vilkar' },
];

export function Footer() {
  return (
    <footer className="bg-slate-900 text-white">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-10 sm:grid-cols-2 lg:grid-cols-4">
          {/* Kolonne 1 - Brand */}
          <div>
            <Link href="/" className="inline-flex items-center gap-2 mb-4">
              <Building2 className="h-6 w-6 text-blue-400" />
              <span className="text-lg font-bold">ByggSjekk</span>
            </Link>
            <p className="text-sm text-slate-400 leading-relaxed">
              Norges smarteste eiendomsverktoy
            </p>
            <p className="mt-2 text-sm text-slate-500">
              En del av nops.no-okosystemet
            </p>
          </div>

          {/* Kolonne 2 - Tjenester */}
          <div>
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
              Tjenester
            </h3>
            <ul className="space-y-2.5">
              {tjenester.map((t) => (
                <li key={t.href}>
                  <Link
                    href={t.href}
                    className="text-sm text-slate-400 hover:text-white transition-colors"
                  >
                    {t.navn}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Kolonne 3 - Okosystem */}
          <div>
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
              Okosystem
            </h3>
            <ul className="space-y-2.5">
              {okosystem.map((o) => (
                <li key={o.href}>
                  <a
                    href={o.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-slate-400 hover:text-white transition-colors"
                  >
                    {o.navn}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Kolonne 4 - Om oss */}
          <div>
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
              Om oss
            </h3>
            <ul className="space-y-2.5">
              {omOss.map((item) => (
                <li key={item.navn}>
                  <Link
                    href={item.href}
                    className="text-sm text-slate-400 hover:text-white transition-colors"
                  >
                    {item.navn}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bunnlinje */}
        <div className="mt-12 border-t border-slate-800 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-slate-500">
            &copy; 2026 Konsepthus AS / nops.no. Alle rettigheter reservert.
          </p>
          <p className="text-sm text-slate-500">
            Laget i Norge 🇳🇴
          </p>
        </div>
      </div>
    </footer>
  );
}
