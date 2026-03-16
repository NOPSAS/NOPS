'use client';

import * as React from 'react';
import {
  MapPin,
  Building2,
  Sparkles,
  Calculator,
  CheckCircle2,
  ArrowRight,
  Loader2,
  Home,
  Trees,
  DollarSign,
  Hammer,
  Zap,
  Star,
  Package,
  ExternalLink,
  AlertCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { fetchJSON } from '@/lib/utils';

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface KostnadPost {
  post: string;
  belop: number;
}

interface KostnadResult {
  poster: KostnadPost[];
  total: number;
}

interface TomteAnalyse {
  areal_m2: number;
  maks_bya_prosent: number;
  maks_hoyde_m: number;
  tomtetype: string;
  solforhold: string;
}

interface Byggemulighet {
  husmodell: string;
  leverandor: string;
  bra_m2: number;
  etasjer: number;
  soverom: number;
  plasseringstips: string;
  passer_tomten: 'god' | 'middels' | 'utfordrende';
}

interface Kostnadsestimat {
  poster: KostnadPost[];
  total: number;
}

interface Leverandor {
  navn: string;
  type: string;
}

interface Presentasjonstekst {
  overskrift: string;
  ingress: string;
  hoveddel: string;
}

interface MulighetsstudieResult {
  tomteanalyse: TomteAnalyse;
  byggemuligheter: Byggemulighet[];
  kostnadsestimat: Kostnadsestimat;
  leverandorer: Leverandor[];
  presentasjonstekst: Presentasjonstekst;
  anbefalinger: string[];
}

/* ------------------------------------------------------------------ */
/*  Data                                                               */
/* ------------------------------------------------------------------ */

const leverandorerListe = [
  { navn: 'Nordbohus', type: 'Eneboliger' },
  { navn: 'Norgeshus', type: 'Eneboliger' },
  { navn: 'Alvsbyhus', type: 'Eneboliger' },
  { navn: 'BoligPartner', type: 'Eneboliger' },
  { navn: 'Mesterhus', type: 'Eneboliger' },
  { navn: 'Huscompagniet', type: 'Eneboliger' },
  { navn: 'Saltdalshytta', type: 'Hytter' },
  { navn: 'Hedda Hytter', type: 'Hytter' },
];

const steg = [
  {
    nummer: 1,
    tittel: 'Vi analyserer tomten',
    beskrivelse: 'Reguleringsplan, maks utnyttelse, solforhold, adkomst',
    icon: <MapPin className="h-6 w-6" />,
  },
  {
    nummer: 2,
    tittel: 'Vi designer løsninger',
    beskrivelse: 'Ferdighusmodeller plassert på tomten med kart og 3D',
    icon: <Home className="h-6 w-6" />,
  },
  {
    nummer: 3,
    tittel: 'Vi presenterer alt',
    beskrivelse: 'Komplett presentasjonsside med kostnadsoverslag og visualiseringer',
    icon: <Star className="h-6 w-6" />,
  },
];

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function formatKr(n: number): string {
  return n.toLocaleString('nb-NO', { maximumFractionDigits: 0 }) + ' kr';
}

function passerBadgeFarge(v: string): string {
  if (v === 'god') return 'bg-emerald-100 text-emerald-700';
  if (v === 'middels') return 'bg-amber-100 text-amber-700';
  return 'bg-red-100 text-red-700';
}

/* ------------------------------------------------------------------ */
/*  Page component                                                     */
/* ------------------------------------------------------------------ */

export default function TomterPage() {
  // Kostnadskalkulator state
  const [kalkTomtepris, setKalkTomtepris] = React.useState('');
  const [kalkFerdighuspris, setKalkFerdighuspris] = React.useState('');
  const [kalkHustype, setKalkHustype] = React.useState('enebolig');
  const [kalkBra, setKalkBra] = React.useState('150');
  const [kalkResult, setKalkResult] = React.useState<KostnadResult | null>(null);
  const [kalkLoading, setKalkLoading] = React.useState(false);
  const [kalkError, setKalkError] = React.useState('');

  // Mulighetsstudie state
  const [msAdresse, setMsAdresse] = React.useState('');
  const [msKommunenr, setMsKommunenr] = React.useState('');
  const [msGnr, setMsGnr] = React.useState('');
  const [msBnr, setMsBnr] = React.useState('');
  const [msTomtepris, setMsTomtepris] = React.useState('');
  const [msHustype, setMsHustype] = React.useState('enebolig');
  const [msAntallEnheter, setMsAntallEnheter] = React.useState('1');
  const [msFinnLink, setMsFinnLink] = React.useState('');
  const [msResult, setMsResult] = React.useState<MulighetsstudieResult | null>(null);
  const [msLoading, setMsLoading] = React.useState(false);
  const [msError, setMsError] = React.useState('');

  React.useEffect(() => {
    document.title = 'Tomtetjenesten \u2013 Mulighetsstudie og presentasjon | nops.no';
  }, []);

  /* Kostnadskalkulator submit */
  async function handleKalkSubmit(e: React.FormEvent) {
    e.preventDefault();
    setKalkLoading(true);
    setKalkError('');
    setKalkResult(null);
    try {
      const data = await fetchJSON<KostnadResult>('/api/v1/tomter/kostnadskalkulator', {
        method: 'POST',
        body: JSON.stringify({
          tomtepris: Number(kalkTomtepris),
          ferdighuspris: Number(kalkFerdighuspris),
          hustype: kalkHustype,
          bra_m2: Number(kalkBra),
        }),
      });
      setKalkResult(data);
    } catch (err: unknown) {
      setKalkError(err instanceof Error ? err.message : 'Noe gikk galt');
    } finally {
      setKalkLoading(false);
    }
  }

  /* Mulighetsstudie submit */
  async function handleMsSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsLoading(true);
    setMsError('');
    setMsResult(null);
    try {
      const data = await fetchJSON<MulighetsstudieResult>('/api/v1/tomter/mulighetsstudie', {
        method: 'POST',
        body: JSON.stringify({
          adresse: msAdresse,
          kommunenummer: msKommunenr,
          gnr: Number(msGnr),
          bnr: Number(msBnr),
          tomtepris: Number(msTomtepris),
          hustype: msHustype,
          antall_enheter: Number(msAntallEnheter),
          finn_lenke: msFinnLink || undefined,
        }),
      });
      setMsResult(data);
    } catch (err: unknown) {
      setMsError(err instanceof Error ? err.message : 'Noe gikk galt');
    } finally {
      setMsLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50">
      {/* ============================================================ */}
      {/*  HEADER                                                       */}
      {/* ============================================================ */}
      <section className="bg-gradient-to-br from-emerald-600 to-green-700 py-16 px-4 text-white">
        <div className="max-w-4xl mx-auto text-center">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-4 py-1.5 text-sm font-medium backdrop-blur mb-6">
            nops.no / Tomtetjenesten
          </span>
          <h1 className="text-3xl sm:text-5xl font-bold mb-4 leading-tight">
            Selg tomten raskere med mulighetsstudie
          </h1>
          <p className="text-lg sm:text-xl text-emerald-100 max-w-2xl mx-auto mb-8">
            Vi viser kj&oslash;perne n&oslash;yaktig hva som kan bygges, hva det koster og hvordan det ser ut &ndash; slik at tomten selger seg selv.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            {['Ferdighus-modeller', '3D-visualisering', 'Komplett kostnadskalkulator'].map((b) => (
              <span
                key={b}
                className="inline-flex items-center rounded-full bg-white/20 px-4 py-1.5 text-sm font-medium backdrop-blur"
              >
                {b}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  SLIK FUNGERER DET                                            */}
      {/* ============================================================ */}
      <section className="max-w-5xl mx-auto px-4 py-16">
        <h2 className="text-2xl font-bold text-slate-900 text-center mb-10">Slik fungerer det</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steg.map((s) => (
            <div key={s.nummer} className="flex flex-col items-center text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-600 mb-4">
                {s.icon}
              </div>
              <span className="text-xs font-semibold text-emerald-600 mb-1">Steg {s.nummer}</span>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">{s.tittel}</h3>
              <p className="text-sm text-slate-500">{s.beskrivelse}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ============================================================ */}
      {/*  PRISER                                                       */}
      {/* ============================================================ */}
      <section className="bg-white border-y border-slate-200 py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-slate-900 text-center mb-10">Priser</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Fastpris */}
            <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm flex flex-col">
              <h3 className="text-xl font-bold text-slate-900 mb-1">Fastpris</h3>
              <p className="text-3xl font-bold text-emerald-600 mb-1">15 000 kr <span className="text-base font-normal text-slate-400">+ mva per hus/hytte</span></p>
              <ul className="mt-6 space-y-3 flex-1">
                {[
                  'Mulighetsstudie',
                  'Inntil 3 husmodeller presentert',
                  'Kostnadskalkulator',
                  'Presentasjonsside',
                  'Kart og plassering',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2 text-sm text-slate-600">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500 mt-0.5 shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
              <a
                href="mailto:hey@nops.no?subject=Bestill mulighetsstudie"
                className="mt-8 inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white hover:bg-emerald-700 transition-colors"
              >
                Bestill mulighetsstudie
                <ArrowRight className="h-4 w-4" />
              </a>
            </div>

            {/* Provisjon */}
            <div className="rounded-2xl border-2 border-emerald-500 bg-emerald-50/50 p-8 shadow-sm flex flex-col relative">
              <span className="absolute -top-3 right-6 rounded-full bg-emerald-600 px-3 py-0.5 text-xs font-semibold text-white">Populær</span>
              <h3 className="text-xl font-bold text-slate-900 mb-1">Provisjon</h3>
              <p className="text-3xl font-bold text-emerald-600 mb-1">Kostnadsfritt <span className="text-base font-normal text-slate-400">&ndash; 2% av salgssum</span></p>
              <ul className="mt-6 space-y-3 flex-1">
                {[
                  'Alt i fastpris inkludert',
                  'Vi deler risikoen med deg',
                  'Betales kun ved salg',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2 text-sm text-slate-600">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500 mt-0.5 shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
              <a
                href="mailto:hey@nops.no?subject=Tomtetjenesten - provisjonsmodell"
                className="mt-8 inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white hover:bg-emerald-700 transition-colors"
              >
                Kontakt oss
                <ArrowRight className="h-4 w-4" />
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  FERDIGHUSLEVERANDORER                                        */}
      {/* ============================================================ */}
      <section className="max-w-5xl mx-auto px-4 py-16">
        <h2 className="text-2xl font-bold text-slate-900 text-center mb-10">
          Ferdighusleverand&oslash;rer vi samarbeider med
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {leverandorerListe.map((l) => (
            <div
              key={l.navn}
              className="flex flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <Building2 className="h-8 w-8 text-emerald-600 mb-2" />
              <span className="text-sm font-semibold text-slate-900">{l.navn}</span>
              <span className="text-xs text-slate-400">{l.type}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ============================================================ */}
      {/*  KOSTNADSKALKULATOR                                           */}
      {/* ============================================================ */}
      <section className="bg-white border-y border-slate-200 py-16 px-4">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Calculator className="h-6 w-6 text-emerald-600" />
            <h2 className="text-2xl font-bold text-slate-900">Kostnadskalkulator</h2>
          </div>
          <p className="text-slate-500 text-center mb-8">F&aring; et raskt overslag over totalkostnadene for tomt og ferdighus.</p>

          <form onSubmit={handleKalkSubmit} className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Tomtepris (kr)</label>
              <input
                type="number"
                value={kalkTomtepris}
                onChange={(e) => setKalkTomtepris(e.target.value)}
                required
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                placeholder="f.eks. 2000000"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Ferdighuspris (kr)</label>
              <input
                type="number"
                value={kalkFerdighuspris}
                onChange={(e) => setKalkFerdighuspris(e.target.value)}
                required
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                placeholder="f.eks. 3500000"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Hustype</label>
              <select
                value={kalkHustype}
                onChange={(e) => setKalkHustype(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              >
                <option value="enebolig">Enebolig</option>
                <option value="tomannsbolig">Tomannsbolig</option>
                <option value="hytte">Hytte</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">BRA (m&sup2;)</label>
              <input
                type="number"
                value={kalkBra}
                onChange={(e) => setKalkBra(e.target.value)}
                required
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                placeholder="150"
              />
            </div>
            <div className="sm:col-span-2">
              <button
                type="submit"
                disabled={kalkLoading}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white hover:bg-emerald-700 transition-colors disabled:opacity-50"
              >
                {kalkLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Calculator className="h-4 w-4" />}
                Beregn
              </button>
            </div>
          </form>

          {kalkError && (
            <div className="flex items-center gap-2 rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700 mb-4">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {kalkError}
            </div>
          )}

          {kalkResult && (
            <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200">
                    <th className="text-left px-4 py-3 font-semibold text-slate-700">Post</th>
                    <th className="text-right px-4 py-3 font-semibold text-slate-700">Bel&oslash;p</th>
                  </tr>
                </thead>
                <tbody>
                  {kalkResult.poster.map((p, i) => (
                    <tr key={i} className="border-b border-slate-100">
                      <td className="px-4 py-3 text-slate-600">{p.post}</td>
                      <td className="px-4 py-3 text-right text-slate-900 font-medium">{formatKr(p.belop)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="bg-emerald-50">
                    <td className="px-4 py-4 font-bold text-emerald-800 text-base">Totalt</td>
                    <td className="px-4 py-4 text-right font-bold text-emerald-800 text-xl">{formatKr(kalkResult.total)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          )}
        </div>
      </section>

      {/* ============================================================ */}
      {/*  MULIGHETSSTUDIE-BESTILLER                                    */}
      {/* ============================================================ */}
      <section className="max-w-3xl mx-auto px-4 py-16">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Sparkles className="h-6 w-6 text-purple-600" />
          <h2 className="text-2xl font-bold text-slate-900">Kj&oslash;r mulighetsstudie</h2>
        </div>
        <p className="text-slate-500 text-center mb-8">Fyll inn informasjon om tomten, s&aring; analyserer vi mulighetene.</p>

        <form onSubmit={handleMsSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Adresse</label>
            <input
              type="text"
              value={msAdresse}
              onChange={(e) => setMsAdresse(e.target.value)}
              required
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              placeholder="f.eks. Storgata 1, 0155 Oslo"
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Kommunenummer</label>
              <input
                type="text"
                value={msKommunenr}
                onChange={(e) => setMsKommunenr(e.target.value)}
                required
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                placeholder="0301"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Gnr</label>
              <input
                type="number"
                value={msGnr}
                onChange={(e) => setMsGnr(e.target.value)}
                required
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Bnr</label>
              <input
                type="number"
                value={msBnr}
                onChange={(e) => setMsBnr(e.target.value)}
                required
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              />
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Tomtepris (kr)</label>
              <input
                type="number"
                value={msTomtepris}
                onChange={(e) => setMsTomtepris(e.target.value)}
                required
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Hustype</label>
              <select
                value={msHustype}
                onChange={(e) => setMsHustype(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              >
                <option value="enebolig">Enebolig</option>
                <option value="tomannsbolig">Tomannsbolig</option>
                <option value="hytte">Hytte</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Antall enheter</label>
              <input
                type="number"
                value={msAntallEnheter}
                onChange={(e) => setMsAntallEnheter(e.target.value)}
                min={1}
                required
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Finn.no-lenke <span className="text-slate-400">(valgfritt)</span></label>
            <input
              type="url"
              value={msFinnLink}
              onChange={(e) => setMsFinnLink(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              placeholder="https://www.finn.no/realestate/..."
            />
          </div>
          <button
            type="submit"
            disabled={msLoading}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-purple-600 px-6 py-3 text-sm font-semibold text-white hover:bg-purple-700 transition-colors disabled:opacity-50"
          >
            {msLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            Kj&oslash;r mulighetsstudie
          </button>
        </form>

        {msError && (
          <div className="mt-4 flex items-center gap-2 rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {msError}
          </div>
        )}
      </section>

      {/* ============================================================ */}
      {/*  MULIGHETSSTUDIE RESULTAT                                     */}
      {/* ============================================================ */}
      {msResult && (
        <section className="max-w-5xl mx-auto px-4 pb-16 space-y-10">
          <div className="border-t border-slate-200 pt-10">
            <h2 className="text-2xl font-bold text-slate-900 text-center mb-10">Resultat av mulighetsstudie</h2>
          </div>

          {/* 1. Tomteanalyse */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <MapPin className="h-5 w-5 text-emerald-600" />
              Tomteanalyse
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
              {[
                { label: 'Areal', value: `${msResult.tomteanalyse.areal_m2} m\u00B2` },
                { label: 'Maks BYA', value: `${msResult.tomteanalyse.maks_bya_prosent}%` },
                { label: 'Maks h\u00F8yde', value: `${msResult.tomteanalyse.maks_hoyde_m} m` },
                { label: 'Tomtetype', value: msResult.tomteanalyse.tomtetype },
                { label: 'Solforhold', value: msResult.tomteanalyse.solforhold },
              ].map((item) => (
                <div key={item.label} className="rounded-xl bg-slate-50 p-3 text-center">
                  <p className="text-xs text-slate-400 mb-1">{item.label}</p>
                  <p className="text-sm font-semibold text-slate-900">{item.value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* 2. Byggemuligheter */}
          <div>
            <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <Home className="h-5 w-5 text-emerald-600" />
              Byggemuligheter
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {msResult.byggemuligheter.map((bm, i) => (
                <div key={i} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="text-base font-semibold text-slate-900">{bm.husmodell}</p>
                      <p className="text-xs text-slate-400">{bm.leverandor}</p>
                    </div>
                    <span className={cn('text-xs font-semibold px-2 py-0.5 rounded-full', passerBadgeFarge(bm.passer_tomten))}>
                      {bm.passer_tomten}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center mb-3">
                    <div className="rounded-lg bg-slate-50 p-2">
                      <p className="text-xs text-slate-400">BRA</p>
                      <p className="text-sm font-semibold">{bm.bra_m2} m&sup2;</p>
                    </div>
                    <div className="rounded-lg bg-slate-50 p-2">
                      <p className="text-xs text-slate-400">Etasjer</p>
                      <p className="text-sm font-semibold">{bm.etasjer}</p>
                    </div>
                    <div className="rounded-lg bg-slate-50 p-2">
                      <p className="text-xs text-slate-400">Soverom</p>
                      <p className="text-sm font-semibold">{bm.soverom}</p>
                    </div>
                  </div>
                  <p className="text-xs text-slate-500">{bm.plasseringstips}</p>
                </div>
              ))}
            </div>
          </div>

          {/* 3. Kostnadsestimat */}
          <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-emerald-600" />
              <h3 className="text-lg font-semibold text-slate-900">Kostnadsestimat</h3>
            </div>
            <table className="w-full text-sm">
              <tbody>
                {msResult.kostnadsestimat.poster.map((p, i) => (
                  <tr key={i} className="border-b border-slate-100">
                    <td className="px-6 py-3 text-slate-600">{p.post}</td>
                    <td className="px-6 py-3 text-right text-slate-900 font-medium">{formatKr(p.belop)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="bg-emerald-50">
                  <td className="px-6 py-4 font-bold text-emerald-800 text-base">Totalt</td>
                  <td className="px-6 py-4 text-right font-bold text-emerald-800 text-xl">{formatKr(msResult.kostnadsestimat.total)}</td>
                </tr>
              </tfoot>
            </table>
          </div>

          {/* 4. Leverandorer */}
          {msResult.leverandorer.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <Package className="h-5 w-5 text-emerald-600" />
                Ferdighusleverand&oslash;rer
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {msResult.leverandorer.map((l, i) => (
                  <div key={i} className="flex flex-col items-center rounded-xl border border-slate-200 bg-white p-4 text-center">
                    <Building2 className="h-6 w-6 text-emerald-600 mb-1" />
                    <span className="text-sm font-semibold text-slate-900">{l.navn}</span>
                    <span className="text-xs text-slate-400">{l.type}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 5. Presentasjonstekst */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900 mb-2 flex items-center gap-2">
              <Star className="h-5 w-5 text-emerald-600" />
              Presentasjonstekst
            </h3>
            <h4 className="text-xl font-bold text-slate-900 mb-2">{msResult.presentasjonstekst.overskrift}</h4>
            <p className="text-slate-600 font-medium mb-4">{msResult.presentasjonstekst.ingress}</p>
            <p className="text-sm text-slate-500 leading-relaxed whitespace-pre-line">{msResult.presentasjonstekst.hoveddel}</p>
          </div>

          {/* 6. Anbefalinger */}
          {msResult.anbefalinger.length > 0 && (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <Zap className="h-5 w-5 text-emerald-600" />
                Anbefalinger
              </h3>
              <ul className="space-y-2">
                {msResult.anbefalinger.map((a, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500 mt-0.5 shrink-0" />
                    {a}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 7. CTA */}
          <div className="rounded-2xl bg-emerald-50 border border-emerald-200 p-8 text-center">
            <h3 className="text-lg font-semibold text-emerald-800 mb-2">
              Vil du at vi lager en komplett presentasjonsside?
            </h3>
            <p className="text-sm text-emerald-600 mb-4">Ta kontakt, s&aring; hjelper vi deg videre.</p>
            <a
              href="mailto:hey@nops.no?subject=Komplett presentasjonsside"
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white hover:bg-emerald-700 transition-colors"
            >
              Kontakt hey@nops.no
              <ArrowRight className="h-4 w-4" />
            </a>
          </div>
        </section>
      )}

      {/* ============================================================ */}
      {/*  CTA BUNNLINJE                                                */}
      {/* ============================================================ */}
      <section className="bg-gradient-to-br from-emerald-600 to-green-700 py-16 px-4 text-center text-white">
        <h2 className="text-2xl font-bold mb-3">Har du en tomt som ikke selger?</h2>
        <p className="text-emerald-100 mb-6">Kontakt oss for en uforpliktende vurdering</p>
        <a
          href="mailto:hey@nops.no?subject=Uforpliktende vurdering av tomt"
          className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-sm font-semibold text-emerald-700 hover:bg-emerald-50 transition-colors"
        >
          hey@nops.no
          <ArrowRight className="h-4 w-4" />
        </a>
      </section>
    </main>
  );
}
