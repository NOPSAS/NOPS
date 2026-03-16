import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Personvernerklæring – nops.no',
};

export default function PersonvernPage() {
  return (
    <main className="min-h-screen bg-white">
      <section className="py-16 px-4">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">
            Personvernerklæring
          </h1>
          <p className="text-sm text-slate-400 mb-10">
            Sist oppdatert: mars 2026
          </p>

          <div className="space-y-10 text-slate-700 leading-relaxed">
            {/* Behandlingsansvarlig */}
            <section>
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                1. Behandlingsansvarlig
              </h2>
              <p>
                Konsepthus AS (org.nr. XXX XXX XXX) er behandlingsansvarlig for
                personopplysninger som behandles i forbindelse med nops.no og
                ByggSjekk-tjenesten.
              </p>
              <p className="mt-2">
                Kontakt:{' '}
                <a href="mailto:hey@nops.no" className="text-blue-600 hover:underline">
                  hey@nops.no
                </a>
              </p>
            </section>

            {/* Hvilke opplysninger */}
            <section>
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                2. Hvilke opplysninger vi samler inn
              </h2>
              <ul className="list-disc pl-5 space-y-1.5">
                <li>Navn og e-postadresse ved registrering</li>
                <li>Adresser og eiendomsidentifikatorer du søker opp i tjenesten</li>
                <li>Betalingsinformasjon som behandles via Stripe (vi lagrer ikke kortnummer)</li>
                <li>Teknisk informasjon som IP-adresse og nettlesertype ved bruk av tjenesten</li>
              </ul>
            </section>

            {/* Formål */}
            <section>
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                3. Formål med behandlingen
              </h2>
              <ul className="list-disc pl-5 space-y-1.5">
                <li>Levere og drifte tjenesten, herunder eiendomsoppslag og AI-analyser</li>
                <li>Fakturering og abonnementshåndtering</li>
                <li>Forbedre og videreutvikle tjenesten</li>
                <li>Kommunikasjon om tjenesten, herunder driftsvarsel og support</li>
              </ul>
            </section>

            {/* Rettslig grunnlag */}
            <section>
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                4. Rettslig grunnlag
              </h2>
              <p>
                Behandlingen av personopplysninger skjer med følgende rettslige
                grunnlag i henhold til personvernforordningen (GDPR):
              </p>
              <ul className="list-disc pl-5 space-y-1.5 mt-2">
                <li>
                  <strong>Avtale</strong> (art. 6 (1)(b)) – nødvendig for å oppfylle
                  avtalen om bruk av tjenesten
                </li>
                <li>
                  <strong>Samtykke</strong> (art. 6 (1)(a)) – der du har gitt
                  uttrykkelig samtykke, for eksempel til markedskommunikasjon
                </li>
                <li>
                  <strong>Berettiget interesse</strong> (art. 6 (1)(f)) – for
                  tjenesteforbedrende analyser og sikkerhet
                </li>
              </ul>
            </section>

            {/* Deling med tredjeparter */}
            <section>
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                5. Deling med tredjeparter
              </h2>
              <p>Vi deler opplysninger med følgende tredjeparter, utelukkende for å levere tjenesten:</p>
              <ul className="list-disc pl-5 space-y-1.5 mt-2">
                <li>
                  <strong>Stripe</strong> – behandling av betalinger. Stripe opptrer
                  som selvstendig behandlingsansvarlig for betalingsdata.
                </li>
                <li>
                  <strong>Resend</strong> – utsending av transaksjonelle e-poster
                  (bekreftelser, varslinger).
                </li>
                <li>
                  <strong>Anthropic</strong> – AI-analyse av eiendomsdata. Ingen
                  personopplysninger sendes til Anthropic; kun offentlig tilgjengelig
                  eiendomsinformasjon benyttes.
                </li>
                <li>
                  <strong>Kartverket</strong> – oppslag i offentlige registre
                  (matrikkel, grunnbok, byggesaker).
                </li>
              </ul>
            </section>

            {/* Lagring */}
            <section>
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                6. Lagring og sikkerhet
              </h2>
              <p>
                Personopplysninger lagres på servere innenfor EU/EØS. Vi benytter
                kryptering i transit og i ro for å beskytte dine data. Data slettes
                ved forespørsel, med unntak av opplysninger vi er lovpålagt å
                oppbevare (f.eks. regnskapsinformasjon).
              </p>
            </section>

            {/* Dine rettigheter */}
            <section>
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                7. Dine rettigheter
              </h2>
              <p>Du har følgende rettigheter i henhold til GDPR:</p>
              <ul className="list-disc pl-5 space-y-1.5 mt-2">
                <li><strong>Innsyn</strong> – rett til å få vite hvilke opplysninger vi har om deg</li>
                <li><strong>Retting</strong> – rett til å korrigere uriktige opplysninger</li>
                <li><strong>Sletting</strong> – rett til å be om at dine data slettes</li>
                <li><strong>Dataportabilitet</strong> – rett til å motta dine data i et maskinlesbart format</li>
                <li><strong>Klage</strong> – rett til å klage til Datatilsynet dersom du mener vi behandler opplysningene dine i strid med regelverket</li>
              </ul>
              <p className="mt-2">
                Henvendelser rettes til{' '}
                <a href="mailto:hey@nops.no" className="text-blue-600 hover:underline">
                  hey@nops.no
                </a>
                .
              </p>
            </section>

            {/* Cookies */}
            <section>
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                8. Cookies og lokal lagring
              </h2>
              <p>
                Vi benytter ikke tradisjonelle informasjonskapsler (cookies).
                Autentiseringstokenet lagres i nettleserens localStorage for å holde
                deg innlogget. Vi bruker ingen tredjepartscookies eller
                sporingsverktøy.
              </p>
            </section>

            {/* Kontakt */}
            <section>
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                9. Kontakt
              </h2>
              <p>
                Har du spørsmål om personvern eller ønsker å utøve dine rettigheter,
                ta kontakt på{' '}
                <a href="mailto:hey@nops.no" className="text-blue-600 hover:underline">
                  hey@nops.no
                </a>
                .
              </p>
            </section>
          </div>

          <div className="mt-12 pt-8 border-t border-slate-200">
            <Link
              href="/tjenester"
              className="text-sm text-blue-600 hover:underline font-medium"
            >
              Tilbake til tjenester
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
