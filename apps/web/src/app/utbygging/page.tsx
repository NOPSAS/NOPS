'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  Building2,
  TrendingUp,
  Layers,
  ArrowRight,
  Loader2,
  AlertCircle,
  CheckCircle2,
  BarChart3,
  Search,
  MapPin,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { getAuthToken } from '@/lib/utils';
import { API_BASE_URL } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Typer
// ---------------------------------------------------------------------------

interface Scenario {
  navn: string;
  beskrivelse: string;
  antall_enheter: number;
  estimert_bra_m2: number;
  estimert_salgsverdi_kr: number;
  estimert_byggekostnad_kr: number;
  estimert_fortjeneste_kr: number;
  gjennomforbarhet: 'Høy' | 'Middels' | 'Lav';
  reguleringsrisiko: 'Lav' | 'Middels' | 'Høy';
}

interface UtbyggingAnalyse {
  nåværende_utnyttelse: {
    bya_prosent: number;
    bra_m2: number;
    antall_bygninger: number;
  };
  maks_tillatt: {
    bya_prosent: number;
    bra_m2: number;
    maks_hoyde_m: number;
  };
  uutnyttet_potensial: {
    ekstra_bra_m2: number;
    potensial_prosent: number;
  };
  scenarioer: Scenario[];
  reguleringsplan_analyse: string;
  anbefalinger: string[];
  disclaimer: string;
}

interface UtbyggingResultat {
  eiendom: {
    knr: string;
    gnr: number;
    bnr: number;
    tiltakstype: string;
    areal_per_enhet: number;
  };
  analyse: UtbyggingAnalyse;
  datakilder: {
    kartverket: boolean;
    planslurpen: boolean;
  };
}

interface AdresseSuggestion {
  text: string;
  knr?: string;
  gnr?: number;
  bnr?: number;
}

// ---------------------------------------------------------------------------
// Hjelpefunksjoner
// ---------------------------------------------------------------------------

function formaterKr(kr: number): string {
  if (kr >= 1_000_000) {
    return `${(kr / 1_000_000).toFixed(1)} mill. kr`;
  }
  return `${kr.toLocaleString('nb-NO')} kr`;
}

function gjennomforbarhetFarge(v: string): string {
  if (v === 'Høy') return 'bg-emerald-100 text-emerald-800 border-emerald-200';
  if (v === 'Middels') return 'bg-amber-100 text-amber-800 border-amber-200';
  return 'bg-red-100 text-red-800 border-red-200';
}

function risikoFarge(v: string): string {
  if (v === 'Lav') return 'bg-emerald-100 text-emerald-700 border-emerald-200';
  if (v === 'Middels') return 'bg-amber-100 text-amber-700 border-amber-200';
  return 'bg-red-100 text-red-700 border-red-200';
}

function ProgressBar({ verdi, maks, farge }: { verdi: number; maks: number; farge: string }) {
  const prosent = maks > 0 ? Math.min(100, (verdi / maks) * 100) : 0;
  return (
    <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
      <div
        className={cn('h-2.5 rounded-full transition-all duration-700', farge)}
        style={{ width: `${prosent}%` }}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Hoved-komponent
// ---------------------------------------------------------------------------

export default function UtbyggingPage() {
  // Skjema-state
  const [adresseInput, setAdresseInput] = React.useState('');
  const [suggestions, setSuggestions] = React.useState<AdresseSuggestion[]>([]);
  const [valgtAdresse, setValgtAdresse] = React.useState<AdresseSuggestion | null>(null);
  const [knr, setKnr] = React.useState('');
  const [gnr, setGnr] = React.useState('');
  const [bnr, setBnr] = React.useState('');
  const [tiltakstype, setTiltakstype] = React.useState<string>('leiligheter');
  const [arealPerEnhet, setArealPerEnhet] = React.useState<number>(80);

  // UI-state
  const [lasterSuggestions, setLasterSuggestions] = React.useState(false);
  const [lasterAnalyse, setLasterAnalyse] = React.useState(false);
  const [feil, setFeil] = React.useState<string | null>(null);
  const [resultat, setResultat] = React.useState<UtbyggingResultat | null>(null);
  const [visDropdown, setVisDropdown] = React.useState(false);
  const [manuellModus, setManuellModus] = React.useState(false);

  const dropdownRef = React.useRef<HTMLDivElement>(null);
  const søkTimer = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  React.useEffect(() => {
    document.title = 'Tomteutviklingsanalyse \u2013 Utbyggingspotensial | nops.no';
  }, []);

  // Lukk dropdown ved klikk utenfor
  React.useEffect(() => {
    function handleOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setVisDropdown(false);
      }
    }
    document.addEventListener('mousedown', handleOutside);
    return () => document.removeEventListener('mousedown', handleOutside);
  }, []);

  // Adressesøk med debounce
  React.useEffect(() => {
    if (søkTimer.current) clearTimeout(søkTimer.current);
    if (!adresseInput || adresseInput.length < 3 || valgtAdresse) {
      setSuggestions([]);
      setVisDropdown(false);
      return;
    }
    søkTimer.current = setTimeout(async () => {
      setLasterSuggestions(true);
      try {
        const token = getAuthToken();
        const url = `${API_BASE_URL}/api/v1/search/address?q=${encodeURIComponent(adresseInput)}`;
        const resp = await fetch(url, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (resp.ok) {
          const data = await resp.json();
          const liste: AdresseSuggestion[] = Array.isArray(data)
            ? data
            : (data.suggestions ?? data.results ?? []);
          setSuggestions(liste.slice(0, 6));
          setVisDropdown(liste.length > 0);
        }
      } catch {
        // Ignorer søkefeil
      } finally {
        setLasterSuggestions(false);
      }
    }, 300);
  }, [adresseInput, valgtAdresse]);

  function velgAdresse(s: AdresseSuggestion) {
    setValgtAdresse(s);
    setAdresseInput(s.text);
    setVisDropdown(false);
    setSuggestions([]);
    if (s.knr) setKnr(s.knr);
    if (s.gnr) setGnr(String(s.gnr));
    if (s.bnr) setBnr(String(s.bnr));
  }

  function nullstillAdresse() {
    setValgtAdresse(null);
    setAdresseInput('');
    setKnr('');
    setGnr('');
    setBnr('');
  }

  async function kjørAnalyse(e: React.FormEvent) {
    e.preventDefault();
    setFeil(null);
    setResultat(null);

    const knrVal = knr.trim();
    const gnrVal = parseInt(gnr, 10);
    const bnrVal = parseInt(bnr, 10);

    if (!knrVal || !gnrVal || !bnrVal) {
      setFeil('Fyll inn kommunenummer, gårdsnummer og bruksnummer for å starte analysen.');
      return;
    }

    setLasterAnalyse(true);
    try {
      const token = getAuthToken();
      const resp = await fetch(`${API_BASE_URL}/api/v1/utbygging/analyser`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          knr: knrVal,
          gnr: gnrVal,
          bnr: bnrVal,
          tiltakstype,
          areal_per_enhet: arealPerEnhet,
        }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(err.detail ?? `HTTP ${resp.status}`);
      }

      const data: UtbyggingResultat = await resp.json();
      setResultat(data);
    } catch (err) {
      setFeil(err instanceof Error ? err.message : 'Analysen feilet. Prøv igjen.');
    } finally {
      setLasterAnalyse(false);
    }
  }

  const analyse = resultat?.analyse;

  return (
    <main className="min-h-screen bg-slate-50">
      {/* ------------------------------------------------------------------ */}
      {/* Header                                                               */}
      {/* ------------------------------------------------------------------ */}
      <section className="bg-gradient-to-br from-green-600 via-emerald-600 to-emerald-700 text-white py-14 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/15 border border-white/25 px-4 py-1.5 text-sm font-medium mb-5">
            <BarChart3 className="h-4 w-4" />
            Inspirert av Archistar og Plot.ai – tilpasset norsk rett
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mb-3">
            Tomteutviklingsanalyse
          </h1>
          <p className="text-emerald-100 text-lg max-w-2xl mx-auto">
            Finn utbyggingspotensial, beregn lønnsomhet og forstå reguleringsplanen for
            hvilken som helst norsk eiendom – basert på Kartverket og plandata.
          </p>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Søkeskjema                                                           */}
      {/* ------------------------------------------------------------------ */}
      <section className="max-w-2xl mx-auto px-4 -mt-8">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-lg p-6">
          <form onSubmit={kjørAnalyse} className="space-y-5">
            {/* Adresseoppslag */}
            {!manuellModus ? (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Søk etter adresse
                </label>
                <div className="relative" ref={dropdownRef}>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <input
                      type="text"
                      value={adresseInput}
                      onChange={(e) => {
                        setAdresseInput(e.target.value);
                        if (valgtAdresse) nullstillAdresse();
                      }}
                      placeholder="F.eks. Storgata 1, Oslo"
                      className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    />
                    {lasterSuggestions && (
                      <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 animate-spin" />
                    )}
                    {valgtAdresse && (
                      <MapPin className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-600" />
                    )}
                  </div>
                  {visDropdown && suggestions.length > 0 && (
                    <div className="absolute z-10 w-full mt-1 bg-white rounded-lg border border-slate-200 shadow-lg overflow-hidden">
                      {suggestions.map((s, i) => (
                        <button
                          key={i}
                          type="button"
                          onClick={() => velgAdresse(s)}
                          className="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-emerald-50 hover:text-emerald-800 transition-colors border-b border-slate-100 last:border-0"
                        >
                          <MapPin className="inline h-3.5 w-3.5 mr-1.5 text-slate-400" />
                          {s.text}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                {valgtAdresse && (
                  <p className="mt-1.5 text-xs text-emerald-700">
                    Eiendom: {knr}/{gnr}/{bnr}
                  </p>
                )}
                <button
                  type="button"
                  onClick={() => setManuellModus(true)}
                  className="mt-2 text-xs text-slate-500 hover:text-slate-700 underline"
                >
                  Fyll inn matrikkeldata manuelt
                </button>
              </div>
            ) : (
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-sm font-medium text-slate-700">Matrikkeldata</span>
                  <button
                    type="button"
                    onClick={() => setManuellModus(false)}
                    className="text-xs text-slate-500 hover:text-slate-700 underline"
                  >
                    Bruk adressesøk
                  </button>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs text-slate-500 mb-1">Kommunenr.</label>
                    <input
                      type="text"
                      value={knr}
                      onChange={(e) => setKnr(e.target.value)}
                      placeholder="3212"
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500 mb-1">Gårdsnr. (gnr)</label>
                    <input
                      type="number"
                      value={gnr}
                      onChange={(e) => setGnr(e.target.value)}
                      placeholder="42"
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500 mb-1">Bruksnr. (bnr)</label>
                    <input
                      type="number"
                      value={bnr}
                      onChange={(e) => setBnr(e.target.value)}
                      placeholder="7"
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Tiltakstype */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Tiltakstype
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {(['enebolig', 'leiligheter', 'tomannsbolig', 'næring'] as const).map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setTiltakstype(t)}
                    className={cn(
                      'rounded-lg border px-3 py-2 text-sm font-medium capitalize transition-all',
                      tiltakstype === t
                        ? 'border-emerald-500 bg-emerald-50 text-emerald-700 ring-1 ring-emerald-400'
                        : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                    )}
                  >
                    {t.charAt(0).toUpperCase() + t.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Areal per enhet */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Ønsket areal per enhet
                <span className="ml-2 font-normal text-slate-500 text-xs">({arealPerEnhet} m²)</span>
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min={20}
                  max={300}
                  step={5}
                  value={arealPerEnhet}
                  onChange={(e) => setArealPerEnhet(Number(e.target.value))}
                  className="flex-1 accent-emerald-600"
                />
                <input
                  type="number"
                  min={20}
                  max={500}
                  value={arealPerEnhet}
                  onChange={(e) => setArealPerEnhet(Number(e.target.value))}
                  className="w-20 px-3 py-1.5 rounded-lg border border-slate-300 text-sm text-center focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>
            </div>

            {/* Feilmelding */}
            {feil && (
              <div className="flex items-start gap-2.5 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
                {feil}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={lasterAnalyse}
              className="w-full rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-300 text-white font-semibold py-3 text-sm transition-colors flex items-center justify-center gap-2"
            >
              {lasterAnalyse ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyserer tomt...
                </>
              ) : (
                <>
                  <BarChart3 className="h-4 w-4" />
                  Analyser tomt
                </>
              )}
            </button>
          </form>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Resultat                                                             */}
      {/* ------------------------------------------------------------------ */}
      {analyse && (
        <section className="max-w-5xl mx-auto px-4 py-10 space-y-8">
          {/* Eiendomsidentifikasjon */}
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Building2 className="h-4 w-4 text-emerald-600" />
            <span className="font-medium text-slate-700">
              {resultat?.eiendom.knr}/{resultat?.eiendom.gnr}/{resultat?.eiendom.bnr}
            </span>
            <span>–</span>
            <span className="capitalize">{resultat?.eiendom.tiltakstype}</span>
            <span>–</span>
            <span>{resultat?.eiendom.areal_per_enhet} m² per enhet</span>
            {resultat?.datakilder.kartverket && (
              <span className="ml-auto inline-flex items-center gap-1 text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full px-2.5 py-0.5">
                <CheckCircle2 className="h-3 w-3" /> Kartverket
              </span>
            )}
            {resultat?.datakilder.planslurpen && (
              <span className="inline-flex items-center gap-1 text-xs bg-blue-50 text-blue-700 border border-blue-200 rounded-full px-2.5 py-0.5">
                <CheckCircle2 className="h-3 w-3" /> Planslurpen
              </span>
            )}
          </div>

          {/* Nåværende vs maks utnyttelse */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {/* Nåværende */}
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-2 mb-4">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100">
                  <Building2 className="h-5 w-5 text-slate-600" />
                </div>
                <div>
                  <p className="text-xs text-slate-500">Nåværende situasjon</p>
                  <p className="font-semibold text-slate-900">Eksisterende utnyttelse</p>
                </div>
              </div>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-500">BYA</span>
                    <span className="font-semibold text-slate-800">
                      {analyse.nåværende_utnyttelse.bya_prosent.toFixed(1)} %
                    </span>
                  </div>
                  <ProgressBar
                    verdi={analyse.nåværende_utnyttelse.bya_prosent}
                    maks={analyse.maks_tillatt.bya_prosent || 100}
                    farge="bg-slate-400"
                  />
                </div>
                <div className="flex justify-between text-sm pt-1">
                  <span className="text-slate-500">BRA totalt</span>
                  <span className="font-semibold">{analyse.nåværende_utnyttelse.bra_m2.toLocaleString('nb-NO')} m²</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Antall bygninger</span>
                  <span className="font-semibold">{analyse.nåværende_utnyttelse.antall_bygninger}</span>
                </div>
              </div>
            </div>

            {/* Maks tillatt */}
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-6 shadow-sm">
              <div className="flex items-center gap-2 mb-4">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-100">
                  <TrendingUp className="h-5 w-5 text-emerald-600" />
                </div>
                <div>
                  <p className="text-xs text-emerald-600">Reguleringsplan tillater</p>
                  <p className="font-semibold text-slate-900">Maks utnyttelse</p>
                </div>
              </div>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-500">Maks BYA</span>
                    <span className="font-semibold text-emerald-700">
                      {analyse.maks_tillatt.bya_prosent.toFixed(1)} %
                    </span>
                  </div>
                  <ProgressBar
                    verdi={analyse.maks_tillatt.bya_prosent}
                    maks={100}
                    farge="bg-emerald-500"
                  />
                </div>
                <div className="flex justify-between text-sm pt-1">
                  <span className="text-slate-500">Maks BRA</span>
                  <span className="font-semibold text-emerald-700">{analyse.maks_tillatt.bra_m2.toLocaleString('nb-NO')} m²</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Maks høyde</span>
                  <span className="font-semibold text-emerald-700">{analyse.maks_tillatt.maks_hoyde_m.toFixed(1)} m</span>
                </div>
              </div>
            </div>
          </div>

          {/* Uutnyttet potensial – banner */}
          <div className="rounded-2xl bg-gradient-to-r from-emerald-600 to-green-600 text-white p-6 flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white/20">
              <Layers className="h-6 w-6 text-white" />
            </div>
            <div className="flex-1">
              <p className="text-emerald-100 text-sm">Uutnyttet potensial</p>
              <p className="text-2xl font-bold mt-0.5">
                + {analyse.uutnyttet_potensial.ekstra_bra_m2.toLocaleString('nb-NO')} m² BRA
              </p>
            </div>
            <div className="text-right">
              <p className="text-emerald-100 text-xs">Ledig kapasitet</p>
              <p className="text-3xl font-bold">
                {analyse.uutnyttet_potensial.potensial_prosent.toFixed(0)} %
              </p>
            </div>
          </div>

          {/* Scenarioer */}
          <div>
            <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-emerald-600" />
              Utviklingsscenarioer
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {analyse.scenarioer.map((s, i) => (
                <div
                  key={i}
                  className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm flex flex-col gap-4"
                >
                  {/* Tittel og badges */}
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <h3 className="font-semibold text-slate-900 text-sm leading-snug">{s.navn}</h3>
                    </div>
                    <div className="flex gap-1.5 flex-wrap">
                      <span className={cn('text-xs border rounded-full px-2 py-0.5 font-medium', gjennomforbarhetFarge(s.gjennomforbarhet))}>
                        {s.gjennomforbarhet} gjennomf.
                      </span>
                      <span className={cn('text-xs border rounded-full px-2 py-0.5 font-medium', risikoFarge(s.reguleringsrisiko))}>
                        {s.reguleringsrisiko} risiko
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-500 leading-relaxed flex-1">{s.beskrivelse}</p>

                  {/* Nøkkeltall */}
                  <div className="space-y-1.5 text-xs">
                    <div className="flex justify-between text-slate-600">
                      <span>Antall enheter</span>
                      <span className="font-semibold text-slate-800">{s.antall_enheter}</span>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Estimert BRA</span>
                      <span className="font-semibold text-slate-800">{s.estimert_bra_m2.toLocaleString('nb-NO')} m²</span>
                    </div>
                    <div className="border-t border-slate-100 pt-1.5 mt-1.5 space-y-1">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Salgsverdi</span>
                        <span className="font-semibold text-slate-700">{formaterKr(s.estimert_salgsverdi_kr)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Byggekostnad</span>
                        <span className="font-semibold text-red-600">{formaterKr(s.estimert_byggekostnad_kr)}</span>
                      </div>
                      <div className="flex justify-between border-t border-slate-100 pt-1.5">
                        <span className="font-medium text-slate-700">Fortjeneste</span>
                        <span className={cn('font-bold text-base', s.estimert_fortjeneste_kr >= 0 ? 'text-emerald-600' : 'text-red-600')}>
                          {s.estimert_fortjeneste_kr >= 0 ? '+' : ''}{formaterKr(s.estimert_fortjeneste_kr)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Reguleringsplan-analyse */}
          <div className="rounded-2xl border border-blue-200 bg-blue-50/50 p-6">
            <h2 className="font-semibold text-slate-900 mb-3 flex items-center gap-2 text-sm">
              <Layers className="h-4 w-4 text-blue-600" />
              Reguleringsplan-analyse
            </h2>
            <p className="text-sm text-slate-700 leading-relaxed">{analyse.reguleringsplan_analyse}</p>
          </div>

          {/* Anbefalinger */}
          <div>
            <h2 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              Anbefalinger
            </h2>
            <ul className="space-y-2">
              {analyse.anbefalinger.map((a, i) => (
                <li key={i} className="flex items-start gap-2.5 text-sm text-slate-700">
                  <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0 text-emerald-500" />
                  {a}
                </li>
              ))}
            </ul>
          </div>

          {/* Disclaimer */}
          <div className="flex items-start gap-2.5 rounded-xl bg-amber-50 border border-amber-200 px-4 py-3 text-xs text-amber-800">
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0 text-amber-500" />
            {analyse.disclaimer}
          </div>

          {/* CTA */}
          <div className="rounded-2xl bg-gradient-to-br from-slate-800 to-slate-900 text-white p-8 text-center">
            <h2 className="text-xl font-bold mb-2">Vil du gå videre?</h2>
            <p className="text-slate-300 text-sm mb-5 max-w-md mx-auto">
              Kontakt nops.no for full prosjektvurdering, arkitektbistand og hjelp med byggesøknad.
            </p>
            <a
              href="https://www.nops.no"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 transition-colors px-6 py-3 text-sm font-semibold"
            >
              Kontakt nops.no
              <ArrowRight className="h-4 w-4" />
            </a>
          </div>
        </section>
      )}

      {/* Blank state mellom form og resultat */}
      {!analyse && !lasterAnalyse && (
        <section className="max-w-2xl mx-auto px-4 py-16 text-center text-slate-400">
          <BarChart3 className="h-12 w-12 mx-auto mb-4 text-slate-200" />
          <p className="text-sm">
            Søk etter en eiendom og velg tiltakstype for å se utbyggingspotensial,
            scenarioer og lønnsomhetsanalyse.
          </p>
        </section>
      )}
    </main>
  );
}
