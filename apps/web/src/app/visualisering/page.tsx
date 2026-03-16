'use client';

import * as React from 'react';
import type { Metadata } from 'next';
import Link from 'next/link';
import {
  Upload,
  Sparkles,
  ImageIcon,
  Loader2,
  Download,
  ArrowRight,
  Camera,
  Box,
  FileImage,
  Home,
  Layers,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const STILER = [
  { id: 'nordisk', label: 'Nordisk', desc: 'Minimalistisk, lyst tre, rent' },
  { id: 'moderne', label: 'Moderne', desc: 'Flatt tak, store vinduer' },
  { id: 'klassisk', label: 'Klassisk', desc: 'Tradisjonell norsk stil' },
  { id: 'industriell', label: 'Industriell', desc: 'Stål, betong, loft' },
  { id: 'naturlig', label: 'Naturlig', desc: 'Organisk, tømmer, jord' },
];

const BILDETYPE_INFO = [
  {
    id: 'foto',
    icon: <Camera className="h-5 w-5" />,
    label: 'Boligfoto',
    desc: 'Foto av eksisterende bygg',
  },
  {
    id: 'finn_annonse',
    icon: <Home className="h-5 w-5" />,
    label: 'Finn.no-bilde',
    desc: 'Bilde fra boligannonse',
  },
  {
    id: 'plantegning',
    icon: <Layers className="h-5 w-5" />,
    label: 'Plantegning',
    desc: 'Arkitektonisk plantegning',
  },
  {
    id: 'skisse',
    icon: <FileImage className="h-5 w-5" />,
    label: 'Skisse',
    desc: 'Håndtegnet skisse',
  },
  {
    id: 'fasade',
    icon: <Box className="h-5 w-5" />,
    label: 'Fasadetegning',
    desc: 'Teknisk fasadetegning',
  },
];

interface AnalyseResultat {
  bygningstype?: string;
  arkitekturstil?: string;
  byggeaar_estimat?: string;
  materialer?: string[];
  tilstand?: string;
  fasade_beskrivelse?: string;
  muligheter?: Array<{
    type: string;
    beskrivelse: string;
    kompleksitet: string;
    estimert_kostnad: string;
  }>;
  anbefalinger?: string[];
  arkitektoniske_styrker?: string[];
  arkitektoniske_utfordringer?: string[];
}

export default function VisualiseringPage() {
  const [fil, setFil] = React.useState<File | null>(null);
  const [forhåndsvisning, setForhåndsvisning] = React.useState<string | null>(null);
  const [bildetype, setBildetype] = React.useState('foto');
  const [ønsketEndring, setØnsketEndring] = React.useState('');
  const [stil, setStil] = React.useState('nordisk');
  const [loading, setLoading] = React.useState(false);
  const [renderLoading, setRenderLoading] = React.useState(false);
  const [analyse, setAnalyse] = React.useState<AnalyseResultat | null>(null);
  const [renderUrl, setRenderUrl] = React.useState<string | null>(null);
  const [feil, setFeil] = React.useState<string | null>(null);
  const [steg, setSteg] = React.useState<'last-opp' | 'analyser' | 'resultat'>('last-opp');

  const fileRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    document.title = 'AI Visualisering og Render | nops.no';
  }, []);

  function håndterFil(valgtFil: File) {
    if (!valgtFil.type.startsWith('image/')) {
      setFeil('Kun bilder støttes (JPEG, PNG, WebP)');
      return;
    }
    if (valgtFil.size > 10 * 1024 * 1024) {
      setFeil('Bildet er for stort. Maks 10 MB.');
      return;
    }
    setFil(valgtFil);
    setFeil(null);
    const reader = new FileReader();
    reader.onload = (e) => setForhåndsvisning(e.target?.result as string);
    reader.readAsDataURL(valgtFil);
    setSteg('analyser');
  }

  async function kjørAnalyse() {
    if (!fil) return;
    setLoading(true);
    setFeil(null);
    try {
      const form = new FormData();
      form.append('fil', fil);
      form.append('bildetype', bildetype);
      form.append('ønsket_endring', ønsketEndring);

      const res = await fetch('/api/v1/visualisering/analyser-bilde', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
        },
        body: form,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Analyse feilet');
      }
      const data = await res.json();
      setAnalyse(data.analyse);
      setSteg('resultat');
    } catch (e: unknown) {
      setFeil(e instanceof Error ? e.message : 'Ukjent feil');
    } finally {
      setLoading(false);
    }
  }

  async function genererRender() {
    setRenderLoading(true);
    setFeil(null);
    try {
      const form = new FormData();
      form.append('stil', stil);
      form.append('beskrivelse', analyse?.fasade_beskrivelse || ønsketEndring || 'Norwegian house');
      form.append('rom_type', 'utendørs');

      const res = await fetch('/api/v1/visualisering/generer-render', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
        },
        body: form,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Render feilet');
      }
      const data = await res.json();
      if (data.status === 'demo') {
        setFeil('Render-generering aktiveres snart. Bildeanalysen er klar.');
      } else {
        setRenderUrl(data.bilde_url);
      }
    } catch (e: unknown) {
      setFeil(e instanceof Error ? e.message : 'Ukjent feil');
    } finally {
      setRenderLoading(false);
    }
  }

  function nullstill() {
    setFil(null);
    setForhåndsvisning(null);
    setAnalyse(null);
    setRenderUrl(null);
    setFeil(null);
    setSteg('last-opp');
    setØnsketEndring('');
  }

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <section className="bg-gradient-to-br from-violet-600 to-purple-700 text-white py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 mb-4 rounded-full bg-white/10 px-4 py-1.5 text-sm font-medium text-purple-100">
            <Sparkles className="h-4 w-4" />
            nops.no / Visualisering
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mb-4">
            AI-visualisering og 3D-analyse
          </h1>
          <p className="text-lg text-purple-100 max-w-2xl">
            Last opp et bilde av ditt bygg, en skisse, plantegning eller Finn.no-annonse –
            og få en øyeblikkelig arkitektonisk analyse og fotorealistisk render.
          </p>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-4 py-10 space-y-6">

        {/* Steg 1: Last opp */}
        {steg === 'last-opp' && (
          <>
            {/* Bildetype-velger */}
            <div>
              <h2 className="text-sm font-semibold text-slate-700 mb-3">
                Hva vil du laste opp?
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                {BILDETYPE_INFO.map((bt) => (
                  <button
                    key={bt.id}
                    type="button"
                    onClick={() => setBildetype(bt.id)}
                    className={cn(
                      'flex flex-col items-center gap-2 rounded-xl border p-3 text-center transition-all',
                      bildetype === bt.id
                        ? 'border-purple-500 bg-purple-50 text-purple-700'
                        : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
                    )}
                  >
                    <span className={bildetype === bt.id ? 'text-purple-600' : 'text-slate-400'}>
                      {bt.icon}
                    </span>
                    <span className="text-xs font-medium">{bt.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Dropzone */}
            <div
              onClick={() => fileRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const dropped = e.dataTransfer.files[0];
                if (dropped) håndterFil(dropped);
              }}
              className="relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 bg-white p-12 text-center cursor-pointer hover:border-purple-400 hover:bg-purple-50/30 transition-colors"
            >
              <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-purple-100 mb-4">
                <Upload className="h-7 w-7 text-purple-600" />
              </div>
              <p className="text-base font-semibold text-slate-800 mb-1">
                Dra og slipp bilde her
              </p>
              <p className="text-sm text-slate-500">
                eller <span className="text-purple-600 font-medium">velg fra datamaskinen</span>
              </p>
              <p className="mt-3 text-xs text-slate-400">
                JPEG, PNG, WebP · Maks 10 MB
              </p>
              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) håndterFil(f);
                }}
              />
            </div>

            {feil && (
              <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {feil}
              </div>
            )}

            {/* Hva kan du bruke dette til */}
            <div className="rounded-xl border border-slate-200 bg-white p-6">
              <h3 className="font-semibold text-slate-900 mb-4 text-sm">Hva kan du bruke dette til?</h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {[
                  {
                    icon: <Camera className="h-5 w-5 text-purple-600" />,
                    title: 'Boliganalyse',
                    desc: 'Last opp bilder fra Finn.no og få umiddelbar analyse av bygningstype, stil og potensial',
                  },
                  {
                    icon: <Sparkles className="h-5 w-5 text-purple-600" />,
                    title: 'Render av tilbygg',
                    desc: 'Tegn opp tilbygget på papir, last det inn og se et fotorealistisk render av resultatet',
                  },
                  {
                    icon: <Box className="h-5 w-5 text-purple-600" />,
                    title: 'Plantegning til 3D',
                    desc: 'Last opp en plantegning og få en beskrivelse av volumet og anbefalinger for prosjektering',
                  },
                ].map((item) => (
                  <div key={item.title} className="flex gap-3">
                    <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-purple-50">
                      {item.icon}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-900">{item.title}</p>
                      <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {/* Steg 2: Analyser */}
        {steg === 'analyser' && (
          <div className="space-y-5">
            <div className="flex items-center gap-4">
              <div className="w-32 h-24 rounded-xl overflow-hidden border border-slate-200 shrink-0">
                {forhåndsvisning && (
                  <img src={forhåndsvisning} alt="Forhåndsvisning" className="w-full h-full object-cover" />
                )}
              </div>
              <div>
                <p className="font-medium text-slate-900">{fil?.name}</p>
                <p className="text-sm text-slate-500 mt-0.5">{(fil?.size ?? 0 / 1024 / 1024).toFixed(1)} MB</p>
                <button
                  type="button"
                  onClick={nullstill}
                  className="mt-2 text-xs text-blue-600 hover:underline"
                >
                  Last opp annet bilde
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Hva ønsker du å gjøre / se? (valgfritt)
              </label>
              <textarea
                value={ønsketEndring}
                onChange={(e) => setØnsketEndring(e.target.value)}
                placeholder="F.eks. «Hva om vi la til et tilbygg mot nord?» eller «Vil se dette i moderne stil med flatt tak»"
                rows={3}
                className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
              />
            </div>

            {feil && (
              <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {feil}
              </div>
            )}

            <button
              type="button"
              onClick={kjørAnalyse}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl bg-purple-600 px-6 py-3 text-sm font-semibold text-white hover:bg-purple-700 disabled:opacity-60 transition-colors"
            >
              {loading ? (
                <><Loader2 className="h-4 w-4 animate-spin" /> Analyserer...</>
              ) : (
                <><Sparkles className="h-4 w-4" /> Start AI-analyse</>
              )}
            </button>
          </div>
        )}

        {/* Steg 3: Resultat */}
        {steg === 'resultat' && analyse && (
          <div className="space-y-5">
            {/* Bilde + grunninfo */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div className="rounded-xl overflow-hidden border border-slate-200">
                {forhåndsvisning && (
                  <img src={forhåndsvisning} alt="Opplastet bilde" className="w-full object-cover max-h-64" />
                )}
              </div>

              <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-3">
                <h3 className="font-semibold text-slate-900 text-sm">Grunninfo</h3>
                {[
                  { label: 'Bygningstype', value: analyse.bygningstype },
                  { label: 'Stil', value: analyse.arkitekturstil },
                  { label: 'Estimert byggeår', value: analyse.byggeaar_estimat },
                  { label: 'Tilstand', value: analyse.tilstand },
                  { label: 'Materialer', value: analyse.materialer?.join(', ') },
                ].filter(item => item.value).map((item) => (
                  <div key={item.label} className="flex justify-between text-sm border-b border-slate-100 pb-2 last:border-0 last:pb-0">
                    <span className="text-slate-500">{item.label}</span>
                    <span className="font-medium text-slate-900 text-right max-w-[60%]">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Fasade */}
            {analyse.fasade_beskrivelse && (
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-900 mb-2 text-sm">Analyse</h3>
                <p className="text-sm text-slate-700 leading-relaxed">{analyse.fasade_beskrivelse}</p>
              </div>
            )}

            {/* Muligheter */}
            {(analyse.muligheter?.length ?? 0) > 0 && (
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-900 mb-4 text-sm">Potensial og muligheter</h3>
                <div className="space-y-3">
                  {analyse.muligheter?.map((m, i) => (
                    <div key={i} className="rounded-lg bg-slate-50 border border-slate-200 p-4">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <p className="text-sm font-semibold text-slate-900">{m.type}</p>
                        <span className={cn(
                          'shrink-0 rounded-full px-2 py-0.5 text-xs font-medium',
                          m.kompleksitet === 'Lav' ? 'bg-green-100 text-green-700' :
                          m.kompleksitet === 'Middels' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        )}>
                          {m.kompleksitet}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">{m.beskrivelse}</p>
                      {m.estimert_kostnad && (
                        <p className="mt-2 text-xs font-semibold text-slate-700">{m.estimert_kostnad}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Anbefalinger */}
            {(analyse.anbefalinger?.length ?? 0) > 0 && (
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-900 mb-3 text-sm">Anbefalinger</h3>
                <ul className="space-y-2">
                  {analyse.anbefalinger?.map((a, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm text-slate-700">
                      <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                      {a}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Generer render */}
            <div className="rounded-xl border border-violet-200 bg-violet-50 p-5">
              <h3 className="font-semibold text-violet-900 mb-2 text-sm">
                Generer fotorealistisk render
              </h3>
              <p className="text-xs text-violet-700 mb-4">
                Velg en stil og se bygget visualisert med AI-generert fotorealistisk render.
              </p>
              <div className="flex flex-wrap gap-2 mb-4">
                {STILER.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => setStil(s.id)}
                    className={cn(
                      'rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors',
                      stil === s.id
                        ? 'border-violet-500 bg-violet-100 text-violet-700'
                        : 'border-slate-200 bg-white text-slate-600 hover:border-violet-300'
                    )}
                  >
                    {s.label}
                  </button>
                ))}
              </div>

              {renderUrl ? (
                <div className="space-y-3">
                  <img
                    src={renderUrl}
                    alt="AI-generert render"
                    className="w-full rounded-xl border border-violet-200 shadow-sm"
                  />
                  <a
                    href={renderUrl}
                    download="render.png"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-700 transition-colors"
                  >
                    <Download className="h-4 w-4" />
                    Last ned render
                  </a>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={genererRender}
                  disabled={renderLoading}
                  className="inline-flex items-center gap-2 rounded-lg bg-violet-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-violet-700 disabled:opacity-60 transition-colors"
                >
                  {renderLoading ? (
                    <><Loader2 className="h-4 w-4 animate-spin" /> Genererer render…</>
                  ) : (
                    <><ImageIcon className="h-4 w-4" /> Generer render</>
                  )}
                </button>
              )}
            </div>

            {feil && (
              <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {feil}
              </div>
            )}

            <div className="flex gap-3">
              <button
                type="button"
                onClick={nullstill}
                className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
              >
                Last opp nytt bilde
              </button>
              <Link
                href="/tjenester"
                className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
              >
                Se alle tjenester
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        )}

        {/* Info footer */}
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <p className="text-xs text-slate-500">
            <strong>Merk:</strong> AI-analysen og renderne er beslutningsstøtte og visualiseringsverktøy.
            Endelig prosjektering og byggesøknad må utføres av kvalifisert arkitekt eller ansvarsretter.
            nops.no er ansvarlig søker og kan hjelpe deg videre – se{' '}
            <Link href="/tjenester" className="text-blue-600 hover:underline">alle tjenester</Link>.
          </p>
        </div>
      </div>
    </main>
  );
}
