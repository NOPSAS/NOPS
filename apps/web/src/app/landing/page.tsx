import Link from 'next/link';
import type { Metadata } from 'next';
import {
  Building2,
  FileText,
  Camera,
  Trees,
  AlertTriangle,
  Search,
  Shield,
  CheckCircle2,
  ArrowRight,
  Star,
  Zap,
  MapPin,
  Scale,
  Users,
  Award,
  TrendingUp,
  BarChart3,
  Sparkles,
  Clock,
  Package,
} from 'lucide-react';

export const metadata: Metadata = {
  title:
    'nops.no – Sjekk eiendommen din gratis | Norges ledende eiendomsplattform',
  description:
    'Avviksdeteksjon, byggesøknad, 2D til 3D, energirådgivning og 20+ tjenester for eiendom. Søk opp adressen og få innsikt på sekunder. Gratis å starte.',
  openGraph: {
    title:
      'nops.no – Sjekk eiendommen din gratis | Norges ledende eiendomsplattform',
    description:
      'Avviksdeteksjon, byggesøknad, 2D til 3D, energirådgivning og 20+ tjenester for eiendom. Søk opp adressen og få innsikt på sekunder.',
    siteName: 'nops.no',
  },
};

export default function LandingPage() {
  return (
    <main className="bg-white">
      {/* ───────────────────────────── 1. HERO ───────────────────────────── */}
      <section className="relative overflow-hidden bg-slate-950 text-white">
        {/* Subtle blue glow */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[900px] rounded-full bg-blue-600/20 blur-[120px]" />
        </div>

        <div className="relative z-10 mx-auto max-w-5xl px-4 pb-24 pt-28 text-center sm:pb-32 sm:pt-36">
          {/* Badge */}
          <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-5 py-2 text-sm font-medium text-blue-300 backdrop-blur">
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            Norges ledende plattform for digitale eiendomstjenester
          </div>

          <h1 className="mx-auto max-w-3xl text-4xl font-extrabold leading-[1.1] tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
            Vet du hva som gjelder for{' '}
            <span className="bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
              eiendommen din?
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-300 sm:text-xl">
            Søk opp adressen og få øyeblikkelig innsikt i byggesaker,
            reguleringsplan, avvik, energi og potensial.
          </p>

          {/* Search bar */}
          <div className="mx-auto mt-10 max-w-xl">
            <Link
              href="/property"
              className="group flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-5 py-4 backdrop-blur transition hover:border-blue-500/40 hover:bg-white/10 sm:px-6 sm:py-5"
            >
              <Search className="h-5 w-5 shrink-0 text-slate-400 sm:h-6 sm:w-6" />
              <span className="flex-1 text-left text-base text-slate-400 sm:text-lg">
                Skriv inn adresse...
              </span>
              <span className="shrink-0 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition group-hover:bg-blue-500 sm:px-6">
                Søk
              </span>
            </Link>
          </div>

          <p className="mt-5 text-sm text-slate-500">
            Gratis &middot; Ingen registrering nødvendig &middot; 100%
            offentlige data
          </p>
        </div>
      </section>

      {/* ─────────────────────── 2. FIRE PRODUKTER ─────────────────────── */}
      <section className="py-24 px-4">
        <div className="mx-auto max-w-6xl">
          <h2 className="mb-4 text-center text-3xl font-extrabold text-slate-900 sm:text-4xl lg:text-5xl">
            Hva trenger du?
          </h2>
          <p className="mx-auto mb-14 max-w-xl text-center text-lg text-slate-500">
            Fire produkter som dekker hele verdikjeden for eiendom.
          </p>

          <div className="grid gap-6 sm:grid-cols-2">
            {/* KORT 1 – Eiendomssjekk */}
            <div className="group relative rounded-3xl border-2 border-transparent bg-white p-8 shadow-sm transition hover:shadow-lg"
              style={{ borderImage: 'linear-gradient(135deg, #3b82f6, #06b6d4) 1' }}>
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-blue-500/5 to-cyan-500/5" />
              <div className="relative">
                <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-100">
                  <Building2 className="h-7 w-7 text-blue-600" />
                </div>
                <h3 className="mb-2 text-xl font-bold text-slate-900">
                  Sjekk eiendommen
                </h3>
                <p className="mb-5 text-sm leading-relaxed text-slate-600">
                  Matrikkeldata, byggesaker, reguleringsplan, DOK-analyse,
                  avviksdeteksjon, energimerke og verdiestimering – på sekunder.
                </p>
                <ul className="mb-6 grid grid-cols-2 gap-x-4 gap-y-2">
                  {[
                    'Avviksdeteksjon',
                    'Ferdigattest-sjekk',
                    'AI-risikoanalyse',
                    'Reguleringsplan',
                  ].map((item) => (
                    <li
                      key={item}
                      className="flex items-center gap-1.5 text-sm text-slate-700"
                    >
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-blue-500" />
                      {item}
                    </li>
                  ))}
                </ul>
                <div className="flex items-center justify-between">
                  <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                    Gratis grunnsjekk
                  </span>
                  <Link
                    href="/property"
                    className="inline-flex items-center gap-1.5 text-sm font-semibold text-blue-600 transition hover:text-blue-700"
                  >
                    Prøv gratis <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>
            </div>

            {/* KORT 2 – Byggesøknad */}
            <div className="group relative rounded-3xl border-2 border-transparent bg-white p-8 shadow-sm transition hover:shadow-lg"
              style={{ borderImage: 'linear-gradient(135deg, #f97316, #f59e0b) 1' }}>
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-orange-500/5 to-amber-500/5" />
              <div className="relative">
                <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-orange-100">
                  <FileText className="h-7 w-7 text-orange-600" />
                </div>
                <h3 className="mb-2 text-xl font-bold text-slate-900">
                  Søk om å bygge
                </h3>
                <p className="mb-5 text-sm leading-relaxed text-slate-600">
                  Tilbygg, påbygg, bruksendring, garasje, tomtedeling – vi
                  håndterer hele søknaden med tegninger og dokumentasjon.
                </p>
                <ul className="mb-6 grid grid-cols-2 gap-x-4 gap-y-2">
                  {[
                    'Tilbygg & påbygg',
                    'Bruksendring',
                    'Dispensasjon',
                    'Situasjonsplan',
                    'Nabovarsel',
                  ].map((item) => (
                    <li
                      key={item}
                      className="flex items-center gap-1.5 text-sm text-slate-700"
                    >
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-orange-500" />
                      {item}
                    </li>
                  ))}
                </ul>
                <div className="flex items-center justify-between">
                  <span className="rounded-full bg-orange-50 px-3 py-1 text-xs font-semibold text-orange-700">
                    Fra 15 000 kr
                  </span>
                  <Link
                    href="/tjenester"
                    className="inline-flex items-center gap-1.5 text-sm font-semibold text-orange-600 transition hover:text-orange-700"
                  >
                    Kom i gang <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>
            </div>

            {/* KORT 3 – Visualisering */}
            <div className="group relative rounded-3xl border-2 border-transparent bg-white p-8 shadow-sm transition hover:shadow-lg"
              style={{ borderImage: 'linear-gradient(135deg, #8b5cf6, #a855f7) 1' }}>
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-violet-500/5 to-purple-500/5" />
              <div className="relative">
                <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-purple-100">
                  <Camera className="h-7 w-7 text-purple-600" />
                </div>
                <h3 className="mb-2 text-xl font-bold text-slate-900">
                  Se før du bygger
                </h3>
                <p className="mb-5 text-sm leading-relaxed text-slate-600">
                  2D til 3D, fotorealistiske renders, virtuell staging og
                  energimodellering – vi gjør ideene dine visuelle.
                </p>
                <ul className="mb-6 grid grid-cols-2 gap-x-4 gap-y-2">
                  {[
                    '2D til 3D',
                    'AI-render',
                    'Virtuell staging',
                    'Energiberegning',
                  ].map((item) => (
                    <li
                      key={item}
                      className="flex items-center gap-1.5 text-sm text-slate-700"
                    >
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-purple-500" />
                      {item}
                    </li>
                  ))}
                </ul>
                <div className="flex items-center justify-between">
                  <span className="rounded-full bg-purple-50 px-3 py-1 text-xs font-semibold text-purple-700">
                    Fra 5 000 kr
                  </span>
                  <Link
                    href="/visualisering"
                    className="inline-flex items-center gap-1.5 text-sm font-semibold text-purple-600 transition hover:text-purple-700"
                  >
                    Se eksempler <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>
            </div>

            {/* KORT 4 – Tomt */}
            <div className="group relative rounded-3xl border-2 border-transparent bg-white p-8 shadow-sm transition hover:shadow-lg"
              style={{ borderImage: 'linear-gradient(135deg, #22c55e, #10b981) 1' }}>
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-green-500/5 to-emerald-500/5" />
              <div className="relative">
                <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-green-100">
                  <Trees className="h-7 w-7 text-green-600" />
                </div>
                <h3 className="mb-2 text-xl font-bold text-slate-900">
                  Selg tomten raskere
                </h3>
                <p className="mb-5 text-sm leading-relaxed text-slate-600">
                  Mulighetsstudie med ferdighusmodeller, kostnadskalkulator og
                  komplett presentasjon – slik at kjøperne ser potensialet.
                </p>
                <ul className="mb-6 grid grid-cols-2 gap-x-4 gap-y-2">
                  {[
                    'Mulighetsstudie',
                    'Ferdighusmodeller',
                    'Kostnadskalkulator',
                    'Presentasjonsside',
                  ].map((item) => (
                    <li
                      key={item}
                      className="flex items-center gap-1.5 text-sm text-slate-700"
                    >
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-green-500" />
                      {item}
                    </li>
                  ))}
                </ul>
                <div className="flex items-center justify-between">
                  <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-green-700">
                    15 000 kr eller 2% av salgssum
                  </span>
                  <Link
                    href="/tomter"
                    className="inline-flex items-center gap-1.5 text-sm font-semibold text-green-600 transition hover:text-green-700"
                  >
                    Bestill <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ────────────────── 3. AVVIKSDETEKSJON – FLAGGSKIP ────────────────── */}
      <section className="px-4 py-20">
        <div className="mx-auto max-w-4xl rounded-3xl border-2 border-red-200 bg-red-50 px-6 py-14 sm:px-12">
          <div className="flex flex-col items-center text-center">
            <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-red-100">
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>
            <h2 className="mb-4 text-3xl font-extrabold text-slate-900 sm:text-4xl">
              Norges eneste automatiske avviksdeteksjon
            </h2>
            <p className="mx-auto mb-10 max-w-2xl text-lg leading-relaxed text-slate-600">
              Vi sammenligner offentlige registre, byggetegninger og
              Finn.no-annonser – og finner avvik som ulovlige tilbygg, manglende
              ferdigattester og feil i plantegninger.
            </p>

            <div className="mb-10 grid gap-6 sm:grid-cols-3">
              {[
                {
                  icon: <Building2 className="h-6 w-6 text-red-600" />,
                  text: 'Sjekker matrikkel mot byggesaker',
                },
                {
                  icon: <Search className="h-6 w-6 text-red-600" />,
                  text: 'Analyserer Finn.no-annonser med AI',
                },
                {
                  icon: <FileText className="h-6 w-6 text-red-600" />,
                  text: 'Sammenligner plantegninger automatisk',
                },
              ].map((item) => (
                <div
                  key={item.text}
                  className="flex flex-col items-center gap-3 rounded-2xl bg-white p-6 shadow-sm"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-red-50">
                    {item.icon}
                  </div>
                  <p className="text-sm font-medium text-slate-700">
                    {item.text}
                  </p>
                </div>
              ))}
            </div>

            <Link
              href="/property"
              className="inline-flex items-center gap-2 rounded-2xl bg-red-600 px-8 py-4 text-base font-semibold text-white shadow-lg shadow-red-600/20 transition hover:bg-red-700"
            >
              Sjekk din eiendom gratis
              <ArrowRight className="h-5 w-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* ──────────────────── 4. SLIK FUNGERER DET ──────────────────── */}
      <section className="border-t border-slate-100 bg-slate-50 px-4 py-24">
        <div className="mx-auto max-w-5xl">
          <h2 className="mb-4 text-center text-3xl font-extrabold text-slate-900 sm:text-4xl">
            Slik fungerer nops.no
          </h2>
          <p className="mx-auto mb-16 max-w-lg text-center text-lg text-slate-500">
            Fra adresse til innsikt på under ett minutt.
          </p>

          <div className="grid gap-10 md:grid-cols-3">
            {[
              {
                step: '1',
                title: 'Søk opp eiendommen',
                desc: 'Skriv inn adresse, vi henter data fra 8+ offentlige registre.',
                icon: <Search className="h-6 w-6 text-blue-600" />,
              },
              {
                step: '2',
                title: 'Få innsikt på sekunder',
                desc: 'Avvik, reguleringsplan, energi, verdi og potensial – alt samlet.',
                icon: <Zap className="h-6 w-6 text-blue-600" />,
              },
              {
                step: '3',
                title: 'Bestill det du trenger',
                desc: 'Tegninger, søknader, visualisering eller mulighetsstudie.',
                icon: <Package className="h-6 w-6 text-blue-600" />,
              },
            ].map((s) => (
              <div key={s.step} className="flex flex-col items-center text-center">
                <div className="relative mb-6">
                  <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-600 text-2xl font-bold text-white shadow-lg shadow-blue-600/20">
                    {s.step}
                  </div>
                </div>
                <h3 className="mb-2 text-lg font-bold text-slate-900">
                  {s.title}
                </h3>
                <p className="text-sm leading-relaxed text-slate-500">
                  {s.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─────────────────── 5. ALLE TJENESTER – GRID ─────────────────── */}
      <section className="px-4 py-24">
        <div className="mx-auto max-w-6xl">
          <h2 className="mb-3 text-center text-3xl font-extrabold text-slate-900 sm:text-4xl">
            Alt du trenger, samlet på ett sted
          </h2>
          <p className="mx-auto mb-14 max-w-md text-center text-lg text-slate-500">
            20+ tjenester for eiendom, byggesak og arkitektur
          </p>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {[
              {
                href: '/property',
                icon: <Search className="h-5 w-5 text-blue-600" />,
                label: 'Eiendomssøk',
                desc: 'Matrikkel, byggesaker og arealplaner',
              },
              {
                href: '/property',
                icon: <AlertTriangle className="h-5 w-5 text-red-600" />,
                label: 'Avviksdeteksjon',
                desc: 'Finn avvik automatisk med AI',
              },
              {
                href: '/property',
                icon: <Sparkles className="h-5 w-5 text-indigo-600" />,
                label: 'AI-analyse',
                desc: 'Risikovurdering og anbefalinger',
              },
              {
                href: '/dispensasjon',
                icon: <Scale className="h-5 w-5 text-amber-600" />,
                label: 'Dispensasjon',
                desc: 'AI-generert dispensasjonssøknad',
              },
              {
                href: '/naboklage',
                icon: <Users className="h-5 w-5 text-indigo-600" />,
                label: 'Nabovarsel',
                desc: 'Merknad og klage på byggesak',
              },
              {
                href: '/ferdigattest',
                icon: <Award className="h-5 w-5 text-green-600" />,
                label: 'Ferdigattest',
                desc: 'Sjekk status og bestill',
              },
              {
                href: '/situasjonsplan',
                icon: <MapPin className="h-5 w-5 text-emerald-600" />,
                label: 'Situasjonsplan',
                desc: 'Profesjonell situasjonsplan',
              },
              {
                href: '/visualisering',
                icon: <Camera className="h-5 w-5 text-purple-600" />,
                label: 'Visualisering',
                desc: '2D til 3D, render og staging',
              },
              {
                href: '/property',
                icon: <Zap className="h-5 w-5 text-yellow-600" />,
                label: 'Energi',
                desc: 'Energimerke og beregning',
              },
              {
                href: '/tomter',
                icon: <Trees className="h-5 w-5 text-green-600" />,
                label: 'Tomteutvikling',
                desc: 'Mulighetsstudie og presentasjon',
              },
              {
                href: '/investering',
                icon: <TrendingUp className="h-5 w-5 text-cyan-600" />,
                label: 'Investeringsanalyse',
                desc: 'Yield, ROI og verdivurdering',
              },
              {
                href: '/finn-analyse',
                icon: <BarChart3 className="h-5 w-5 text-rose-600" />,
                label: 'Finn-analyse',
                desc: 'Avvik i Finn.no-annonser',
              },
            ].map((t) => (
              <Link
                key={t.label}
                href={t.href}
                className="flex flex-col items-center gap-2.5 rounded-2xl border border-slate-200 bg-white p-5 text-center transition hover:border-blue-300 hover:shadow-md"
              >
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-50">
                  {t.icon}
                </div>
                <span className="text-sm font-semibold text-slate-900">
                  {t.label}
                </span>
                <span className="text-xs leading-snug text-slate-500">
                  {t.desc}
                </span>
              </Link>
            ))}
          </div>

          <div className="mt-10 text-center">
            <Link
              href="/tjenester"
              className="inline-flex items-center gap-2 text-sm font-semibold text-blue-600 transition hover:text-blue-700"
            >
              Se alle tjenester <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* ─────────────────── 6. SOSIAL BEVISFØRING ─────────────────── */}
      <section className="border-t border-slate-100 bg-slate-50 px-4 py-24">
        <div className="mx-auto max-w-5xl">
          <div className="mb-12 text-center">
            <div className="mb-3 inline-flex items-center gap-1">
              {[1, 2, 3, 4, 5].map((i) => (
                <Star
                  key={i}
                  className="h-5 w-5 fill-yellow-400 text-yellow-400"
                />
              ))}
            </div>
            <h2 className="mb-3 text-3xl font-extrabold text-slate-900 sm:text-4xl">
              Brukt av arkitekter og eiendomsaktører
            </h2>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {[
              {
                quote:
                  'Jeg brukte å bruke halve arbeidsdagen på å innhente eiendomsinformasjon. Med nops.no gjør jeg det på fem minutter.',
                name: 'Marie Andersen',
                title: 'Arkitekt MNAL, Oslo',
                initials: 'MA',
              },
              {
                quote:
                  'Endelig et verktøy som faktisk forstår arkitektens hverdag. AI-analysen fanger opp dispensasjonsbehov jeg lett kunne oversett.',
                name: 'Torbjørn Hegdahl',
                title: 'Sivilarkitekt, Bergen',
                initials: 'TH',
              },
              {
                quote:
                  'Vi bruker nops.no på alle nye prosjekter. Det reduserer risiko og gjør at vi kan gi kunden et mye bedre svar allerede i første møte.',
                name: 'Ingrid Solberg',
                title: 'Partner, Arkitektkontor AS',
                initials: 'IS',
              },
            ].map((t) => (
              <div
                key={t.name}
                className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
              >
                <p className="text-sm italic leading-relaxed text-slate-700">
                  &ldquo;{t.quote}&rdquo;
                </p>
                <div className="mt-auto flex items-center gap-3 border-t border-slate-100 pt-4">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">
                    {t.initials}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">
                      {t.name}
                    </p>
                    <p className="text-xs text-slate-500">{t.title}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Trust signals */}
          <div className="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm font-medium text-slate-500">
            {[
              { icon: <Shield className="h-4 w-4" />, label: 'GDPR' },
              {
                icon: <Building2 className="h-4 w-4" />,
                label: 'Norske data',
              },
              {
                icon: <Clock className="h-4 w-4" />,
                label: 'Alltid oppdatert',
              },
              {
                icon: <MapPin className="h-4 w-4" />,
                label: '100+ kommuner',
              },
            ].map((ts) => (
              <span
                key={ts.label}
                className="inline-flex items-center gap-1.5"
              >
                {ts.icon}
                {ts.label}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ──────────────────────── 7. PRISER ──────────────────────── */}
      <section className="px-4 py-24">
        <div className="mx-auto max-w-5xl">
          <h2 className="mb-4 text-center text-3xl font-extrabold text-slate-900 sm:text-4xl">
            Kom i gang gratis
          </h2>
          <p className="mx-auto mb-14 max-w-md text-center text-lg text-slate-500">
            Velg planen som passer ditt behov.
          </p>

          <div className="grid gap-6 md:grid-cols-3">
            {/* Gratis */}
            <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-8">
              <h3 className="mb-1 text-lg font-bold text-slate-900">Gratis</h3>
              <p className="mb-6 text-sm text-slate-500">
                For deg som vil prøve
              </p>
              <p className="mb-6 text-4xl font-extrabold text-slate-900">
                0 kr
                <span className="text-base font-normal text-slate-400">
                  /mnd
                </span>
              </p>
              <ul className="mb-8 space-y-2.5">
                {[
                  '5 eiendomsoppslag/mnd',
                  'Matrikkeldata',
                  'Byggesakshistorikk',
                  'Reguleringsplan',
                ].map((f) => (
                  <li
                    key={f}
                    className="flex items-center gap-2 text-sm text-slate-600"
                  >
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-green-500" />
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                href="/register"
                className="mt-auto inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                Opprett gratis konto
              </Link>
            </div>

            {/* Starter */}
            <div className="relative flex flex-col rounded-2xl border-2 border-blue-600 bg-white p-8 shadow-lg shadow-blue-600/10">
              <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full bg-blue-600 px-4 py-1 text-xs font-semibold text-white">
                Populær
              </span>
              <h3 className="mb-1 text-lg font-bold text-slate-900">
                Starter
              </h3>
              <p className="mb-6 text-sm text-slate-500">
                For profesjonelle brukere
              </p>
              <p className="mb-6 text-4xl font-extrabold text-slate-900">
                499 kr
                <span className="text-base font-normal text-slate-400">
                  /mnd
                </span>
              </p>
              <ul className="mb-8 space-y-2.5">
                {[
                  'Ubegrenset oppslag',
                  'AI-analyse og risikovurdering',
                  'PDF-rapporter',
                  'Avviksdeteksjon',
                  'Finn-analyse',
                ].map((f) => (
                  <li
                    key={f}
                    className="flex items-center gap-2 text-sm text-slate-600"
                  >
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-blue-500" />
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                href="/register"
                className="mt-auto inline-flex items-center justify-center rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
              >
                Start Starter
              </Link>
            </div>

            {/* Professional */}
            <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-8">
              <h3 className="mb-1 text-lg font-bold text-slate-900">
                Professional
              </h3>
              <p className="mb-6 text-sm text-slate-500">
                For team og selskaper
              </p>
              <p className="mb-6 text-4xl font-extrabold text-slate-900">
                999 kr
                <span className="text-base font-normal text-slate-400">
                  /mnd
                </span>
              </p>
              <ul className="mb-8 space-y-2.5">
                {[
                  'Alt i Starter',
                  'Hvit-etikett rapporter',
                  'API-tilgang',
                  'Prioritert support',
                  'Team-administrasjon',
                ].map((f) => (
                  <li
                    key={f}
                    className="flex items-center gap-2 text-sm text-slate-600"
                  >
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-green-500" />
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                href="/register"
                className="mt-auto inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                Start Professional
              </Link>
            </div>
          </div>

          <p className="mt-8 text-center text-sm text-slate-400">
            Ingen bindingstid. Avbryt når som helst.{' '}
            <Link
              href="/pricing"
              className="font-medium text-blue-600 hover:text-blue-700"
            >
              Se alle priser
            </Link>
          </p>
        </div>
      </section>

      {/* ──────────────────────── 8. PARTNERE ──────────────────────── */}
      <section className="border-t border-slate-100 bg-slate-50 px-4 py-16">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="mb-3 text-2xl font-bold text-slate-900">
            Et komplett økosystem
          </h2>
          <p className="mx-auto mb-8 max-w-md text-slate-500">
            Alle våre merkevarer – samlet under nops.no
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {[
              'nops.no',
              'situasjonsplan.no',
              'dispensasjonen.no',
              'naboklagen.no',
              'ferdigattesten.no',
              'minni.no',
            ].map((d) => (
              <span
                key={d}
                className="rounded-full border border-slate-200 bg-white px-5 py-2 text-sm font-semibold text-slate-700 shadow-sm"
              >
                {d}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ──────────────────────── 9. CTA FOOTER ──────────────────────── */}
      <section className="bg-slate-900 px-4 py-24">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="mb-4 text-3xl font-extrabold text-white sm:text-4xl">
            Klar for å sjekke eiendommen din?
          </h2>
          <p className="mx-auto mb-10 max-w-md text-lg text-slate-400">
            Søk opp adressen og få innsikt på sekunder. Helt gratis.
          </p>
          <Link
            href="/property"
            className="inline-flex items-center gap-2 rounded-2xl bg-blue-600 px-10 py-4 text-lg font-semibold text-white shadow-lg shadow-blue-600/20 transition hover:bg-blue-500"
          >
            Søk opp eiendom gratis
            <ArrowRight className="h-5 w-5" />
          </Link>
          <p className="mt-6 text-sm text-slate-500">
            Eller kontakt oss:{' '}
            <a
              href="mailto:hey@nops.no"
              className="font-medium text-slate-400 underline transition hover:text-white"
            >
              hey@nops.no
            </a>
          </p>
        </div>
      </section>
    </main>
  );
}
