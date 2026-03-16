'use client';

import * as React from 'react';
import { X } from 'lucide-react';

const STORAGE_KEY = 'byggsjekk_onboarding_dismissed';

const steg = [
  {
    ikon: '🔍',
    tittel: 'Søk opp en eiendom',
    tekst: 'Skriv inn adresse og få full eiendomsprofil på sekunder.',
  },
  {
    ikon: '🤖',
    tittel: 'Kjør AI-analyse',
    tekst: 'Få risikovurdering med lovhenvisninger fra PBL og TEK17.',
  },
  {
    ikon: '📄',
    tittel: 'Last ned rapport',
    tekst: 'Eksporter komplett PDF-rapport til klient eller arkiv.',
  },
];

export function OnboardingBanner() {
  const [synlig, setSynlig] = React.useState(false);

  React.useEffect(() => {
    const dismissed = localStorage.getItem(STORAGE_KEY);
    if (!dismissed) {
      setSynlig(true);
    }
  }, []);

  const handleLukk = () => {
    localStorage.setItem(STORAGE_KEY, 'true');
    setSynlig(false);
  };

  if (!synlig) return null;

  return (
    <div className="mb-6 rounded-xl bg-gradient-to-r from-blue-600 to-blue-700 p-5 text-white shadow-md">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-100 mb-1">
            Kom i gang
          </p>
          <h2 className="text-lg font-bold mb-4">
            Slik bruker du ByggSjekk
          </h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {steg.map((s, i) => (
              <div
                key={i}
                className="flex items-start gap-3 rounded-lg bg-white/10 px-4 py-3 backdrop-blur-sm"
              >
                <span className="text-xl leading-none mt-0.5">{s.ikon}</span>
                <div>
                  <p className="text-sm font-semibold">{s.tittel}</p>
                  <p className="mt-0.5 text-xs text-blue-100">{s.tekst}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        <button
          type="button"
          onClick={handleLukk}
          aria-label="Lukk onboarding"
          className="shrink-0 rounded-lg p-1.5 text-white/70 hover:bg-white/20 hover:text-white transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
