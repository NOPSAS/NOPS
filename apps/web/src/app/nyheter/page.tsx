'use client';

import * as React from 'react';
import {
  Newspaper,
  ExternalLink,
  Loader2,
  Filter,
  RefreshCw,
  Building2,
  TrendingUp,
  Landmark,
  Globe,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Artikkel {
  tittel: string;
  url: string;
  kilde: string;
  kilde_id: string;
  publisert: string;
  beskrivelse: string;
  kategori: string;
}

const KATEGORIER = [
  { id: null, label: 'Alle', icon: <Globe className="h-4 w-4" /> },
  { id: 'bransje', label: 'Bransje', icon: <Building2 className="h-4 w-4" /> },
  { id: 'marked', label: 'Marked', icon: <TrendingUp className="h-4 w-4" /> },
  { id: 'politikk', label: 'Politikk', icon: <Landmark className="h-4 w-4" /> },
  { id: 'generelt', label: 'Generelt', icon: <Newspaper className="h-4 w-4" /> },
];

const KILDE_FARGER: Record<string, string> = {
  estate: 'bg-red-100 text-red-700',
  eiendomswatch: 'bg-blue-100 text-blue-700',
  eiendomnorge: 'bg-green-100 text-green-700',
  norskeiendom: 'bg-indigo-100 text-indigo-700',
  e24: 'bg-orange-100 text-orange-700',
  aftenposten: 'bg-slate-100 text-slate-700',
  abc: 'bg-purple-100 text-purple-700',
  regjeringen: 'bg-amber-100 text-amber-800',
};

function formatDato(publisert: string): string {
  if (!publisert) return '';
  try {
    const d = new Date(publisert);
    if (isNaN(d.getTime())) return publisert;
    const nå = new Date();
    const diff = nå.getTime() - d.getTime();
    const timer = Math.floor(diff / (1000 * 60 * 60));
    if (timer < 1) return 'Akkurat nå';
    if (timer < 24) return `${timer}t siden`;
    const dager = Math.floor(timer / 24);
    if (dager === 1) return 'I går';
    if (dager < 7) return `${dager}d siden`;
    return d.toLocaleDateString('no-NO', { day: 'numeric', month: 'short' });
  } catch {
    return publisert;
  }
}

export default function NyheterPage() {
  const [artikler, setArtikler] = React.useState<Artikkel[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [kategori, setKategori] = React.useState<string | null>(null);
  const [feil, setFeil] = React.useState<string | null>(null);

  React.useEffect(() => {
    document.title = 'Eiendomsnyheter | nops.no';
  }, []);

  const hentNyheter = React.useCallback(async (kat: string | null) => {
    setLoading(true);
    setFeil(null);
    try {
      const params = new URLSearchParams({ antall: '40' });
      if (kat) params.set('kategori', kat);

      const token = typeof window !== 'undefined' ? localStorage.getItem('token') || '' : '';
      const res = await fetch(`/api/v1/nyheter?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setArtikler(data.artikler || []);
    } catch (e: unknown) {
      setFeil(e instanceof Error ? e.message : 'Kunne ikke hente nyheter');
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    hentNyheter(kategori);
  }, [kategori, hentNyheter]);

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <section className="bg-white border-b border-slate-200 py-10 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-100">
              <Newspaper className="h-5 w-5 text-red-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Eiendomsnyheter</h1>
              <p className="text-sm text-slate-500">
                Siste nytt fra Norges ledende eiendomsmedier
              </p>
            </div>
          </div>

          {/* Kategori-filter */}
          <div className="flex flex-wrap gap-2 mt-5">
            {KATEGORIER.map((k) => (
              <button
                key={k.id ?? 'alle'}
                type="button"
                onClick={() => setKategori(k.id)}
                className={cn(
                  'inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-colors',
                  kategori === k.id
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                )}
              >
                {k.icon}
                {k.label}
              </button>
            ))}
            <button
              type="button"
              onClick={() => hentNyheter(kategori)}
              disabled={loading}
              className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors ml-auto"
            >
              <RefreshCw className={cn('h-3.5 w-3.5', loading && 'animate-spin')} />
              Oppdater
            </button>
          </div>
        </div>
      </section>

      <div className="max-w-5xl mx-auto px-4 py-8">
        {loading && artikler.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="h-8 w-8 text-blue-600 animate-spin mb-3" />
            <p className="text-sm text-slate-500">Henter nyheter fra {KATEGORIER.length} kilder…</p>
          </div>
        )}

        {feil && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-center">
            <p className="text-sm text-red-700">{feil}</p>
            <button
              type="button"
              onClick={() => hentNyheter(kategori)}
              className="mt-3 text-sm font-medium text-red-600 hover:underline"
            >
              Prøv igjen
            </button>
          </div>
        )}

        {!loading && artikler.length === 0 && !feil && (
          <div className="text-center py-16">
            <Newspaper className="h-10 w-10 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500">Ingen nyheter funnet for denne kategorien</p>
          </div>
        )}

        {artikler.length > 0 && (
          <div className="space-y-3">
            {artikler.map((a, i) => (
              <a
                key={`${a.kilde_id}-${i}`}
                href={a.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-start gap-4 rounded-xl border border-slate-200 bg-white p-4 hover:border-slate-300 hover:shadow-sm transition-all"
              >
                {/* Kilde-badge */}
                <div className={cn(
                  'flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-xs font-bold',
                  KILDE_FARGER[a.kilde_id] || 'bg-slate-100 text-slate-600'
                )}>
                  {a.kilde.split(' ')[0].substring(0, 3).toUpperCase()}
                </div>

                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-2">
                    {a.tittel}
                  </h3>
                  {a.beskrivelse && (
                    <p className="mt-1 text-xs text-slate-500 line-clamp-2 leading-relaxed">
                      {a.beskrivelse}
                    </p>
                  )}
                  <div className="mt-2 flex items-center gap-3 text-xs text-slate-400">
                    <span className="font-medium">{a.kilde}</span>
                    <span>{formatDato(a.publisert)}</span>
                    <span className={cn(
                      'rounded-full px-2 py-0.5 text-[10px] font-medium',
                      a.kategori === 'bransje' ? 'bg-blue-50 text-blue-600' :
                      a.kategori === 'marked' ? 'bg-green-50 text-green-600' :
                      a.kategori === 'politikk' ? 'bg-amber-50 text-amber-600' :
                      'bg-slate-50 text-slate-500'
                    )}>
                      {a.kategori}
                    </span>
                  </div>
                </div>

                <ExternalLink className="h-4 w-4 text-slate-300 group-hover:text-blue-500 shrink-0 mt-1 transition-colors" />
              </a>
            ))}
          </div>
        )}

        {/* Kilder */}
        <div className="mt-12 rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="text-sm font-bold text-slate-900 mb-4">Våre nyhetskilder</h2>
          <div className="flex flex-wrap gap-2">
            {[
              { navn: 'Estate Nyheter', url: 'https://estatenyheter.no' },
              { navn: 'EiendomsWatch', url: 'https://eiendomswatch.no' },
              { navn: 'Eiendom Norge', url: 'https://eiendomnorge.no' },
              { navn: 'Norsk Eiendom', url: 'https://norskeiendom.org' },
              { navn: 'E24 Eiendom', url: 'https://e24.no/emne/eiendom' },
              { navn: 'Aftenposten Bolig', url: 'https://aftenposten.no' },
              { navn: 'ABC Nyheter', url: 'https://abcnyheter.no/tag/eiendom' },
              { navn: 'Regjeringen', url: 'https://regjeringen.no/no/tema/plan-bygg-og-eiendom' },
            ].map((k) => (
              <a
                key={k.navn}
                href={k.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100 hover:border-slate-300 transition-colors"
              >
                {k.navn}
                <ExternalLink className="h-3 w-3" />
              </a>
            ))}
          </div>
          <p className="mt-4 text-xs text-slate-400">
            Innholdet hentes fra offentlig tilgjengelige RSS-feeds. nops.no er ikke redaksjonelt ansvarlig for innholdet.
          </p>
        </div>
      </div>
    </main>
  );
}
