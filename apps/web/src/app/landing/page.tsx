import Link from 'next/link';
import type { Metadata } from 'next';
import {
  Building2,
  Archive,
  Sparkles,
  FileText,
  TrendingUp,
  Search,
  ShieldCheck,
  Clock,
  Star,
  CheckCircle2,
  ArrowRight,
  ChevronDown,
  AlertTriangle,
  Box,
  Scale,
  Users,
  Map,
  Award,
  Camera,
  BarChart3,
  Package,
} from 'lucide-react';

export const metadata: Metadata = {
  title: 'nops.no – Norges ledende plattform for digitale eiendomstjenester',
  description:
    'nops.no samler avviksdeteksjon, 2D til 3D, AI-analyse, dispensasjon, nabovarsel, ferdigattest, situasjonsplan og 20+ tjenester – alt på ett sted. Gratis å starte.',
  openGraph: {
    title: 'nops.no – Norges ledende plattform for digitale eiendomstjenester',
    description:
      'Avviksdeteksjon, 2D til 3D-konvertering, AI-analyse, dispensasjon, ferdigattest og mer. Alt samlet på ett sted.',
    siteName: 'nops.no',
  },
};

const features = [
  {
    icon: <Building2 className="h-6 w-6 text-blue-600" aria-hidden="true" />,
    title: 'Matrikkeldata',
    description:
      'Hent bygningsinfo, areal og byggeår direkte fra Kartverket Matrikkelen.',
  },
  {
    icon: <Archive className="h-6 w-6 text-blue-600" aria-hidden="true" />,
    title: 'Byggesakshistorikk',
    description:
      'Komplett oversikt over søknader, tillatelser og ferdigattester fra kommunalt arkiv.',
  },
  {
    icon: <Sparkles className="h-6 w-6 text-blue-600" aria-hidden="true" />,
    title: 'AI-analyse',
    description:
      'Claude AI analyserer risiko, avvik og reguleringsplan – gir konkrete anbefalinger på sekunder.',
  },
  {
    icon: <FileText className="h-6 w-6 text-blue-600" aria-hidden="true" />,
    title: 'Arealplaner & DOK',
    description:
      'Gjeldende reguleringsplaner, dispensasjoner og DOK-analyse av kartgrunnlaget.',
  },
  {
    icon: <TrendingUp className="h-6 w-6 text-blue-600" aria-hidden="true" />,
    title: 'Verdiestimator',
    description:
      'Estimert markedsverdi basert på kommunestatistikk og bygningsdata.',
  },
  {
    icon: <Search className="h-6 w-6 text-blue-600" aria-hidden="true" />,
    title: 'Adresseoppslag',
    description:
      'Søk på hvilken som helst norsk adresse og få full eiendomsprofil på sekunder.',
  },
];

const steps = [
  {
    number: '1',
    title: 'Søk opp adressen',
    description: 'Skriv inn en norsk adresse og velg riktig eiendom fra listen.',
  },
  {
    number: '2',
    title: 'Hent all offentlig informasjon automatisk',
    description:
      'ByggSjekk henter data fra Matrikkelen, kommunale arkiver, arealplaner og mer – automatisk.',
  },
  {
    number: '3',
    title: 'Kjør AI-analyse og eksporter rapport',
    description:
      'Få en strukturert analyse med risikopunkter, anbefalinger og eksportér som rapport.',
  },
];

const stats = [
  { value: '100+', label: 'kommuner dekket' },
  { value: '< 10 sek', label: 'til full eiendomsdata' },
  { value: '100%', label: 'offentlige data' },
];

const testimonials = [
  {
    quote:
      'Jeg brukte å bruke halve arbeidsdagen på å innhente eiendomsinformasjon. Med ByggSjekk gjør jeg det på fem minutter.',
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
      'Vi bruker ByggSjekk på alle nye prosjekter. Det reduserer risiko og gjør at vi kan gi kunden et mye bedre svar allerede i første møte.',
    name: 'Ingrid Solberg',
    title: 'Partner, Arkitektkontor AS',
    initials: 'IS',
  },
];

const faqs = [
  {
    q: 'Hvilke data hentes automatisk?',
    a: 'ByggSjekk kobler seg til Kartverket Matrikkelen, kommunale saksarkiver, Plandata (reguleringsplaner), DOK-tjenesten og SSB for statistikk. Alt hentes automatisk når du søker opp en eiendom.',
  },
  {
    q: 'Er det bindingstid?',
    a: 'Nei. Du kan avslutte eller endre abonnementet ditt når som helst. Ingen bindingstid, ingen skjulte gebyrer.',
  },
  {
    q: 'Fungerer det for alle norske kommuner?',
    a: 'Matrikkeldata og arealplaner er tilgjengelig for hele Norge. Tilgangen til historiske byggesaker varierer noe per kommune, men dekker de fleste større kommuner.',
  },
  {
    q: 'Hva er inkludert i gratisplanen?',
    a: '5 eiendomsoppslag per måned med full tilgang til matrikkeldata, byggesaker og arealplaner. AI-analyse og PDF-rapporter krever Starter eller Professional.',
  },
  {
    q: 'Hvordan fungerer AI-analysen?',
    a: 'Claude AI leser og sammenstiller all eiendomsdata og gir deg en strukturert risikovurdering: avvik, dispensasjonsbehov, reguleringsplanens krav og konkrete anbefalinger tilpasset prosjektet.',
  },
];

const trustSignals = [
  {
    icon: <ShieldCheck className="h-5 w-5 text-green-600" />,
    label: 'GDPR-kompatibel',
    desc: 'Data behandles iht. norsk personvernlovgivning',
  },
  {
    icon: <Building2 className="h-5 w-5 text-blue-600" />,
    label: 'Kun offentlige data',
    desc: 'All data fra Kartverket og offentlige registre',
  },
  {
    icon: <Clock className="h-5 w-5 text-purple-600" />,
    label: 'Alltid oppdatert',
    desc: 'Henter sanntidsdata direkte fra kilden',
  },
];

export default function LandingPage() {
  return (
    <main className="bg-white">
      {/* Hero */}
      <section className="bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 text-white py-24 px-4">
        <div className="container mx-auto max-w-5xl text-center">
          <div className="inline-flex items-center gap-2 mb-6 rounded-full bg-white/10 px-4 py-1.5 text-sm font-medium text-blue-200">
            <Building2 className="h-4 w-4" aria-hidden="true" />
            nops.no – Norges ledende plattform for digitale eiendomstjenester
          </div>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold leading-tight tracking-tight mb-6">
            Alt du trenger for eiendom,<br className="hidden sm:block" /> byggesak og arkitektur
          </h1>
          <p className="text-lg sm:text-xl text-blue-100 max-w-2xl mx-auto mb-4">
            Avviksdeteksjon, 2D til 3D, AI-analyse, dispensasjon, ferdigattest,
            situasjonsplan, nabovarsel og mer – samlet på ett sted.
          </p>
          <p className="text-sm text-blue-300 mb-10">
            Søk opp eiendommen din gratis &middot; Ingen kredittkort nødvendig
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/register"
              className="inline-flex items-center justify-center rounded-lg bg-white px-6 py-3 text-base font-semibold text-blue-700 shadow-md hover:bg-blue-50 transition-colors"
            >
              Kom i gang gratis
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
            <Link
              href="/property"
              className="inline-flex items-center justify-center rounded-lg border border-white/40 bg-white/10 px-6 py-3 text-base font-semibold text-white hover:bg-white/20 transition-colors"
            >
              Prøv eiendomssøk
            </Link>
          </div>
        </div>
      </section>

      {/* Stats banner */}
      <section className="bg-slate-50 border-y border-slate-200 py-10 px-4">
        <div className="container mx-auto max-w-3xl">
          <ul className="flex flex-col sm:flex-row items-center justify-center gap-8 sm:gap-16 list-none">
            {stats.map((stat) => (
              <li key={stat.label} className="text-center">
                <p className="text-3xl font-bold text-blue-600">{stat.value}</p>
                <p className="text-sm font-medium text-slate-500 mt-1">{stat.label}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Hovedtjenester – Avvik + 2D til 3D */}
      <section className="py-20 px-4 bg-white">
        <div className="container mx-auto max-w-5xl">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-3">
              Våre hovedtjenester
            </h2>
            <p className="text-lg text-slate-500">
              To bransjeledende tjenester – tilgjengelig via e-torget (Norkart)
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Avvikstjenesten */}
            <div className="relative rounded-2xl border-2 border-red-200 bg-gradient-to-br from-red-50 to-orange-50 p-8 overflow-hidden">
              <div className="absolute top-4 right-4">
                <span className="rounded-full bg-red-100 border border-red-200 px-3 py-1 text-xs font-semibold text-red-700">
                  Flaggskip
                </span>
              </div>
              <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-red-100 mb-5">
                <AlertTriangle className="h-7 w-7 text-red-600" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-2">Avviksdeteksjon</h3>
              <p className="text-sm text-slate-600 mb-4 leading-relaxed">
                AI-drevet analyse som sammenligner godkjente tegninger med faktisk tilstand.
                Avdekker ulovlige tilbygg, bruksendringer og manglende ferdigattester – automatisk.
              </p>
              <ul className="space-y-2 mb-6">
                {['Sammenligner matrikkel med byggesaker', 'Finn.no-analyse med avviksrapport', 'Plantegning-analyse med Claude Vision', 'Automatisk risikovurdering'].map((item) => (
                  <li key={item} className="flex items-center gap-2 text-sm text-slate-700">
                    <CheckCircle2 className="h-4 w-4 text-red-500 shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
              <Link href="/property" className="inline-flex items-center gap-2 rounded-xl bg-red-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-red-700 transition-colors">
                Prøv avvikssjekk <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            {/* 2D til 3D */}
            <div className="relative rounded-2xl border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50 p-8 overflow-hidden">
              <div className="absolute top-4 right-4">
                <span className="rounded-full bg-blue-100 border border-blue-200 px-3 py-1 text-xs font-semibold text-blue-700">
                  Tilgjengelig via e-torget
                </span>
              </div>
              <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-blue-100 mb-5">
                <Box className="h-7 w-7 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-2">2D til 3D-konvertering</h3>
              <p className="text-sm text-slate-600 mb-4 leading-relaxed">
                Konverter plantegninger og fasadetegninger til komplette 3D-modeller.
                Leveres som IFC, SketchUp eller Revit – klar for prosjektering og byggesak.
              </p>
              <ul className="space-y-2 mb-6">
                {['Plantegning til 3D-modell', 'AI-visualisering og render', 'IFC, SKP, RVT-eksport', 'Fotorealistiske presentasjoner'].map((item) => (
                  <li key={item} className="flex items-center gap-2 text-sm text-slate-700">
                    <CheckCircle2 className="h-4 w-4 text-blue-500 shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
              <Link href="/visualisering" className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 transition-colors">
                Prøv visualisering <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* In-house tjenester */}
      <section className="py-16 px-4 bg-slate-50 border-t border-slate-200">
        <div className="container mx-auto max-w-5xl">
          <div className="text-center mb-10">
            <h2 className="text-2xl font-bold text-slate-900 mb-3">
              Alle tjenester – bygd inn i nops.no
            </h2>
            <p className="text-slate-500">
              Vi har bygd inn alle tjenestene direkte – ingen eksterne sider, ingen ekstra innlogging.
            </p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {[
              { href: '/property', icon: <Search className="h-5 w-5 text-blue-600" />, label: 'Eiendomssøk', desc: 'Matrikkel, byggesaker, arealplaner' },
              { href: '/dispensasjon', icon: <Scale className="h-5 w-5 text-red-600" />, label: 'Dispensasjon', desc: 'AI-generert søknad' },
              { href: '/naboklage', icon: <Users className="h-5 w-5 text-indigo-600" />, label: 'Nabovarsel', desc: 'Merknad og klage' },
              { href: '/ferdigattest', icon: <Award className="h-5 w-5 text-green-600" />, label: 'Ferdigattest', desc: 'Sjekk og bestill' },
              { href: '/situasjonsplan', icon: <Map className="h-5 w-5 text-emerald-600" />, label: 'Situasjonsplan', desc: 'Fra 3 000 kr' },
              { href: '/visualisering', icon: <Camera className="h-5 w-5 text-purple-600" />, label: 'Visualisering', desc: 'AI-render og staging' },
              { href: '/utbygging', icon: <BarChart3 className="h-5 w-5 text-amber-600" />, label: 'Utbygging', desc: 'Tomtepotensial' },
              { href: '/investering', icon: <TrendingUp className="h-5 w-5 text-cyan-600" />, label: 'Investering', desc: 'Yield og ROI' },
              { href: '/tomter', icon: <Building2 className="h-5 w-5 text-orange-600" />, label: 'Tomter', desc: 'Mulighetsstudie' },
              { href: '/finn-analyse', icon: <Search className="h-5 w-5 text-rose-600" />, label: 'Finn-analyse', desc: 'Avvik i annonser' },
              { href: '/dokumenter', icon: <FileText className="h-5 w-5 text-teal-600" />, label: 'Dokumenter', desc: 'Gratis tegninger' },
              { href: '/pakke', icon: <Package className="h-5 w-5 text-slate-600" />, label: 'Komplett pakke', desc: 'Alt automatisk' },
            ].map((t) => (
              <Link
                key={t.href}
                href={t.href}
                className="flex flex-col items-center gap-2 rounded-xl border border-slate-200 bg-white p-4 text-center hover:border-blue-300 hover:shadow-md transition-all"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-50">
                  {t.icon}
                </div>
                <span className="text-sm font-semibold text-slate-900">{t.label}</span>
                <span className="text-[11px] text-slate-500">{t.desc}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Features grid */}
      <section className="py-24 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
              Eiendomssøk med komplett analyse
            </h2>
            <p className="text-lg text-slate-500 max-w-xl mx-auto">
              Søk opp en eiendom og få all informasjon samlet –
              fra matrikkeldata til AI-risikovurdering og reguleringsplan.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg bg-blue-50">
                  {feature.icon}
                </div>
                <h3 className="text-base font-semibold text-slate-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-slate-500 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="bg-slate-50 py-24 px-4 border-t border-slate-200">
        <div className="container mx-auto max-w-4xl">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
              Slik fungerer det
            </h2>
            <p className="text-lg text-slate-500">
              Fra adresse til fullstendig rapport på under ett minutt.
            </p>
          </div>
          <ol className="relative grid grid-cols-1 md:grid-cols-3 gap-8 list-none">
            {steps.map((step, index) => (
              <li key={step.number} className="flex flex-col items-center text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-600 text-white text-lg font-bold mb-4 shadow-md">
                  {step.number}
                </div>
                {index < steps.length - 1 && (
                  <div className="hidden md:block absolute top-6 left-1/3 w-1/3 border-t-2 border-dashed border-blue-200" />
                )}
                <h3 className="text-base font-semibold text-slate-900 mb-2">
                  {step.title}
                </h3>
                <p className="text-sm text-slate-500 leading-relaxed">
                  {step.description}
                </p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-24 px-4 bg-white border-t border-slate-200">
        <div className="container mx-auto max-w-5xl">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-1 mb-3">
              {[1,2,3,4,5].map((i) => (
                <Star key={i} className="h-5 w-5 fill-yellow-400 text-yellow-400" />
              ))}
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-3">
              Brukt av arkitekter og eiendomsaktører
            </h2>
            <p className="text-slate-500 text-lg">
              Se hva profesjonelle sier om ByggSjekk.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {testimonials.map((t) => (
              <div
                key={t.name}
                className="rounded-2xl border border-slate-200 bg-slate-50 p-6 flex flex-col gap-4"
              >
                <p className="text-sm text-slate-700 leading-relaxed italic">
                  &ldquo;{t.quote}&rdquo;
                </p>
                <div className="flex items-center gap-3 mt-auto pt-4 border-t border-slate-200">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-600 text-white text-xs font-bold">
                    {t.initials}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{t.name}</p>
                    <p className="text-xs text-slate-500">{t.title}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Trust signals */}
      <section className="bg-slate-50 border-t border-slate-200 py-12 px-4">
        <div className="container mx-auto max-w-4xl">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {trustSignals.map((ts) => (
              <div key={ts.label} className="flex items-start gap-3">
                <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white border border-slate-200 shadow-sm">
                  {ts.icon}
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-900">{ts.label}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{ts.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20 px-4 bg-white border-t border-slate-200">
        <div className="container mx-auto max-w-3xl">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-slate-900 mb-3">
              Vanlige spørsmål
            </h2>
          </div>
          <dl className="space-y-4">
            {faqs.map((faq) => (
              <details
                key={faq.q}
                className="group rounded-xl border border-slate-200 bg-slate-50 px-5 py-4 cursor-pointer"
              >
                <summary className="flex items-center justify-between gap-4 list-none font-medium text-slate-900 text-sm">
                  {faq.q}
                  <ChevronDown className="h-4 w-4 text-slate-400 transition-transform group-open:rotate-180 shrink-0" />
                </summary>
                <p className="mt-3 text-sm text-slate-600 leading-relaxed">
                  {faq.a}
                </p>
              </details>
            ))}
          </dl>
        </div>
      </section>

      {/* Tjenester-banner */}
      <section className="py-16 px-4 bg-slate-50 border-t border-slate-200">
        <div className="container mx-auto max-w-4xl text-center">
          <h2 className="text-2xl font-bold text-slate-900 mb-3">
            Et komplett økosystem for eiendom
          </h2>
          <p className="text-slate-500 mb-8 max-w-xl mx-auto">
            Fra eiendomsanalyse og situasjonsplan til 3D-modell, dispensasjon og boligpresentasjon – alt på ett sted.
          </p>
          <div className="flex flex-wrap justify-center gap-3 mb-8">
            {['situasjonsplan.no', 'dispensasjonen.no', 'naboklagen.no', 'ferdigattesten.no', 'minni.no', 'nops.no'].map((d) => (
              <span key={d} className="rounded-full border border-slate-200 bg-white px-4 py-1.5 text-sm font-medium text-slate-600">
                {d}
              </span>
            ))}
          </div>
          <Link
            href="/tjenester"
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            Se alle tjenester
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* What's included checklist */}
      <section className="py-16 px-4 bg-white border-t border-slate-200">
        <div className="container mx-auto max-w-4xl">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-10 items-center">
            <div>
              <h2 className="text-2xl font-bold text-slate-900 mb-4">
                Gratis konto inkluderer
              </h2>
              <ul className="space-y-3">
                {[
                  '5 eiendomsoppslag per måned',
                  'Full matrikkeldata fra Kartverket',
                  'Byggesakshistorikk',
                  'Gjeldende reguleringsplaner',
                  'Kartvisualisering',
                  'Del-lenke for eiendomsrapport',
                ].map((item) => (
                  <li key={item} className="flex items-center gap-2.5 text-sm text-slate-700">
                    <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-2xl border border-blue-100 bg-blue-50 p-8 text-center">
              <p className="text-4xl font-bold text-blue-700 mb-2">Gratis</p>
              <p className="text-sm text-blue-600 mb-6">Ingen kredittkort. Ingen bindingstid.</p>
              <Link
                href="/register"
                className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-700 transition-colors w-full"
              >
                Opprett gratis konto
              </Link>
              <p className="mt-4 text-xs text-blue-500">
                Oppgrader til Starter (499 kr/mnd) for AI-analyse og PDF-rapporter
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA footer */}
      <section className="py-24 px-4 bg-gradient-to-br from-blue-600 to-indigo-700 text-white">
        <div className="container mx-auto max-w-2xl text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            Klar for å prøve Norges mest komplette eiendomsverktøy?
          </h2>
          <p className="text-blue-100 text-lg mb-2">
            20+ tjenester samlet på ett sted. Avviksdeteksjon, 2D til 3D, dispensasjon, ferdigattest og mer.
          </p>
          <p className="text-blue-200 text-sm mb-10">
            Gratis å starte &middot; Ingen binding &middot; Avbryt når som helst
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/register"
              className="inline-flex items-center justify-center rounded-lg bg-white px-8 py-3.5 text-base font-semibold text-blue-700 shadow-md hover:bg-blue-50 transition-colors"
            >
              Opprett gratis konto
            </Link>
            <Link
              href="/pricing"
              className="inline-flex items-center justify-center rounded-lg border border-white/40 bg-white/10 px-8 py-3.5 text-base font-semibold text-white hover:bg-white/20 transition-colors"
            >
              Se priser
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
