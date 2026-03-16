import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Brukervilkår – nops.no',
};

export default function VilkarPage() {
  return (
    <main className="min-h-screen bg-white">
      <section className="py-16 px-4">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">
            Brukervilkår
          </h1>
          <p className="text-sm text-slate-400 mb-10">
            Sist oppdatert: mars 2026
          </p>

          <div className="space-y-10 text-slate-700 leading-relaxed">
            {/* Tjenesten */}
            <section>
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                1. Om tjenesten
              </h2>
              <p>
                nops.no og ByggSjekk leveres av Konsepthus AS (org.nr. XXX XXX
                XXX). Tjenesten gir tilgang til eiendomsdata, AI-baserte analyser,
                visualisering og rapporter for eiendom og byggesak i Norge.
              </p>
            </section>

            {/* Bruk */}
            <section>
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                2. Bruk av tjenesten
              </h2>
              <p>
                Tjenesten skal kun benyttes til lovlige formål. Brukeren er
                ansvarlig for at opplysninger som legges inn er korrekte, og at
                tjenesten brukes i samsvar med gjeldende lover og regler.
              </p>
              <p className="mt-2">
                Det er ikke tillatt å misbruke tjenesten, herunder å forsøke å
                omgå tekniske begrensninger, scrape data i stor skala, eller
                bruke tjenesten på en måte som kan skade andre brukere eller
                tredjeparter.
              </p>
            </section>

            {/* AI-disclaimer */}
            <section>
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                3. AI-analyse og beslutningsstøtte
              </h2>
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
                <p className="font-semibold text-amber-900 mb-2">Viktig</p>
                <p className="text-amber-800">
                  Alle AI-genererte analyser, rapporter og anbefalinger i
                  tjenesten er ment som beslutningsstøtte. De utgjør ikke
                  juridisk, finansiell eller teknisk rådgivning. Ansvarlig
                  fagperson (arkitekt, ingeniør, advokat, takstmann e.l.) må
                  alltid kvalitetssikre resultater før de legges til grunn for
                  beslutninger.
                </p>
              </div>
            </section>

            {/* Abonnement */}
            <section>
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                4. Abonnement og betaling
              </h2>
              <p>
                Tilgang til utvidede funksjoner krever et betalt abonnement.
                Betaling håndteres av Stripe og kan gjennomføres med
                betalingskort. Abonnement faktureres månedlig eller årlig,
                avhengig av valgt plan.
              </p>
              <p className="mt-2">
                Du kan avslutte abonnementet når som helst. Ved oppsigelse
                beholder du tilgang til tjenesten ut inneværende betalingsperiode.
                Det gis ingen refusjon for delvis brukte perioder, med mindre
                annet følger av gjeldende forbrukerlovgivning.
              </p>
            </section>

            {/* Immaterielle rettigheter */}
            <section>
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                5. Immaterielle rettigheter
              </h2>
              <p>
                Alle rettigheter til tjenesten, herunder design, kode,
                varemerker og innhold, tilhører Konsepthus AS. Brukeren beholder
                alle rettigheter til egne data som lastes opp eller genereres
                gjennom tjenesten.
              </p>
            </section>

            {/* Ansvarsbegrensning */}
            <section>
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                6. Ansvarsbegrensning
              </h2>
              <p>
                Konsepthus AS er ikke ansvarlig for direkte eller indirekte tap
                som følge av:
              </p>
              <ul className="list-disc pl-5 space-y-1.5 mt-2">
                <li>Feil, mangler eller unøyaktigheter i AI-genererte analyser</li>
                <li>Manglende, forsinkede eller feilaktige data fra offentlige registre</li>
                <li>Driftsavbrudd, tekniske feil eller andre hendelser utenfor vår kontroll</li>
                <li>Beslutninger tatt på bakgrunn av informasjon fra tjenesten</li>
              </ul>
              <p className="mt-2">
                Tjenesten leveres &laquo;som den er&raquo;. Vi tilstreber høy
                kvalitet og tilgjengelighet, men kan ikke garantere at tjenesten
                til enhver tid er feilfri eller tilgjengelig.
              </p>
            </section>

            {/* Endringer */}
            <section>
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                7. Endringer i vilkårene
              </h2>
              <p>
                Vi forbeholder oss retten til å endre disse vilkårene. Vesentlige
                endringer varsles med minimum 30 dagers varsel via e-post eller
                gjennom tjenesten. Fortsatt bruk av tjenesten etter
                varslingsperioden anses som aksept av de oppdaterte vilkårene.
              </p>
            </section>

            {/* Tvister */}
            <section>
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                8. Lovvalg og verneting
              </h2>
              <p>
                Disse vilkårene reguleres av norsk rett. Eventuelle tvister som
                ikke kan løses i minnelighet, skal avgjøres av Oslo tingrett som
                verneting.
              </p>
            </section>

            {/* Kontakt */}
            <section>
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                9. Kontakt
              </h2>
              <p>
                Spørsmål om vilkårene kan rettes til{' '}
                <a href="mailto:hey@nops.no" className="text-blue-600 hover:underline">
                  hey@nops.no
                </a>
                .
              </p>
            </section>
          </div>

          <div className="mt-12 pt-8 border-t border-slate-200 flex items-center gap-6">
            <Link
              href="/personvern"
              className="text-sm text-blue-600 hover:underline font-medium"
            >
              Personvernerklæring
            </Link>
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
