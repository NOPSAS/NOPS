'use client';

import * as React from 'react';
import {
  TrendingUp,
  Calculator,
  DollarSign,
  BarChart3,
  Percent,
  Home,
  ArrowRight,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Info,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// ─── Types ─────────────────────────────────────────────────────────────────────

interface Finansiering {
  kjøpspris: number;
  egenkapital: number;
  lån: number;
  månedlig_renter: number;
  månedlig_avdrag: number;
  total_månedskostnad: number;
}

interface Leieinntekter {
  estimert_leie_per_mnd: number;
  årlig_leieinntekt: number;
  yield_prosent: number;
  netto_yield_prosent: number;
}

interface Prisvekst {
  estimert_vekst_per_aar: number;
  verdi_om_5_aar: number;
  verdi_om_10_aar: number;
  total_avkastning_10_aar_kr: number;
  total_avkastning_10_aar_prosent: number;
}

interface Cashflow {
  månedlig_positiv_cashflow: number;
  break_even_mnd: number;
  anbefaling: 'Kjøp' | 'Avvent' | 'Selg';
}

interface AnalyseResultat {
  eiendom: { knr: string; gnr: string; bnr: string; kommunenavn: string; kjøpspris: number; renovering_kr: number; total_investering: number };
  finansiering: Finansiering;
  leieinntekter: Leieinntekter;
  prisvekst: Prisvekst;
  cashflow: Cashflow;
  risiko_vurdering: string;
  nøkkeltall_markedet: string;
  anbefalinger: string[];
  disclaimer: string;
}

// ─── Helpers ───────────────────────────────────────────────────────────────────

function fmt(n: number): string {
  return new Intl.NumberFormat('nb-NO').format(Math.round(n));
}

function fmtFloat(n: number, decimals = 1): string {
  return n.toFixed(decimals).replace('.', ',');
}

const anbefalingFarge: Record<string, string> = {
  Kjøp: 'bg-emerald-100 text-emerald-800 border-emerald-300',
  Avvent: 'bg-amber-100 text-amber-800 border-amber-300',
  Selg: 'bg-red-100 text-red-800 border-red-300',
};

// ─── Component ─────────────────────────────────────────────────────────────────

export default function InvesteringPage() {
  // Form state
  const [adresse, setAdresse] = React.useState('');
  const [knr, setKnr] = React.useState('');
  const [gnr, setGnr] = React.useState('');
  const [bnr, setBnr] = React.useState('');
  const [kjøpspris, setKjøpspris] = React.useState<number | ''>('');
  const [egenkapitalProsent, setEgenkapitalProsent] = React.useState(25);
  const [rentenivaa, setRentenivaa] = React.useState(5.5);
  const [renoveringKr, setRenoveringKr] = React.useState<number | ''>(0);
  const [leiePerMnd, setLeiePerMnd] = React.useState<number | ''>('');
  const [horisont, setHorisont] = React.useState(10);

  React.useEffect(() => {
    document.title = 'Investeringsanalyse \u2013 Yield, ROI og cashflow | nops.no';
  }, []);

  // Result state
  const [loading, setLoading] = React.useState(false);
  const [feil, setFeil] = React.useState<string | null>(null);
  const [resultat, setResultat] = React.useState<AnalyseResultat | null>(null);

  const egenkapitalKr = kjøpspris
    ? Math.round((Number(kjøpspris) + Number(renoveringKr || 0)) * egenkapitalProsent / 100)
    : 0;

  async function kjørAnalyse(e: React.FormEvent) {
    e.preventDefault();
    if (!kjøpspris || !knr || !gnr || !bnr) {
      setFeil('Fyll inn kommunenummer, gnr, bnr og kjøpspris.');
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
        kjøpspris: String(kjøpspris),
        egenkapital_prosent: String(egenkapitalProsent),
        rentenivaa: String(rentenivaa),
        renovering_kr: String(renoveringKr || 0),
        investeringshorisont_aar: String(horisont),
      });
      if (leiePerMnd) params.set('leie_per_mnd', String(leiePerMnd));

      const res = await fetch(`/api/v1/investering/analyser?${params.toString()}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('token') || ''}` },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error((err as { detail?: string }).detail || 'Analyse feilet');
      }
      const data = await res.json() as AnalyseResultat;
      setResultat(data);
    } catch (err: unknown) {
      setFeil(err instanceof Error ? err.message : 'Ukjent feil');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <section className="bg-gradient-to-br from-blue-600 to-violet-700 text-white py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 mb-4 rounded-full bg-white/10 px-4 py-1.5 text-sm font-medium text-blue-100">
            <TrendingUp className="h-4 w-4" />
            nops.no / Investeringsanalyse
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mb-3">Investeringsanalyse</h1>
          <p className="text-lg text-blue-100 max-w-2xl">
            Beregn yield, ROI og lønnsomhet for enhver norsk eiendom. Komplett analyse med cashflow,
            break-even og 10-års prognoser.
          </p>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-4 py-10 space-y-6">
        {/* Skjema */}
        <form onSubmit={kjørAnalyse}>
          <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6 space-y-6">
            <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
              <Calculator className="h-4 w-4 text-blue-600" />
              Eiendomsdetaljer
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              {/* Adresse (fri tekst) */}
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Adresse (valgfritt – for referanse)
                </label>
                <input
                  type="text"
                  value={adresse}
                  onChange={(e) => setAdresse(e.target.value)}
                  placeholder="F.eks. Storgata 1, Oslo"
                  className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Kommunenummer */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Kommunenummer <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={knr}
                  onChange={(e) => setKnr(e.target.value)}
                  placeholder="F.eks. 0301"
                  required
                  className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* GNR / BNR side by side */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    GNR <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={gnr}
                    onChange={(e) => setGnr(e.target.value)}
                    placeholder="123"
                    required
                    className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    BNR <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={bnr}
                    onChange={(e) => setBnr(e.target.value)}
                    placeholder="45"
                    required
                    className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Kjøpspris */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Kjøpspris (kr) <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Home className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <input
                    type="number"
                    value={kjøpspris}
                    onChange={(e) => setKjøpspris(e.target.value === '' ? '' : Number(e.target.value))}
                    placeholder="4 500 000"
                    required
                    min={100000}
                    className="w-full rounded-lg border border-slate-300 pl-9 pr-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Rentenivå */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Rentenivå (%)
                </label>
                <div className="relative">
                  <Percent className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <input
                    type="number"
                    value={rentenivaa}
                    onChange={(e) => setRentenivaa(Number(e.target.value))}
                    step={0.1}
                    min={1}
                    max={15}
                    className="w-full rounded-lg border border-slate-300 pl-9 pr-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Egenkapital slider */}
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Egenkapital: <span className="text-blue-600 font-semibold">{egenkapitalProsent}%</span>
                  {kjøpspris ? (
                    <span className="ml-2 text-slate-400 font-normal">({fmt(egenkapitalKr)} kr)</span>
                  ) : null}
                </label>
                <input
                  type="range"
                  min={10}
                  max={40}
                  step={1}
                  value={egenkapitalProsent}
                  onChange={(e) => setEgenkapitalProsent(Number(e.target.value))}
                  className="w-full accent-blue-600"
                />
                <div className="flex justify-between text-xs text-slate-400 mt-1">
                  <span>10%</span>
                  <span>25%</span>
                  <span>40%</span>
                </div>
              </div>

              {/* Renovering */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Renovering (kr)
                </label>
                <input
                  type="number"
                  value={renoveringKr}
                  onChange={(e) => setRenoveringKr(e.target.value === '' ? '' : Number(e.target.value))}
                  placeholder="0"
                  min={0}
                  className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Leie per mnd */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Leie per mnd (kr) <span className="text-slate-400 font-normal text-xs">– valgfritt</span>
                </label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <input
                    type="number"
                    value={leiePerMnd}
                    onChange={(e) => setLeiePerMnd(e.target.value === '' ? '' : Number(e.target.value))}
                    placeholder="Estimer automatisk"
                    min={0}
                    className="w-full rounded-lg border border-slate-300 pl-9 pr-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Investeringshorisont */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Investeringshorisont
                </label>
                <select
                  value={horisont}
                  onChange={(e) => setHorisont(Number(e.target.value))}
                  className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value={5}>5 år</option>
                  <option value={10}>10 år</option>
                  <option value={15}>15 år</option>
                  <option value={20}>20 år</option>
                </select>
              </div>
            </div>

            {feil && (
              <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {feil}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60 transition-colors"
            >
              {loading ? (
                <><Loader2 className="h-4 w-4 animate-spin" /> Beregner investering…</>
              ) : (
                <><BarChart3 className="h-4 w-4" /> Beregn investering</>
              )}
            </button>
          </div>
        </form>

        {/* Resultat */}
        {resultat && (
          <div className="space-y-5">
            {/* Anbefaling badge */}
            <div className="flex items-center gap-3">
              <span
                className={cn(
                  'inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-bold',
                  anbefalingFarge[resultat.cashflow.anbefaling] ?? 'bg-slate-100 text-slate-700 border-slate-300'
                )}
              >
                {resultat.cashflow.anbefaling === 'Kjøp' && <CheckCircle2 className="h-4 w-4" />}
                {resultat.cashflow.anbefaling === 'Avvent' && <Info className="h-4 w-4" />}
                {resultat.cashflow.anbefaling === 'Selg' && <AlertCircle className="h-4 w-4" />}
                Anbefaling: {resultat.cashflow.anbefaling}
              </span>
              <span className="text-sm text-slate-500">
                {resultat.eiendom.kommunenavn} – {resultat.eiendom.knr}-{resultat.eiendom.gnr}/{resultat.eiendom.bnr}
              </span>
            </div>

            {/* 4 nøkkeltall-kort */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                {
                  icon: <Percent className="h-5 w-5 text-blue-600" />,
                  label: 'Brutto yield',
                  verdi: `${fmtFloat(resultat.leieinntekter.yield_prosent)}%`,
                  sub: `Netto ${fmtFloat(resultat.leieinntekter.netto_yield_prosent)}%`,
                  farge: 'bg-blue-50',
                },
                {
                  icon: <DollarSign className="h-5 w-5 text-emerald-600" />,
                  label: 'Månedlig cashflow',
                  verdi: `${resultat.cashflow.månedlig_positiv_cashflow >= 0 ? '+' : ''}${fmt(resultat.cashflow.månedlig_positiv_cashflow)} kr`,
                  sub: 'Leieinntekt minus kostnader',
                  farge: resultat.cashflow.månedlig_positiv_cashflow >= 0 ? 'bg-emerald-50' : 'bg-red-50',
                },
                {
                  icon: <BarChart3 className="h-5 w-5 text-violet-600" />,
                  label: 'Break-even',
                  verdi: `${resultat.cashflow.break_even_mnd} mnd`,
                  sub: `≈ ${Math.round(resultat.cashflow.break_even_mnd / 12)} år`,
                  farge: 'bg-violet-50',
                },
                {
                  icon: <TrendingUp className="h-5 w-5 text-amber-600" />,
                  label: 'Verdi om 10 år',
                  verdi: `${fmt(resultat.prisvekst.verdi_om_10_aar)} kr`,
                  sub: `+${fmtFloat(resultat.prisvekst.estimert_vekst_per_aar)}%/år`,
                  farge: 'bg-amber-50',
                },
              ].map((k) => (
                <div key={k.label} className={cn('rounded-xl border border-slate-200 p-4', k.farge)}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white shadow-sm">
                      {k.icon}
                    </div>
                  </div>
                  <p className="text-xs text-slate-500 mb-0.5">{k.label}</p>
                  <p className="text-xl font-bold text-slate-900 leading-tight">{k.verdi}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{k.sub}</p>
                </div>
              ))}
            </div>

            {/* Detaljer – to kolonner */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              {/* Finansiering */}
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-900 mb-4 text-sm flex items-center gap-2">
                  <Calculator className="h-4 w-4 text-blue-600" />
                  Finansiering
                </h3>
                <div className="space-y-2.5">
                  {[
                    { label: 'Kjøpspris', verdi: `${fmt(resultat.finansiering.kjøpspris)} kr` },
                    { label: 'Egenkapital', verdi: `${fmt(resultat.finansiering.egenkapital)} kr` },
                    { label: 'Lån', verdi: `${fmt(resultat.finansiering.lån)} kr` },
                    { label: 'Månedlige renter', verdi: `${fmt(resultat.finansiering.månedlig_renter)} kr` },
                    { label: 'Månedlig avdrag', verdi: `${fmt(resultat.finansiering.månedlig_avdrag)} kr` },
                    { label: 'Total månedskostnad', verdi: `${fmt(resultat.finansiering.total_månedskostnad)} kr`, bold: true },
                  ].map((rad) => (
                    <div key={rad.label} className="flex justify-between text-sm border-b border-slate-100 pb-2 last:border-0 last:pb-0">
                      <span className="text-slate-500">{rad.label}</span>
                      <span className={cn('font-medium text-slate-900', rad.bold && 'font-bold text-blue-700')}>{rad.verdi}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Prisvekst */}
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-900 mb-4 text-sm flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-amber-600" />
                  Prisvekst og avkastning
                </h3>
                <div className="space-y-2.5">
                  {[
                    { label: 'Estimert vekst/år', verdi: `${fmtFloat(resultat.prisvekst.estimert_vekst_per_aar)}%` },
                    { label: 'Verdi om 5 år', verdi: `${fmt(resultat.prisvekst.verdi_om_5_aar)} kr` },
                    { label: 'Verdi om 10 år', verdi: `${fmt(resultat.prisvekst.verdi_om_10_aar)} kr` },
                    { label: 'Total avkastning 10 år', verdi: `${fmt(resultat.prisvekst.total_avkastning_10_aar_kr)} kr` },
                    { label: 'Avkastning på EK', verdi: `${fmtFloat(resultat.prisvekst.total_avkastning_10_aar_prosent)}%`, bold: true },
                    { label: 'Leie estimert/mnd', verdi: `${fmt(resultat.leieinntekter.estimert_leie_per_mnd)} kr` },
                  ].map((rad) => (
                    <div key={rad.label} className="flex justify-between text-sm border-b border-slate-100 pb-2 last:border-0 last:pb-0">
                      <span className="text-slate-500">{rad.label}</span>
                      <span className={cn('font-medium text-slate-900', rad.bold && 'font-bold text-amber-700')}>{rad.verdi}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Cashflow-diagram */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900 mb-4 text-sm flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-violet-600" />
                Cashflow-oversikt
              </h3>
              <div className="space-y-3">
                {[
                  {
                    label: 'Leieinntekt',
                    kr: resultat.leieinntekter.estimert_leie_per_mnd,
                    maks: resultat.leieinntekter.estimert_leie_per_mnd,
                    farge: 'bg-emerald-500',
                  },
                  {
                    label: 'Renter + avdrag',
                    kr: resultat.finansiering.månedlig_renter + resultat.finansiering.månedlig_avdrag,
                    maks: resultat.leieinntekter.estimert_leie_per_mnd,
                    farge: 'bg-red-400',
                  },
                  {
                    label: 'Øvrige kostnader',
                    kr: Math.max(0, resultat.finansiering.total_månedskostnad - resultat.finansiering.månedlig_renter - resultat.finansiering.månedlig_avdrag),
                    maks: resultat.leieinntekter.estimert_leie_per_mnd,
                    farge: 'bg-amber-400',
                  },
                ].map((rad) => (
                  <div key={rad.label}>
                    <div className="flex justify-between text-xs text-slate-500 mb-1">
                      <span>{rad.label}</span>
                      <span className="font-medium text-slate-700">{fmt(rad.kr)} kr/mnd</span>
                    </div>
                    <div className="h-5 w-full rounded-full bg-slate-100 overflow-hidden">
                      <div
                        className={cn('h-full rounded-full transition-all', rad.farge)}
                        style={{ width: `${Math.min(100, (rad.kr / (rad.maks * 1.2)) * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
                <div className="mt-3 pt-3 border-t border-slate-100 flex justify-between items-center">
                  <span className="text-sm font-semibold text-slate-700">Netto cashflow/mnd</span>
                  <span className={cn(
                    'text-base font-bold',
                    resultat.cashflow.månedlig_positiv_cashflow >= 0 ? 'text-emerald-600' : 'text-red-600'
                  )}>
                    {resultat.cashflow.månedlig_positiv_cashflow >= 0 ? '+' : ''}{fmt(resultat.cashflow.månedlig_positiv_cashflow)} kr
                  </span>
                </div>
              </div>
            </div>

            {/* Risikovurdering */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900 mb-2 text-sm flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-amber-600" />
                Risikovurdering
              </h3>
              <p className="text-sm text-slate-700 leading-relaxed">{resultat.risiko_vurdering}</p>
            </div>

            {/* Markedsdata */}
            {resultat.nøkkeltall_markedet && (
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-900 mb-2 text-sm flex items-center gap-2">
                  <Info className="h-4 w-4 text-blue-600" />
                  Lokalt markedet – {resultat.eiendom.kommunenavn}
                </h3>
                <p className="text-sm text-slate-700 leading-relaxed">{resultat.nøkkeltall_markedet}</p>
              </div>
            )}

            {/* Anbefalinger */}
            {(resultat.anbefalinger?.length ?? 0) > 0 && (
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-900 mb-3 text-sm flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  Anbefalinger
                </h3>
                <ul className="space-y-2">
                  {resultat.anbefalinger.map((a, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm text-slate-700">
                      <ArrowRight className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />
                      {a}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Disclaimer */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs text-slate-500 leading-relaxed">
                <strong>Merk:</strong> {resultat.disclaimer}
              </p>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
