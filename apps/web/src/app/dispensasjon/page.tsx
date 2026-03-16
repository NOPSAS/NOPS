'use client';

import * as React from 'react';
import {
  Scale,
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Info,
  Copy,
  Check,
  FileText,
  Lightbulb,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface DispensasjonResultat {
  dispensasjon_tekst: string;
  vurdering_fordeler_ulemper: string;
  sannsynlighet: string;
  sannsynlighet_begrunnelse: string;
  paragraf_referanser: string[];
  nodvendige_vedlegg: string[];
  tips: string[];
  disclaimer: string;
}

const DISPENSASJON_VALG = [
  { value: 'avstand_nabogrense', label: 'Avstand til nabogrense' },
  { value: 'bya_grense', label: 'BYA-grense (bebygd areal)' },
  { value: 'reguleringsformaal', label: 'Reguleringsformål' },
  { value: 'hoydegrense', label: 'Høydegrense' },
  { value: 'annet', label: 'Annet (spesifiser under)' },
];

export default function DispensasjonPage() {
  const [knr, setKnr] = React.useState('');
  const [gnr, setGnr] = React.useState('');
  const [bnr, setBnr] = React.useState('');
  const [tiltaksbeskrivelse, setTiltaksbeskrivelse] = React.useState('');
  const [dispensasjonFraValg, setDispensasjonFraValg] = React.useState('avstand_nabogrense');
  const [dispensasjonFraTekst, setDispensasjonFraTekst] = React.useState('');
  const [begrunnelse, setBegrunnelse] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [resultat, setResultat] = React.useState<DispensasjonResultat | null>(null);
  const [feil, setFeil] = React.useState<string | null>(null);
  const [kopiert, setKopiert] = React.useState(false);

  React.useEffect(() => {
    document.title = 'Dispensasjonssoknad | nops.no';
  }, []);

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') || '' : '';

  function getDispensasjonFra(): string {
    if (dispensasjonFraValg === 'annet') return dispensasjonFraTekst;
    const valgt = DISPENSASJON_VALG.find((v) => v.value === dispensasjonFraValg);
    return dispensasjonFraTekst
      ? `${valgt?.label || dispensasjonFraValg}: ${dispensasjonFraTekst}`
      : valgt?.label || dispensasjonFraValg;
  }

  async function generer() {
    if (!knr || !gnr || !bnr) { setFeil('Fyll inn kommunenr, gnr og bnr'); return; }
    if (!tiltaksbeskrivelse.trim()) { setFeil('Beskriv hva du vil bygge'); return; }
    if (!begrunnelse.trim()) { setFeil('Fyll inn begrunnelse for dispensasjon'); return; }

    setLoading(true);
    setFeil(null);
    setResultat(null);

    try {
      const params = new URLSearchParams({
        knr,
        gnr,
        bnr,
        tiltaksbeskrivelse,
        dispensasjon_fra: getDispensasjonFra(),
        begrunnelse,
      });
      const res = await fetch(`/api/v1/dispensasjon/generer?${params}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 402) { setFeil('Dispensasjonssoknad krever Starter-plan eller hoyere.'); return; }
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
    if (!resultat?.dispensasjon_tekst) return;
    navigator.clipboard.writeText(resultat.dispensasjon_tekst);
    setKopiert(true);
    setTimeout(() => setKopiert(false), 2000);
  }

  const sannsynlighetFarge = (s: string) => {
    const lower = s?.toLowerCase() || '';
    if (lower.includes('hoy') || lower.includes('høy')) return 'border-green-200 bg-green-50 text-green-800';
    if (lower.includes('middels')) return 'border-amber-200 bg-amber-50 text-amber-800';
    return 'border-red-200 bg-red-50 text-red-800';
  };

  const sannsynlighetDot = (s: string) => {
    const lower = s?.toLowerCase() || '';
    if (lower.includes('hoy') || lower.includes('høy')) return 'bg-green-500';
    if (lower.includes('middels')) return 'bg-amber-500';
    return 'bg-red-500';
  };

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <section className="bg-gradient-to-br from-red-600 to-orange-500 text-white py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 mb-4 rounded-full bg-white/10 px-4 py-1.5 text-sm font-medium text-red-100">
            <Scale className="h-4 w-4" /> nops.no / Dispensasjon
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mb-4">
            Dispensasjonssoknad
          </h1>
          <p className="text-lg text-red-100 max-w-2xl">
            Generer en komplett dispensasjonssoknad med AI &ndash; med fordel/ulempe-vurdering etter PBL &sect;19-2
          </p>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-4 py-10 space-y-6">
        {/* Skjema */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-5">
          {/* Eiendom */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">Eiendom</label>
            <div className="grid grid-cols-3 gap-2">
              <input type="text" placeholder="Kommunenr. *" value={knr} onChange={(e) => setKnr(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500" />
              <input type="number" placeholder="Gnr. *" value={gnr} onChange={(e) => setGnr(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500" />
              <input type="number" placeholder="Bnr. *" value={bnr} onChange={(e) => setBnr(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500" />
            </div>
          </div>

          {/* Hva vil du bygge */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">Hva vil du bygge?</label>
            <textarea value={tiltaksbeskrivelse} onChange={(e) => setTiltaksbeskrivelse(e.target.value)} rows={3}
              placeholder="F.eks. Tilbygg pa 30 m2 i to etasjer mot sor, garasje 50 m2 narmere nabogrense enn 4 meter..."
              className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 resize-none" />
          </div>

          {/* Hva soker du dispensasjon fra */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">Hva soker du dispensasjon fra?</label>
            <select value={dispensasjonFraValg} onChange={(e) => setDispensasjonFraValg(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm mb-2 focus:outline-none focus:ring-2 focus:ring-red-500">
              {DISPENSASJON_VALG.map((v) => (
                <option key={v.value} value={v.value}>{v.label}</option>
              ))}
            </select>
            <textarea value={dispensasjonFraTekst} onChange={(e) => setDispensasjonFraTekst(e.target.value)} rows={2}
              placeholder={dispensasjonFraValg === 'annet' ? 'Beskriv hva du soker dispensasjon fra...' : 'Valgfritt: Utdyp (f.eks. onsker 1,5 m avstand i stedet for 4 m)'}
              className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 resize-none" />
          </div>

          {/* Begrunnelse */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">Hvorfor bor dispensasjon innvilges?</label>
            <textarea value={begrunnelse} onChange={(e) => setBegrunnelse(e.target.value)} rows={3}
              placeholder="Begrunn hvorfor fordelene ved dispensasjon er klart storre enn ulempene. F.eks. tomtens form, eksisterende bebyggelse, nabosituasjon..."
              className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 resize-none" />
          </div>
        </div>

        {/* Feil */}
        {feil && (
          <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <AlertTriangle className="h-4 w-4 shrink-0" /> {feil}
          </div>
        )}

        {/* Send-knapp */}
        <button type="button" onClick={generer} disabled={loading}
          className="inline-flex items-center gap-2 rounded-xl bg-red-600 px-6 py-3 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60 transition-colors">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          Generer dispensasjonssoknad
        </button>

        {/* Resultat */}
        {resultat && (
          <div className="space-y-5">
            {/* Sannsynlighet */}
            {resultat.sannsynlighet && (
              <div className={cn('rounded-xl border p-5 flex items-start gap-3', sannsynlighetFarge(resultat.sannsynlighet))}>
                <div className={cn('mt-1 h-3 w-3 rounded-full shrink-0', sannsynlighetDot(resultat.sannsynlighet))} />
                <div>
                  <p className="font-bold text-lg">Sannsynlighet: {resultat.sannsynlighet}</p>
                  <p className="text-sm mt-1">{resultat.sannsynlighet_begrunnelse}</p>
                </div>
              </div>
            )}

            {/* Fordel/ulempe-vurdering */}
            {resultat.vurdering_fordeler_ulemper && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-bold text-slate-900 mb-3 flex items-center gap-2">
                  <Scale className="h-5 w-5 text-red-600" /> Fordel/ulempe-vurdering (PBL &sect;19-2)
                </h3>
                <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                  {resultat.vurdering_fordeler_ulemper}
                </div>
              </div>
            )}

            {/* Soknadstekst */}
            {resultat.dispensasjon_tekst && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-bold text-slate-900 flex items-center gap-2">
                    <FileText className="h-5 w-5 text-red-600" /> Dispensasjonssoknad
                  </h3>
                  <button type="button" onClick={kopierTekst}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 transition-colors">
                    {kopiert ? <Check className="h-3.5 w-3.5 text-green-600" /> : <Copy className="h-3.5 w-3.5" />}
                    {kopiert ? 'Kopiert!' : 'Kopier'}
                  </button>
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-5 text-sm text-slate-800 leading-relaxed whitespace-pre-line">
                  {resultat.dispensasjon_tekst}
                </div>
              </div>
            )}

            {/* Paragraf-referanser */}
            {resultat.paragraf_referanser && resultat.paragraf_referanser.length > 0 && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-bold text-slate-900 mb-3">Paragraf-referanser</h3>
                <div className="flex flex-wrap gap-2">
                  {resultat.paragraf_referanser.map((p, i) => (
                    <span key={i} className="inline-flex items-center rounded-full bg-red-50 border border-red-200 text-red-700 px-3 py-1 text-xs font-semibold">
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Nodvendige vedlegg */}
            {resultat.nodvendige_vedlegg && resultat.nodvendige_vedlegg.length > 0 && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-bold text-slate-900 mb-3">Nodvendige vedlegg</h3>
                <ul className="space-y-2">
                  {resultat.nodvendige_vedlegg.map((v, i) => (
                    <li key={i} className="flex items-center gap-2.5 text-sm text-slate-700">
                      <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" /> {v}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Tips */}
            {resultat.tips && resultat.tips.length > 0 && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-bold text-slate-900 mb-3 flex items-center gap-2">
                  <Lightbulb className="h-5 w-5 text-amber-500" /> Tips
                </h3>
                <ul className="space-y-2">
                  {resultat.tips.map((t, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm text-slate-700">
                      <span className="mt-0.5 text-amber-500 font-bold">&bull;</span> {t}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Disclaimer */}
            <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-4">
              <Info className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
              <p className="text-xs text-amber-800 leading-relaxed">
                {resultat.disclaimer || 'Denne soknadsteksten er AI-generert beslutningsstotte og erstatter ikke juridisk radgivning.'}
              </p>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
