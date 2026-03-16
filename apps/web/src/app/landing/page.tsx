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
} from 'lucide-react';

export const metadata: Metadata = {
  title: 'ByggSjekk – Norges smarteste eiendomsverktøy for arkitekter | nops.no',
  description:
    'ByggSjekk gir arkitekter og eiendomsaktører øyeblikkelig tilgang til byggesaker, arealplaner og AI-analyse – direkte fra offentlige registre. Gratis å starte.',
  openGraph: {
    title: 'ByggSjekk – Norges smarteste eiendomsverktøy for arkitekter',
    description:
      'Avdekk avvik, sjekk byggesaker og hent arealplaner på sekunder. Powered by Kartverket og AI.',
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
      <section className="bg-gradient-to-br from-blue-600 to-indigo-700 text-white py-24 px-4">
        <div className="container mx-auto max-w-4xl text-center">
          <div className="inline-flex items-center gap-2 mb-6 rounded-full bg-white/10 px-4 py-1.5 text-sm font-medium text-blue-100">
            <Building2 className="h-4 w-4" aria-hidden="true" />
            nops.no / ByggSjekk
          </div>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold leading-tight tracking-tight mb-6">
            Full eiendomsanalyse<br className="hidden sm:block" /> på under ett minutt
          </h1>
          <p className="text-lg sm:text-xl text-blue-100 max-w-2xl mx-auto mb-4">
            ByggSjekk gir deg øyeblikkelig tilgang til byggesaker, arealplaner,
            AI-analyse og verdiestimater – direkte fra offentlige registre.
          </p>
          <p className="text-sm text-blue-200 mb-10">
            Gratis å starte &middot; Ingen kredittkort nødvendig
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

      {/* Features grid */}
      <section className="py-24 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
              Alt du trenger, samlet på ett sted
            </h2>
            <p className="text-lg text-slate-500 max-w-xl mx-auto">
              ByggSjekk kobler deg til de viktigste offentlige registrene og gir
              deg AI-drevne innsikter tilpasset din arbeidsflyt.
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
            Klar for å spare timer per prosjekt?
          </h2>
          <p className="text-blue-100 text-lg mb-2">
            Bli med arkitekter og eiendomsaktører som allerede bruker ByggSjekk.
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
