'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  Scale,
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  BookOpen,
  Gavel,
  ShieldCheck,
  ArrowRight,
  Info,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ParagrafRef {
  lov: string;
  paragraf: string;
  tittel: string;
  relevans: string;
}

export default function JuridiskPage() {
  const [modus, setModus] = React.useState<'sporsmal' | 'tiltak'>('sporsmal');
  const [sporsmal, setSporsmal] = React.useState('');
  const [tiltaksBeskrivelse, setTiltaksBeskrivelse] = React.useState('');
  const [tiltakstype, setTiltakstype] = React.useState('tilbygg');
  const [knr, setKnr] = React.useState('');
  const [gnr, setGnr] = React.useState('');
  const [bnr, setBnr] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [resultat, setResultat] = React.useState<Record<string, unknown> | null>(null);
  const [feil, setFeil] = React.useState<string | null>(null);

  React.useEffect(() => {
    document.title = 'Juridisk AI-assistent for byggesak | nops.no';
  }, []);

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') || '' : '';

  async function send() {
    setLoading(true);
    setFeil(null);
    setResultat(null);
    try {
      let url: string;
      if (modus === 'sporsmal') {
        if (!sporsmal.trim()) { setFeil('Skriv inn et spørsmål'); setLoading(false); return; }
        const params = new URLSearchParams({ sporsmal });
        if (knr) params.set('knr', knr);
        if (gnr) params.set('gnr', gnr);
        if (bnr) params.set('bnr', bnr);
        url = `/api/v1/juridisk/spor?${params}`;
      } else {
        if (!tiltaksBeskrivelse.trim() || !knr || !gnr || !bnr) {
          setFeil('Fyll inn alle feltene');
          setLoading(false);
          return;
        }
        const params = new URLSearchParams({
          knr, gnr, bnr,
          tiltaksbeskrivelse: tiltaksBeskrivelse,
          tiltakstype,
        });
        url = `/api/v1/juridisk/vurder-tiltak?${params}`;
      }
      const res = await fetch(url, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 402) { setFeil('Juridisk AI krever Starter-plan eller høyere.'); return; }
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || `HTTP ${res.status}`); }
      setResultat(await res.json());
    } catch (e: unknown) {
      setFeil(e instanceof Error ? e.message : 'Feil');
    } finally {
      setLoading(false);
    }
  }

  const paragrafRefs = (resultat?.paragraf_referanser ?? resultat?.tek17_krav ?? []) as ParagrafRef[];
  const anbefalinger = (resultat?.anbefalinger ?? []) as string[];
  const risiko = (resultat?.risiko ?? resultat?.risikovurdering ?? '') as string;

  return (
    <main className="min-h-screen bg-slate-50">
      <section className="bg-gradient-to-br from-indigo-700 to-purple-800 text-white py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 mb-4 rounded-full bg-white/10 px-4 py-1.5 text-sm font-medium text-indigo-200">
            <Scale className="h-4 w-4" /> nops.no / Juridisk AI
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mb-4">
            Juridisk AI-assistent for byggesak
          </h1>
          <p className="text-lg text-indigo-100 max-w-2xl">
            Still spørsmål om PBL, TEK17 og SAK10 – eller få en komplett juridisk vurdering
            av ditt planlagte tiltak. Med eksakte paragrafhenvisninger.
          </p>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-4 py-10 space-y-6">
        {/* Modus-velger */}
        <div className="flex gap-2">
          {[
            { id: 'sporsmal' as const, label: 'Still et spørsmål', icon: <BookOpen className="h-4 w-4" /> },
            { id: 'tiltak' as const, label: 'Vurder tiltak', icon: <Gavel className="h-4 w-4" /> },
          ].map((m) => (
            <button key={m.id} type="button" onClick={() => { setModus(m.id); setResultat(null); }}
              className={cn(
                'inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-medium transition-colors',
                modus === m.id ? 'bg-indigo-600 text-white' : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'
              )}>
              {m.icon} {m.label}
            </button>
          ))}
        </div>

        {/* Spørsmål-modus */}
        {modus === 'sporsmal' && (
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <label className="block text-sm font-semibold text-slate-700 mb-2">Ditt spørsmål om byggesak</label>
            <textarea value={sporsmal} onChange={(e) => setSporsmal(e.target.value)} rows={4}
              placeholder="F.eks. «Kan jeg bygge garasje 2 meter fra nabogrense?» eller «Trenger jeg søknad for å innrede kjeller til soverom?»"
              className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none mb-3" />
            <p className="text-xs text-slate-500 mb-4">Valgfritt: Legg til eiendom for mer presis vurdering</p>
            <div className="grid grid-cols-3 gap-2 mb-4">
              <input type="text" placeholder="Kommunenr." value={knr} onChange={(e) => setKnr(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              <input type="number" placeholder="Gnr." value={gnr} onChange={(e) => setGnr(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              <input type="number" placeholder="Bnr." value={bnr} onChange={(e) => setBnr(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
          </div>
        )}

        {/* Tiltak-modus */}
        {modus === 'tiltak' && (
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="grid grid-cols-3 gap-2 mb-4">
              <input type="text" placeholder="Kommunenr. *" value={knr} onChange={(e) => setKnr(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              <input type="number" placeholder="Gnr. *" value={gnr} onChange={(e) => setGnr(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              <input type="number" placeholder="Bnr. *" value={bnr} onChange={(e) => setBnr(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <select value={tiltakstype} onChange={(e) => setTiltakstype(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-500">
              {['tilbygg','påbygg','garasje','carport','bruksendring','riving','nybygg','terrasse','fasadeendring'].map((t) => (
                <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
              ))}
            </select>
            <textarea value={tiltaksBeskrivelse} onChange={(e) => setTiltaksBeskrivelse(e.target.value)} rows={3}
              placeholder="Beskriv tiltaket: hva du planlegger å bygge, størrelse, plassering..."
              className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none" />
          </div>
        )}

        {feil && (
          <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <AlertTriangle className="h-4 w-4 shrink-0" /> {feil}
          </div>
        )}

        <button type="button" onClick={send} disabled={loading}
          className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60 transition-colors">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          {modus === 'sporsmal' ? 'Få juridisk svar' : 'Kjør juridisk vurdering'}
        </button>

        {/* Resultat */}
        {resultat && (
          <div className="space-y-5">
            {/* Risiko-badge */}
            {risiko && (
              <div className={cn(
                'rounded-xl border p-5 flex items-center gap-3',
                risiko === 'LAV' ? 'border-green-200 bg-green-50' :
                risiko === 'MIDDELS' ? 'border-amber-200 bg-amber-50' :
                'border-red-200 bg-red-50'
              )}>
                <ShieldCheck className="h-6 w-6" />
                <div>
                  <p className="font-bold">Risiko: {risiko}</p>
                  {resultat.samlet_vurdering && (
                    <p className="text-sm mt-1">{resultat.samlet_vurdering as string}</p>
                  )}
                </div>
              </div>
            )}

            {/* Svar (spørsmål-modus) */}
            {resultat.svar && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm prose prose-sm max-w-none">
                <div dangerouslySetInnerHTML={{ __html: (resultat.svar as string).replace(/\n/g, '<br/>') }} />
              </div>
            )}

            {/* Søknadsplikt (tiltak-modus) */}
            {resultat.soknadsplikt && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-bold text-slate-900 mb-2">Søknadsplikt</h3>
                <p className="text-sm font-semibold text-indigo-700 mb-1">
                  {(resultat.soknadsplikt as Record<string, string>).vurdering}
                </p>
                <p className="text-xs text-slate-500 mb-1">Hjemmel: {(resultat.soknadsplikt as Record<string, string>).hjemmel}</p>
                <p className="text-sm text-slate-700">{(resultat.soknadsplikt as Record<string, string>).begrunnelse}</p>
              </div>
            )}

            {/* Paragraf-referanser */}
            {paragrafRefs.length > 0 && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-bold text-slate-900 mb-3">Relevante paragrafer</h3>
                <div className="space-y-2">
                  {paragrafRefs.map((p, i) => (
                    <div key={i} className="flex items-start gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
                      <span className="shrink-0 rounded-full bg-indigo-100 text-indigo-700 px-2 py-0.5 text-xs font-bold">
                        {p.lov || ''} {p.paragraf || ''}
                      </span>
                      <div>
                        <p className="text-sm font-medium text-slate-900">{p.tittel || (p as Record<string, string>).krav || ''}</p>
                        <p className="text-xs text-slate-500 mt-0.5">{p.relevans || (p as Record<string, string>).kommentar || ''}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Anbefalinger */}
            {anbefalinger.length > 0 && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-bold text-slate-900 mb-3">Anbefalinger</h3>
                <ul className="space-y-2">
                  {anbefalinger.map((a, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm text-slate-700">
                      <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 shrink-0" /> {a}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Disclaimer */}
            <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-4">
              <Info className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
              <p className="text-xs text-amber-800 leading-relaxed">
                {(resultat.disclaimer as string) || 'Denne vurderingen er beslutningsstøtte og erstatter ikke juridisk rådgivning.'}
              </p>
            </div>
          </div>
        )}

        {/* Hva vi dekker */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="text-lg font-bold text-slate-900 mb-4">Regelverk vi dekker</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { lov: 'PBL', tittel: 'Plan- og bygningsloven', desc: 'Søknadsplikt, dispensasjon, nabovarsel' },
              { lov: 'TEK17', tittel: 'Byggteknisk forskrift', desc: 'Dagslys, brannsikkerhet, tilgjengelighet' },
              { lov: 'SAK10', tittel: 'Byggesaksforskriften', desc: 'Ansvarsretter, tidsfrister, dokumentasjon' },
              { lov: 'Byggforsk', tittel: 'SINTEF Byggforsk', desc: 'Veiledere, detaljer, god praksis' },
            ].map((l) => (
              <div key={l.lov} className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-center">
                <p className="text-lg font-bold text-indigo-600">{l.lov}</p>
                <p className="text-xs font-semibold text-slate-700 mt-1">{l.tittel}</p>
                <p className="text-[10px] text-slate-500 mt-1">{l.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
