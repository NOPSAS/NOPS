'use client';

import * as React from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import {
  Home,
  ExternalLink,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Loader2,
  Image,
  FileText,
  Building2,
  MapPin,
  TrendingUp,
  ShieldCheck,
  Camera,
  Search,
  Info,
} from 'lucide-react';

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface Avvik {
  type: string;
  beskrivelse: string;
  alvorlighetsgrad: 'LAV' | 'MIDDELS' | 'HØY';
  anbefaling: string;
}

interface BygningsAnalyse {
  type: string;
  stil: string;
  tilstand: string;
  materialer: string[];
  tak: string;
}

interface PlantegningAnalyse {
  funnet: boolean;
  soverom: number;
  bad: number;
  kjeller: boolean;
  loft: boolean;
  spesielleRom: string[];
}

interface Forbedring {
  type: string;
  beskrivelse: string;
  estimertKostnad: string;
  verdiøkning: string;
  roi: string;
}

interface MatrikkelSammenligning {
  felt: string;
  annonsert: string;
  matrikkel: string;
  avvik: boolean;
}

interface AnalyseResultat {
  tittel: string;
  pris: string;
  adresse: string;
  nøkkelinfo: { label: string; verdi: string }[];
  antallBilder: number;
  finnUrl: string;
  risikoNivå: 'LAV' | 'MIDDELS' | 'HØY';
  avvik: Avvik[];
  bygningsAnalyse: BygningsAnalyse;
  plantegningAnalyse: PlantegningAnalyse;
  plantegningAvvik: string[];
  sammendrag: string;
  styrker: string[];
  svakheter: string[];
  kjøperAnbefaling: string;
  oppussingsbehov: string;
  forbedringer: Forbedring[];
  matrikkelData: MatrikkelSammenligning[];
  knr: string;
  gnr: string;
  bnr: string;
}

/* ------------------------------------------------------------------ */
/*  Mock data                                                          */
/* ------------------------------------------------------------------ */

const MOCK_RESULTAT: AnalyseResultat = {
  tittel: 'Pen enebolig med stor hage og garasje – Sentralt og barnevennlig',
  pris: '5 490 000 kr',
  adresse: 'Eksempelveien 42, 1234 Eksempelby',
  nøkkelinfo: [
    { label: 'Primærrom', verdi: '142 m²' },
    { label: 'Bruksareal', verdi: '168 m²' },
    { label: 'Soverom', verdi: '4' },
    { label: 'Byggeår', verdi: '1987' },
    { label: 'Tomteareal', verdi: '652 m²' },
    { label: 'Eierform', verdi: 'Selveier' },
  ],
  antallBilder: 34,
  finnUrl: 'https://www.finn.no/realestate/homes/ad.html?finnkode=123456789',
  risikoNivå: 'MIDDELS',
  avvik: [
    {
      type: 'AREAL_AVVIK',
      beskrivelse: 'Annonsert primærrom (142 m²) avviker fra matrikkeldata (128 m²) med 14 m².',
      alvorlighetsgrad: 'HØY',
      anbefaling: 'Be om takstrapport og sjekk om tilleggsareal (f.eks. kjeller) er godkjent som P-rom.',
    },
    {
      type: 'FERDIGATTEST_MANGLER',
      beskrivelse: 'Ingen registrert ferdigattest for tilbygg godkjent i 2015.',
      alvorlighetsgrad: 'MIDDELS',
      anbefaling: 'Kontakt kommunen for å avklare status. Selger bør fremskaffe ferdigattest før salg.',
    },
    {
      type: 'ROMTALL_AVVIK',
      beskrivelse: 'Plantegning viser 5 soverom, men annonsen oppgir 4.',
      alvorlighetsgrad: 'LAV',
      anbefaling: 'Avklar om det femte rommet brukes som kontor eller om det ikke oppfyller krav til soverom.',
    },
  ],
  bygningsAnalyse: {
    type: 'Enebolig',
    stil: 'Funkis / Modernisme',
    tilstand: 'God, noe slitasje utvendig',
    materialer: ['Trekledning', 'Teglstein (gavlvegg)', 'Betongfundament'],
    tak: 'Skråtak med betongtakstein, alder ca. 20 år',
  },
  plantegningAnalyse: {
    funnet: true,
    soverom: 5,
    bad: 2,
    kjeller: true,
    loft: false,
    spesielleRom: ['Vaskerom', 'Kontor', 'Bod under trapp'],
  },
  plantegningAvvik: [
    'Plantegning viser 5 soverom, annonsen oppgir 4',
    'Kjeller er markert på plantegning men ikke nevnt i annonsetekst',
  ],
  sammendrag:
    'Eneboligen fremstår som et solid familiehjem med god planløsning og stor tomt. Boligen har gjennomgått oppgradering av bad og kjøkken. Det er imidlertid avvik mellom annonsert areal og matrikkeldata som bør avklares.',
  styrker: [
    'Stor, solrik hage med gode utemuligheter',
    'Nytt kjøkken og bad (2019)',
    'Garasje med god lagringsplass',
    'Barnevennlig nabolag nær skole',
    'Lav fellesgjeld / ingen fellesutgifter',
  ],
  svakheter: [
    'Arealavvik på 14 m² mot matrikkel',
    'Mangler ferdigattest for tilbygg',
    'Taket nærmer seg forventet levetid',
    'Noe slitasje på utvendig kledning',
  ],
  kjøperAnbefaling:
    'Boligen har godt potensial, men vi anbefaler å avklare arealavviket og ferdigattest-status før bud. Innhent takstrapport med spesielt fokus på tilbygget fra 2015.',
  oppussingsbehov: 'Moderat',
  forbedringer: [
    {
      type: 'Tak',
      beskrivelse: 'Bytte av takstein og membran',
      estimertKostnad: '180 000 – 250 000 kr',
      verdiøkning: '150 000 – 200 000 kr',
      roi: '70–80 %',
    },
    {
      type: 'Utvendig kledning',
      beskrivelse: 'Male og reparere trekledning',
      estimertKostnad: '80 000 – 120 000 kr',
      verdiøkning: '100 000 – 150 000 kr',
      roi: '110–125 %',
    },
    {
      type: 'Energieffektivisering',
      beskrivelse: 'Etterisolering og varmepumpe',
      estimertKostnad: '120 000 – 180 000 kr',
      verdiøkning: '100 000 – 140 000 kr',
      roi: '75–85 %',
    },
    {
      type: 'Hage/uteområde',
      beskrivelse: 'Terrasse og beplantning',
      estimertKostnad: '60 000 – 100 000 kr',
      verdiøkning: '80 000 – 130 000 kr',
      roi: '120–130 %',
    },
  ],
  matrikkelData: [
    { felt: 'Primærrom (P-rom)', annonsert: '142 m²', matrikkel: '128 m²', avvik: true },
    { felt: 'Bruksareal (BRA)', annonsert: '168 m²', matrikkel: '165 m²', avvik: false },
    { felt: 'Byggeår', annonsert: '1987', matrikkel: '1987', avvik: false },
    { felt: 'Antall rom', annonsert: '7', matrikkel: '8', avvik: true },
    { felt: 'Ferdigattest', annonsert: 'Ikke oppgitt', matrikkel: 'Mangler (tilbygg 2015)', avvik: true },
  ],
  knr: '3024',
  gnr: '45',
  bnr: '123',
};

/* ------------------------------------------------------------------ */
/*  Loading steps                                                      */
/* ------------------------------------------------------------------ */

const LOADING_STEPS = [
  'Henter annonsedata...',
  'Analyserer bilder...',
  'Sammenligner med matrikkel...',
];

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function FinnAnalysePage() {
  const [url, setUrl] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [loadingStep, setLoadingStep] = React.useState(0);
  const [resultat, setResultat] = React.useState<AnalyseResultat | null>(null);

  React.useEffect(() => {
    document.title = 'Finn.no Boliganalyse | nops.no';
  }, []);

  const handleAnalyse = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setResultat(null);
    setLoadingStep(0);

    for (let i = 0; i < LOADING_STEPS.length; i++) {
      setLoadingStep(i);
      await new Promise((r) => setTimeout(r, 1200));
    }

    setResultat(MOCK_RESULTAT);
    setLoading(false);
  };

  const risikoFarge = (nivå: 'LAV' | 'MIDDELS' | 'HØY') => {
    switch (nivå) {
      case 'LAV':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'MIDDELS':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'HØY':
        return 'bg-red-100 text-red-800 border-red-300';
    }
  };

  const alvorlighetFarge = (grad: 'LAV' | 'MIDDELS' | 'HØY') => {
    switch (grad) {
      case 'LAV':
        return 'bg-green-50 text-green-700';
      case 'MIDDELS':
        return 'bg-yellow-50 text-yellow-700';
      case 'HØY':
        return 'bg-red-50 text-red-700';
    }
  };

  return (
    <main className="min-h-screen bg-slate-50">
      {/* ---- Header ---- */}
      <section className="bg-gradient-to-br from-orange-500 to-red-600 text-white py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <span className="inline-flex items-center gap-2 rounded-full bg-white/20 backdrop-blur px-4 py-1.5 text-sm font-medium mb-6">
            <Home className="h-4 w-4" />
            nops.no / Finn.no Analyse
          </span>
          <h1 className="text-3xl sm:text-5xl font-bold mb-4">
            Analyser enhver boligannonse med AI
          </h1>
          <p className="text-lg sm:text-xl text-orange-100 max-w-2xl mx-auto mb-6">
            Lim inn en Finn.no-lenke og få øyeblikkelig innsikt: avvik, risiko, muligheter og
            komplett eiendomsrapport.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-sm">
              <Camera className="h-3.5 w-3.5" />
              Automatisk bildeanalyse
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-sm">
              <AlertTriangle className="h-3.5 w-3.5" />
              Avviksdeteksjon
            </span>
          </div>
        </div>
      </section>

      {/* ---- Input ---- */}
      <section className="max-w-3xl mx-auto px-4 -mt-8 relative z-10">
        <div className="rounded-2xl border border-slate-200 bg-white shadow-lg p-6 sm:p-8">
          <label htmlFor="finn-url" className="block text-sm font-semibold text-slate-700 mb-2">
            Lim inn Finn.no-annonselenke
          </label>
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <ExternalLink className="absolute left-3.5 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
              <input
                id="finn-url"
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://www.finn.no/realestate/homes/ad.html?finnkode=..."
                className="w-full rounded-xl border border-slate-300 bg-slate-50 pl-11 pr-4 py-3.5 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition"
                onKeyDown={(e) => e.key === 'Enter' && handleAnalyse()}
              />
            </div>
            <button
              type="button"
              onClick={handleAnalyse}
              disabled={loading || !url.trim()}
              className={cn(
                'inline-flex items-center justify-center gap-2 rounded-xl px-6 py-3.5 text-sm font-semibold text-white transition-all',
                loading || !url.trim()
                  ? 'bg-slate-300 cursor-not-allowed'
                  : 'bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 shadow-md hover:shadow-lg'
              )}
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              {loading ? 'Analyserer...' : 'Analyser annonse'}
            </button>
          </div>
          <p className="mt-3 text-xs text-slate-400 text-center">
            Fungerer med alle Finn.no boligannonser
          </p>
        </div>
      </section>

      {/* ---- Loading state ---- */}
      {loading && (
        <section className="max-w-3xl mx-auto px-4 mt-8">
          <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center">
            <Loader2 className="h-8 w-8 animate-spin text-orange-500 mx-auto mb-4" />
            <p className="text-sm font-medium text-slate-700">{LOADING_STEPS[loadingStep]}</p>
            <div className="flex items-center justify-center gap-2 mt-4">
              {LOADING_STEPS.map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    'h-2 w-2 rounded-full transition-colors',
                    i <= loadingStep ? 'bg-orange-500' : 'bg-slate-200'
                  )}
                />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ---- Resultat ---- */}
      {resultat && (
        <div className="max-w-5xl mx-auto px-4 py-10 space-y-8">
          {/* 1. Annonse-sammendrag */}
          <section className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6 sm:p-8">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
              <div>
                <h2 className="text-xl font-bold text-slate-900 mb-1">{resultat.tittel}</h2>
                <p className="flex items-center gap-1.5 text-sm text-slate-500">
                  <MapPin className="h-4 w-4" />
                  {resultat.adresse}
                </p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-slate-900">{resultat.pris}</p>
                <a
                  href={resultat.finnUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-orange-600 hover:underline mt-1"
                >
                  Se på Finn.no <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </div>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              {resultat.nøkkelinfo.map((info) => (
                <div key={info.label} className="rounded-xl bg-slate-50 border border-slate-100 px-3 py-2.5 text-center">
                  <p className="text-xs text-slate-500">{info.label}</p>
                  <p className="text-sm font-semibold text-slate-900">{info.verdi}</p>
                </div>
              ))}
            </div>
            <p className="mt-4 flex items-center gap-1.5 text-xs text-slate-400">
              <Image className="h-3.5 w-3.5" />
              {resultat.antallBilder} bilder funnet i annonsen
            </p>
          </section>

          {/* 2. Avviksrapport */}
          <section className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6 sm:p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-slate-600" />
                Avviksrapport
              </h2>
              <span
                className={cn(
                  'inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold',
                  risikoFarge(resultat.risikoNivå)
                )}
              >
                <AlertTriangle className="h-3.5 w-3.5" />
                Risiko: {resultat.risikoNivå}
              </span>
            </div>

            {resultat.avvik.length === 0 ? (
              <div className="rounded-xl bg-green-50 border border-green-200 p-4 flex items-center gap-3">
                <CheckCircle2 className="h-5 w-5 text-green-600 shrink-0" />
                <p className="text-sm font-medium text-green-800">
                  Ingen vesentlige avvik funnet
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {resultat.avvik.map((a, i) => (
                  <div
                    key={i}
                    className="rounded-xl border border-slate-200 p-4 hover:border-slate-300 transition-colors"
                  >
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 text-xs font-mono font-semibold text-slate-700">
                        {a.type}
                      </span>
                      <span
                        className={cn(
                          'inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold',
                          alvorlighetFarge(a.alvorlighetsgrad)
                        )}
                      >
                        {a.alvorlighetsgrad}
                      </span>
                    </div>
                    <p className="text-sm text-slate-700 mb-2">{a.beskrivelse}</p>
                    <p className="text-sm text-slate-500 flex items-start gap-1.5">
                      <Info className="h-4 w-4 shrink-0 mt-0.5" />
                      {a.anbefaling}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* 3. Bildeanalyse */}
          <section className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6 sm:p-8">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-6">
              <Camera className="h-5 w-5 text-slate-600" />
              Bildeanalyse
            </h2>

            <div className="grid sm:grid-cols-2 gap-6">
              {/* Bygningsanalyse */}
              <div className="rounded-xl border border-slate-200 p-5">
                <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                  <Building2 className="h-4 w-4 text-slate-500" />
                  Bygningsanalyse
                </h3>
                <dl className="space-y-2 text-sm">
                  {[
                    ['Type', resultat.bygningsAnalyse.type],
                    ['Stil', resultat.bygningsAnalyse.stil],
                    ['Tilstand', resultat.bygningsAnalyse.tilstand],
                    ['Materialer', resultat.bygningsAnalyse.materialer.join(', ')],
                    ['Tak', resultat.bygningsAnalyse.tak],
                  ].map(([label, value]) => (
                    <div key={label} className="flex justify-between gap-4">
                      <dt className="text-slate-500">{label}</dt>
                      <dd className="text-right font-medium text-slate-700">{value}</dd>
                    </div>
                  ))}
                </dl>
              </div>

              {/* Plantegning-analyse */}
              <div className="rounded-xl border border-slate-200 p-5">
                <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                  <FileText className="h-4 w-4 text-slate-500" />
                  Plantegning-analyse
                </h3>
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-slate-500">Plantegning funnet</dt>
                    <dd>
                      {resultat.plantegningAnalyse.funnet ? (
                        <span className="text-green-600 font-medium">Ja</span>
                      ) : (
                        <span className="text-red-600 font-medium">Nei</span>
                      )}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-500">Soverom</dt>
                    <dd className="font-medium text-slate-700">{resultat.plantegningAnalyse.soverom}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-500">Bad</dt>
                    <dd className="font-medium text-slate-700">{resultat.plantegningAnalyse.bad}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-500">Kjeller</dt>
                    <dd className="font-medium text-slate-700">{resultat.plantegningAnalyse.kjeller ? 'Ja' : 'Nei'}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-500">Loft</dt>
                    <dd className="font-medium text-slate-700">{resultat.plantegningAnalyse.loft ? 'Ja' : 'Nei'}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-500">Spesielle rom</dt>
                    <dd className="text-right font-medium text-slate-700">
                      {resultat.plantegningAnalyse.spesielleRom.join(', ')}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>

            {/* Avvik mellom plantegning og bilder */}
            {resultat.plantegningAvvik.length > 0 && (
              <div className="mt-4 rounded-xl bg-yellow-50 border border-yellow-200 p-4">
                <h4 className="text-sm font-semibold text-yellow-800 mb-2 flex items-center gap-1.5">
                  <AlertTriangle className="h-4 w-4" />
                  Avvik mellom plantegning og bilder
                </h4>
                <ul className="space-y-1">
                  {resultat.plantegningAvvik.map((avvik, i) => (
                    <li key={i} className="text-sm text-yellow-700 flex items-start gap-2">
                      <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-yellow-500 shrink-0" />
                      {avvik}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>

          {/* 4. Eiendomsoppsummering */}
          <section className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6 sm:p-8">
            <h2 className="text-lg font-bold text-slate-900 mb-2">Eiendomsoppsummering</h2>
            <p className="text-sm text-slate-600 mb-6">{resultat.sammendrag}</p>

            <div className="grid sm:grid-cols-2 gap-6 mb-6">
              {/* Styrker */}
              <div>
                <h3 className="text-sm font-semibold text-green-700 mb-3">Styrker</h3>
                <ul className="space-y-2">
                  {resultat.styrker.map((s, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                      <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0 mt-0.5" />
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
              {/* Svakheter */}
              <div>
                <h3 className="text-sm font-semibold text-red-700 mb-3">Svakheter</h3>
                <ul className="space-y-2">
                  {resultat.svakheter.map((s, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                      <XCircle className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="rounded-xl bg-blue-50 border border-blue-200 p-4 mb-4">
              <h4 className="text-sm font-semibold text-blue-800 mb-1">Anbefaling for kjøper</h4>
              <p className="text-sm text-blue-700">{resultat.kjøperAnbefaling}</p>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Oppussingsbehov:</span>
              <span className="inline-flex items-center rounded-full bg-orange-100 text-orange-700 border border-orange-200 px-3 py-0.5 text-xs font-semibold">
                {resultat.oppussingsbehov}
              </span>
            </div>
          </section>

          {/* 5. Forbedringspotensial */}
          <section className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6 sm:p-8">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-6">
              <TrendingUp className="h-5 w-5 text-slate-600" />
              Forbedringspotensial
            </h2>
            <div className="grid sm:grid-cols-2 gap-4">
              {resultat.forbedringer.map((f, i) => (
                <div key={i} className="rounded-xl border border-slate-200 p-5 hover:border-slate-300 transition-colors">
                  <h3 className="text-sm font-semibold text-slate-900 mb-2">{f.type}</h3>
                  <p className="text-sm text-slate-600 mb-3">{f.beskrivelse}</p>
                  <dl className="space-y-1.5 text-xs">
                    <div className="flex justify-between">
                      <dt className="text-slate-500">Estimert kostnad</dt>
                      <dd className="font-medium text-slate-700">{f.estimertKostnad}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-slate-500">Verdiøkning</dt>
                      <dd className="font-medium text-green-700">{f.verdiøkning}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-slate-500">ROI</dt>
                      <dd className="font-semibold text-orange-600">{f.roi}</dd>
                    </div>
                  </dl>
                </div>
              ))}
            </div>
          </section>

          {/* 6. Matrikkeldata-sammenligning */}
          <section className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6 sm:p-8">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-6">
              <FileText className="h-5 w-5 text-slate-600" />
              Matrikkeldata-sammenligning
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-3 px-4 font-semibold text-slate-600">Felt</th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-600">Annonsert</th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-600">Matrikkel (offentlig)</th>
                    <th className="text-center py-3 px-4 font-semibold text-slate-600">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {resultat.matrikkelData.map((rad, i) => (
                    <tr
                      key={i}
                      className={cn(
                        'border-b border-slate-100',
                        rad.avvik && 'bg-yellow-50'
                      )}
                    >
                      <td className="py-3 px-4 font-medium text-slate-700">{rad.felt}</td>
                      <td className="py-3 px-4 text-slate-600">{rad.annonsert}</td>
                      <td className="py-3 px-4 text-slate-600">{rad.matrikkel}</td>
                      <td className="py-3 px-4 text-center">
                        {rad.avvik ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-red-100 text-red-700 px-2 py-0.5 text-xs font-semibold">
                            <AlertTriangle className="h-3 w-3" />
                            Avvik
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full bg-green-100 text-green-700 px-2 py-0.5 text-xs font-semibold">
                            <CheckCircle2 className="h-3 w-3" />
                            OK
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* 7. CTA-bunn */}
          <section className="rounded-2xl bg-gradient-to-br from-orange-500 to-red-600 p-8 text-center text-white">
            <h2 className="text-xl font-bold mb-2">Vil du vite mer?</h2>
            <p className="text-orange-100 mb-6">
              Se full eiendomsanalyse eller kontakt oss for profesjonell vurdering.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link
                href={`/property?knr=${resultat.knr}&gnr=${resultat.gnr}&bnr=${resultat.bnr}`}
                className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-sm font-semibold text-orange-600 hover:bg-orange-50 transition-colors"
              >
                Se full eiendomsanalyse i ByggSjekk
                <ArrowRight className="h-4 w-4" />
              </Link>
              <a
                href="mailto:hey@nops.no"
                className="inline-flex items-center gap-2 rounded-xl border-2 border-white/40 px-6 py-3 text-sm font-semibold text-white hover:bg-white/10 transition-colors"
              >
                Kontakt oss for profesjonell vurdering
              </a>
            </div>
          </section>
        </div>
      )}

      {/* ---- Slik fungerer det ---- */}
      <section className="bg-white border-t border-slate-200 py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-slate-900 text-center mb-10">Slik fungerer det</h2>
          <div className="grid sm:grid-cols-3 gap-8">
            {[
              {
                step: '1',
                icon: <ExternalLink className="h-6 w-6" />,
                title: 'Lim inn Finn-lenken',
                desc: 'Vi henter all data automatisk fra boligannonsen.',
              },
              {
                step: '2',
                icon: <Sparkles className="h-6 w-6" />,
                title: 'AI analyserer alt',
                desc: 'Bilder, plantegninger og data sammenlignes med offentlige registre.',
              },
              {
                step: '3',
                icon: <FileText className="h-6 w-6" />,
                title: 'Få komplett rapport',
                desc: 'Avvik, risiko og muligheter presentert oversiktlig.',
              },
            ].map((s) => (
              <div key={s.step} className="text-center">
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-orange-100 text-orange-600">
                  {s.icon}
                </div>
                <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-orange-500 text-white text-xs font-bold mb-2">
                  {s.step}
                </span>
                <h3 className="text-base font-semibold text-slate-900 mb-1">{s.title}</h3>
                <p className="text-sm text-slate-500">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---- Hva vi sjekker ---- */}
      <section className="bg-slate-50 py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-slate-900 text-center mb-10">Hva vi sjekker</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              {
                icon: <Search className="h-5 w-5" />,
                title: 'Areal-avvik',
                desc: 'Annonsert areal sammenlignes med matrikkeldata',
              },
              {
                icon: <FileText className="h-5 w-5" />,
                title: 'Plantegning-analyse',
                desc: 'Rom, layout og arealer fra plantegning',
              },
              {
                icon: <ShieldCheck className="h-5 w-5" />,
                title: 'Ferdigattest-status',
                desc: 'Sjekker om alle byggetiltak har ferdigattest',
              },
              {
                icon: <Building2 className="h-5 w-5" />,
                title: 'Byggesakshistorikk',
                desc: 'Oversikt over alle byggesaker på eiendommen',
              },
              {
                icon: <TrendingUp className="h-5 w-5" />,
                title: 'Forbedringspotensial',
                desc: 'Estimater for oppgradering og verdiøkning',
              },
              {
                icon: <MapPin className="h-5 w-5" />,
                title: 'Prisvurdering vs marked',
                desc: 'Sammenligning med lignende boliger i området',
              },
            ].map((item) => (
              <div
                key={item.title}
                className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-orange-100 text-orange-600 shrink-0">
                  {item.icon}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">{item.title}</h3>
                  <p className="text-xs text-slate-500 mt-0.5">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
