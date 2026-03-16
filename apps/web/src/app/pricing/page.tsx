'use client';

import * as React from 'react';
import Link from 'next/link';
import { CheckCircle2, ShieldCheck, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/app/auth-provider';

const plans = [
  {
    id: 'free',
    name: 'Gratis',
    price: { monthly: 0, yearly: 0 },
    description: 'Kom i gang med grunnleggende eiendomssjekk.',
    features: [
      '5 eiendomsoppslag per måned',
      'Matrikkeldata og kartvisualisering',
      'Byggesaker og arealplaner',
      'Del-lenke for eiendomsrapport',
      'Ingen AI-analyser',
      'Ingen PDF-rapporter',
    ],
    cta: 'Kom i gang gratis',
    hrefGuest: '/register',
    hrefUser: '/account/billing',
    highlighted: false,
  },
  {
    id: 'starter',
    name: 'Starter',
    price: { monthly: 499, yearly: 4490 },
    description: 'Perfekt for mindre arkitektkontorer og konsulenter.',
    features: [
      '100 eiendomsoppslag per måned',
      '20 AI-analyser per måned',
      '20 PDF-rapporter per måned',
      'Matrikkeldata og kartvisualisering',
      'Byggesaker og arealplaner',
      'Verdiestimator',
      'E-poststøtte',
    ],
    cta: 'Velg Starter',
    hrefGuest: '/register',
    hrefUser: '/account/billing',
    highlighted: false,
  },
  {
    id: 'professional',
    name: 'Professional',
    price: { monthly: 999, yearly: 8990 },
    description: 'For profesjonelle aktører med høyt volum.',
    features: [
      'Ubegrenset eiendomsoppslag',
      'Ubegrenset AI-analyser',
      'Ubegrenset PDF-rapporter',
      'Matrikkeldata og kartvisualisering',
      'Byggesaker og arealplaner',
      'Verdiestimator',
      'API-tilgang',
      'Prioritert support',
    ],
    cta: 'Velg Professional',
    hrefGuest: '/register',
    hrefUser: '/account/billing',
    highlighted: true,
    badge: 'Mest populær',
  },
];

const faqs = [
  {
    q: 'Kan jeg bytte plan når som helst?',
    a: 'Ja. Oppgrader eller nedgrader abonnementet ditt til enhver tid. Endringer trer i kraft umiddelbart, og du betaler bare for det du faktisk bruker.',
  },
  {
    q: 'Er det bindingstid?',
    a: 'Nei. Månedlige abonnementer kan avsluttes når som helst. Årsabonnement faktureres for hele året, men gir 25% rabatt.',
  },
  {
    q: 'Hva skjer når jeg bruker opp kvoten min?',
    a: 'Du varsles når du nærmer deg grensen. Du kan enten oppgradere planen eller vente til neste måned. Vi stopper aldri tilgang uten varsel.',
  },
  {
    q: 'Støtter dere faktura?',
    a: 'Ja. Bedrifter med Professional-plan kan kontakte oss for faktureringsavtale.',
  },
  {
    q: 'Er dataene sikre?',
    a: 'All data behandles iht. norsk personvernlovgivning (GDPR). Vi lagrer kun det som er nødvendig for å levere tjenesten. Data fra offentlige registre deles aldri videre.',
  },
];

export default function PricingPage() {
  const [yearly, setYearly] = React.useState(false);
  const { user } = useAuth();

  return (
    <main className="min-h-screen bg-white">
      {/* Hero */}
      <section className="py-16 px-4 text-center">
        <div className="inline-flex items-center gap-1.5 mb-4 rounded-full bg-green-50 border border-green-200 px-3 py-1 text-xs font-semibold text-green-700">
          <ShieldCheck className="h-3.5 w-3.5" />
          Ingen bindingstid &middot; Avbryt når som helst
        </div>
        <h1 className="text-4xl font-bold text-slate-900 mb-4">
          Enkle og transparente priser
        </h1>
        <p className="text-lg text-slate-600 max-w-2xl mx-auto mb-8">
          Velg planen som passer ditt behov. Start gratis – oppgrader når du trenger mer.
        </p>

        {/* Billing toggle */}
        <div className="inline-flex items-center gap-3 bg-slate-100 rounded-full p-1">
          <button
            type="button"
            onClick={() => setYearly(false)}
            className={cn(
              'px-4 py-2 rounded-full text-sm font-medium transition-colors',
              !yearly
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            )}
          >
            Månedlig
          </button>
          <button
            type="button"
            onClick={() => setYearly(true)}
            className={cn(
              'px-4 py-2 rounded-full text-sm font-medium transition-colors',
              yearly
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            )}
          >
            Årlig
            <span className="ml-1.5 text-xs text-green-600 font-semibold">spar 25%</span>
          </button>
        </div>
      </section>

      {/* Plans */}
      <section className="px-4 pb-16">
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan) => {
            const price = yearly ? plan.price.yearly : plan.price.monthly;
            const period = yearly ? '/år' : '/mnd';

            return (
              <div
                key={plan.id}
                className={cn(
                  'relative rounded-2xl border p-8 flex flex-col',
                  plan.highlighted
                    ? 'border-blue-600 ring-2 ring-blue-600 shadow-lg'
                    : 'border-slate-200 shadow-sm'
                )}
              >
                {plan.badge && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                    <span className="bg-blue-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
                      {plan.badge}
                    </span>
                  </div>
                )}

                <div className="mb-6">
                  <h2 className="text-xl font-bold text-slate-900 mb-1">{plan.name}</h2>
                  <p className="text-sm text-slate-500 mb-4">{plan.description}</p>
                  <div className="flex items-baseline gap-1">
                    <span className="text-4xl font-bold text-slate-900">
                      {price === 0 ? 'Gratis' : `${price.toLocaleString('no-NO')} kr`}
                    </span>
                    {price > 0 && (
                      <span className="text-slate-500 text-sm">{period}</span>
                    )}
                  </div>
                  {yearly && price > 0 && (
                    <p className="text-xs text-slate-400 mt-1">
                      Faktureres {price.toLocaleString('no-NO')} kr per år
                    </p>
                  )}
                </div>

                <ul className="space-y-3 mb-8 flex-1">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2.5 text-sm text-slate-700">
                      <CheckCircle2
                        className={cn(
                          'h-5 w-5 mt-0.5 shrink-0',
                          plan.highlighted ? 'text-blue-600' : 'text-slate-400'
                        )}
                        aria-hidden="true"
                      />
                      {feature}
                    </li>
                  ))}
                </ul>

                <Link
                  href={user ? plan.hrefUser : plan.hrefGuest}
                  className={cn(
                    'block text-center rounded-xl px-6 py-3 text-sm font-semibold transition-colors',
                    plan.highlighted
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-slate-100 text-slate-900 hover:bg-slate-200'
                  )}
                >
                  {plan.cta}
                </Link>
              </div>
            );
          })}
        </div>
      </section>

      {/* Included in all plans */}
      <section className="bg-slate-50 border-t border-slate-200 py-12 px-4 text-center">
        <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">
          Alle planer inkluderer
        </p>
        <p className="text-slate-700 text-base">
          Matrikkeldata &middot; Byggesaker &middot; Arealplaner &middot; Planslurpen &middot; Verdiestimator &middot; Kartvisualisering
        </p>
      </section>

      {/* Trust row */}
      <section className="py-10 px-4 border-t border-slate-200 bg-white">
        <div className="max-w-3xl mx-auto flex flex-wrap justify-center gap-8 text-sm text-slate-500">
          {[
            'GDPR-kompatibel',
            'Norsk databehandling',
            'Avbryt når som helst',
            'Ingen skjulte gebyrer',
            'Faktura tilgjengelig (Pro)',
          ].map((t) => (
            <span key={t} className="flex items-center gap-1.5">
              <ShieldCheck className="h-4 w-4 text-green-500" />
              {t}
            </span>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20 px-4 bg-slate-50 border-t border-slate-200">
        <div className="container mx-auto max-w-3xl">
          <div className="text-center mb-10">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">
              Vanlige spørsmål om priser
            </h2>
          </div>
          <dl className="space-y-4">
            {faqs.map((faq) => (
              <details
                key={faq.q}
                className="group rounded-xl border border-slate-200 bg-white px-5 py-4 cursor-pointer"
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
          <p className="mt-8 text-center text-sm text-slate-500">
            Har du andre spørsmål?{' '}
            <a href="mailto:hey@nops.no" className="text-blue-600 hover:underline font-medium">
              Kontakt oss på hey@nops.no
            </a>
          </p>
        </div>
      </section>
    </main>
  );
}
