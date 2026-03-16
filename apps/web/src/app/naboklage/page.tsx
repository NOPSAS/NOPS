'use client';

import * as React from 'react';
import {
  Users,
  Sparkles,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Download,
  Info,
  Clock,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const KLAGEGRUNNER = [
  { id: 'utsikt', label: 'Utsikt' },
  { id: 'skygge', label: 'Skygge' },
  { id: 'privatlivets fred', label: 'Privatlivets fred' },
  { id: 'avstand', label: 'Avstand til grense' },
  { id: 'trafikk', label: 'Trafikk' },
  { id: 'stoy', label: 'Stoey' },
  { id: 'annet', label: 'Annet' },
];

interface NaboklageResultat {
  merknad_tekst: string;
  juridisk_grunnlag: string;
  styrke: string;
  styrke_begrunnelse: string;
  paragraf_referanser: string[];
  tips_for_naboen: string[];
  frist_info: string;
  disclaimer?: string;
}

export default function NaboklagePage() {
  const [knr, setKnr] = React.useState('');
  const [gnr, setGnr] = React.useState('');
  const [bnr, setBnr] = React.useState('');
  const [naboKnr, setNaboKnr] = React.useState('');
  const [naboGnr, setNaboGnr] = React.useState('');
  const [naboBnr, setNaboBnr] = React.useState('');
  const [tiltaksbeskrivelse, setTiltaksbeskrivelse] = React.useState('');
  const [valgteGrunner, setValgteGrunner] = React.useState<string[]>([]);
  const [tilleggsinformasjon, setTilleggsinformasjon] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [resultat, setResultat] = React.useState<NaboklageResultat | null>(null);
  const [feil, setFeil] = React.useState<string | null>(null);
  const [kopiert, setKopiert] = React.useState(false);

  React.useEffect(() => {
    document.title = 'Merknad pa nabovarsel | nops.no';
  }, []);

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') || '' : '';

  function toggleGrunn(id: string) {
    setValgteGrunner((prev) =>
      prev.includes(id) ? prev.filter((g) => g !== id) : [...prev, id]
    );
  }

  async function generer() {
    if (!knr || !gnr || !bnr || !naboKnr || !naboGnr || !naboBnr) {
      setFeil('Fyll inn alle eiendomsfeltene');
      return;
    }
    if (!tiltaksbeskrivelse.trim()) {
      setFeil('Beskriv hva naboen planlegger');
      return;
    }
    if (valgteGrunner.length === 0) {
      setFeil('Velg minst en klagegrunn');
      return;
    }

    setLoading(true);
    setFeil(null);
    setResultat(null);

    try {
      const params = new URLSearchParams({
        knr,
        gnr,
        bnr,
        nabo_knr: naboKnr,
        nabo_gnr: naboGnr,
        nabo_bnr: naboBnr,
        tiltaksbeskrivelse,
        klagegrunn: valgteGrunner.join(', '),
      });
      if (tilleggsinformasjon.trim()) {
        params.set('tilleggsinformasjon', tilleggsinformasjon);
      }

      const res = await fetch(`/api/v1/naboklage/generer?${params}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.status === 402) {
        setFeil('Naboklage-tjenesten krever Starter-plan eller hoyere.');
        return;
      }
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

  function kopierTekst() {
    if (!resultat?.merknad_tekst) return;
    navigator.clipboard.writeText(resultat.merknad_tekst);
    setKopiert(true);
    setTimeout(() => setKopiert(false), 2000);
  }

  function lastNedTekst() {
    if (!resultat?.merknad_tekst) return;
    const blob = new Blob([resultat.merknad_tekst], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'merknad-nabovarsel.txt';
    a.click();
    URL.revokeObjectURL(url);
  }

  const styrkeColor =
    resultat?.styrke === 'Sterk'
      ? 'border-green-200 bg-green-50 text-green-800'
      : resultat?.styrke === 'Middels'
        ? 'border-amber-200 bg-amber-50 text-amber-800'
        : 'border-red-200 bg-red-50 text-red-800';

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <section className="bg-gradient-to-br from-blue-600 to-indigo-700 text-white py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 mb-4 rounded-full bg-white/10 px-4 py-1.5 text-sm font-medium text-blue-200">
            <Users className="h-4 w-4" /> nops.no / Naboklage
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mb-4">
            Merknad pa nabovarsel
          </h1>
          <p className="text-lg text-blue-100 max-w-2xl">
            Skriv en profesjonell og juridisk holdbar merknad -- med AI
          </p>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-4 py-10 space-y-6">
        {/* Din eiendom */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">Din eiendom</h2>
          <div className="grid grid-cols-3 gap-2">
            <input
              type="text"
              placeholder="Kommunenr."
              value={knr}
              onChange={(e) => setKnr(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              type="number"
              placeholder="Gnr."
              value={gnr}
              onChange={(e) => setGnr(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              type="number"
              placeholder="Bnr."
              value={bnr}
              onChange={(e) => setBnr(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Naboens eiendom */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">Naboens eiendom (den som bygger)</h2>
          <div className="grid grid-cols-3 gap-2">
            <input
              type="text"
              placeholder="Kommunenr."
              value={naboKnr}
              onChange={(e) => setNaboKnr(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              type="number"
              placeholder="Gnr."
              value={naboGnr}
              onChange={(e) => setNaboGnr(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              type="number"
              placeholder="Bnr."
              value={naboBnr}
              onChange={(e) => setNaboBnr(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Hva planlegger naboen */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Hva planlegger naboen?
          </label>
          <textarea
            value={tiltaksbeskrivelse}
            onChange={(e) => setTiltaksbeskrivelse(e.target.value)}
            rows={3}
            placeholder="Beskriv tiltaket: hva naboen planlegger a bygge, stoerrelse, plassering..."
            className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>

        {/* Klagegrunn */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <label className="block text-sm font-semibold text-slate-700 mb-3">
            Hva er du bekymret for?
          </label>
          <div className="flex flex-wrap gap-2">
            {KLAGEGRUNNER.map((g) => (
              <button
                key={g.id}
                type="button"
                onClick={() => toggleGrunn(g.id)}
                className={cn(
                  'rounded-lg border px-4 py-2 text-sm font-medium transition-colors',
                  valgteGrunner.includes(g.id)
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                )}
              >
                {g.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tilleggsinformasjon */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Tilleggsinformasjon <span className="text-slate-400 font-normal">(valgfritt)</span>
          </label>
          <textarea
            value={tilleggsinformasjon}
            onChange={(e) => setTilleggsinformasjon(e.target.value)}
            rows={3}
            placeholder="Utdyp gjerne med mer informasjon om situasjonen..."
            className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>

        {/* Feilmelding */}
        {feil && (
          <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <AlertTriangle className="h-4 w-4 shrink-0" /> {feil}
          </div>
        )}

        {/* Generer-knapp */}
        <button
          type="button"
          onClick={generer}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60 transition-colors"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          Generer merknad
        </button>

        {/* Resultat */}
        {resultat && (
          <div className="space-y-5">
            {/* Styrke-badge */}
            <div className={cn('rounded-xl border p-5 flex items-center gap-3', styrkeColor)}>
              <CheckCircle2 className="h-6 w-6 shrink-0" />
              <div>
                <p className="font-bold">Styrke: {resultat.styrke}</p>
                <p className="text-sm mt-1">{resultat.styrke_begrunnelse}</p>
              </div>
            </div>

            {/* Juridisk grunnlag */}
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="font-bold text-slate-900 mb-2">Juridisk grunnlag</h3>
              <p className="text-sm text-slate-700 leading-relaxed">{resultat.juridisk_grunnlag}</p>
            </div>

            {/* Merknad-tekst */}
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-slate-900">Merknadstekst</h3>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={kopierTekst}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                  >
                    <Copy className="h-3.5 w-3.5" />
                    {kopiert ? 'Kopiert!' : 'Kopier'}
                  </button>
                  <button
                    type="button"
                    onClick={lastNedTekst}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                  >
                    <Download className="h-3.5 w-3.5" />
                    Last ned .txt
                  </button>
                </div>
              </div>
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">
                {resultat.merknad_tekst}
              </div>
            </div>

            {/* Frist-info */}
            <div className="flex items-center gap-2 rounded-xl border border-blue-200 bg-blue-50 p-4">
              <Clock className="h-4 w-4 text-blue-600 shrink-0" />
              <p className="text-sm text-blue-800 font-medium">{resultat.frist_info}</p>
            </div>

            {/* Paragraf-referanser */}
            {resultat.paragraf_referanser && resultat.paragraf_referanser.length > 0 && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-bold text-slate-900 mb-3">Paragraf-referanser</h3>
                <div className="flex flex-wrap gap-2">
                  {resultat.paragraf_referanser.map((p, i) => (
                    <span
                      key={i}
                      className="rounded-full bg-indigo-100 text-indigo-700 px-3 py-1 text-xs font-bold"
                    >
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Tips */}
            {resultat.tips_for_naboen && resultat.tips_for_naboen.length > 0 && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-bold text-slate-900 mb-3">Tips</h3>
                <ul className="space-y-2">
                  {resultat.tips_for_naboen.map((tip, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm text-slate-700">
                      <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 shrink-0" /> {tip}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Disclaimer */}
            <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-4">
              <Info className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
              <p className="text-xs text-amber-800 leading-relaxed">
                {resultat.disclaimer || 'Denne merknaden er beslutningsstotte og erstatter ikke juridisk radgivning.'}
              </p>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
