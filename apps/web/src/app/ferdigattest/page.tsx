'use client';

import * as React from 'react';
import {
  Award,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowRight,
  Info,
  FileText,
  Mail,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Byggesak {
  saksnummer: string;
  sakstype: string;
  tittel: string;
  status: string;
  vedtaksdato: string | null;
  innsendtdato: string | null;
  tiltakstype: string;
}

interface FerdigattestResultat {
  eiendom: { knr: string; gnr: number; bnr: number; info: string };
  har_ferdigattest: boolean;
  byggesaker: Byggesak[];
  mangler_ferdigattest: Byggesak[];
  anbefaling: string;
  estimert_kostnad: string;
  neste_steg: string[];
}

export default function FerdigattestPage() {
  const [knr, setKnr] = React.useState('');
  const [gnr, setGnr] = React.useState('');
  const [bnr, setBnr] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [resultat, setResultat] = React.useState<FerdigattestResultat | null>(null);
  const [feil, setFeil] = React.useState<string | null>(null);

  React.useEffect(() => {
    document.title = 'Ferdigattest-sjekk | nops.no';
  }, []);

  async function sjekk() {
    if (!knr || !gnr || !bnr) { setFeil('Fyll inn kommunenr, gnr og bnr'); return; }

    setLoading(true);
    setFeil(null);
    setResultat(null);

    try {
      const params = new URLSearchParams({ knr, gnr, bnr });
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') || '' : '';
      const headers: Record<string, string> = {};
      if (token) headers.Authorization = `Bearer ${token}`;

      const res = await fetch(`/api/v1/dispensasjon/ferdigattest-sjekk?${params}`, {
        method: 'POST',
        headers,
      });
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        throw new Error(e.detail || `HTTP ${res.status}`);
      }
      setResultat(await res.json());
    } catch (e: unknown) {
      setFeil(e instanceof Error ? e.message : 'Noe gikk galt');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <section className="bg-gradient-to-br from-green-600 to-emerald-500 text-white py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 mb-4 rounded-full bg-white/10 px-4 py-1.5 text-sm font-medium text-green-100">
            <Award className="h-4 w-4" /> nops.no / Ferdigattest
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mb-4">
            Ferdigattest-sjekk
          </h1>
          <p className="text-lg text-green-100 max-w-2xl">
            Sjekk om eiendommen har ferdigattest og hva som trengs
          </p>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-4 py-10 space-y-6">
        {/* Skjema */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <label className="block text-sm font-semibold text-slate-700">Eiendom</label>
            <span className="inline-flex items-center rounded-full bg-green-100 text-green-700 px-2.5 py-0.5 text-xs font-bold">
              GRATIS
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            <input type="text" placeholder="Kommunenr. *" value={knr} onChange={(e) => setKnr(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500" />
            <input type="number" placeholder="Gnr. *" value={gnr} onChange={(e) => setGnr(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500" />
            <input type="number" placeholder="Bnr. *" value={bnr} onChange={(e) => setBnr(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500" />
          </div>
        </div>

        {/* Feil */}
        {feil && (
          <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <AlertTriangle className="h-4 w-4 shrink-0" /> {feil}
          </div>
        )}

        {/* Send-knapp */}
        <button type="button" onClick={sjekk} disabled={loading}
          className="inline-flex items-center gap-2 rounded-xl bg-green-600 px-6 py-3 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60 transition-colors">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Award className="h-4 w-4" />}
          Sjekk ferdigattest
        </button>

        {/* Resultat */}
        {resultat && (
          <div className="space-y-5">
            {/* Status-kort */}
            <div className={cn(
              'rounded-2xl border-2 p-8 text-center',
              resultat.har_ferdigattest
                ? 'border-green-300 bg-green-50'
                : 'border-red-300 bg-red-50'
            )}>
              {resultat.har_ferdigattest ? (
                <>
                  <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto mb-4" />
                  <h2 className="text-2xl font-bold text-green-800 mb-2">Ferdigattest funnet</h2>
                  <p className="text-sm text-green-700">Eiendommen har ferdigattest for registrerte byggesaker.</p>
                </>
              ) : (
                <>
                  <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
                  <h2 className="text-2xl font-bold text-red-800 mb-2">Mangler ferdigattest</h2>
                  <p className="text-sm text-red-700">
                    {resultat.mangler_ferdigattest.length > 0
                      ? `${resultat.mangler_ferdigattest.length} byggesak(er) kan mangle ferdigattest.`
                      : 'Kunne ikke bekrefte ferdigattest for eiendommen.'}
                  </p>
                </>
              )}
              <p className="text-xs text-slate-500 mt-3">{resultat.eiendom.info}</p>
            </div>

            {/* Anbefaling */}
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="font-bold text-slate-900 mb-2">Anbefaling</h3>
              <p className="text-sm text-slate-700 leading-relaxed">{resultat.anbefaling}</p>
              {resultat.estimert_kostnad && (
                <p className="text-sm font-semibold text-slate-900 mt-3">
                  Estimert kostnad: {resultat.estimert_kostnad}
                </p>
              )}
            </div>

            {/* Byggesaker uten ferdigattest */}
            {resultat.mangler_ferdigattest.length > 0 && (
              <div className="rounded-2xl border border-red-200 bg-white p-6 shadow-sm">
                <h3 className="font-bold text-slate-900 mb-3 flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-red-500" />
                  Byggesaker uten ferdigattest
                </h3>
                <div className="space-y-3">
                  {resultat.mangler_ferdigattest.map((sak, i) => (
                    <div key={i} className="rounded-lg border border-red-100 bg-red-50 p-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="text-sm font-semibold text-slate-900">{sak.tittel || sak.sakstype || 'Byggesak'}</p>
                          <p className="text-xs text-slate-500 mt-0.5">Saksnr: {sak.saksnummer}</p>
                        </div>
                        <span className="text-xs font-medium text-red-600 bg-red-100 rounded-full px-2 py-0.5">
                          {sak.status}
                        </span>
                      </div>
                      {sak.vedtaksdato && (
                        <p className="text-xs text-slate-500 mt-1">Vedtaksdato: {sak.vedtaksdato}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Alle byggesaker */}
            {resultat.byggesaker.length > 0 && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-bold text-slate-900 mb-3 flex items-center gap-2">
                  <FileText className="h-5 w-5 text-slate-400" />
                  Alle registrerte byggesaker ({resultat.byggesaker.length})
                </h3>
                <div className="space-y-2">
                  {resultat.byggesaker.map((sak, i) => (
                    <div key={i} className="rounded-lg border border-slate-200 bg-slate-50 p-3 flex items-start justify-between">
                      <div>
                        <p className="text-sm font-medium text-slate-900">{sak.tittel || sak.sakstype || 'Byggesak'}</p>
                        <p className="text-xs text-slate-500">Saksnr: {sak.saksnummer}{sak.vedtaksdato ? ` | Vedtak: ${sak.vedtaksdato}` : ''}</p>
                      </div>
                      <span className="text-xs text-slate-500">{sak.status}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Neste steg */}
            {resultat.neste_steg.length > 0 && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-bold text-slate-900 mb-3">Neste steg</h3>
                <ol className="space-y-3">
                  {resultat.neste_steg.map((steg, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm text-slate-700">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-green-100 text-green-700 text-xs font-bold shrink-0">
                        {i + 1}
                      </span>
                      {steg}
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {/* CTA */}
            <div className="rounded-2xl border-2 border-green-200 bg-gradient-to-br from-green-50 to-emerald-50 p-8 text-center">
              <Mail className="h-10 w-10 text-green-600 mx-auto mb-3" />
              <h3 className="text-lg font-bold text-slate-900 mb-2">Trenger du hjelp?</h3>
              <p className="text-sm text-slate-600 mb-4">
                Vi ordner ferdigattest for deg &ndash; fra dokumentasjon til innsendt soknad.
              </p>
              <a href="mailto:hey@nops.no"
                className="inline-flex items-center gap-2 rounded-xl bg-green-600 px-6 py-3 text-sm font-semibold text-white hover:bg-green-700 transition-colors">
                Kontakt hey@nops.no <ArrowRight className="h-4 w-4" />
              </a>
            </div>

            {/* Info */}
            <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-4">
              <Info className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
              <p className="text-xs text-amber-800 leading-relaxed">
                Denne sjekken er basert pa tilgjengelige offentlige data fra Kartverket og DIBK.
                For komplett og juridisk bindende informasjon, kontakt kommunens byggesaksavdeling.
              </p>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
