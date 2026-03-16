import Link from 'next/link';
import {
  Box,
  Camera,
  FileOutput,
  Sun,
  Home,
  FileText,
  Scale,
  Users,
  Map,
  Award,
  ArrowRight,
  ExternalLink,
  Sparkles,
  BarChart3,
  TrendingUp,
  Layers,
  Trees,
  Search,
  FileSearch,
  Gavel,
  Zap,
} from 'lucide-react';

interface Tjeneste {
  icon: React.ReactNode;
  navn: string;
  beskrivelse: string;
  pris?: string;
  url: string;
  ekstern: boolean;
  kategori: 'tegning' | 'dokumentasjon' | 'juridisk' | 'salg';
  badge?: string;
}

const tjenester: Tjeneste[] = [
  // Tegning og modellering
  {
    icon: <Sparkles className="h-6 w-6" />,
    navn: 'AI-visualisering og render',
    beskrivelse: 'Last opp boligfoto, Finn.no-bilder, skisser eller plantegninger og få øyeblikkelig arkitektonisk analyse og fotorealistiske renders.',
    url: '/visualisering',
    ekstern: false,
    kategori: 'tegning',
    badge: 'ByggSjekk',
  },
  {
    icon: <Box className="h-6 w-6" />,
    navn: '3D-modell av bygning',
    beskrivelse: 'Digitale 3D-modeller basert på godkjente tegninger for byggesak og prosjektering. Leveres som IFC, SKP eller RVT.',
    url: 'https://www.nops.no',
    ekstern: true,
    kategori: 'tegning',
    badge: 'nops.no',
  },
  {
    icon: <FileOutput className="h-6 w-6" />,
    navn: 'Formatkonvertering',
    beskrivelse: 'Konvertering mellom CAD-formater: DWG, IFC, SketchUp, Revit og PDF. Rask levering.',
    url: 'https://www.nops.no',
    ekstern: true,
    kategori: 'tegning',
    badge: 'nops.no',
  },
  {
    icon: <Map className="h-6 w-6" />,
    navn: 'Situasjonsplan',
    beskrivelse: 'Profesjonelle situasjonsplaner til byggesøknad. Kommuneklar PDF. Dekker hele Norge.',
    pris: 'fra 3 000 kr',
    url: '/situasjonsplan',
    ekstern: false,
    kategori: 'tegning',
    badge: 'ByggSjekk',
  },
  // Dokumentasjon
  {
    icon: <Camera className="h-6 w-6" />,
    navn: 'Boligfoto med 360° visning',
    beskrivelse: 'Profesjonell fotodokumentasjon med interaktiv 360-graders visning for byggesak og markedsføring.',
    url: 'https://www.nops.no',
    ekstern: true,
    kategori: 'dokumentasjon',
    badge: 'nops.no',
  },
  {
    icon: <Sun className="h-6 w-6" />,
    navn: 'Lysberegning',
    beskrivelse: 'Beregning av dagslys og solinnfall for byggesøknad og prosjektering. Dokumentasjon etter TEK17.',
    url: 'https://www.nops.no',
    ekstern: true,
    kategori: 'dokumentasjon',
    badge: 'nops.no',
  },
  {
    icon: <Award className="h-6 w-6" />,
    navn: 'Ferdigattest',
    beskrivelse: 'Profesjonell hjelp til å få ferdigattest for ditt bygg. Vi håndterer søknadsprosessen.',
    url: '/ferdigattest',
    ekstern: false,
    kategori: 'dokumentasjon',
    badge: 'ByggSjekk',
  },
  // Juridisk
  {
    icon: <Gavel className="h-6 w-6" />,
    navn: 'Juridisk AI-assistent',
    beskrivelse: 'Still spørsmål om PBL, TEK17 og SAK10 – eller få komplett juridisk vurdering av et tiltak. Med paragrafhenvisninger.',
    url: '/juridisk',
    ekstern: false,
    kategori: 'juridisk',
    badge: 'ByggSjekk',
  },
  {
    icon: <Scale className="h-6 w-6" />,
    navn: 'Dispensasjon',
    beskrivelse: 'Profesjonell hjelp til byggesøknader og dispensasjoner fra plan- og bygningsloven.',
    url: '/dispensasjon',
    ekstern: false,
    kategori: 'juridisk',
    badge: 'ByggSjekk',
  },
  {
    icon: <Users className="h-6 w-6" />,
    navn: 'Naboklage',
    beskrivelse: 'Profesjonell hjelp til merknader på nabovarsel. Vi hjelper deg med å formulere og levere klage.',
    url: '/naboklage',
    ekstern: false,
    kategori: 'juridisk',
    badge: 'ByggSjekk',
  },
  // Salg
  {
    icon: <BarChart3 className="h-6 w-6" />,
    navn: 'Komplett eiendomspakke',
    beskrivelse: 'Automatisk pipeline: adresse inn → matrikkel, byggesaker, AI-analyse, renders og PDF-rapport ut. Kjøper-, selger- og arkitektpakke.',
    pris: 'fra 2 490 kr',
    url: '/pakke',
    ekstern: false,
    kategori: 'salg',
    badge: 'ByggSjekk',
  },
  {
    icon: <TrendingUp className="h-6 w-6" />,
    navn: 'Investeringsanalyse',
    beskrivelse: 'Beregn yield, ROI, cashflow og break-even for enhver eiendom. Komplett lønnsomhetsanalyse for kjøp og utleie.',
    url: '/investering',
    ekstern: false,
    kategori: 'salg',
    badge: 'ByggSjekk',
  },
  {
    icon: <Layers className="h-6 w-6" />,
    navn: 'AI Romplanlegger',
    beskrivelse: 'Beskriv rommet ditt og få fargepalette, materialanbefalinger, møbelplan og produktforslag fra norske butikker.',
    url: '/romplanlegger',
    ekstern: false,
    kategori: 'tegning',
    badge: 'ByggSjekk',
  },
  {
    icon: <Trees className="h-6 w-6" />,
    navn: 'Tomtetjenesten',
    beskrivelse: 'Mulighetsstudie, kostnadsberegning og presentasjon av tomter. Vi hjelper selgere å vise hva som kan bygges.',
    pris: 'fra 15 000 kr',
    url: '/tomter',
    ekstern: false,
    kategori: 'salg',
    badge: 'ByggSjekk',
  },
  {
    icon: <Home className="h-6 w-6" />,
    navn: 'Boligpresentasjon',
    beskrivelse: 'Komplett visuell presentasjon: 360°-omvisning, plantegning, foto, video og egen boligside. Levert på 24–48 timer.',
    pris: 'fra 4 990 kr',
    url: 'https://www.minni.no',
    ekstern: true,
    kategori: 'salg',
    badge: 'minni.no',
  },
  {
    icon: <FileText className="h-6 w-6" />,
    navn: 'Eiendomsrapport (PDF)',
    beskrivelse: 'Generer en komplett PDF-rapport for en eiendom med matrikkeldata, byggesaker, arealplaner og AI-analyse.',
    url: '/property',
    ekstern: false,
    kategori: 'dokumentasjon',
    badge: 'ByggSjekk',
  },
  {
    icon: <FileSearch className="h-6 w-6" />,
    navn: 'Dokumentanalyse og Tegninger',
    beskrivelse: 'Hent godkjente byggetegninger gratis (erstatter Norkart/Ambita). AI-analyse av dokumentasjonsstatus, compliance-gap og risiko.',
    url: '/dokumenter',
    ekstern: false,
    kategori: 'dokumentasjon',
    badge: 'ByggSjekk',
  },
  {
    icon: <Search className="h-6 w-6" />,
    navn: 'Finn.no Boliganalyse',
    beskrivelse: 'Analyser enhver Finn.no-annonse med AI. Finn avvik, vurder risiko og se forbedringspotensial – automatisk.',
    url: '/finn-analyse',
    ekstern: false,
    kategori: 'dokumentasjon',
    badge: 'ByggSjekk',
  },
  {
    icon: <Zap className="h-6 w-6" />,
    navn: 'Energiradgivning',
    beskrivelse: 'Se energimerke, sparepotensial og Enova-stotte for din bolig. Gratis AI-analyse med TEK17-sjekk og tiltaksplan.',
    url: '/energi',
    ekstern: false,
    kategori: 'dokumentasjon',
    badge: 'ByggSjekk',
  },
  {
    icon: <BarChart3 className="h-6 w-6" />,
    navn: 'Tomteutviklingsanalyse',
    beskrivelse: 'AI-analyse av utbyggingspotensial basert på Kartverket-data og reguleringsplan. Beregn antall enheter, lønnsomhet og scenarioer.',
    url: '/utbygging',
    ekstern: false,
    kategori: 'dokumentasjon',
    badge: 'ByggSjekk',
  },
];

const kategorier = [
  { id: 'tegning', label: 'Tegning og modellering' },
  { id: 'dokumentasjon', label: 'Dokumentasjon' },
  { id: 'juridisk', label: 'Juridisk og søknad' },
  { id: 'salg', label: 'Salg og markedsføring' },
] as const;

const kategoriFarge: Record<string, string> = {
  tegning: 'bg-blue-50 text-blue-700 border-blue-200',
  dokumentasjon: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  juridisk: 'bg-purple-50 text-purple-700 border-purple-200',
  salg: 'bg-amber-50 text-amber-700 border-amber-200',
};

const ikonfarge: Record<string, string> = {
  tegning: 'bg-blue-100 text-blue-600',
  dokumentasjon: 'bg-emerald-100 text-emerald-600',
  juridisk: 'bg-purple-100 text-purple-600',
  salg: 'bg-amber-100 text-amber-600',
};

export default function TjenesterPage() {
  return (
    <main className="min-h-screen bg-slate-50">
      {/* Hero */}
      <section className="bg-white border-b border-slate-200 py-12 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
            Alle tjenester
          </h1>
          <p className="text-lg text-slate-500 max-w-2xl mx-auto">
            nops.no samler Norges beste verktøy for eiendom, byggesak og arkitektur på ett sted.
            Fra eiendomsanalyse til 3D-modell og juridisk hjelp.
          </p>
        </div>
      </section>

      {/* Tjenester per kategori */}
      <div className="max-w-6xl mx-auto px-4 py-12 space-y-14">
        {kategorier.map((kat) => {
          const utvalg = tjenester.filter((t) => t.kategori === kat.id);
          return (
            <section key={kat.id}>
              <div className="flex items-center gap-3 mb-6">
                <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold ${kategoriFarge[kat.id]}`}>
                  {kat.label}
                </span>
                <div className="flex-1 border-t border-slate-200" />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                {utvalg.map((t) => {
                  const innhold = (
                    <div className="group relative flex flex-col h-full rounded-2xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md hover:border-slate-300 transition-all">
                      {/* Badge */}
                      <span className="absolute top-4 right-4 text-xs font-medium text-slate-400">
                        {t.badge}
                      </span>

                      {/* Ikon */}
                      <div className={`mb-4 flex h-11 w-11 items-center justify-center rounded-xl ${ikonfarge[t.kategori]}`}>
                        {t.icon}
                      </div>

                      {/* Innhold */}
                      <h3 className="text-base font-semibold text-slate-900 mb-2">{t.navn}</h3>
                      <p className="text-sm text-slate-500 leading-relaxed flex-1">{t.beskrivelse}</p>

                      {/* Footer */}
                      <div className="mt-5 flex items-center justify-between">
                        {t.pris ? (
                          <span className="text-sm font-semibold text-slate-700">{t.pris}</span>
                        ) : (
                          <span />
                        )}
                        <span className="inline-flex items-center gap-1 text-sm font-medium text-blue-600 group-hover:underline">
                          {t.ekstern ? (
                            <>Les mer <ExternalLink className="h-3.5 w-3.5" /></>
                          ) : (
                            <>Åpne <ArrowRight className="h-3.5 w-3.5" /></>
                          )}
                        </span>
                      </div>
                    </div>
                  );

                  return t.ekstern ? (
                    <a key={t.navn} href={t.url} target="_blank" rel="noopener noreferrer">
                      {innhold}
                    </a>
                  ) : (
                    <Link key={t.navn} href={t.url}>
                      {innhold}
                    </Link>
                  );
                })}
              </div>
            </section>
          );
        })}
      </div>

      {/* CTA */}
      <section className="bg-gradient-to-br from-blue-600 to-indigo-700 py-16 px-4 text-center text-white">
        <h2 className="text-2xl font-bold mb-3">Usikker på hva du trenger?</h2>
        <p className="text-blue-100 mb-6">Søk opp eiendommen og få en komplett oversikt – med anbefalte neste steg.</p>
        <Link
          href="/property"
          className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-sm font-semibold text-blue-700 hover:bg-blue-50 transition-colors"
        >
          Søk opp eiendom
          <ArrowRight className="h-4 w-4" />
        </Link>
      </section>
    </main>
  );
}
