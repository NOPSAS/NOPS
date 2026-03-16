import type { Metadata } from 'next';
import Link from 'next/link';
import { hentEiendomData } from './route-helpers';

interface Props {
  params: { knr: string; gnr: string; bnr: string };
}

function formaterAdresse(data: Record<string, unknown> | null): string {
  if (!data) return '';
  // Kartverket API returnerer adresse på ulike nivåer
  const adresser = data.adresser as Array<Record<string, unknown>> | undefined;
  if (adresser && adresser.length > 0) {
    const a = adresser[0];
    const veg = a.adressenavn as string | undefined;
    const nr = a.nummer as string | number | undefined;
    const bokstav = a.bokstav as string | undefined;
    const post = a.postnummer as string | undefined;
    const sted = a.poststed as string | undefined;
    const deler = [
      veg && nr != null ? `${veg} ${nr}${bokstav ?? ''}` : veg,
      [post, sted].filter(Boolean).join(' '),
    ].filter(Boolean);
    if (deler.length > 0) return deler.join(', ');
  }
  // Fallback til matrikkelnummer
  const knr = data.kommunenummer as string | undefined;
  const gnr = data.gaardsnummer as number | undefined;
  const bnr = data.bruksnummer as number | undefined;
  if (knr && gnr != null && bnr != null) {
    return `Gnr. ${gnr} Bnr. ${bnr}, kommune ${knr}`;
  }
  return 'Ukjent eiendom';
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const data = await hentEiendomData(params.knr, params.gnr, params.bnr);
  const adresse = formaterAdresse(data);
  return {
    title: adresse ? `${adresse} – nops.no ByggSjekk` : 'Eiendomsinformasjon – nops.no ByggSjekk',
    description: adresse
      ? `Se eiendomsdata, areal, byggeår og mer for ${adresse}. Kjør full AI-analyse med ByggSjekk.`
      : 'Se eiendomsdata og kjør full AI-analyse med ByggSjekk fra nops.no.',
  };
}

export default async function EiendomPage({ params }: Props) {
  const { knr, gnr, bnr } = params;
  const data = await hentEiendomData(knr, gnr, bnr);
  const adresse = formaterAdresse(data);

  // Hent bygningsdata om tilgjengelig
  const bygninger = data?.bygninger as Array<Record<string, unknown>> | undefined;
  const forsteBygning = bygninger?.[0];
  const byggeaar = forsteBygning?.byggeaar as number | undefined;
  const bygningstype = forsteBygning?.bygningstype as string | undefined;
  const areal = data?.arealer as Record<string, unknown> | undefined;
  const bruksareal = areal?.bruksareal as number | undefined;
  const grunnflate = areal?.grunnflate as number | undefined;
  const tomteareal = data?.areal_m2 as number | undefined;

  const propertyUrl = `/property?knr=${knr}&gnr=${gnr}&bnr=${bnr}`;

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Gradient header */}
      <div className="bg-gradient-to-br from-blue-600 to-blue-800 px-4 py-16 text-white">
        <div className="mx-auto max-w-3xl">
          <p className="mb-2 text-sm font-medium uppercase tracking-widest text-blue-200">
            Eiendomsinformasjon
          </p>
          <h1 className="text-3xl font-bold leading-tight sm:text-4xl">
            {adresse || `Gnr. ${gnr} / Bnr. ${bnr}`}
          </h1>
          {data ? (
            <p className="mt-2 text-blue-200">
              Kommune {knr} &middot; Gnr. {gnr} &middot; Bnr. {bnr}
            </p>
          ) : (
            <p className="mt-2 text-blue-200">Ingen data funnet for denne eiendommen</p>
          )}

          {/* CTA */}
          <Link
            href={propertyUrl}
            className="mt-8 inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-base font-semibold text-blue-700 shadow-lg transition hover:bg-blue-50 hover:shadow-xl"
          >
            Se full analyse
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2.5}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </Link>
        </div>
      </div>

      {/* Data cards */}
      <div className="mx-auto max-w-3xl px-4 py-10">
        {data ? (
          <>
            <h2 className="mb-4 text-lg font-semibold text-slate-700">Grunndata</h2>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              {(bruksareal ?? grunnflate ?? tomteareal) != null && (
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Areal</p>
                  <p className="mt-2 text-2xl font-bold text-slate-900">
                    {bruksareal ?? grunnflate ?? tomteareal} m²
                  </p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {bruksareal ? 'Bruksareal' : grunnflate ? 'Grunnflate' : 'Tomteareal'}
                  </p>
                </div>
              )}

              {byggeaar != null && (
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Byggeår</p>
                  <p className="mt-2 text-2xl font-bold text-slate-900">{byggeaar}</p>
                  <p className="mt-0.5 text-xs text-slate-500">Oppført</p>
                </div>
              )}

              {bygningstype && (
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm col-span-2">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Bygningstype</p>
                  <p className="mt-2 text-lg font-bold text-slate-900 leading-tight">{bygningstype}</p>
                </div>
              )}

              <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Kommunenr.</p>
                <p className="mt-2 text-2xl font-bold text-slate-900">{knr}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Gnr / Bnr</p>
                <p className="mt-2 text-2xl font-bold text-slate-900">{gnr} / {bnr}</p>
              </div>
            </div>
          </>
        ) : (
          <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
            <p className="text-slate-500">
              Kunne ikke hente eiendomsdata fra Kartverket. Eiendommen kan likevel analyseres.
            </p>
          </div>
        )}

        {/* Bottom CTA */}
        <div className="mt-10 rounded-xl border border-blue-100 bg-blue-50 p-6 text-center">
          <p className="font-semibold text-blue-900">Vil du se full eiendomsanalyse?</p>
          <p className="mt-1 text-sm text-blue-700">
            ByggSjekk henter byggesaker, arealplaner, avstand til vann og mer – med AI-risikovurdering.
          </p>
          <Link
            href={propertyUrl}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow transition hover:bg-blue-700"
          >
            Se full analyse
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2.5}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </Link>
        </div>

        <p className="mt-8 text-center text-xs text-slate-400">
          Data fra Kartverket Eiendomsregister &middot; nops.no ByggSjekk
        </p>
      </div>
    </main>
  );
}
