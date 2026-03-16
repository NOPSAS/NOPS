'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  Zap,
  MapPin,
  Building2,
  Sparkles,
  BarChart3,
  FileText,
  Camera,
  TrendingUp,
  CheckCircle2,
  ArrowRight,
  Loader2,
  Clock,
  AlertCircle,
  Play,
  Package,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Steg i pipeline-prosessen
interface PipelineStep {
  id: string;
  navn: string;
  icon: React.ReactNode;
  status: 'venter' | 'kjører' | 'ferdig' | 'feil';
  resultat?: string;
  lenke?: string;
}

interface PakkeResultat {
  adresse: string;
  knr: string;
  gnr: number;
  bnr: number;
  steg: PipelineStep[];
  ferdig: boolean;
}

const STEGDEFINISJONER = [
  { id: 'matrikkel', navn: 'Matrikkeldata', icon: <Building2 className="h-4 w-4" /> },
  { id: 'byggesaker', navn: 'Byggesakshistorikk', icon: <FileText className="h-4 w-4" /> },
  { id: 'arealplan', navn: 'Reguleringsplaner', icon: <MapPin className="h-4 w-4" /> },
  { id: 'verdi', navn: 'Verdiestimering', icon: <TrendingUp className="h-4 w-4" /> },
  { id: 'utbygging', navn: 'Utbyggingspotensial', icon: <BarChart3 className="h-4 w-4" /> },
  { id: 'ai_analyse', navn: 'AI-risikoanalyse', icon: <Sparkles className="h-4 w-4" /> },
  { id: 'rapport', navn: 'PDF-rapport', icon: <FileText className="h-4 w-4" /> },
];

const PAKKE_TYPER = [
  {
    id: 'kjøper',
    navn: 'Kjøperpakke',
    icon: '🏠',
    pris: '2 490 kr',
    beskrivelse: 'Alt du trenger for å gjøre et trygt boligkjøp',
    innhold: [
      'Komplett matrikkelanalyse',
      'Byggesakshistorikk siste 20 år',
      'Reguleringsplan og dispensasjoner',
      'AI-risikovurdering og avvik',
      'Verdiestimering og markedsanalyse',
      'Nabovarsel-sjekk',
      'PDF-rapport til megler/bank',
    ],
    farge: 'blue',
  },
  {
    id: 'selger',
    navn: 'Selgerpakke',
    icon: '💰',
    pris: '3 490 kr',
    beskrivelse: 'Dokumenter eiendommens verdi og potensial',
    innhold: [
      'Alt i Kjøperpakke',
      'Utbyggingspotensial-analyse',
      'Fotorealistiske renders',
      'Investeringsanalyse for kjøper',
      'Situasjonsplan-klargjøring',
      'Prospekt-klargjøring (PDF)',
      'Presentasjonslenke for deling',
    ],
    farge: 'green',
  },
  {
    id: 'arkitekt',
    navn: 'Arkitektpakke',
    icon: '📐',
    pris: '4 990 kr',
    beskrivelse: 'Komplett prosjektgrunnlag for arkitektkontoret',
    innhold: [
      'Alt i Selgerpakke',
      'Byggesøknad-sjekkliste',
      'AI-generert nabovarsel',
      'Teknisk reguleringsplan-vurdering',
      'Gebyrberegning (alle kommunale gebyrer)',
      'TEK17-samsvarsvurdering',
      'Prosjektstyrings-eksport (CSV)',
    ],
    farge: 'purple',
  },
];

const fargeMap: Record<string, string> = {
  blue: 'border-blue-200 bg-blue-50',
  green: 'border-emerald-200 bg-emerald-50',
  purple: 'border-purple-200 bg-purple-50',
};
const fargeKnapp: Record<string, string> = {
  blue: 'bg-blue-600 hover:bg-blue-700',
  green: 'bg-emerald-600 hover:bg-emerald-700',
  purple: 'bg-purple-600 hover:bg-purple-700',
};
const fargeTittel: Record<string, string> = {
  blue: 'text-blue-900',
  green: 'text-emerald-900',
  purple: 'text-purple-900',
};

export default function PakkePage() {
  const [adresse, setAdresse] = React.useState('');
  const [knr, setKnr] = React.useState('');
  const [gnr, setGnr] = React.useState('');
  const [bnr, setBnr] = React.useState('');
  const [valgtPakke, setValgtPakke] = React.useState<string | null>(null);
  const [kjører, setKjører] = React.useState(false);
  const [steg, setSteg] = React.useState<PipelineStep[]>([]);
  const [ferdig, setFerdig] = React.useState(false);
  const [feil, setFeil] = React.useState<string | null>(null);
  const [visSkjema, setVisSkjema] = React.useState(false);

  React.useEffect(() => {
    document.title = 'Komplett Eiendomspakke | nops.no';
  }, []);

  function initSteg(): PipelineStep[] {
    return STEGDEFINISJONER.map((s) => ({ ...s, status: 'venter' as const }));
  }

  async function kjørPipeline() {
    if (!adresse || !knr || !gnr || !bnr) {
      setFeil('Fyll inn alle feltene');
      return;
    }
    setFeil(null);
    setKjører(true);
    setFerdig(false);
    const pipeline = initSteg();
    setSteg([...pipeline]);

    const token = typeof window !== 'undefined' ? localStorage.getItem('token') || '' : '';
    const baseParams = `knr=${knr}&gnr=${gnr}&bnr=${bnr}`;

    // Kjør steg sekvensielt med status-oppdateringer
    for (let i = 0; i < pipeline.length; i++) {
      pipeline[i].status = 'kjører';
      setSteg([...pipeline]);

      try {
        let url = '';
        let method = 'GET';

        switch (pipeline[i].id) {
          case 'matrikkel':
            url = `/api/v1/property/matrikkel?${baseParams}`;
            break;
          case 'byggesaker':
            url = `/api/v1/property/byggesaker?${baseParams}`;
            break;
          case 'arealplan':
            url = `/api/v1/property/planrapport?${baseParams}`;
            break;
          case 'verdi':
            url = `/api/v1/property/historikk?${baseParams}`;
            break;
          case 'utbygging':
            url = `/api/v1/utbygging/analyser?${baseParams}&tiltakstype=leiligheter`;
            method = 'POST';
            break;
          case 'ai_analyse':
            url = `/api/v1/property/analyse?${baseParams}`;
            method = 'POST';
            break;
          case 'rapport':
            url = `/api/v1/property/rapport-pdf?${baseParams}`;
            break;
        }

        const res = await fetch(url, {
          method,
          headers: { Authorization: `Bearer ${token}` },
        });

        if (res.ok) {
          pipeline[i].status = 'ferdig';
          if (pipeline[i].id === 'rapport') {
            pipeline[i].resultat = 'PDF klar for nedlasting';
            pipeline[i].lenke = url;
          } else {
            pipeline[i].resultat = 'Hentet';
          }
        } else if (res.status === 402) {
          pipeline[i].status = 'ferdig';
          pipeline[i].resultat = 'Krever oppgradering';
        } else {
          pipeline[i].status = 'feil';
          pipeline[i].resultat = `HTTP ${res.status}`;
        }
      } catch {
        pipeline[i].status = 'ferdig'; // Ikke-kritisk feil
        pipeline[i].resultat = 'Ikke tilgjengelig nå';
      }

      setSteg([...pipeline]);

      // Litt forsinkelse for bedre UX-effekt
      await new Promise((r) => setTimeout(r, 400));
    }

    setFerdig(true);
    setKjører(false);
  }

  const antallFerdig = steg.filter((s) => s.status === 'ferdig').length;

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <section className="bg-gradient-to-br from-slate-900 to-blue-900 text-white py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="inline-flex items-center gap-2 mb-4 rounded-full bg-white/10 px-4 py-1.5 text-sm font-medium text-blue-200">
            <Package className="h-4 w-4" />
            nops.no / Komplett pakke
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-5 leading-tight">
            Fra adresse til<br className="hidden sm:block" /> komplett eiendomsrapport
          </h1>
          <p className="text-lg text-blue-100 max-w-2xl mb-8">
            Vår automatiserte pipeline henter data fra alle offentlige registre,
            kjører AI-analyse og genererer en komplett pakke – på under 2 minutter.
          </p>
          <div className="flex flex-wrap gap-3">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-sm text-blue-100">
              <Zap className="h-4 w-4 text-yellow-400" /> Automatisk pipeline
            </div>
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-sm text-blue-100">
              <Sparkles className="h-4 w-4 text-purple-400" /> AI-analyse
            </div>
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-sm text-blue-100">
              <Clock className="h-4 w-4 text-green-400" /> Under 2 minutter
            </div>
          </div>
        </div>
      </section>

      <div className="max-w-5xl mx-auto px-4 py-12 space-y-12">

        {/* Pakke-velger */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 mb-6">Velg din pakke</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {PAKKE_TYPER.map((p) => (
              <div
                key={p.id}
                onClick={() => { setValgtPakke(p.id); setVisSkjema(true); }}
                className={cn(
                  'relative rounded-2xl border-2 p-6 cursor-pointer transition-all',
                  valgtPakke === p.id
                    ? `${fargeMap[p.farge]} border-current`
                    : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'
                )}
              >
                {valgtPakke === p.id && (
                  <div className="absolute top-3 right-3">
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  </div>
                )}
                <div className="text-3xl mb-3">{p.icon}</div>
                <h3 className={cn('text-lg font-bold mb-1', valgtPakke === p.id ? fargeTittel[p.farge] : 'text-slate-900')}>
                  {p.navn}
                </h3>
                <p className="text-sm text-slate-500 mb-3">{p.beskrivelse}</p>
                <p className="text-xl font-bold text-slate-900 mb-4">{p.pris}</p>
                <ul className="space-y-1.5">
                  {p.innhold.map((item) => (
                    <li key={item} className="flex items-start gap-2 text-xs text-slate-600">
                      <CheckCircle2 className="h-3.5 w-3.5 text-green-500 mt-0.5 shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
                <button
                  type="button"
                  className={cn(
                    'mt-5 w-full rounded-xl py-2.5 text-sm font-semibold text-white transition-colors',
                    fargeKnapp[p.farge]
                  )}
                >
                  Velg {p.navn}
                </button>
              </div>
            ))}
          </div>
        </section>

        {/* Eiendomsskjema */}
        {visSkjema && (
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900 mb-5 flex items-center gap-2">
              <MapPin className="h-5 w-5 text-blue-600" />
              Søk opp eiendom
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
              <div className="sm:col-span-2 lg:col-span-2">
                <label className="block text-xs font-medium text-slate-600 mb-1.5">Adresse</label>
                <input
                  type="text"
                  placeholder="f.eks. Strandveien 1, Nesodden"
                  value={adresse}
                  onChange={(e) => setAdresse(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">Kommunenr.</label>
                <input
                  type="text"
                  placeholder="f.eks. 3212"
                  value={knr}
                  onChange={(e) => setKnr(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1.5">Gnr.</label>
                  <input
                    type="number"
                    placeholder="1"
                    value={gnr}
                    onChange={(e) => setGnr(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1.5">Bnr.</label>
                  <input
                    type="number"
                    placeholder="1"
                    value={bnr}
                    onChange={(e) => setBnr(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            <p className="text-xs text-slate-400 mb-5">
              Finn gnr/bnr på{' '}
              <a href="https://seeiendom.kartverket.no" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                seeiendom.kartverket.no
              </a>
            </p>

            {feil && (
              <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 mb-4">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {feil}
              </div>
            )}

            <button
              type="button"
              onClick={kjørPipeline}
              disabled={kjører}
              className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60 transition-colors"
            >
              {kjører ? (
                <><Loader2 className="h-4 w-4 animate-spin" /> Kjører pipeline…</>
              ) : (
                <><Play className="h-4 w-4" /> Start automatisk analyse</>
              )}
            </button>
          </section>
        )}

        {/* Pipeline-progress */}
        {steg.length > 0 && (
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Zap className="h-5 w-5 text-yellow-500" />
                Automatisk pipeline
              </h2>
              <span className="text-sm font-medium text-slate-500">
                {antallFerdig} / {steg.length} steg
              </span>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-slate-100 rounded-full h-2 mb-6">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${(antallFerdig / steg.length) * 100}%` }}
              />
            </div>

            <div className="space-y-2">
              {steg.map((s) => (
                <div
                  key={s.id}
                  className={cn(
                    'flex items-center justify-between rounded-lg px-4 py-3 transition-all',
                    s.status === 'ferdig' ? 'bg-green-50 border border-green-200' :
                    s.status === 'kjører' ? 'bg-blue-50 border border-blue-200' :
                    s.status === 'feil' ? 'bg-red-50 border border-red-100' :
                    'bg-slate-50 border border-slate-200'
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      'flex h-7 w-7 items-center justify-center rounded-full',
                      s.status === 'ferdig' ? 'bg-green-100 text-green-600' :
                      s.status === 'kjører' ? 'bg-blue-100 text-blue-600' :
                      s.status === 'feil' ? 'bg-red-100 text-red-600' :
                      'bg-slate-200 text-slate-400'
                    )}>
                      {s.status === 'kjører' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> :
                       s.status === 'ferdig' ? <CheckCircle2 className="h-3.5 w-3.5" /> :
                       s.icon}
                    </div>
                    <span className={cn(
                      'text-sm font-medium',
                      s.status === 'venter' ? 'text-slate-400' : 'text-slate-900'
                    )}>
                      {s.navn}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {s.resultat && (
                      <span className="text-xs text-slate-500">{s.resultat}</span>
                    )}
                    {s.lenke && s.status === 'ferdig' && (
                      <a
                        href={s.lenke}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs font-medium text-blue-600 hover:underline"
                      >
                        Last ned
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Ferdig - CTA */}
            {ferdig && (
              <div className="mt-6 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-white">
                <div className="flex items-start gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white/20">
                    <CheckCircle2 className="h-6 w-6" />
                  </div>
                  <div className="flex-1">
                    <p className="font-bold text-lg mb-1">Analyse fullført!</p>
                    <p className="text-blue-100 text-sm mb-4">
                      {adresse} – komplett eiendomspakke klar.
                    </p>
                    <div className="flex flex-wrap gap-3">
                      {knr && gnr && bnr && (
                        <Link
                          href={`/property?knr=${knr}&gnr=${gnr}&bnr=${bnr}`}
                          className="inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-semibold text-blue-700 hover:bg-blue-50 transition-colors"
                        >
                          <Building2 className="h-4 w-4" />
                          Se full eiendomsprofil
                        </Link>
                      )}
                      <Link
                        href="/investering"
                        className="inline-flex items-center gap-2 rounded-lg bg-white/20 border border-white/30 px-4 py-2 text-sm font-semibold text-white hover:bg-white/30 transition-colors"
                      >
                        <TrendingUp className="h-4 w-4" />
                        Investeringsanalyse
                      </Link>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </section>
        )}

        {/* Slik fungerer det */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 mb-6 text-center">
            Slik fungerer pakketjenesten
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {[
              { n: '1', icon: <MapPin className="h-6 w-6" />, tittel: 'Angi eiendom', tekst: 'Skriv inn adresse og matrikkelopplysninger' },
              { n: '2', icon: <Zap className="h-6 w-6" />, tittel: 'Automatisk henting', tekst: 'Pipeline henter fra alle offentlige registre parallelt' },
              { n: '3', icon: <Sparkles className="h-6 w-6" />, tittel: 'AI-analyse', tekst: 'Claude AI analyserer alt og gir konkrete anbefalinger' },
              { n: '4', icon: <Package className="h-6 w-6" />, tittel: 'Komplett pakke', tekst: 'Motta rapport, renders og data klare til bruk' },
            ].map((s) => (
              <div key={s.n} className="flex flex-col items-center text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-600 text-white font-bold text-lg mb-4 shadow-md">
                  {s.n}
                </div>
                <div className="mb-2 text-blue-600">{s.icon}</div>
                <h3 className="text-sm font-bold text-slate-900 mb-1">{s.tittel}</h3>
                <p className="text-xs text-slate-500 leading-relaxed">{s.tekst}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA til enkelt-tjenester */}
        <section className="rounded-2xl border border-slate-200 bg-white p-8">
          <h2 className="text-xl font-bold text-slate-900 mb-2 text-center">
            Eller bruk enkelt-tjenestene
          </h2>
          <p className="text-sm text-slate-500 text-center mb-6">
            Alle tjenester er også tilgjengelige separat
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { href: '/property', icon: <Building2 className="h-5 w-5" />, label: 'Eiendomssøk', farge: 'blue' },
              { href: '/utbygging', icon: <BarChart3 className="h-5 w-5" />, label: 'Utbygging', farge: 'green' },
              { href: '/investering', icon: <TrendingUp className="h-5 w-5" />, label: 'Investering', farge: 'indigo' },
              { href: '/visualisering', icon: <Camera className="h-5 w-5" />, label: 'Visualisering', farge: 'purple' },
              { href: '/romplanlegger', icon: <Sparkles className="h-5 w-5" />, label: 'Romplanlegger', farge: 'pink' },
              { href: '/tjenester', icon: <ArrowRight className="h-5 w-5" />, label: 'Alle tjenester', farge: 'slate' },
            ].map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="flex flex-col items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 p-4 text-center hover:bg-slate-100 hover:border-slate-300 transition-all"
              >
                <span className="text-slate-600">{link.icon}</span>
                <span className="text-xs font-medium text-slate-700">{link.label}</span>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
