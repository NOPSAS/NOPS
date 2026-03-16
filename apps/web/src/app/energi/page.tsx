'use client';

import * as React from 'react';
import {
  Zap,
  Leaf,
  ThermometerSun,
  DollarSign,
  TrendingDown,
  BarChart3,
  CheckCircle2,
  XCircle,
  ExternalLink,
  AlertTriangle,
  ArrowRight,
  Loader2,
  Wind,
  Droplets,
} from 'lucide-react';
import { fetchJSON } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Tiltak {
  prioritet: number;
  tiltak: string;
  beskrivelse: string;
  estimert_kostnad_kr: number;
  estimert_besparelse_aar_kr: number;
  tilbakebetalingstid_aar: number;
  enova_stotte_kr: number;
  netto_kostnad_kr: number;
  ny_u_verdi: number | null;
  energibesparelse_kwh: number;
  co2_reduksjon_kg: number;
  kompleksitet: string;
}

interface EnovaStotte {
  tiltak: string;
  maks_stotte: number;
  vilkaar: string;
}

interface AnalyseResult {
  eiendom: {
    knr: string;
    gnr: string;
    bnr: string;
    byggeaar: number | string;
    bra_m2: number | string;
    bygningstype: string;
  };
  energiprofil: {
    estimert_energimerke: string;
    estimert_forbruk_kwh: number;
    forbruk_per_m2: number;
    nasjonalt_gjennomsnitt_kwh_m2: number;
    over_under_snitt: string;
    co2_utslipp_kg: number;
    energikostnad_aar_kr: number;
  };
  bygningsanalyse: {
    byggeaar: number | string;
    antatt_isolasjonsstandard: string;
    antatt_vinduer: string;
    antatt_tetthet: string;
    antatt_u_verdi_vegg: number;
    antatt_u_verdi_tak: number;
    antatt_u_verdi_vindu: number;
    svake_punkter: string[];
  };
  anbefalte_tiltak: Tiltak[];
  enova_muligheter: {
    total_mulig_stotte_kr: number;
    tiltak_med_stotte: EnovaStotte[];
    lenke: string;
  };
  energimerke_potensial: {
    naavaerende: string;
    etter_alle_tiltak: string;
    forbedring_steg: string[];
  };
  sammenligning_tek17: {
    oppfyller_tek17: boolean;
    mangler: string[];
    estimert_kostnad_tek17_nivaa: number;
  };
  tips: string[];
  neste_steg: string[];
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const ENERGIMERKE_FARGER: Record<string, string> = {
  A: 'bg-green-600',
  B: 'bg-green-500',
  C: 'bg-yellow-500',
  D: 'bg-orange-500',
  E: 'bg-red-500',
  F: 'bg-red-700',
  G: 'bg-gray-900',
};

const ENERGIMERKE_TEKST_FARGER: Record<string, string> = {
  A: 'text-green-600',
  B: 'text-green-500',
  C: 'text-yellow-600',
  D: 'text-orange-500',
  E: 'text-red-500',
  F: 'text-red-700',
  G: 'text-gray-900',
};

const ALLE_MERKER = ['A', 'B', 'C', 'D', 'E', 'F', 'G'];

function formatKr(n: number): string {
  return n.toLocaleString('nb-NO') + ' kr';
}

function formatKwh(n: number): string {
  return n.toLocaleString('nb-NO') + ' kWh';
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function EnergiPage() {
  const [knr, setKnr] = React.useState('');
  const [gnr, setGnr] = React.useState('');
  const [bnr, setBnr] = React.useState('');
  const [oppvarming, setOppvarming] = React.useState('elektrisk');
  const [harSolceller, setHarSolceller] = React.useState(false);
  const [tiltak, setTiltak] = React.useState<Record<string, boolean>>({
    etterisolering: false,
    vinduer: false,
    varmepumpe: false,
    solceller: false,
    'balansert ventilasjon': false,
  });

  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<AnalyseResult | null>(null);

  React.useEffect(() => {
    document.title = 'Energiradgivning | ByggSjekk';
  }, []);

  const handleAnalyser = async () => {
    if (!knr || !gnr || !bnr) {
      setError('Fyll inn kommunenummer, gardsnummer og bruksnummer.');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);

    const valgte = Object.entries(tiltak)
      .filter(([, v]) => v)
      .map(([k]) => k)
      .join(',');

    const params = new URLSearchParams({
      knr,
      gnr,
      bnr,
      oppvarmingskilde: oppvarming,
      har_solceller: String(harSolceller),
      planlagte_tiltak: valgte,
    });

    try {
      const data = await fetchJSON<AnalyseResult>(
        `/api/v1/energi/analyser?${params.toString()}`,
        { method: 'POST' }
      );
      setResult(data);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Noe gikk galt. Prov igjen.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <section className="bg-gradient-to-br from-green-600 to-teal-600 py-14 px-4 text-center text-white">
        <div className="max-w-3xl mx-auto">
          <div className="flex justify-center mb-4">
            <div className="rounded-2xl bg-white/20 p-3">
              <Zap className="h-8 w-8" />
            </div>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mb-3">
            Energiradgivning for din bolig
          </h1>
          <p className="text-green-100 text-lg mb-5">
            Se energimerke, sparepotensial og Enova-stotte &ndash; basert pa din
            bolig
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {['Gratis energianalyse', 'Enova-stotte', 'TEK17-sjekk'].map(
              (badge) => (
                <span
                  key={badge}
                  className="inline-flex items-center gap-1.5 rounded-full bg-white/20 px-3 py-1 text-sm font-medium"
                >
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  {badge}
                </span>
              )
            )}
          </div>
        </div>
      </section>

      {/* Skjema */}
      <section className="max-w-2xl mx-auto -mt-8 px-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-lg">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">
            Sok opp eiendom
          </h2>

          <div className="grid grid-cols-3 gap-3 mb-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Kommunenr
              </label>
              <input
                type="text"
                value={knr}
                onChange={(e) => setKnr(e.target.value)}
                placeholder="0301"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Gnr
              </label>
              <input
                type="text"
                value={gnr}
                onChange={(e) => setGnr(e.target.value)}
                placeholder="100"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Bnr
              </label>
              <input
                type="text"
                value={bnr}
                onChange={(e) => setBnr(e.target.value)}
                placeholder="50"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none"
              />
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Oppvarmingskilde
            </label>
            <select
              value={oppvarming}
              onChange={(e) => setOppvarming(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none"
            >
              <option value="elektrisk">Elektrisk</option>
              <option value="varmepumpe">Varmepumpe</option>
              <option value="fjernvarme">Fjernvarme</option>
              <option value="ved">Ved</option>
              <option value="olje">Olje</option>
              <option value="gass">Gass</option>
            </select>
          </div>

          <div className="mb-4">
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={harSolceller}
                onChange={(e) => setHarSolceller(e.target.checked)}
                className="rounded border-slate-300 text-green-600 focus:ring-green-500"
              />
              <span>Har solceller?</span>
            </label>
          </div>

          <div className="mb-5">
            <p className="text-sm font-medium text-slate-700 mb-2">
              Planlagte tiltak
            </p>
            <div className="flex flex-wrap gap-3">
              {Object.keys(tiltak).map((t) => (
                <label
                  key={t}
                  className="flex items-center gap-2 text-sm text-slate-700"
                >
                  <input
                    type="checkbox"
                    checked={tiltak[t]}
                    onChange={(e) =>
                      setTiltak((prev) => ({ ...prev, [t]: e.target.checked }))
                    }
                    className="rounded border-slate-300 text-green-600 focus:ring-green-500"
                  />
                  <span className="capitalize">{t}</span>
                </label>
              ))}
            </div>
          </div>

          <button
            type="button"
            onClick={handleAnalyser}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-green-600 px-5 py-3 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60 transition-colors"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Analyserer...
              </>
            ) : (
              <>
                <Zap className="h-4 w-4" />
                Analyser energi
              </>
            )}
          </button>

          {error && (
            <div className="mt-4 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
              {error}
            </div>
          )}
        </div>
      </section>

      {/* Resultater */}
      {result && (
        <div className="max-w-5xl mx-auto px-4 py-10 space-y-8">
          {/* 1. Energimerke-kort */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Naavaerende merke */}
            <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
              <p className="text-sm font-medium text-slate-500 mb-3">
                Navarende energimerke
              </p>
              <div
                className={`inline-flex items-center justify-center h-24 w-24 rounded-2xl text-5xl font-black text-white ${
                  ENERGIMERKE_FARGER[result.energiprofil.estimert_energimerke] ||
                  'bg-gray-400'
                }`}
              >
                {result.energiprofil.estimert_energimerke}
              </div>
              <p className="mt-3 text-sm text-slate-500">
                {result.energiprofil.forbruk_per_m2} kWh/m2
              </p>
            </div>

            {/* Potensiale */}
            <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
              <p className="text-sm font-medium text-slate-500 mb-3">
                Potensiale etter tiltak
              </p>
              <div
                className={`inline-flex items-center justify-center h-24 w-24 rounded-2xl text-5xl font-black text-white ${
                  ENERGIMERKE_FARGER[
                    result.energimerke_potensial.etter_alle_tiltak
                  ] || 'bg-gray-400'
                }`}
              >
                {result.energimerke_potensial.etter_alle_tiltak}
              </div>
              <p className="mt-3 text-sm text-slate-500">
                Fra {result.energimerke_potensial.naavaerende} til{' '}
                {result.energimerke_potensial.etter_alle_tiltak}
              </p>
            </div>
          </div>

          {/* 2. Nokkeltall */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              icon={<Zap className="h-5 w-5 text-yellow-600" />}
              label="Forbruk"
              value={formatKwh(result.energiprofil.estimert_forbruk_kwh)}
              bg="bg-yellow-50"
            />
            <StatCard
              icon={<DollarSign className="h-5 w-5 text-green-600" />}
              label="Kostnad/ar"
              value={formatKr(result.energiprofil.energikostnad_aar_kr)}
              bg="bg-green-50"
            />
            <StatCard
              icon={<Leaf className="h-5 w-5 text-emerald-600" />}
              label="CO2-utslipp"
              value={`${result.energiprofil.co2_utslipp_kg.toLocaleString('nb-NO')} kg`}
              bg="bg-emerald-50"
            />
            <StatCard
              icon={<BarChart3 className="h-5 w-5 text-blue-600" />}
              label="vs. snitt"
              value={result.energiprofil.over_under_snitt}
              bg="bg-blue-50"
            />
          </div>

          {/* 3. Bygningsanalyse */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <ThermometerSun className="h-5 w-5 text-orange-500" />
              Bygningsanalyse
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
              <InfoRow
                label="Isolasjonsstandard"
                value={result.bygningsanalyse.antatt_isolasjonsstandard}
              />
              <InfoRow
                label="Vinduer"
                value={result.bygningsanalyse.antatt_vinduer}
              />
              <InfoRow
                label="Tetthet"
                value={result.bygningsanalyse.antatt_tetthet}
              />
              <InfoRow
                label="U-verdi vegg"
                value={`${result.bygningsanalyse.antatt_u_verdi_vegg} W/(m2K)`}
              />
              <InfoRow
                label="U-verdi tak"
                value={`${result.bygningsanalyse.antatt_u_verdi_tak} W/(m2K)`}
              />
              <InfoRow
                label="U-verdi vindu"
                value={`${result.bygningsanalyse.antatt_u_verdi_vindu} W/(m2K)`}
              />
            </div>
            {result.bygningsanalyse.svake_punkter.length > 0 && (
              <div>
                <p className="text-sm font-medium text-slate-700 mb-2">
                  Svake punkter
                </p>
                <ul className="space-y-1">
                  {result.bygningsanalyse.svake_punkter.map((p, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-sm text-slate-600"
                    >
                      <AlertTriangle className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                      {p}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* 4. Anbefalte tiltak */}
          <div>
            <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <TrendingDown className="h-5 w-5 text-green-600" />
              Anbefalte tiltak
            </h3>
            <div className="space-y-4">
              {(result.anbefalte_tiltak || [])
                .sort((a, b) => a.prioritet - b.prioritet)
                .map((t, i) => (
                  <div
                    key={i}
                    className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-green-100 text-green-700 text-xs font-bold">
                            {t.prioritet}
                          </span>
                          <h4 className="font-semibold text-slate-900">
                            {t.tiltak}
                          </h4>
                        </div>
                        <p className="text-sm text-slate-500">
                          {t.beskrivelse}
                        </p>
                      </div>
                      <span
                        className={`flex-shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          t.kompleksitet === 'Lav'
                            ? 'bg-green-100 text-green-700'
                            : t.kompleksitet === 'Middels'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {t.kompleksitet}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                      <div>
                        <p className="text-slate-500">Kostnad</p>
                        <p className="font-semibold text-slate-900">
                          {formatKr(t.estimert_kostnad_kr)}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-500">Besparelse/ar</p>
                        <p className="font-semibold text-green-700">
                          {formatKr(t.estimert_besparelse_aar_kr)}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-500">Tilbakebetalingstid</p>
                        <p className="font-semibold text-slate-900">
                          {t.tilbakebetalingstid_aar} ar
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-500">Energibesparelse</p>
                        <p className="font-semibold text-slate-900">
                          {formatKwh(t.energibesparelse_kwh)}
                        </p>
                      </div>
                    </div>

                    {t.enova_stotte_kr > 0 && (
                      <div className="mt-3 flex items-center gap-3">
                        <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700">
                          <Leaf className="h-3 w-3" />
                          Enova-stotte: {formatKr(t.enova_stotte_kr)}
                        </span>
                        <span className="text-sm text-slate-500">
                          Netto kostnad:{' '}
                          <span className="font-semibold text-slate-900">
                            {formatKr(t.netto_kostnad_kr)}
                          </span>
                        </span>
                      </div>
                    )}
                  </div>
                ))}
            </div>
          </div>

          {/* 5. Enova-stotte oppsummering */}
          <div className="rounded-2xl border border-green-200 bg-green-50 p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-green-900 mb-3 flex items-center gap-2">
              <Leaf className="h-5 w-5 text-green-600" />
              Enova-stotte
            </h3>
            <p className="text-2xl font-bold text-green-700 mb-4">
              Opptil {formatKr(result.enova_muligheter.total_mulig_stotte_kr)}
            </p>
            <div className="space-y-2 mb-4">
              {result.enova_muligheter.tiltak_med_stotte.map((s, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-green-800">{s.tiltak}</span>
                  <div className="text-right">
                    <span className="font-semibold text-green-700">
                      {formatKr(s.maks_stotte)}
                    </span>
                    <p className="text-xs text-green-600">{s.vilkaar}</p>
                  </div>
                </div>
              ))}
            </div>
            <a
              href={result.enova_muligheter.lenke}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-green-700 hover:underline"
            >
              Sok om stotte pa enova.no
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </div>

          {/* 6. TEK17-sjekk */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
              {result.sammenligning_tek17.oppfyller_tek17 ? (
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              ) : (
                <XCircle className="h-5 w-5 text-red-500" />
              )}
              TEK17-sjekk
            </h3>

            {result.sammenligning_tek17.oppfyller_tek17 ? (
              <p className="text-sm text-green-700 font-medium">
                Boligen oppfyller TEK17-krav for energi.
              </p>
            ) : (
              <>
                <p className="text-sm text-red-700 font-medium mb-3">
                  Boligen oppfyller ikke TEK17-krav.
                </p>
                <ul className="space-y-1 mb-3">
                  {result.sammenligning_tek17.mangler.map((m, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-sm text-slate-600"
                    >
                      <XCircle className="h-4 w-4 text-red-400 mt-0.5 flex-shrink-0" />
                      {m}
                    </li>
                  ))}
                </ul>
                <p className="text-sm text-slate-500">
                  Estimert kostnad for TEK17-niva:{' '}
                  <span className="font-semibold text-slate-900">
                    {formatKr(
                      result.sammenligning_tek17.estimert_kostnad_tek17_nivaa
                    )}
                  </span>
                </p>
              </>
            )}
          </div>

          {/* 7. Energimerke-trapp */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">
              Energimerke-trapp
            </h3>
            <div className="space-y-2">
              {ALLE_MERKER.map((merke) => {
                const erNaa =
                  merke === result.energimerke_potensial.naavaerende;
                const erPotensial =
                  merke === result.energimerke_potensial.etter_alle_tiltak;
                const widths: Record<string, string> = {
                  A: 'w-[30%]',
                  B: 'w-[40%]',
                  C: 'w-[50%]',
                  D: 'w-[60%]',
                  E: 'w-[70%]',
                  F: 'w-[85%]',
                  G: 'w-full',
                };

                return (
                  <div key={merke} className="flex items-center gap-3">
                    <div
                      className={`${widths[merke]} ${ENERGIMERKE_FARGER[merke]} rounded-lg py-2 px-3 text-white text-sm font-bold flex items-center justify-between ${
                        erNaa || erPotensial
                          ? 'ring-2 ring-offset-2 ring-slate-900'
                          : 'opacity-50'
                      }`}
                    >
                      <span>{merke}</span>
                      <div className="flex gap-1.5">
                        {erNaa && (
                          <span className="text-xs font-medium bg-white/30 rounded px-1.5">
                            Na
                          </span>
                        )}
                        {erPotensial && (
                          <span className="text-xs font-medium bg-white/30 rounded px-1.5">
                            Potensial
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
            {result.energimerke_potensial.forbedring_steg.length > 0 && (
              <div className="mt-4 space-y-1">
                {result.energimerke_potensial.forbedring_steg.map((steg, i) => (
                  <p key={i} className="text-sm text-slate-600 flex items-center gap-2">
                    <ArrowRight className="h-3.5 w-3.5 text-green-500" />
                    {steg}
                  </p>
                ))}
              </div>
            )}
          </div>

          {/* Tips */}
          {result.tips && result.tips.length > 0 && (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-900 mb-3">
                Tips
              </h3>
              <ul className="space-y-2">
                {result.tips.map((tip, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-sm text-slate-600"
                  >
                    <Zap className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* CTA */}
          <div className="rounded-2xl bg-gradient-to-br from-green-600 to-teal-600 p-8 text-center text-white">
            <h3 className="text-xl font-bold mb-2">
              Vil du ha presis energiberegning?
            </h3>
            <p className="text-green-100 mb-5">
              Vi lager 3D-modell av boligen din for presis energiberegning og
              dokumentasjon.
            </p>
            <a
              href="mailto:hey@nops.no"
              className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-sm font-semibold text-green-700 hover:bg-green-50 transition-colors"
            >
              Kontakt hey@nops.no
              <ArrowRight className="h-4 w-4" />
            </a>
          </div>
        </div>
      )}
    </main>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatCard({
  icon,
  label,
  value,
  bg,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  bg: string;
}) {
  return (
    <div className={`rounded-2xl border border-slate-200 ${bg} p-4 shadow-sm`}>
      <div className="mb-2">{icon}</div>
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="text-base font-bold text-slate-900">{value}</p>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="text-sm text-slate-800">{value}</p>
    </div>
  );
}
