'use client';

import * as React from 'react';
import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import {
  Building2,
  Search,
  MapPin,
  FileText,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Home,
  Ruler,
  Calendar,
  Archive,
  CheckCircle2,
  XCircle,
  Info,
  Loader2,
  Sparkles,
  ShieldAlert,
  ShieldCheck,
  ShieldQuestion,
  TrendingUp,
  BarChart3,
  Printer,
  Download,
  Scale,
  Box,
  FileOutput,
  Map,
  Award,
  Home as HomeIcon,
  Wrench,
  Clock,
  Star,
  Share2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { getFullPropertyData, getPropertyAIAnalysis } from '@/lib/api';
import { AddressAutocomplete } from '@/components/address-autocomplete';
import { PropertyMap } from '@/components/property-map';
import { SjekklisteWidget } from '@/components/sjekkliste-widget';
import { GebyrKalkulator } from '@/components/gebyr-kalkulator';
import type { AddressSuggestion } from '@/lib/api';
import type { FullPropertyResult, PropertyAIAnalysis, VerdiestimatorData, PlanslurpenData } from '@/lib/types';
import { useSisteSøk } from '@/hooks/use-siste-sok';
import { useFavoritter } from '@/hooks/use-favoritter';

// ─── Kommunenavnliste ─────────────────────────────────────────────────────────

const KJENTE_KOMMUNER: Record<string, string> = {
  '0301': 'Oslo',
  '3201': 'Bærum',
  '3203': 'Asker',
  '3205': 'Lillestrøm',
  '3207': 'Nordre Follo',
  '3212': 'Nesodden',
  '3214': 'Ås',
  '4601': 'Bergen',
  '5001': 'Trondheim',
  '1103': 'Stavanger',
  '4204': 'Kristiansand',
  '3005': 'Drammen',
  '3403': 'Hamar',
  '3801': 'Skien',
  '3804': 'Porsgrunn',
};

function kommuneNavn(knr: string): string {
  return KJENTE_KOMMUNER[knr] ?? `Kommune ${knr}`;
}

// ─── Hjelpefunksjoner ─────────────────────────────────────────────────────────

function formatDato(dato: string | null | undefined): string {
  if (!dato) return '–';
  try {
    return new Date(dato).toLocaleDateString('nb-NO', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  } catch {
    return dato;
  }
}

// ─── Badge helpers ────────────────────────────────────────────────────────────

function planStatusBadge(status: string) {
  const s = status.toLowerCase();
  if (s.includes('vedtatt') || s.includes('gjeldende')) {
    return <Badge variant="success">{status}</Badge>;
  }
  if (s.includes('forslag') || s.includes('høring')) {
    return <Badge variant="warning">{status}</Badge>;
  }
  return <Badge variant="secondary">{status || 'Ukjent'}</Badge>;
}

function dispStatusBadge(status: string) {
  const s = status.toLowerCase();
  if (s.includes('innvilget') || s.includes('godkjent') || s.includes('innvilga')) {
    return <Badge variant="success">{status}</Badge>;
  }
  if (s.includes('avvist') || s.includes('avslått')) {
    return <Badge variant="destructive">{status}</Badge>;
  }
  if (s.includes('under behandling') || s.includes('mottatt')) {
    return <Badge variant="info">{status}</Badge>;
  }
  return <Badge variant="secondary">{status || 'Ukjent'}</Badge>;
}

function byggesakStatusBadge(status: string) {
  const s = status.toLowerCase();
  if (s.includes('ferdigattest') || s.includes('fs')) return <Badge variant="success">{status}</Badge>;
  if (s.includes('igangsett') || s.includes('ig') || s.includes('ramme')) return <Badge variant="info">{status}</Badge>;
  if (s.includes('avvist') || s.includes('avslått')) return <Badge variant="destructive">{status}</Badge>;
  return <Badge variant="secondary">{status || 'Ukjent'}</Badge>;
}

// ─── Collapsible section ──────────────────────────────────────────────────────

function Section({
  title,
  icon,
  count,
  children,
  defaultOpen = true,
}: {
  title: string;
  icon: React.ReactNode;
  count?: number;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = React.useState(defaultOpen);
  return (
    <Card>
      <CardHeader
        className="cursor-pointer select-none pb-3"
        onClick={() => setOpen((v) => !v)}
      >
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            {icon}
            {title}
            {count != null && (
              <span className="ml-1 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-700 dark:bg-blue-900 dark:text-blue-300">
                {count}
              </span>
            )}
          </CardTitle>
          {open ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </CardHeader>
      {open && <CardContent>{children}</CardContent>}
    </Card>
  );
}

// ─── Bygning card ─────────────────────────────────────────────────────────────

function BygningCard({ bygning }: { bygning: FullPropertyResult['bygninger'][0] }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-semibold text-slate-900 dark:text-white">
            {bygning.bygningstype || 'Ukjent bygningstype'}
          </p>
          <p className="text-xs text-muted-foreground">
            Bygningsnr. {bygning.bygningsnummer}
          </p>
        </div>
        {bygning.bygningstatus && (
          <Badge variant="outline" className="text-xs shrink-0">
            {bygning.bygningstatus}
          </Badge>
        )}
      </div>
      <div className="mt-3 grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
        {bygning.byggeaar != null && (
          <div>
            <span className="text-xs text-muted-foreground">Byggeår</span>
            <p className="font-medium">{bygning.byggeaar}</p>
          </div>
        )}
        {bygning.bruksareal != null && (
          <div>
            <span className="text-xs text-muted-foreground">Bruksareal</span>
            <p className="font-medium">{bygning.bruksareal.toFixed(0)} m²</p>
          </div>
        )}
        {bygning.etasjer.length > 0 && (
          <div>
            <span className="text-xs text-muted-foreground">Etasjer</span>
            <p className="font-medium">{bygning.etasjer.length}</p>
          </div>
        )}
        {bygning.bruksenheter.length > 0 && (
          <div>
            <span className="text-xs text-muted-foreground">Bruksenheter</span>
            <p className="font-medium">{bygning.bruksenheter.length}</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Byggesak row ─────────────────────────────────────────────────────────────

function ByggesakRow({ sak }: { sak: FullPropertyResult['byggesaker'][0] }) {
  const [open, setOpen] = React.useState(false);
  const tittel = sak.tittel || sak.beskrivelse || sak.sakstype || 'Ukjent sak';
  return (
    <div className="border-b border-slate-100 py-3 last:border-0 dark:border-slate-800">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            {byggesakStatusBadge(sak.status)}
            <span className="text-xs text-muted-foreground">{sak.saksnummer || '–'}</span>
            {sak.vedtaksdato && (
              <span className="text-xs text-muted-foreground">
                {formatDato(sak.vedtaksdato)}
              </span>
            )}
          </div>
          <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white line-clamp-2">
            {tittel}
          </p>
          {sak.tiltakstype && (
            <p className="text-xs text-muted-foreground">{sak.tiltakstype}</p>
          )}
        </div>
        {(sak.tiltakshaver || sak.ansvarlig_soeker || sak.dokumenter.length > 0) && (
          <button
            type="button"
            className="text-xs text-blue-600 hover:underline dark:text-blue-400 shrink-0"
            onClick={() => setOpen((v) => !v)}
          >
            {open ? 'Skjul' : 'Detaljer'}
          </button>
        )}
      </div>
      {open && (
        <div className="mt-2 space-y-1 text-xs text-muted-foreground pl-2 border-l-2 border-slate-200 dark:border-slate-700">
          {sak.tiltakshaver && (
            <p><span className="font-medium">Tiltakshaver:</span> {sak.tiltakshaver}</p>
          )}
          {sak.ansvarlig_soeker && (
            <p><span className="font-medium">Ansvarlig søker:</span> {sak.ansvarlig_soeker}</p>
          )}
          {sak.innsendtdato && (
            <p><span className="font-medium">Innsendt:</span> {formatDato(sak.innsendtdato)}</p>
          )}
          <p className="text-xs text-muted-foreground italic">Kilde: {sak.kilde}</p>
        </div>
      )}
    </div>
  );
}

// ─── Relaterte tjenester ──────────────────────────────────────────────────────

interface RelaterteTjenesterProps {
  adresse: string;
  gnr: number;
  bnr: number;
  knr: string;
  harDispensasjon: boolean;
  manglerFerdigattest: boolean;
}

function RelaterteTjenester({
  adresse, gnr, bnr, knr,
  harDispensasjon, manglerFerdigattest,
}: RelaterteTjenesterProps) {
  const adresseParam = encodeURIComponent(adresse);
  const eiendomParam = `gnr=${gnr}&bnr=${bnr}&knr=${knr}`;

  const tjenester = [
    {
      icon: <Map className="h-4 w-4" />,
      navn: 'Situasjonsplan',
      beskrivelse: 'Kommuneklar PDF til byggesøknad.',
      href: `https://www.situasjonsplan.no?adresse=${adresseParam}`,
      farge: 'border-blue-200 bg-blue-50 hover:bg-blue-100',
      ikonfarge: 'bg-blue-100 text-blue-600',
      badge: null,
    },
    {
      icon: <Scale className="h-4 w-4" />,
      navn: 'Dispensasjon',
      beskrivelse: harDispensasjon
        ? 'Dispensasjonsbehov oppdaget – få profesjonell hjelp.'
        : 'Hjelp med søknad om dispensasjon fra PBL.',
      href: `https://www.dispensasjonen.no?${eiendomParam}&adresse=${adresseParam}`,
      farge: harDispensasjon
        ? 'border-amber-300 bg-amber-50 hover:bg-amber-100'
        : 'border-slate-200 bg-white hover:bg-slate-50',
      ikonfarge: harDispensasjon ? 'bg-amber-100 text-amber-600' : 'bg-slate-100 text-slate-600',
      badge: harDispensasjon ? 'Anbefalt' : null,
    },
    {
      icon: <Award className="h-4 w-4" />,
      navn: 'Ferdigattest',
      beskrivelse: manglerFerdigattest
        ? 'Aktiv byggesak – sikre at ferdigattest er på plass.'
        : 'Hjelp til å skaffe ferdigattest for ditt bygg.',
      href: `https://www.ferdigattesten.no?${eiendomParam}&adresse=${adresseParam}`,
      farge: manglerFerdigattest
        ? 'border-orange-300 bg-orange-50 hover:bg-orange-100'
        : 'border-slate-200 bg-white hover:bg-slate-50',
      ikonfarge: manglerFerdigattest ? 'bg-orange-100 text-orange-600' : 'bg-slate-100 text-slate-600',
      badge: manglerFerdigattest ? 'OBS' : null,
    },
    {
      icon: <Box className="h-4 w-4" />,
      navn: '3D-modell',
      beskrivelse: 'Digitale 3D-modeller fra godkjente tegninger.',
      href: `https://www.nops.no?adresse=${adresseParam}`,
      farge: 'border-slate-200 bg-white hover:bg-slate-50',
      ikonfarge: 'bg-slate-100 text-slate-600',
      badge: null,
    },
    {
      icon: <FileOutput className="h-4 w-4" />,
      navn: 'Formatkonvertering',
      beskrivelse: 'DWG, IFC, SKP, RVT og PDF – konverter mellom formater.',
      href: 'https://www.nops.no',
      farge: 'border-slate-200 bg-white hover:bg-slate-50',
      ikonfarge: 'bg-slate-100 text-slate-600',
      badge: null,
    },
    {
      icon: <HomeIcon className="h-4 w-4" />,
      navn: 'Boligpresentasjon',
      beskrivelse: '360°, plantegning, foto og video til fast pris.',
      href: `https://www.minni.no?adresse=${adresseParam}`,
      farge: 'border-slate-200 bg-white hover:bg-slate-50',
      ikonfarge: 'bg-slate-100 text-slate-600',
      badge: null,
    },
  ];

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
      <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2 mb-4">
        <Wrench className="h-4 w-4 text-slate-500" />
        Relaterte tjenester
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {tjenester.map((t) => (
          <a
            key={t.navn}
            href={t.href}
            target="_blank"
            rel="noopener noreferrer"
            className={`relative flex items-start gap-3 rounded-xl border p-3 transition-colors ${t.farge}`}
          >
            {t.badge && (
              <span className="absolute top-2 right-2 rounded-full bg-amber-500 px-1.5 py-0.5 text-[10px] font-bold text-white">
                {t.badge}
              </span>
            )}
            <div className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${t.ikonfarge}`}>
              {t.icon}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-slate-900 dark:text-white">{t.navn}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">{t.beskrivelse}</p>
            </div>
            <ExternalLink className="ml-auto h-3 w-3 shrink-0 text-slate-400 mt-1" />
          </a>
        ))}
      </div>
    </div>
  );
}

// ─── Verdiestimator ───────────────────────────────────────────────────────────

function VerdiestimatorSection({ data }: { data: VerdiestimatorData }) {
  const formatKr = (v: number) =>
    new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(v);

  return (
    <Section
      title="Verdiestimator"
      icon={<TrendingUp className="h-4 w-4 text-emerald-600" />}
      defaultOpen={true}
    >
      <div className="space-y-4">
        {data.estimert_verdi != null ? (
          <>
            <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4 dark:bg-emerald-950 dark:border-emerald-900">
              <p className="text-xs text-emerald-700 dark:text-emerald-400 mb-0.5">Estimert markedsverdi</p>
              <p className="text-3xl font-bold text-emerald-900 dark:text-emerald-100">
                {formatKr(data.estimert_verdi)}
              </p>
              {data.konfidensintervall && (
                <p className="text-xs text-emerald-700 dark:text-emerald-400 mt-1">
                  Intervall: {formatKr(data.konfidensintervall[0])} – {formatKr(data.konfidensintervall[1])}
                </p>
              )}
              <p className="text-xs text-emerald-600 dark:text-emerald-500 mt-1 italic">
                {data.estimat_metode}
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {data.pris_per_kvm != null && (
                <div className="rounded-lg border border-slate-200 p-3 dark:border-slate-700">
                  <p className="text-xs text-muted-foreground">Pris per m²</p>
                  <p className="font-semibold text-slate-900 dark:text-white">
                    {new Intl.NumberFormat('nb-NO').format(data.pris_per_kvm)} kr/m²
                  </p>
                </div>
              )}
              {data.kommune_median_pris != null && (
                <div className="rounded-lg border border-slate-200 p-3 dark:border-slate-700">
                  <p className="text-xs text-muted-foreground">Kommunemedian</p>
                  <p className="font-semibold text-slate-900 dark:text-white">
                    {formatKr(data.kommune_median_pris)}
                  </p>
                </div>
              )}
              {data.kommune_prisvekst_prosent != null && (
                <div className="rounded-lg border border-slate-200 p-3 dark:border-slate-700">
                  <p className="text-xs text-muted-foreground flex items-center gap-1">
                    <BarChart3 className="h-3 w-3" />
                    Prisvekst (5 år)
                  </p>
                  <p className="font-semibold text-slate-900 dark:text-white">
                    +{data.kommune_prisvekst_prosent.toFixed(1)}%
                  </p>
                </div>
              )}
            </div>

            <p className="text-xs text-muted-foreground italic">
              MERK: Dette er et grovt estimat basert på kommunestatistikk og offentlige data.
              For nøyaktig verdsetting anbefales faglig takst eller data fra Eiendomsverdi AS.
              {data.statistikk_aar && ` Statistikk fra ${data.statistikk_aar}.`}
            </p>
          </>
        ) : data.kommune_median_pris != null ? (
          <div className="rounded-xl bg-slate-50 border border-slate-200 p-4 dark:bg-slate-800 dark:border-slate-700">
            <p className="text-sm text-slate-800 dark:text-slate-200">
              Kommunemedian: {new Intl.NumberFormat('nb-NO').format(data.kommune_median_pris)} kr/m².
              Noyaktig estimat beregnes etter oppmaaling.
            </p>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            Utilstrekkelig data for å beregne verdiestimatet. Oppgi bruksareal for å få estimat.
          </p>
        )}
      </div>
    </Section>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

function PropertyPageInner() {
  const searchParams = useSearchParams();
  const [knr, setKnr] = React.useState(searchParams.get('knr') || '3212');
  const [gnr, setGnr] = React.useState(searchParams.get('gnr') || '');
  const [bnr, setBnr] = React.useState(searchParams.get('bnr') || '');
  const [fnr, setFnr] = React.useState(searchParams.get('fnr') || '');

  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<FullPropertyResult | null>(null);
  const [aiAnalysis, setAiAnalysis] = React.useState<PropertyAIAnalysis | null>(null);

  const { leggTil: leggTilSøk, søk: sisteSøk } = useSisteSøk();
  const { toggleFavoritt, erFavoritt } = useFavoritter();
  const [aiLoading, setAiLoading] = React.useState(false);
  const [aiError, setAiError] = React.useState<string | null>(null);
  const [aiUpsell, setAiUpsell] = React.useState(false);
  const [pdfUpsell, setPdfUpsell] = React.useState(false);
  const [kopiert, setKopiert] = React.useState(false);

  // Auto-search when arriving from a case link with params
  React.useEffect(() => {
    const pKnr = searchParams.get('knr');
    const pGnr = searchParams.get('gnr');
    const pBnr = searchParams.get('bnr');
    if (pKnr && pGnr && pBnr) {
      setKnr(pKnr);
      setGnr(pGnr);
      setBnr(pBnr);
      // Trigger search automatically
      setLoading(true);
      setError(null);
      setResult(null);
      getFullPropertyData(pKnr, pGnr, pBnr).then((res) => {
        setResult(res);
        leggTilSøk({ knr: pKnr, gnr: pGnr, bnr: pBnr, adresse: res.eiendom?.adresse ?? `${pGnr}/${pBnr}`, timestamp: Date.now() });
      }).catch((err) => {
        setError(err instanceof Error ? err.message : 'Ukjent feil');
      }).finally(() => setLoading(false));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!gnr || !bnr) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await getFullPropertyData(knr, gnr, bnr, fnr || undefined);
      setResult(data);
      leggTilSøk({ knr, gnr, bnr, adresse: data.eiendom?.adresse ?? `${gnr}/${bnr}`, timestamp: Date.now() });
      setAiAnalysis(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Ukjent feil ved eiendomsoppslag');
    } finally {
      setLoading(false);
    }
  };

  const handleAIAnalyse = async () => {
    if (!result) return;
    setAiLoading(true);
    setAiError(null);
    setAiUpsell(false);
    try {
      const analyse = await getPropertyAIAnalysis(knr, gnr, bnr);
      setAiAnalysis(analyse);
    } catch (err: unknown) {
      const e = err as Error & { status?: number };
      if (e.status === 401 || e.status === 402) {
        setAiUpsell(true);
      } else {
        setAiError(e.message || 'AI-analyse feilet');
      }
    } finally {
      setAiLoading(false);
    }
  };

  const handlePrint = () => window.print();

  const handleDelRapport = () => {
    const url = `${window.location.origin}/eiendom/${knr}/${gnr}/${bnr}`;
    navigator.clipboard.writeText(url).then(() => {
      setKopiert(true);
      setTimeout(() => setKopiert(false), 2000);
    });
  };

  const [innsynSendt, setInnsynSendt] = React.useState(false);
  const [innsynLaster, setInnsynLaster] = React.useState(false);

  const handleBeOmTegninger = async () => {
    setInnsynLaster(true);
    try {
      const params = new URLSearchParams({ knr, gnr, bnr });
      const token = typeof window !== 'undefined' ? localStorage.getItem('byggsjekk_token') : null;
      const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiBase}/api/v1/property/innsyn-tegninger?${params}`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        if (data.sendt) {
          setInnsynSendt(true);
        }
      }
    } catch {
      // Stille feil
    } finally {
      setInnsynLaster(false);
    }
  };

  const handleDownloadPdf = async () => {
    setPdfUpsell(false);
    const params = new URLSearchParams({ knr, gnr, bnr });
    if (fnr) params.set('fnr', fnr);
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const url = `${apiBase}/api/v1/property/rapport-pdf?${params}`;
    const token = typeof window !== 'undefined' ? localStorage.getItem('byggsjekk_token') : null;
    const res = await fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
    if (res.status === 402) {
      setPdfUpsell(true);
      return;
    }
    if (!res.ok) return;
    const blob = await res.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `ByggSjekk_${gnr}_${bnr}.pdf`;
    a.click();
  };

  return (
    <main className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <style>{`
  @media print {
    .no-print { display: none !important; }
    body { background: white !important; }
    .min-h-screen { min-height: auto !important; }
  }
`}</style>
      {/* Header */}
      <div className="no-print border-b border-slate-200 bg-white px-4 py-6 dark:border-slate-700 dark:bg-slate-900">
        <div className="mx-auto max-w-5xl">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600">
              <MapPin className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-white">
                Eiendomsoppslag
              </h1>
              <p className="text-sm text-muted-foreground">
                Matrikkel · Bygningsregister · Byggesaker · Arealplaner · DOK-analyse
              </p>
            </div>
          </div>

          {/* Address autocomplete */}
          <div className="mt-4 mb-2">
            <AddressAutocomplete
              placeholder="Søk adresse (f.eks. Storgata 1, Oslo)..."
              className="max-w-xl"
              onSelect={(s: AddressSuggestion) => {
                if (s.kommunenummer) setKnr(s.kommunenummer);
                if (s.gnr) setGnr(String(s.gnr));
                if (s.bnr) setBnr(String(s.bnr));
                if (s.fnr) setFnr(String(s.fnr));
              }}
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Søk på adresse for å fylle ut feltene automatisk, eller skriv inn gnr/bnr direkte
            </p>
          </div>

          {/* Siste søk */}
          {!result && sisteSøk.length > 0 && (
            <div className="mt-4">
              <p className="text-xs text-muted-foreground mb-2">Siste søk:</p>
              <div className="flex flex-wrap gap-2">
                {sisteSøk.slice(0, 6).map((s) => (
                  <button
                    key={`${s.knr}-${s.gnr}-${s.bnr}`}
                    onClick={() => { setKnr(s.knr); setGnr(s.gnr); setBnr(s.bnr); }}
                    className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                  >
                    <Clock className="h-3 w-3 text-slate-400" />
                    {s.adresse || `${s.gnr}/${s.bnr}`}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Search form */}
          <form onSubmit={handleSearch} className="mt-5">
            <div className="flex flex-wrap items-end gap-3">
              {/* Kommunenummer */}
              <div className="min-w-0">
                <label className="mb-1 block text-xs font-medium text-muted-foreground">
                  Kommunenummer
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={knr}
                    onChange={(e) => setKnr(e.target.value)}
                    placeholder="3212"
                    maxLength={4}
                    className="w-24 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {kommuneNavn(knr)}
                  </span>
                </div>
              </div>

              {/* GNR */}
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">
                  Gårdsnr.
                </label>
                <input
                  type="number"
                  value={gnr}
                  onChange={(e) => setGnr(e.target.value)}
                  placeholder="1"
                  min={1}
                  required
                  className="w-24 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
              </div>

              {/* BNR */}
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">
                  Bruksnr.
                </label>
                <input
                  type="number"
                  value={bnr}
                  onChange={(e) => setBnr(e.target.value)}
                  placeholder="1"
                  min={1}
                  required
                  className="w-24 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
              </div>

              {/* FNR */}
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">
                  Festenr.
                </label>
                <input
                  type="number"
                  value={fnr}
                  onChange={(e) => setFnr(e.target.value)}
                  placeholder="0"
                  min={0}
                  className="w-20 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
              </div>

              <Button type="submit" disabled={loading || !gnr || !bnr} className="h-9">
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Search className="h-4 w-4" />
                )}
                Søk
              </Button>
            </div>
          </form>
        </div>
      </div>

      <div className="mx-auto max-w-5xl px-4 py-6 space-y-5">
        {/* Error */}
        {error && (
          <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
            <XCircle className="h-4 w-4 mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-40 animate-pulse rounded-xl bg-slate-200 dark:bg-slate-800"
              />
            ))}
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <>
            {/* Eiendomsinfo header */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
                    <MapPin className="h-3.5 w-3.5" />
                    {result.kommune?.kommunenavn ?? kommuneNavn(result.kommunenummer)}
                    {' · '}{result.kommunenummer}/{result.gnr}/{result.bnr}
                    {result.fnr ? `/${result.fnr}` : ''}
                  </div>
                  {result.eiendom ? (
                    <>
                      <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                        {result.eiendom.adresse || `Gnr. ${result.gnr}, Bnr. ${result.bnr}`}
                      </h2>
                      {result.eiendom.postnummer && (
                        <p className="mt-0.5 text-muted-foreground">
                          {result.eiendom.postnummer} {result.eiendom.poststed}
                        </p>
                      )}
                    </>
                  ) : (
                    <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                      Gnr. {result.gnr}, Bnr. {result.bnr}
                    </h2>
                  )}
                </div>

                <div className="flex flex-wrap gap-2">
                  <a
                    href={result.se_eiendom_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
                  >
                    <ExternalLink className="h-3 w-3" />
                    Se Eiendom
                  </a>
                  {result.kommune?.innsyn_url && (
                    <a
                      href={result.kommune.innsyn_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
                    >
                      <ExternalLink className="h-3 w-3" />
                      Kommunalt innsyn
                    </a>
                  )}
                  <button
                    type="button"
                    onClick={handlePrint}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
                  >
                    <Printer className="h-3 w-3" />
                    Skriv ut
                  </button>
                  <button
                    type="button"
                    onClick={handleDelRapport}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors"
                  >
                    {kopiert ? <CheckCircle2 className="h-3 w-3 text-green-600" /> : <Share2 className="h-3 w-3" />}
                    {kopiert ? 'Kopiert!' : 'Del'}
                  </button>
                  <button
                    type="button"
                    onClick={() => toggleFavoritt({ knr, gnr, bnr, adresse: result.eiendom?.adresse ?? '', lagretDato: new Date().toISOString() })}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors"
                  >
                    {erFavoritt(knr, gnr, bnr) ? <Star className="h-3 w-3 fill-amber-400 text-amber-400" /> : <Star className="h-3 w-3" />}
                    {erFavoritt(knr, gnr, bnr) ? 'Lagret' : 'Lagre'}
                  </button>
                  <button
                    type="button"
                    onClick={handleBeOmTegninger}
                    disabled={innsynSendt || innsynLaster}
                    className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                      innsynSendt
                        ? 'border-green-200 bg-green-50 text-green-700'
                        : 'border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100'
                    }`}
                  >
                    {innsynSendt ? <CheckCircle2 className="h-3 w-3" /> : <FileText className="h-3 w-3" />}
                    {innsynSendt ? 'Tegninger forespurt!' : innsynLaster ? 'Sender...' : 'Be om tegninger'}
                  </button>
                  <button
                    type="button"
                    onClick={handleDownloadPdf}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
                  >
                    <Download className="h-3 w-3" />
                    PDF-rapport
                  </button>
                </div>
                {pdfUpsell && (
                  <p className="mt-2 text-xs text-amber-700 dark:text-amber-400">
                    PDF-rapport krever Starter-abonnement.{' '}
                    <a href="/pricing" className="underline font-medium">Oppgrader</a>
                  </p>
                )}
              </div>

              {/* Nøkkeltall */}
              {result.eiendom && (
                <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4 border-t pt-4 dark:border-slate-700">
                  {result.eiendom.areal_m2 != null && (
                    <div>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Ruler className="h-3 w-3" />
                        Tomteareal
                      </span>
                      <p className="mt-0.5 font-semibold">
                        {result.eiendom.areal_m2.toFixed(0)} m²
                      </p>
                    </div>
                  )}
                  <div>
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                      <Building2 className="h-3 w-3" />
                      Bygninger
                    </span>
                    <p className="mt-0.5 font-semibold">{result.bygninger.length}</p>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                      <Archive className="h-3 w-3" />
                      Byggesaker
                    </span>
                    <p className="mt-0.5 font-semibold">{result.byggesaker.length}</p>
                  </div>
                  {result.bygninger.length > 0 && result.bygninger[0].byggeaar && (
                    <div>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        Byggeår
                      </span>
                      <p className="mt-0.5 font-semibold">{result.bygninger[0].byggeaar}</p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Kart */}
            {result.eiendom?.koordinat_nord && result.eiendom?.koordinat_ost && (
              <PropertyMap
                lat={result.eiendom.koordinat_nord}
                lon={result.eiendom.koordinat_ost}
                address={result.eiendom.adresse}
                className="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700"
              />
            )}

            {/* AI Analyse */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
              <div className="flex items-center justify-between gap-4 flex-wrap">
                <div>
                  <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-purple-600" />
                    AI-analyse
                  </h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Analyser risiko, avvik og reguleringsplan med Anthropic Claude
                  </p>
                </div>
                {!aiAnalysis && (
                  <div className="no-print">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleAIAnalyse}
                    disabled={aiLoading}
                  >
                    {aiLoading ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Sparkles className="h-3.5 w-3.5 text-purple-600" />
                    )}
                    {aiLoading ? 'Analyserer…' : 'Kjør AI-analyse'}
                  </Button>
                  </div>
                )}
              </div>

              {aiError && (
                <div className="mt-3 text-xs text-red-600 dark:text-red-400">{aiError}</div>
              )}

              {aiUpsell && (
                <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 flex items-start gap-3 dark:border-amber-900 dark:bg-amber-950">
                  <ShieldAlert className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-amber-800 dark:text-amber-200">Starter-abonnement kreves</p>
                    <p className="text-xs text-amber-700 dark:text-amber-300 mt-0.5">
                      Logg inn og oppgrader til Starter (499 kr/mnd) for AI-analyse.{' '}
                      <a href="/register" className="underline font-medium">Registrer deg / logg inn</a>
                    </p>
                  </div>
                </div>
              )}

              {aiAnalysis && (
                <div className="mt-4 space-y-4">
                  {/* Risiko badge */}
                  <div className="flex items-center gap-3">
                    {aiAnalysis.risiko_nivaa === 'LAV' && (
                      <div className="flex items-center gap-2 rounded-lg bg-green-50 border border-green-200 px-3 py-2 dark:bg-green-950 dark:border-green-900">
                        <ShieldCheck className="h-5 w-5 text-green-600" />
                        <span className="font-semibold text-green-800 dark:text-green-300">Lav risiko</span>
                      </div>
                    )}
                    {aiAnalysis.risiko_nivaa === 'MIDDELS' && (
                      <div className="flex items-center gap-2 rounded-lg bg-yellow-50 border border-yellow-200 px-3 py-2 dark:bg-yellow-950 dark:border-yellow-900">
                        <ShieldQuestion className="h-5 w-5 text-yellow-600" />
                        <span className="font-semibold text-yellow-800 dark:text-yellow-300">Middels risiko</span>
                      </div>
                    )}
                    {(aiAnalysis.risiko_nivaa === 'HØY' || aiAnalysis.risiko_nivaa === 'KRITISK') && (
                      <div className="flex items-center gap-2 rounded-lg bg-red-50 border border-red-200 px-3 py-2 dark:bg-red-950 dark:border-red-900">
                        <ShieldAlert className="h-5 w-5 text-red-600" />
                        <span className="font-semibold text-red-800 dark:text-red-300">
                          {aiAnalysis.risiko_nivaa === 'KRITISK' ? 'Kritisk risiko' : 'Høy risiko'}
                        </span>
                      </div>
                    )}
                    <span className="text-xs text-muted-foreground">
                      Score: {(aiAnalysis.risiko_score * 100).toFixed(0)}%
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="ml-auto text-xs"
                      onClick={handleAIAnalyse}
                    >
                      Oppdater
                    </Button>
                  </div>

                  {/* Sammendrag */}
                  <p className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed">
                    {aiAnalysis.sammendrag}
                  </p>

                  {/* Nøkkelfinninger */}
                  {aiAnalysis.nøkkelfinninger.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                        Nøkkelfinninger
                      </p>
                      <ul className="space-y-1">
                        {aiAnalysis.nøkkelfinninger.map((f, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm">
                            <AlertTriangle className="h-3.5 w-3.5 mt-0.5 shrink-0 text-yellow-500" />
                            {f}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Anbefalinger */}
                  {aiAnalysis.anbefalinger.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                        Anbefalinger
                      </p>
                      <ul className="space-y-1">
                        {aiAnalysis.anbefalinger.map((a, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm">
                            <CheckCircle2 className="h-3.5 w-3.5 mt-0.5 shrink-0 text-green-500" />
                            {a}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Detaljer */}
                  {(aiAnalysis.reguleringsplan_vurdering || aiAnalysis.avviksvurdering) && (
                    <div className="grid gap-3 sm:grid-cols-2 pt-2">
                      {aiAnalysis.reguleringsplan_vurdering && (
                        <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-800">
                          <p className="text-xs font-semibold text-muted-foreground mb-1">Reguleringsplan</p>
                          <p className="text-xs text-slate-700 dark:text-slate-300">
                            {aiAnalysis.reguleringsplan_vurdering}
                          </p>
                        </div>
                      )}
                      {aiAnalysis.avviksvurdering && (
                        <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-800">
                          <p className="text-xs font-semibold text-muted-foreground mb-1">Avviksvurdering</p>
                          <p className="text-xs text-slate-700 dark:text-slate-300">
                            {aiAnalysis.avviksvurdering}
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Fraskrivelse */}
                  <p className="text-xs text-muted-foreground italic border-t pt-3 dark:border-slate-700">
                    {aiAnalysis.fraskrivelse}
                  </p>
                </div>
              )}
            </div>

            {/* Verdiestimator */}
            {result.verdiestimator && (
              <VerdiestimatorSection data={result.verdiestimator} />
            )}

            {/* Bygninger */}
            {result.bygninger.length > 0 && (
              <Section
                title="Bygninger"
                icon={<Home className="h-4 w-4 text-blue-600" />}
                count={result.bygninger.length}
              >
                <div className="grid gap-3 sm:grid-cols-2">
                  {result.bygninger.map((b) => (
                    <BygningCard key={b.bygningsnummer} bygning={b} />
                  ))}
                </div>
              </Section>
            )}

            {/* Byggesaker */}
            <Section
              title="Byggesaker"
              icon={<Archive className="h-4 w-4 text-orange-600" />}
              count={result.byggesaker.length}
            >
              {result.byggesaker.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Ingen byggesaker funnet via offentlige registre. Sjekk kommunens innsynsportal for komplett historikk.
                </p>
              ) : (
                <div>
                  {result.byggesaker.map((s, i) => (
                    <ByggesakRow key={s.saksnummer || i} sak={s} />
                  ))}
                </div>
              )}
              {result.kommune?.innsyn_url && (
                <div className="mt-3 pt-3 border-t dark:border-slate-700">
                  <a
                    href={result.kommune.innsyn_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs text-blue-600 hover:underline dark:text-blue-400"
                  >
                    <ExternalLink className="h-3 w-3" />
                    Se alle byggesaker i kommunens arkiv
                  </a>
                </div>
              )}
            </Section>

            {/* Gjeldende arealplaner */}
            {result.planrapport && (
              <Section
                title="Gjeldende arealplaner (reguleringsplan)"
                icon={<FileText className="h-4 w-4 text-green-600" />}
                count={result.planrapport.gjeldende_planer.length}
              >
                {(result.planrapport as Record<string, unknown>).feilmelding && (
                  <div className="mb-4 rounded-lg border border-yellow-300 bg-yellow-50 px-4 py-3 dark:border-yellow-800 dark:bg-yellow-950">
                    <p className="text-sm text-yellow-800 dark:text-yellow-200">
                      <strong>Merk:</strong> Plandata er forelopig basert pa standardsok. Kontakt oss for full planrapport.
                    </p>
                  </div>
                )}
                {result.planrapport.gjeldende_planer.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Ingen gjeldende arealplaner funnet.</p>
                ) : (
                  <div className="space-y-3">
                    {result.planrapport.gjeldende_planer.map((plan) => (
                      <div
                        key={plan.plan_id}
                        className="flex flex-wrap items-start justify-between gap-3 rounded-lg border border-slate-200 p-3 dark:border-slate-700"
                      >
                        <div>
                          <p className="font-medium text-slate-900 dark:text-white text-sm">
                            {plan.plan_navn}
                          </p>
                          <div className="mt-1 flex flex-wrap items-center gap-2">
                            {planStatusBadge(plan.status)}
                            <span className="text-xs text-muted-foreground">{plan.plan_type}</span>
                            {plan.vedtaksdato && (
                              <span className="text-xs text-muted-foreground">
                                Vedtatt: {formatDato(plan.vedtaksdato)}
                              </span>
                            )}
                          </div>
                          {plan.arealformål && (
                            <p className="mt-1 text-xs text-muted-foreground">
                              Arealformål: {plan.arealformål}
                            </p>
                          )}
                        </div>
                        {plan.url && (
                          <a
                            href={plan.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-600 hover:bg-slate-50 transition-colors dark:border-slate-700 dark:text-slate-400 shrink-0"
                          >
                            <ExternalLink className="h-3 w-3" />
                            Plan
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                {result.planrapport.planrapport_url && (
                  <div className="mt-3 pt-3 border-t dark:border-slate-700">
                    <a
                      href={result.planrapport.planrapport_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs text-blue-600 hover:underline dark:text-blue-400"
                    >
                      <ExternalLink className="h-3 w-3" />
                      Åpne full planrapport
                    </a>
                  </div>
                )}
              </Section>
            )}

            {/* Planbestemmelser (Planslurpen) */}
            {result.planslurpen && (result.planslurpen.antall_planer > 0 || result.planslurpen.feilmelding) && (
              <Section
                title="Planbestemmelser (AI-strukturert)"
                icon={<Scale className="h-4 w-4 text-violet-600" />}
                count={result.planslurpen.antall_planer > 0 ? result.planslurpen.antall_planer : undefined}
                defaultOpen={result.planslurpen.antall_planer > 0}
              >
                {result.planslurpen.feilmelding && result.planslurpen.antall_planer === 0 ? (
                  <p className="text-sm text-muted-foreground">{result.planslurpen.feilmelding}</p>
                ) : (
                  <div className="space-y-4">
                    {result.planslurpen.planer.map((plan) => (
                      <div key={plan.plan_id} className="space-y-3">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="font-medium text-slate-900 dark:text-white text-sm">{plan.plan_navn || plan.plan_id}</p>
                            {plan.plantype && <p className="text-xs text-muted-foreground">{plan.plantype}</p>}
                          </div>
                          {plan.droemmeplan_url && (
                            <a href={plan.droemmeplan_url} target="_blank" rel="noopener noreferrer"
                              className="shrink-0 inline-flex items-center gap-1 text-xs text-violet-600 hover:underline">
                              <ExternalLink className="h-3 w-3" />
                              Drømmeplan
                            </a>
                          )}
                        </div>

                        {/* Nøkkelverdier */}
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                          {plan.maks_hoyde && (
                            <div className="rounded-lg bg-violet-50 border border-violet-200 px-3 py-2 dark:bg-violet-950 dark:border-violet-900">
                              <p className="text-xs text-violet-600 dark:text-violet-400">Maks høyde</p>
                              <p className="font-semibold text-violet-900 dark:text-violet-100">{plan.maks_hoyde}</p>
                            </div>
                          )}
                          {plan.maks_utnyttelse && (
                            <div className="rounded-lg bg-violet-50 border border-violet-200 px-3 py-2 dark:bg-violet-950 dark:border-violet-900">
                              <p className="text-xs text-violet-600 dark:text-violet-400">Utnyttelse</p>
                              <p className="font-semibold text-violet-900 dark:text-violet-100">{plan.maks_utnyttelse}</p>
                            </div>
                          )}
                          {plan.tillatt_bruk.length > 0 && (
                            <div className="rounded-lg bg-violet-50 border border-violet-200 px-3 py-2 dark:bg-violet-950 dark:border-violet-900">
                              <p className="text-xs text-violet-600 dark:text-violet-400">Tillatt bruk</p>
                              <p className="font-semibold text-violet-900 dark:text-violet-100 text-xs">{plan.tillatt_bruk[0]}</p>
                            </div>
                          )}
                        </div>

                        {/* Bestemmelser liste */}
                        {plan.bestemmelser.length > 0 && (
                          <details className="group">
                            <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground list-none flex items-center gap-1">
                              <ChevronDown className="h-3 w-3 group-open:rotate-180 transition-transform" />
                              {plan.antall_bestemmelser} bestemmelser fra Planslurpen
                            </summary>
                            <div className="mt-2 space-y-1.5 pl-2 border-l-2 border-violet-200 dark:border-violet-800">
                              {plan.bestemmelser.filter(b => b.tittel || b.tekst).map((b, i) => (
                                <div key={i} className="text-xs">
                                  <p className="font-medium text-slate-800 dark:text-slate-200">{b.tittel || b.kode}</p>
                                  {b.verdi && <span className="text-violet-700 dark:text-violet-300 font-semibold">{b.verdi} · </span>}
                                  <span className="text-muted-foreground">{b.tekst?.slice(0, 200)}{(b.tekst?.length ?? 0) > 200 ? '…' : ''}</span>
                                </div>
                              ))}
                            </div>
                          </details>
                        )}
                      </div>
                    ))}
                    <p className="text-xs text-muted-foreground italic">
                      Kilde: Planslurpen (DiBK) – AI-strukturerte planbestemmelser. Beta-tjeneste.
                    </p>
                  </div>
                )}
              </Section>
            )}

            {/* Dispensasjoner */}
            {result.planrapport && result.planrapport.dispensasjoner.length > 0 && (
              <Section
                title="Dispensasjoner"
                icon={<AlertTriangle className="h-4 w-4 text-yellow-600" />}
                count={result.planrapport.dispensasjoner.length}
                defaultOpen={false}
              >
                <div className="space-y-3">
                  {result.planrapport.dispensasjoner.map((d, i) => (
                    <div
                      key={d.saks_id || i}
                      className="rounded-lg border border-slate-200 p-3 dark:border-slate-700"
                    >
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        {dispStatusBadge(d.status)}
                        <span className="text-xs text-muted-foreground">{d.saks_id}</span>
                        {d.vedtaksdato && (
                          <span className="text-xs text-muted-foreground">
                            {formatDato(d.vedtaksdato)}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-slate-900 dark:text-white">
                        {d.beskrivelse || d.saks_type}
                      </p>
                      {d.paragraf && (
                        <p className="text-xs text-muted-foreground mt-0.5">{d.paragraf}</p>
                      )}
                    </div>
                  ))}
                </div>
              </Section>
            )}

            {/* DOK-analyse */}
            {result.dok_analyse ? (
              <Section
                title="DOK-analyse (Det offentlige kartgrunnlaget)"
                icon={<Info className="h-4 w-4 text-purple-600" />}
                count={result.dok_analyse.antall_berørt}
                defaultOpen={true}
              >
                <div className="mb-3 flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-1.5 text-red-600 dark:text-red-400">
                    <XCircle className="h-4 w-4" />
                    <span className="font-medium">{result.dok_analyse.antall_berørt}</span>
                    <span className="text-muted-foreground">berørt</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-green-600 dark:text-green-400">
                    <CheckCircle2 className="h-4 w-4" />
                    <span className="font-medium">{result.dok_analyse.antall_ikke_berørt}</span>
                    <span className="text-muted-foreground">ikke berørt</span>
                  </div>
                </div>

                {result.dok_analyse.berørte_datasett.length > 0 && (
                  <div className="space-y-1.5">
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                      Berørte datasett
                    </p>
                    {result.dok_analyse.berørte_datasett.map((d) => (
                      <div
                        key={d.uuid}
                        className="flex items-center justify-between gap-2 rounded-md border border-red-100 bg-red-50 px-3 py-2 dark:border-red-900 dark:bg-red-950"
                      >
                        <div>
                          <p className="text-sm font-medium text-red-900 dark:text-red-200">
                            {d.navn}
                          </p>
                          {d.tema && (
                            <p className="text-xs text-red-700 dark:text-red-400">{d.tema}</p>
                          )}
                        </div>
                        {d.url && (
                          <a
                            href={d.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="shrink-0 text-xs text-red-600 hover:underline"
                          >
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {result.dok_analyse.rapport_url && (
                  <div className="mt-3 pt-3 border-t dark:border-slate-700">
                    <a
                      href={result.dok_analyse.rapport_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs text-blue-600 hover:underline dark:text-blue-400"
                    >
                      <ExternalLink className="h-3 w-3" />
                      Last ned DOK-analyserapport (PDF)
                    </a>
                  </div>
                )}
              </Section>
            ) : (
              <Section
                title="DOK-analyse (Det offentlige kartgrunnlaget)"
                icon={<Info className="h-4 w-4 text-purple-600" />}
                defaultOpen={true}
              >
                <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-900 dark:bg-amber-950">
                  <p className="text-sm text-amber-800 dark:text-amber-200">
                    DOK-analyse krever API-tilgang. Kontakt{' '}
                    <a href="mailto:hey@nops.no" className="underline font-medium">hey@nops.no</a>{' '}
                    for aktivering.
                  </p>
                </div>
              </Section>
            )}

            {/* Byggesøknad-sjekkliste */}
            <SjekklisteWidget knr={knr} gnr={gnr} bnr={bnr} />

            {/* Gebyrberegning */}
            <GebyrKalkulator knr={knr} gnr={gnr} bnr={bnr} />

            {/* ── Relaterte tjenester ─────────────────────────────────── */}
            <RelaterteTjenester
              adresse={result.eiendom?.adresse ?? ''}
              gnr={result.gnr}
              bnr={result.bnr}
              knr={result.kommunenummer}
              harDispensasjon={
                (result.planrapport?.dispensasjoner?.length ?? 0) > 0 ||
                (aiAnalysis?.dispensasjonsgrunnlag?.length ?? 0) > 20
              }
              manglerFerdigattest={result.byggesaker?.some(
                (s) =>
                  s.status?.toLowerCase().includes('igangsatt') ||
                  s.status?.toLowerCase().includes('under arbeid')
              ) ?? false}
            />

            {/* Feilmeldinger */}
            {((result.feilmeldinger?.length ?? 0) > 0 || (result.kartverket_feilmeldinger?.length ?? 0) > 0) && (
              <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-900 dark:bg-yellow-950">
                <p className="text-xs font-medium text-yellow-800 dark:text-yellow-300 mb-2">
                  Noen datakilder returnerte feil:
                </p>
                <ul className="list-disc list-inside space-y-1">
                  {[...(result.feilmeldinger || []), ...(result.kartverket_feilmeldinger || [])].map(
                    (f, i) => (
                      <li key={i} className="text-xs text-yellow-700 dark:text-yellow-400">
                        {f}
                      </li>
                    )
                  )}
                </ul>
              </div>
            )}
          </>
        )}

        {/* Empty state */}
        {!result && !loading && !error && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-50 dark:bg-blue-950 mb-4">
              <MapPin className="h-8 w-8 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
              Søk opp en eiendom
            </h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              Skriv inn kommunenummer, gårdsnummer og bruksnummer for å hente
              eiendomsdata, bygningsinfo, byggesaker og arealplaner fra alle offentlige registre.
            </p>
            <p className="mt-3 text-xs text-muted-foreground">
              Eksempel Nesodden: kommunenr 3212 · gnr 1 · bnr 100
            </p>
          </div>
        )}
      </div>
    </main>
  );
}

export default function PropertyPage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </main>
    }>
      <PropertyPageInner />
    </Suspense>
  );
}
