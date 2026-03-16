import Link from 'next/link';
import type { Metadata } from 'next';
import {
  AlertTriangle,
  Box,
  FileText,
  Search,
  ArrowRight,
  CheckCircle2,
  Shield,
  Zap,
  Star,
  Building2,
  Trees,
  Camera,
  Clock,
  MapPin,
} from 'lucide-react';

export const metadata: Metadata = {
  title: 'nops.no – Sjekk eiendommen din gratis | Avviksdeteksjon og byggesøknad',
  description:
    'Norges ledende plattform for eiendom og byggesak. Avviksdeteksjon, 2D til 3D, byggesøknad og 20+ tjenester. Søk opp adressen gratis.',
  openGraph: {
    title: 'nops.no – Sjekk eiendommen din gratis',
    description: 'Avviksdeteksjon, 2D til 3D, byggesøknad og 20+ tjenester for eiendom.',
    siteName: 'nops.no',
  },
};

export default function LandingPage() {
  return (
    <main>
      {/* ━━━━━━━━━━━━━━━━━━━━ HERO ━━━━━━━━━━━━━━━━━━━━ */}
      <section className="relative overflow-hidden bg-[#0a0f1e] text-white">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-1/2 top-1/3 -translate-x-1/2 h-[600px] w-[900px] rounded-full bg-blue-600/10 blur-[140px]" />
        </div>

        <div className="relative z-10 mx-auto max-w-5xl px-6 pb-28 pt-32 sm:pb-36 sm:pt-40">
          <p className="mb-8 text-sm font-medium uppercase tracking-widest text-blue-400">
            Eiendomsintelligens for profesjonelle
          </p>

          <h1 className="max-w-3xl text-[2.75rem] font-extrabold leading-[1.08] tracking-tight sm:text-6xl lg:text-7xl">
            Vi finner avvik<br className="hidden sm:block" />
            <span className="text-blue-400">før de blir et problem</span>
          </h1>

          <p className="mt-7 max-w-xl text-lg leading-relaxed text-slate-400">
            nops.no sammenligner godkjente tegninger med faktisk bruk – automatisk.
            Avviksdeteksjon, byggesøknad, 2D til 3D og 20+ tjenester for eiendom.
          </p>

          <div className="mt-10 flex flex-col gap-4 sm:flex-row">
            <Link
              href="/property"
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-7 py-4 text-[15px] font-semibold text-white transition hover:bg-blue-500"
            >
              Sjekk eiendom gratis <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/avvik"
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/15 bg-white/5 px-7 py-4 text-[15px] font-semibold text-white transition hover:bg-white/10"
            >
              Bestill avvikskontroll
            </Link>
          </div>

          <div className="mt-14 flex flex-wrap gap-x-8 gap-y-3 text-[13px] text-slate-500">
            <span className="flex items-center gap-1.5"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> Gratis eiendomssjekk</span>
            <span className="flex items-center gap-1.5"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> Tilgjengelig via e-Torg (Norkart)</span>
            <span className="flex items-center gap-1.5"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> 100 % offentlige data</span>
          </div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━ TRE HOVEDPRODUKTER ━━━━━━━━━━━━━━━ */}
      <section className="bg-white px-6 py-28">
        <div className="mx-auto max-w-6xl">
          <p className="text-center text-sm font-semibold uppercase tracking-widest text-blue-600">Våre tjenester</p>
          <h2 className="mt-3 text-center text-3xl font-extrabold text-slate-900 sm:text-4xl">
            Tre produkter. Ett mål.
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-center text-[17px] leading-relaxed text-slate-500">
            Alt du trenger for å kontrollere, dokumentere og utvikle eiendom.
          </p>

          <div className="mt-16 grid gap-8 lg:grid-cols-3">
            {/* AVVIKSDETEKSJON */}
            <div className="group flex flex-col rounded-2xl border border-slate-200 bg-white p-8 transition hover:border-red-300 hover:shadow-xl">
              <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-red-50">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>
              <p className="text-xs font-bold uppercase tracking-widest text-red-600">Flaggskip · Gratis</p>
              <h3 className="mt-2 text-xl font-bold text-slate-900">Avviksdeteksjon</h3>
              <p className="mt-3 flex-1 text-[15px] leading-relaxed text-slate-500">
                Faglig kontroll av om annonsert bruk og areal samsvarer med
                godkjente tegninger. Vi sammenligner – du slipper overraskelser.
              </p>
              <ul className="mt-6 space-y-2">
                {['Godkjent bruk vs. faktisk bruk', 'Areal-avvik', 'Manglende ferdigattest', 'Finn.no-analyse'].map((t) => (
                  <li key={t} className="flex items-center gap-2 text-sm text-slate-600">
                    <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-red-500" />{t}
                  </li>
                ))}
              </ul>
              <Link href="/avvik" className="mt-8 inline-flex items-center gap-1.5 text-sm font-semibold text-red-600 transition hover:text-red-700">
                Bestill avvikskontroll <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            {/* 2D TIL 3D */}
            <div className="group flex flex-col rounded-2xl border border-slate-200 bg-white p-8 transition hover:border-blue-300 hover:shadow-xl">
              <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50">
                <Box className="h-6 w-6 text-blue-600" />
              </div>
              <p className="text-xs font-bold uppercase tracking-widest text-blue-600">Tilgjengelig via e-Torg</p>
              <h3 className="mt-2 text-xl font-bold text-slate-900">2D til 3D</h3>
              <p className="mt-3 flex-1 text-[15px] leading-relaxed text-slate-500">
                Vi konverterer plantegninger til komplette 3D-modeller.
                Leveres som IFC, SketchUp eller Revit – klar for prosjektering.
              </p>
              <ul className="mt-6 space-y-2">
                {['Plantegning → 3D-modell', 'IFC / SKP / RVT', 'Energiberegning', 'Fotorealistisk render'].map((t) => (
                  <li key={t} className="flex items-center gap-2 text-sm text-slate-600">
                    <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-blue-500" />{t}
                  </li>
                ))}
              </ul>
              <Link href="/visualisering" className="mt-8 inline-flex items-center gap-1.5 text-sm font-semibold text-blue-600 transition hover:text-blue-700">
                Se visualisering <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            {/* BYGGESØKNAD */}
            <div className="group flex flex-col rounded-2xl border border-slate-200 bg-white p-8 transition hover:border-emerald-300 hover:shadow-xl">
              <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-50">
                <FileText className="h-6 w-6 text-emerald-600" />
              </div>
              <p className="text-xs font-bold uppercase tracking-widest text-emerald-600">Komplett leveranse</p>
              <h3 className="mt-2 text-xl font-bold text-slate-900">Byggesøknad</h3>
              <p className="mt-3 flex-1 text-[15px] leading-relaxed text-slate-500">
                Vi tegner, søker og følger opp. Tilbygg, påbygg, bruksendring,
                garasje, tomtedeling og dispensasjon – fra A til Å.
              </p>
              <ul className="mt-6 space-y-2">
                {['Tegninger og søknad', 'Dispensasjon', 'Nabovarsel', 'Situasjonsplan', 'Ferdigattest'].map((t) => (
                  <li key={t} className="flex items-center gap-2 text-sm text-slate-600">
                    <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-500" />{t}
                  </li>
                ))}
              </ul>
              <Link href="/tjenester" className="mt-8 inline-flex items-center gap-1.5 text-sm font-semibold text-emerald-600 transition hover:text-emerald-700">
                Se alle tjenester <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━ GRATIS EIENDOMSSJEKK ━━━━━━━━━━━━━ */}
      <section className="bg-slate-50 px-6 py-24">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-3xl font-extrabold text-slate-900 sm:text-4xl">
            Søk opp eiendommen din – helt gratis
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-[17px] text-slate-500">
            Skriv inn adressen og få øyeblikkelig innsikt i byggesaker, reguleringsplan,
            DOK-analyse, ferdigattest og potensielle avvik.
          </p>

          <Link
            href="/property"
            className="group mx-auto mt-10 flex max-w-xl items-center gap-4 rounded-2xl border border-slate-200 bg-white px-6 py-5 shadow-sm transition hover:border-blue-400 hover:shadow-lg"
          >
            <Search className="h-6 w-6 shrink-0 text-slate-400" />
            <span className="flex-1 text-left text-lg text-slate-400">Skriv inn adresse...</span>
            <span className="shrink-0 rounded-xl bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white transition group-hover:bg-blue-500">
              Søk
            </span>
          </Link>

          <div className="mx-auto mt-10 grid max-w-2xl grid-cols-2 gap-4 sm:grid-cols-4">
            {[
              { ikon: <Building2 className="h-5 w-5" />, tekst: 'Matrikkeldata' },
              { ikon: <FileText className="h-5 w-5" />, tekst: 'Byggesaker' },
              { ikon: <MapPin className="h-5 w-5" />, tekst: 'Reguleringsplan' },
              { ikon: <Zap className="h-5 w-5" />, tekst: 'Energimerke' },
            ].map((i) => (
              <div key={i.tekst} className="flex flex-col items-center gap-2 rounded-xl bg-white p-4 shadow-sm">
                <span className="text-blue-600">{i.ikon}</span>
                <span className="text-xs font-semibold text-slate-700">{i.tekst}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━ SLIK FUNGERER DET ━━━━━━━━━━━━━━━━ */}
      <section className="bg-white px-6 py-28">
        <div className="mx-auto max-w-5xl">
          <p className="text-center text-sm font-semibold uppercase tracking-widest text-blue-600">Prosessen</p>
          <h2 className="mt-3 text-center text-3xl font-extrabold text-slate-900 sm:text-4xl">
            Fra adresse til innsikt på sekunder
          </h2>

          <div className="mt-16 grid gap-12 md:grid-cols-3">
            {[
              { nr: '01', tittel: 'Søk opp', tekst: 'Skriv inn adresse. Vi henter data fra Kartverket, eByggesak, DOK, Planslurpen og mer.' },
              { nr: '02', tittel: 'Se innsikt', tekst: 'Avvik, reguleringsplan, energimerke, byggesaker og verdiestimering – samlet på ett sted.' },
              { nr: '03', tittel: 'Bestill tjeneste', tekst: 'Trenger du tegninger, søknad eller avvikskontroll? Vi leverer komplett.' },
            ].map((s) => (
              <div key={s.nr} className="text-center">
                <p className="text-5xl font-extrabold text-slate-100">{s.nr}</p>
                <h3 className="mt-4 text-lg font-bold text-slate-900">{s.tittel}</h3>
                <p className="mt-2 text-[15px] leading-relaxed text-slate-500">{s.tekst}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━ TOMTETJENESTEN ━━━━━━━━━━━━━━━━ */}
      <section className="bg-slate-50 px-6 py-24">
        <div className="mx-auto flex max-w-5xl flex-col items-center gap-12 lg:flex-row">
          <div className="flex-1">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-emerald-50 px-4 py-1.5 text-xs font-semibold text-emerald-700">
              <Trees className="h-3.5 w-3.5" /> Tomtetjenesten
            </div>
            <h2 className="text-3xl font-extrabold text-slate-900">
              Selg tomten raskere
            </h2>
            <p className="mt-4 max-w-md text-[15px] leading-relaxed text-slate-500">
              Vi lager mulighetsstudie med ferdighusmodeller, kostnadskalkulator
              og komplett presentasjon. Kjøperne ser potensialet – tomten selger seg selv.
            </p>
            <div className="mt-6 flex gap-6">
              <div>
                <p className="text-2xl font-extrabold text-slate-900">15 000 kr</p>
                <p className="text-xs text-slate-500">fastpris per hus</p>
              </div>
              <div className="border-l border-slate-200 pl-6">
                <p className="text-2xl font-extrabold text-slate-900">2 %</p>
                <p className="text-xs text-slate-500">av salgssum (alternativ)</p>
              </div>
            </div>
            <Link href="/tomter" className="mt-8 inline-flex items-center gap-2 text-sm font-semibold text-emerald-600 transition hover:text-emerald-700">
              Les mer om tomtetjenesten <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="grid w-full max-w-sm grid-cols-2 gap-3">
            {['Nordbohus', 'Norgeshus', 'Alvsbyhus', 'BoligPartner', 'Mesterhus', 'Huscompagniet'].map((l) => (
              <div key={l} className="flex items-center justify-center rounded-xl border border-slate-200 bg-white py-4 text-sm font-semibold text-slate-600">
                {l}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━ TILLIT ━━━━━━━━━━━━━━━━ */}
      <section className="bg-white px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <div className="mb-10 flex items-center justify-center gap-1">
            {[1,2,3,4,5].map((i) => (
              <Star key={i} className="h-5 w-5 fill-yellow-400 text-yellow-400" />
            ))}
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {[
              { q: 'Med nops.no gjør jeg eiendomssjekken på fem minutter i stedet for en halv dag.', n: 'Marie Andersen', t: 'Arkitekt MNAL, Oslo' },
              { q: 'AI-analysen fanger opp dispensasjonsbehov jeg lett kunne oversett. Uunnværlig.', n: 'Torbjørn Hegdahl', t: 'Sivilarkitekt, Bergen' },
              { q: 'Vi bruker nops.no på alle nye prosjekter. Reduserer risiko og gir bedre svar i første møte.', n: 'Ingrid Solberg', t: 'Partner, Arkitektkontor AS' },
            ].map((t) => (
              <div key={t.n} className="rounded-2xl border border-slate-100 bg-slate-50 p-6">
                <p className="text-[15px] italic leading-relaxed text-slate-600">&ldquo;{t.q}&rdquo;</p>
                <div className="mt-5 border-t border-slate-200 pt-4">
                  <p className="text-sm font-semibold text-slate-900">{t.n}</p>
                  <p className="text-xs text-slate-500">{t.t}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-14 flex flex-wrap items-center justify-center gap-8 text-sm text-slate-400">
            {[
              { i: <Shield className="h-4 w-4" />, t: 'GDPR-kompatibel' },
              { i: <Building2 className="h-4 w-4" />, t: 'Offentlige data' },
              { i: <Clock className="h-4 w-4" />, t: 'Sanntidsdata' },
              { i: <MapPin className="h-4 w-4" />, t: '100+ kommuner' },
            ].map((s) => (
              <span key={s.t} className="flex items-center gap-1.5">{s.i} {s.t}</span>
            ))}
          </div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━ PRISER ━━━━━━━━━━━━━━━━ */}
      <section className="bg-slate-50 px-6 py-24">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-3xl font-extrabold text-slate-900">Kom i gang gratis</h2>
          <p className="mt-3 text-slate-500">Oppgrader når du trenger mer.</p>
        </div>

        <div className="mx-auto mt-12 grid max-w-4xl gap-6 md:grid-cols-3">
          {/* Gratis */}
          <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-8">
            <h3 className="text-lg font-bold text-slate-900">Gratis</h3>
            <p className="mt-1 text-4xl font-extrabold text-slate-900">0 <span className="text-base font-normal text-slate-400">kr/mnd</span></p>
            <ul className="mt-6 flex-1 space-y-2.5">
              {['5 eiendomsoppslag', 'Matrikkeldata', 'Byggesaker', 'Reguleringsplan', 'DOK-analyse'].map((f) => (
                <li key={f} className="flex items-center gap-2 text-sm text-slate-600">
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" />{f}
                </li>
              ))}
            </ul>
            <Link href="/register" className="mt-8 block rounded-xl border border-slate-200 py-3 text-center text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
              Opprett gratis konto
            </Link>
          </div>

          {/* Starter */}
          <div className="relative flex flex-col rounded-2xl border-2 border-blue-600 bg-white p-8 shadow-lg shadow-blue-600/10">
            <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-blue-600 px-4 py-1 text-xs font-semibold text-white">Populær</span>
            <h3 className="text-lg font-bold text-slate-900">Starter</h3>
            <p className="mt-1 text-4xl font-extrabold text-slate-900">499 <span className="text-base font-normal text-slate-400">kr/mnd</span></p>
            <ul className="mt-6 flex-1 space-y-2.5">
              {['Ubegrenset oppslag', 'AI-risikoanalyse', 'Avviksdeteksjon', 'PDF-rapporter', 'Finn-analyse', 'Energirådgivning'].map((f) => (
                <li key={f} className="flex items-center gap-2 text-sm text-slate-600">
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-blue-500" />{f}
                </li>
              ))}
            </ul>
            <Link href="/register" className="mt-8 block rounded-xl bg-blue-600 py-3 text-center text-sm font-semibold text-white transition hover:bg-blue-500">
              Start Starter
            </Link>
          </div>

          {/* Professional */}
          <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-8">
            <h3 className="text-lg font-bold text-slate-900">Professional</h3>
            <p className="mt-1 text-4xl font-extrabold text-slate-900">999 <span className="text-base font-normal text-slate-400">kr/mnd</span></p>
            <ul className="mt-6 flex-1 space-y-2.5">
              {['Alt i Starter', 'API-tilgang', 'Team-administrasjon', 'Hvit-etikett', 'Prioritert support'].map((f) => (
                <li key={f} className="flex items-center gap-2 text-sm text-slate-600">
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" />{f}
                </li>
              ))}
            </ul>
            <Link href="/register" className="mt-8 block rounded-xl border border-slate-200 py-3 text-center text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
              Start Professional
            </Link>
          </div>
        </div>
        <p className="mt-6 text-center text-sm text-slate-400">
          Ingen bindingstid · <Link href="/pricing" className="text-blue-600 hover:underline">Se alle priser</Link>
        </p>
      </section>

      {/* ━━━━━━━━━━━━━━━━ CTA ━━━━━━━━━━━━━━━━ */}
      <section className="bg-[#0a0f1e] px-6 py-24">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-extrabold text-white sm:text-4xl">
            Klar for å sjekke eiendommen?
          </h2>
          <p className="mt-4 text-lg text-slate-400">
            Søk opp adressen og få innsikt på sekunder. Helt gratis.
          </p>
          <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:justify-center">
            <Link href="/property" className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-8 py-4 text-base font-semibold text-white transition hover:bg-blue-500">
              Søk opp eiendom gratis <ArrowRight className="h-5 w-5" />
            </Link>
            <Link href="/avvik" className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/15 bg-white/5 px-8 py-4 text-base font-semibold text-white transition hover:bg-white/10">
              Bestill avvikskontroll
            </Link>
          </div>
          <p className="mt-8 text-sm text-slate-500">
            Spørsmål? <a href="mailto:hey@nops.no" className="text-slate-400 underline hover:text-white">hey@nops.no</a>
          </p>
        </div>
      </section>
    </main>
  );
}
