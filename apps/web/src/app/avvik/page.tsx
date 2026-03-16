'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  AlertTriangle,
  Upload,
  FileText,
  CheckCircle2,
  XCircle,
  Search,
  ArrowRight,
  Loader2,
  Building2,
  Shield,
  Users,
  Clock,
  ExternalLink,
  Info,
  Sparkles,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const STEG = [
  {
    nr: '1',
    tittel: 'Last opp dokumentasjon',
    beskrivelse: 'Boligannonse, salgsoppgave, takstrapport eller annen dokumentasjon som beskriver boligens rom og bruk.',
  },
  {
    nr: '2',
    tittel: 'Vi henter godkjente tegninger',
    beskrivelse: 'Vi innhenter sist godkjente plantegninger, byggesakstegninger og situasjonstegninger fra kommunen – eller du laster dem opp selv.',
  },
  {
    nr: '3',
    tittel: 'Faglig gjennomgang og rapport',
    beskrivelse: 'Kvalifiserte fagpersoner sammenligner annonsert bruk med godkjent bruk og leverer en tydelig vurdering.',
  },
];

const SJEKKER = [
  'Rom markedsført som soverom som er godkjent som bod',
  'Kjellerrom brukt som oppholdsrom uten godkjenning',
  'Loft eller hems brukt til boligformål uten godkjenning',
  'Utleiedeler uten godkjent bruksendring',
  'Planløsning som avviker fra godkjente tegninger',
  'Areal-avvik mellom annonse og godkjente tegninger',
];

const MAALGRUPPER = [
  { ikon: <Search className="h-5 w-5" />, tittel: 'Boligkjøpere', desc: 'Sjekk før du legger inn bud' },
  { ikon: <Building2 className="h-5 w-5" />, tittel: 'Boligeiere', desc: 'Sjekk før du legger ut for salg' },
  { ikon: <Users className="h-5 w-5" />, tittel: 'Eiendomsmeglere', desc: 'Kvalitetssikre objekter' },
  { ikon: <Shield className="h-5 w-5" />, tittel: 'Takstmenn', desc: 'Supplement til tilstandsrapport' },
  { ikon: <FileText className="h-5 w-5" />, tittel: 'Investorer', desc: 'Due diligence på eiendom' },
];

export default function AvvikPage() {
  const [finnUrl, setFinnUrl] = React.useState('');
  const [knr, setKnr] = React.useState('');
  const [gnr, setGnr] = React.useState('');
  const [bnr, setBnr] = React.useState('');
  const [filer, setFiler] = React.useState<File[]>([]);
  const [harEgneTegninger, setHarEgneTegninger] = React.useState(false);
  const [tegningFiler, setTegningFiler] = React.useState<File[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [bestilt, setBestilt] = React.useState(false);
  const fileRef = React.useRef<HTMLInputElement>(null);
  const tegningRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    document.title = 'Avviksdeteksjon – Faglig kontroll av bolig | nops.no';
  }, []);

  async function bestillKontroll() {
    setLoading(true);
    // I MVP: send bestilling til hey@nops.no via API
    // Senere: full automatisert flyt
    await new Promise((r) => setTimeout(r, 2000));
    setBestilt(true);
    setLoading(false);
  }

  return (
    <main className="bg-white">
      {/* Hero */}
      <section className="relative overflow-hidden bg-slate-950 text-white">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-1/2 top-1/3 -translate-x-1/2 h-[500px] w-[800px] rounded-full bg-red-600/15 blur-[120px]" />
        </div>
        <div className="relative z-10 mx-auto max-w-4xl px-4 pb-20 pt-24 text-center sm:pb-28 sm:pt-32">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-red-500/20 bg-red-500/10 px-5 py-2 text-sm font-medium text-red-300">
            <AlertTriangle className="h-4 w-4" />
            Flaggskiptjeneste
          </div>
          <h1 className="mx-auto max-w-3xl text-4xl font-extrabold leading-tight tracking-tight sm:text-5xl lg:text-6xl">
            Avviksdeteksjon
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-xl font-medium text-slate-300">
            Faglig kontroll av om annonsert bruk og areal samsvarer med sist godkjente tegninger fra kommunen.
          </p>
          <p className="mx-auto mt-4 max-w-xl text-base text-slate-400">
            Tjenesten avdekker avvik mellom det som markedsføres og det som er godkjent – slik at problemer oppdages før kjøp eller salg.
          </p>
          <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <a href="#bestill" className="inline-flex items-center gap-2 rounded-2xl bg-red-600 px-8 py-4 text-base font-semibold text-white shadow-lg shadow-red-600/20 transition hover:bg-red-500">
              Bestill avvikssjekk <ArrowRight className="h-5 w-5" />
            </a>
            <Link href="/property" className="inline-flex items-center gap-2 rounded-2xl border border-white/20 bg-white/5 px-8 py-4 text-base font-semibold text-white transition hover:bg-white/10">
              Gratis forhåndssjekk
            </Link>
          </div>
        </div>
      </section>

      {/* Hva vi sjekker */}
      <section className="border-b border-slate-100 bg-slate-50 px-4 py-20">
        <div className="mx-auto max-w-4xl">
          <h2 className="mb-3 text-center text-3xl font-extrabold text-slate-900">Hva kontrolleres?</h2>
          <p className="mx-auto mb-12 max-w-xl text-center text-lg text-slate-500">
            Vi sammenligner annonsert bruk mot godkjent bruk – punkt for punkt.
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            {SJEKKER.map((s) => (
              <div key={s} className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-5">
                <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
                <p className="text-sm font-medium text-slate-700">{s}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Formål */}
      <section className="px-4 py-20">
        <div className="mx-auto max-w-4xl">
          <h2 className="mb-10 text-center text-3xl font-extrabold text-slate-900">Formål</h2>
          <div className="grid gap-6 sm:grid-cols-2">
            {[
              { ikon: <Search className="h-6 w-6 text-blue-600" />, tekst: 'Avdekke avvik mellom annonsert bruk og godkjent bruk' },
              { ikon: <FileText className="h-6 w-6 text-blue-600" />, tekst: 'Avdekke avvik mellom oppgitt areal og godkjente tegninger' },
              { ikon: <Shield className="h-6 w-6 text-blue-600" />, tekst: 'Gi en faglig vurdering basert på dokumentasjon' },
              { ikon: <CheckCircle2 className="h-6 w-6 text-blue-600" />, tekst: 'Redusere risiko for konflikter, prisavslag eller byggesaksproblemer' },
            ].map((f) => (
              <div key={f.tekst} className="flex items-start gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-50">{f.ikon}</div>
                <p className="text-sm font-medium leading-relaxed text-slate-700">{f.tekst}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Slik fungerer det */}
      <section className="border-t border-slate-100 bg-slate-50 px-4 py-20">
        <div className="mx-auto max-w-4xl">
          <h2 className="mb-12 text-center text-3xl font-extrabold text-slate-900">Slik fungerer det</h2>
          <div className="grid gap-8 md:grid-cols-3">
            {STEG.map((s) => (
              <div key={s.nr} className="flex flex-col items-center text-center">
                <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-red-600 text-xl font-bold text-white shadow-lg shadow-red-600/20">
                  {s.nr}
                </div>
                <h3 className="mb-2 text-base font-bold text-slate-900">{s.tittel}</h3>
                <p className="text-sm leading-relaxed text-slate-500">{s.beskrivelse}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Bestillingsskjema */}
      <section id="bestill" className="px-4 py-20">
        <div className="mx-auto max-w-3xl">
          <h2 className="mb-3 text-center text-3xl font-extrabold text-slate-900">Bestill avvikskontroll</h2>
          <p className="mx-auto mb-10 max-w-lg text-center text-slate-500">
            Last opp dokumentasjon, så tar vi oss av resten. Levering 3–5 virkedager etter mottatt tegninger.
          </p>

          {bestilt ? (
            <div className="rounded-2xl border-2 border-green-200 bg-green-50 p-10 text-center">
              <CheckCircle2 className="mx-auto mb-4 h-12 w-12 text-green-600" />
              <h3 className="mb-2 text-xl font-bold text-green-900">Bestilling mottatt!</h3>
              <p className="text-sm text-green-700">
                Vi innhenter godkjente tegninger fra kommunen og starter gjennomgangen.
                Du hører fra oss innen 1 virkedag.
              </p>
              <p className="mt-4 text-xs text-green-600">Bekreftelse sendes til din e-postadresse.</p>
            </div>
          ) : (
            <div className="space-y-6 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
              {/* Eiendom */}
              <div>
                <label className="mb-2 block text-sm font-semibold text-slate-700">Eiendom</label>
                <div className="grid grid-cols-3 gap-3">
                  <input type="text" placeholder="Kommunenr." value={knr} onChange={(e) => setKnr(e.target.value)}
                    className="rounded-xl border border-slate-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-red-500" />
                  <input type="number" placeholder="Gnr." value={gnr} onChange={(e) => setGnr(e.target.value)}
                    className="rounded-xl border border-slate-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-red-500" />
                  <input type="number" placeholder="Bnr." value={bnr} onChange={(e) => setBnr(e.target.value)}
                    className="rounded-xl border border-slate-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-red-500" />
                </div>
              </div>

              {/* Finn.no-lenke */}
              <div>
                <label className="mb-2 block text-sm font-semibold text-slate-700">Finn.no-lenke (valgfritt)</label>
                <div className="flex items-center gap-2 rounded-xl border border-slate-300 px-4 py-3">
                  <ExternalLink className="h-4 w-4 shrink-0 text-slate-400" />
                  <input type="url" placeholder="https://www.finn.no/realestate/homes/ad.html?finnkode=..." value={finnUrl}
                    onChange={(e) => setFinnUrl(e.target.value)}
                    className="w-full text-sm focus:outline-none" />
                </div>
              </div>

              {/* Dokumentasjon */}
              <div>
                <label className="mb-2 block text-sm font-semibold text-slate-700">
                  Dokumentasjon (annonse, salgsoppgave, takstrapport)
                </label>
                <button type="button" onClick={() => fileRef.current?.click()}
                  className="flex w-full items-center justify-center gap-3 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 p-6 transition hover:border-red-400 hover:bg-red-50">
                  <Upload className="h-5 w-5 text-slate-400" />
                  <span className="text-sm text-slate-600">
                    {filer.length > 0 ? `${filer.length} fil(er) valgt` : 'Last opp dokumenter (PDF, bilder)'}
                  </span>
                </button>
                <input ref={fileRef} type="file" multiple accept=".pdf,image/*" className="hidden"
                  onChange={(e) => setFiler(Array.from(e.target.files || []))} />
              </div>

              {/* Godkjente tegninger */}
              <div>
                <div className="mb-3 flex items-center gap-3">
                  <label className="text-sm font-semibold text-slate-700">Godkjente tegninger</label>
                  <label className="flex items-center gap-2 text-sm text-slate-500">
                    <input type="checkbox" checked={harEgneTegninger}
                      onChange={(e) => setHarEgneTegninger(e.target.checked)}
                      className="rounded border-slate-300" />
                    Jeg har egne tegninger
                  </label>
                </div>

                {harEgneTegninger ? (
                  <div>
                    <button type="button" onClick={() => tegningRef.current?.click()}
                      className="flex w-full items-center justify-center gap-3 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 p-6 transition hover:border-blue-400 hover:bg-blue-50">
                      <FileText className="h-5 w-5 text-slate-400" />
                      <span className="text-sm text-slate-600">
                        {tegningFiler.length > 0 ? `${tegningFiler.length} tegning(er) valgt` : 'Last opp godkjente tegninger'}
                      </span>
                    </button>
                    <input ref={tegningRef} type="file" multiple accept=".pdf,image/*,.dwg" className="hidden"
                      onChange={(e) => setTegningFiler(Array.from(e.target.files || []))} />
                  </div>
                ) : (
                  <div className="rounded-xl border border-green-200 bg-green-50 p-4">
                    <p className="flex items-center gap-2 text-sm font-medium text-green-800">
                      <CheckCircle2 className="h-4 w-4" />
                      Vi innhenter godkjente tegninger fra kommunen for deg – gratis
                    </p>
                    <p className="mt-1 text-xs text-green-600">
                      Innsynsbegjæring sendes automatisk. Kommunen svarer normalt innen 1–3 virkedager.
                    </p>
                  </div>
                )}
              </div>

              {/* Pris */}
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-bold text-slate-900">Avvikskontroll</p>
                    <p className="text-xs text-slate-500">Faglig gjennomgang med rapport · 3–5 virkedager</p>
                  </div>
                  <p className="text-2xl font-extrabold text-slate-900">4 900 kr</p>
                </div>
                <p className="mt-2 text-xs text-slate-400">ekskl. mva. Faktureres etter gjennomført kontroll.</p>
              </div>

              <button type="button" onClick={bestillKontroll} disabled={loading || (!knr && !finnUrl)}
                className="flex w-full items-center justify-center gap-2 rounded-2xl bg-red-600 py-4 text-base font-semibold text-white shadow-lg shadow-red-600/20 transition hover:bg-red-500 disabled:opacity-50">
                {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Sparkles className="h-5 w-5" />}
                {loading ? 'Sender bestilling...' : 'Bestill avvikskontroll'}
              </button>
            </div>
          )}
        </div>
      </section>

      {/* Resultat/leveranse */}
      <section className="border-t border-slate-100 bg-slate-50 px-4 py-20">
        <div className="mx-auto max-w-4xl">
          <h2 className="mb-10 text-center text-3xl font-extrabold text-slate-900">Hva du mottar</h2>
          <div className="grid gap-6 md:grid-cols-2">
            <div className="rounded-2xl border-2 border-green-200 bg-green-50 p-8">
              <CheckCircle2 className="mb-4 h-8 w-8 text-green-600" />
              <h3 className="mb-2 text-lg font-bold text-green-900">Ingen avvik</h3>
              <p className="text-sm text-green-700">
                &ldquo;Det er ikke identifisert avvik mellom annonsert bruk og godkjente tegninger.&rdquo;
              </p>
              <p className="mt-3 text-xs text-green-600">
                Du kan trygt gå videre med kjøp eller salg.
              </p>
            </div>
            <div className="rounded-2xl border-2 border-red-200 bg-red-50 p-8">
              <XCircle className="mb-4 h-8 w-8 text-red-600" />
              <h3 className="mb-2 text-lg font-bold text-red-900">Avvik identifisert</h3>
              <p className="text-sm text-red-700">
                &ldquo;Det er identifisert mulige eller klare avvik.&rdquo;
              </p>
              <p className="mt-3 text-xs text-red-600">
                Rapporten beskriver hvert avvik med anbefalt videre handling.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Videre oppfølging */}
      <section className="px-4 py-20">
        <div className="mx-auto max-w-4xl">
          <h2 className="mb-3 text-center text-2xl font-extrabold text-slate-900">Trenger du hjelp videre?</h2>
          <p className="mx-auto mb-10 max-w-lg text-center text-slate-500">
            Dersom avvik identifiseres kan vi hjelpe med videre arbeid:
          </p>
          <div className="grid gap-4 sm:grid-cols-3">
            {[
              { href: '/dispensasjon', tittel: 'Bruksendring', desc: 'Søknad om å endre bruk av rom' },
              { href: '/tjenester', tittel: 'Oppdaterte tegninger', desc: 'Vi tegner opp faktisk tilstand' },
              { href: '/dispensasjon', tittel: 'Dispensasjon', desc: 'Søknad om unntak fra krav' },
              { href: '/ferdigattest', tittel: 'Ferdigattest', desc: 'Ordne manglende ferdigattest' },
              { href: '/situasjonsplan', tittel: 'Situasjonsplan', desc: 'Oppdatert kart til søknad' },
              { href: '/naboklage', tittel: 'Nabovarsel', desc: 'Håndtering av nabovarsling' },
            ].map((t) => (
              <Link key={t.tittel} href={t.href}
                className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-5 transition hover:border-blue-300 hover:shadow-md">
                <ArrowRight className="mt-0.5 h-4 w-4 shrink-0 text-blue-600" />
                <div>
                  <p className="text-sm font-semibold text-slate-900">{t.tittel}</p>
                  <p className="text-xs text-slate-500">{t.desc}</p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Målgrupper */}
      <section className="border-t border-slate-100 bg-slate-50 px-4 py-16">
        <div className="mx-auto max-w-4xl">
          <h2 className="mb-8 text-center text-2xl font-bold text-slate-900">Hvem er tjenesten for?</h2>
          <div className="flex flex-wrap items-center justify-center gap-4">
            {MAALGRUPPER.map((m) => (
              <div key={m.tittel} className="flex items-center gap-3 rounded-full border border-slate-200 bg-white px-5 py-3 shadow-sm">
                <span className="text-slate-500">{m.ikon}</span>
                <div>
                  <span className="text-sm font-semibold text-slate-900">{m.tittel}</span>
                  <span className="ml-2 text-xs text-slate-400">{m.desc}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Avgrensning */}
      <section className="px-4 py-12">
        <div className="mx-auto max-w-3xl rounded-2xl border border-amber-200 bg-amber-50 p-6">
          <div className="flex items-start gap-3">
            <Info className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />
            <div>
              <p className="text-sm font-semibold text-amber-900">Avgrensninger</p>
              <p className="mt-1 text-xs leading-relaxed text-amber-700">
                Tjenesten er basert på tilgjengelig dokumentasjon og inkluderer ikke fysisk befaring,
                oppmåling av areal, juridisk garanti for lovlighet eller full byggesaksanalyse.
                Resultatet er en faglig vurdering basert på dokumenter.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-slate-900 px-4 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="mb-4 text-3xl font-extrabold text-white">
            Usikker på om boligen er lovlig?
          </h2>
          <p className="mx-auto mb-8 max-w-md text-slate-400">
            Sjekk gratis med vår forhåndskontroll, eller bestill full faglig gjennomgang.
          </p>
          <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
            <Link href="/property"
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-white px-8 py-4 text-base font-semibold text-slate-900 transition hover:bg-slate-100">
              Gratis forhåndssjekk
            </Link>
            <a href="#bestill"
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-red-600 px-8 py-4 text-base font-semibold text-white transition hover:bg-red-500">
              Bestill avvikskontroll – 4 900 kr
            </a>
          </div>
        </div>
      </section>
    </main>
  );
}
