'use client';

import * as React from 'react';
import Link from 'next/link';
import { CheckCircle2, ShieldCheck, ChevronDown, ArrowRight, AlertTriangle, Box, FileText, Trees, Scale, MapPin, Camera } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/app/auth-provider';

export default function PricingPage() {
  const [yearly, setYearly] = React.useState(false);
  const { user } = useAuth();

  React.useEffect(() => {
    document.title = 'Priser – nops.no';
  }, []);

  return (
    <main className="min-h-screen bg-white">
      {/* Hero */}
      <section className="bg-[#0a0f1e] px-6 py-20 text-center text-white">
        <p className="text-sm font-semibold uppercase tracking-widest text-blue-400">Priser</p>
        <h1 className="mt-3 text-4xl font-extrabold sm:text-5xl">
          Enkle og transparente priser
        </h1>
        <p className="mx-auto mt-4 max-w-lg text-lg text-slate-400">
          Gratis eiendomssjekk for alle. Abonnement for profesjonelle.
          Engangstjenester for prosjekter.
        </p>
      </section>

      {/* ━━━━━━━━━━━━━ ABONNEMENT ━━━━━━━━━━━━━ */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <div className="mb-4 flex items-center gap-3">
            <div className="h-px flex-1 bg-slate-200" />
            <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Abonnement – digital selvbetjening</p>
            <div className="h-px flex-1 bg-slate-200" />
          </div>
          <p className="mb-10 text-center text-sm text-slate-500">
            Løpende tilgang til alle digitale verktøy. Avbryt når som helst.
          </p>

          {/* Toggle */}
          <div className="mb-10 flex justify-center">
            <div className="inline-flex items-center gap-3 rounded-full bg-slate-100 p-1">
              <button type="button" onClick={() => setYearly(false)}
                className={cn('rounded-full px-5 py-2 text-sm font-medium transition', !yearly ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500')}>
                Månedlig
              </button>
              <button type="button" onClick={() => setYearly(true)}
                className={cn('rounded-full px-5 py-2 text-sm font-medium transition', yearly ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500')}>
                Årlig <span className="ml-1 text-xs font-semibold text-emerald-600">spar 25%</span>
              </button>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {/* Gratis */}
            <div className="flex flex-col rounded-2xl border border-slate-200 p-8">
              <h3 className="text-lg font-bold text-slate-900">Gratis</h3>
              <p className="mt-1 text-sm text-slate-500">Prøv nops.no uten forpliktelse</p>
              <p className="mt-4 text-4xl font-extrabold text-slate-900">0 <span className="text-base font-normal text-slate-400">kr/mnd</span></p>
              <ul className="mt-6 flex-1 space-y-3">
                {[
                  '5 eiendomsoppslag per måned',
                  'Matrikkeldata og byggesaker',
                  'Reguleringsplan og DOK-analyse',
                  'Ferdigattest-sjekk',
                  'Energimerke-estimat',
                  'Gratis avvikskontroll',
                ].map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-sm text-slate-600">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />{f}
                  </li>
                ))}
              </ul>
              <Link href={user ? '/account/billing' : '/register'}
                className="mt-8 block rounded-xl border border-slate-200 py-3 text-center text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
                {user ? 'Administrer' : 'Kom i gang gratis'}
              </Link>
            </div>

            {/* Starter */}
            <div className="relative flex flex-col rounded-2xl border-2 border-blue-600 p-8 shadow-lg shadow-blue-600/10">
              <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full bg-blue-600 px-4 py-1 text-xs font-semibold text-white">Mest populær</span>
              <h3 className="text-lg font-bold text-slate-900">Starter</h3>
              <p className="mt-1 text-sm text-slate-500">For arkitekter og rådgivere</p>
              <p className="mt-4 text-4xl font-extrabold text-slate-900">
                {yearly ? '4 490' : '499'} <span className="text-base font-normal text-slate-400">kr/{yearly ? 'år' : 'mnd'}</span>
              </p>
              {yearly && <p className="text-xs text-slate-400">Faktureres 4 490 kr per år</p>}
              <ul className="mt-6 flex-1 space-y-3">
                {[
                  'Ubegrenset eiendomsoppslag',
                  'AI-risikoanalyse',
                  'Avviksdeteksjon med AI',
                  'PDF-rapporter',
                  'Finn.no-analyse',
                  'Energirådgivning',
                  'Juridisk AI-assistent',
                  'Godkjente tegninger (gratis)',
                ].map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-sm text-slate-600">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-blue-500" />{f}
                  </li>
                ))}
              </ul>
              <Link href={user ? '/account/billing' : '/register'}
                className="mt-8 block rounded-xl bg-blue-600 py-3 text-center text-sm font-semibold text-white transition hover:bg-blue-500">
                {user ? 'Oppgrader' : 'Start Starter'}
              </Link>
            </div>

            {/* Professional */}
            <div className="flex flex-col rounded-2xl border border-slate-200 p-8">
              <h3 className="text-lg font-bold text-slate-900">Professional</h3>
              <p className="mt-1 text-sm text-slate-500">For team og selskaper</p>
              <p className="mt-4 text-4xl font-extrabold text-slate-900">
                {yearly ? '8 990' : '999'} <span className="text-base font-normal text-slate-400">kr/{yearly ? 'år' : 'mnd'}</span>
              </p>
              {yearly && <p className="text-xs text-slate-400">Faktureres 8 990 kr per år</p>}
              <ul className="mt-6 flex-1 space-y-3">
                {[
                  'Alt i Starter',
                  'API-tilgang',
                  'Team-administrasjon',
                  'Hvit-etikett rapporter',
                  'Prioritert support',
                  'Faktura-betaling',
                ].map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-sm text-slate-600">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />{f}
                  </li>
                ))}
              </ul>
              <Link href={user ? '/account/billing' : '/register'}
                className="mt-8 block rounded-xl border border-slate-200 py-3 text-center text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
                {user ? 'Oppgrader' : 'Start Professional'}
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━ ENGANGSTJENESTER ━━━━━━━━━━━━━ */}
      <section className="bg-slate-50 px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <div className="mb-4 flex items-center gap-3">
            <div className="h-px flex-1 bg-slate-200" />
            <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Engangstjenester – hands-on leveranse</p>
            <div className="h-px flex-1 bg-slate-200" />
          </div>
          <p className="mb-10 text-center text-sm text-slate-500">
            Prosjektbaserte tjenester levert av vårt team. Betales per oppdrag.
          </p>

          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {/* Avvikskontroll */}
            <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-red-50">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Avvikskontroll</h3>
              <p className="mt-1 flex-1 text-sm leading-relaxed text-slate-500">
                Faglig kontroll av om annonsert bruk samsvarer med godkjente tegninger.
              </p>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-2xl font-extrabold text-emerald-600">Gratis</span>
              </div>
              <p className="mt-1 text-xs text-slate-400">Avvik fikses mot tilbud</p>
              <Link href="/avvik" className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-red-600 hover:text-red-700">
                Bestill kontroll <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            {/* Dispensasjon */}
            <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50">
                <Scale className="h-5 w-5 text-amber-600" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Dispensasjonssøknad</h3>
              <p className="mt-1 flex-1 text-sm leading-relaxed text-slate-500">
                AI-generert dispensasjonssøknad med fordel/ulempe-vurdering etter PBL §19-2.
              </p>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-2xl font-extrabold text-slate-900">3 000</span>
                <span className="text-sm text-slate-400">kr</span>
              </div>
              <Link href="/dispensasjon" className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-amber-600 hover:text-amber-700">
                Bestill søknad <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            {/* 2D til 3D */}
            <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50">
                <Box className="h-5 w-5 text-blue-600" />
              </div>
              <h3 className="text-base font-bold text-slate-900">2D til 3D-modell</h3>
              <p className="mt-1 flex-1 text-sm leading-relaxed text-slate-500">
                Plantegninger konvertert til IFC, SketchUp eller Revit.
              </p>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-sm font-semibold text-slate-500">fra</span>
                <span className="text-2xl font-extrabold text-slate-900">5 000</span>
                <span className="text-sm text-slate-400">kr</span>
              </div>
              <Link href="/visualisering" className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-blue-600 hover:text-blue-700">
                Bestill modell <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            {/* Byggesøknad */}
            <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50">
                <FileText className="h-5 w-5 text-emerald-600" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Byggesøknad</h3>
              <p className="mt-1 flex-1 text-sm leading-relaxed text-slate-500">
                Komplett byggesøknad med tegninger, nabovarsel og oppfølging. Leveres av Tegnebua.no.
              </p>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-sm font-semibold text-slate-500">fra</span>
                <span className="text-2xl font-extrabold text-slate-900">15 000</span>
                <span className="text-sm text-slate-400">kr</span>
              </div>
              <a href="https://tegnebua.no" target="_blank" rel="noopener noreferrer"
                className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-emerald-600 hover:text-emerald-700">
                Bestill via Tegnebua.no <ArrowRight className="h-3.5 w-3.5" />
              </a>
            </div>

            {/* Tomtetjenesten */}
            <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-green-50">
                <Trees className="h-5 w-5 text-green-600" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Tomtetjenesten</h3>
              <p className="mt-1 flex-1 text-sm leading-relaxed text-slate-500">
                Mulighetsstudie med ferdighusmodeller, kostnadskalkulator og presentasjonsside.
              </p>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-2xl font-extrabold text-slate-900">15 000</span>
                <span className="text-sm text-slate-400">kr</span>
                <span className="text-xs text-slate-400">eller 2% av salgssum</span>
              </div>
              <Link href="/tomter" className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-green-600 hover:text-green-700">
                Les mer <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            {/* Situasjonsplan */}
            <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-50">
                <MapPin className="h-5 w-5 text-cyan-600" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Situasjonsplan</h3>
              <p className="mt-1 flex-1 text-sm leading-relaxed text-slate-500">
                Profesjonell situasjonsplan til byggesøknad. Kommuneklar PDF.
              </p>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-sm font-semibold text-slate-500">fra</span>
                <span className="text-2xl font-extrabold text-slate-900">3 000</span>
                <span className="text-sm text-slate-400">kr</span>
              </div>
              <Link href="/situasjonsplan" className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-cyan-600 hover:text-cyan-700">
                Bestill <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━ TILLIT ━━━━━━━━━━━━━ */}
      <section className="bg-white px-6 py-12">
        <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-center gap-8 text-sm text-slate-400">
          {['Ingen bindingstid', 'GDPR-kompatibel', 'Norske data', 'Avbryt når som helst', 'Faktura (Pro)'].map((t) => (
            <span key={t} className="flex items-center gap-1.5">
              <ShieldCheck className="h-4 w-4 text-emerald-500" />{t}
            </span>
          ))}
        </div>
      </section>

      {/* ━━━━━━━━━━━━━ FAQ ━━━━━━━━━━━━━ */}
      <section className="bg-slate-50 px-6 py-20">
        <div className="mx-auto max-w-3xl">
          <h2 className="mb-10 text-center text-2xl font-extrabold text-slate-900">Vanlige spørsmål</h2>
          <dl className="space-y-3">
            {[
              { q: 'Hva er forskjellen på abonnement og engangstjenester?', a: 'Abonnement gir deg tilgang til alle digitale verktøy (eiendomssøk, AI-analyse, avviksdeteksjon, rapporter). Engangstjenester er prosjektbaserte leveranser der teamet vårt gjør arbeidet for deg (tegninger, søknader, avvikskontroll).' },
              { q: 'Er avvikskontrollen virkelig gratis?', a: 'Ja, selve kontrollen er kostnadsfri. Dersom vi finner avvik, får du et tilbud på hva det koster å rette opp. Du forplikter deg ikke til noe.' },
              { q: 'Hvem gjør byggesøknaden?', a: 'Byggesøknader leveres av Tegnebua.no, som er en del av samme selskap (Konsepthus AS). Vi har ansvarlig søker-kompetanse og håndterer hele prosessen.' },
              { q: 'Kan jeg bytte plan?', a: 'Ja. Oppgrader eller nedgrader når som helst. Ingen bindingstid. Årlig betaling gir 25% rabatt.' },
              { q: 'Hva er inkludert i gratisplanen?', a: '5 eiendomsoppslag per måned med matrikkeldata, byggesaker, reguleringsplan, DOK-analyse, energimerke og ferdigattest-sjekk. AI-analyse og PDF krever Starter.' },
            ].map((faq) => (
              <details key={faq.q} className="group rounded-xl border border-slate-200 bg-white px-5 py-4">
                <summary className="flex cursor-pointer items-center justify-between gap-4 text-sm font-medium text-slate-900">
                  {faq.q}
                  <ChevronDown className="h-4 w-4 shrink-0 text-slate-400 transition group-open:rotate-180" />
                </summary>
                <p className="mt-3 text-sm leading-relaxed text-slate-500">{faq.a}</p>
              </details>
            ))}
          </dl>
          <p className="mt-8 text-center text-sm text-slate-500">
            Flere spørsmål? <a href="mailto:hey@nops.no" className="font-medium text-blue-600 hover:underline">hey@nops.no</a>
          </p>
        </div>
      </section>
    </main>
  );
}
