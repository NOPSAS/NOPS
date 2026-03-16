'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  FileText,
  Search,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Loader2,
  Upload,
  Building2,
  MapPin,
  Sparkles,
  ExternalLink,
  Info,
  FileSearch,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface DokumentStatus {
  status: string;
  kommentar: string;
}

interface ComplianceGap {
  dokument: string;
  alvorlighet: string;
  konsekvens: string;
  handling: string;
}

interface Tegning {
  tittel: string;
  type: string;
  url: string | null;
  saksnummer: string | null;
  vedtaksdato: string | null;
  status: string | null;
}

const STATUS_FARGE: Record<string, string> = {
  'Godkjent': 'text-green-700 bg-green-50 border-green-200',
  'Gjeldende': 'text-green-700 bg-green-50 border-green-200',
  'Tilgjengelig': 'text-green-700 bg-green-50 border-green-200',
  'Mangler': 'text-red-700 bg-red-50 border-red-200',
  'Ukjent': 'text-amber-700 bg-amber-50 border-amber-200',
  'Anbefalt': 'text-blue-700 bg-blue-50 border-blue-200',
  'Ikke funnet': 'text-slate-600 bg-slate-50 border-slate-200',
  'Utgått': 'text-red-700 bg-red-50 border-red-200',
};

function StatusBadge({ status }: { status: string }) {
  const farge = Object.entries(STATUS_FARGE).find(([k]) =>
    status.toLowerCase().includes(k.toLowerCase())
  )?.[1] || 'text-slate-600 bg-slate-50 border-slate-200';

  return (
    <span className={cn('inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium', farge)}>
      {status.includes('Godkjent') || status.includes('Gjeldende') || status.includes('Tilgjengelig') ? (
        <CheckCircle2 className="h-3 w-3" />
      ) : status.includes('Mangler') ? (
        <XCircle className="h-3 w-3" />
      ) : (
        <Info className="h-3 w-3" />
      )}
      {status}
    </span>
  );
}

export default function DokumenterPage() {
  const [knr, setKnr] = React.useState('');
  const [gnr, setGnr] = React.useState('');
  const [bnr, setBnr] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [tegningerLoading, setTegningerLoading] = React.useState(false);
  const [analyse, setAnalyse] = React.useState<Record<string, unknown> | null>(null);
  const [tegninger, setTegninger] = React.useState<Record<string, unknown> | null>(null);
  const [feil, setFeil] = React.useState<string | null>(null);

  // Salgsoppgave-upload
  const [salgsoppgaveFil, setSalgsoppgaveFil] = React.useState<File | null>(null);
  const [salgsoppgaveLoading, setSalgsoppgaveLoading] = React.useState(false);
  const [salgsoppgaveResultat, setSalgsoppgaveResultat] = React.useState<Record<string, unknown> | null>(null);
  const fileRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    document.title = 'Dokumentanalyse og Godkjente Tegninger | nops.no';
  }, []);

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') || '' : '';

  async function hentTegninger() {
    if (!knr || !gnr || !bnr) { setFeil('Fyll inn alle feltene'); return; }
    setTegningerLoading(true);
    setFeil(null);
    try {
      const res = await fetch(`/api/v1/dokumentanalyse/tegninger?knr=${knr}&gnr=${gnr}&bnr=${bnr}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setTegninger(await res.json());
    } catch (e: unknown) {
      setFeil(e instanceof Error ? e.message : 'Feil');
    } finally {
      setTegningerLoading(false);
    }
  }

  async function kjørDokumentanalyse() {
    if (!knr || !gnr || !bnr) { setFeil('Fyll inn alle feltene'); return; }
    setLoading(true);
    setFeil(null);
    try {
      const res = await fetch(`/api/v1/dokumentanalyse/eiendom?knr=${knr}&gnr=${gnr}&bnr=${bnr}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 402) {
        setFeil('Dokumentanalyse krever Starter-plan eller høyere.');
        return;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setAnalyse(await res.json());
    } catch (e: unknown) {
      setFeil(e instanceof Error ? e.message : 'Feil');
    } finally {
      setLoading(false);
    }
  }

  async function analyserSalgsoppgave() {
    if (!salgsoppgaveFil) return;
    setSalgsoppgaveLoading(true);
    try {
      const form = new FormData();
      form.append('fil', salgsoppgaveFil);
      if (knr) form.append('knr', knr);
      if (gnr) form.append('gnr', gnr);
      if (bnr) form.append('bnr', bnr);
      const res = await fetch('/api/v1/dokumentanalyse/salgsoppgave', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setSalgsoppgaveResultat(await res.json());
    } catch (e: unknown) {
      setFeil(e instanceof Error ? e.message : 'Feil');
    } finally {
      setSalgsoppgaveLoading(false);
    }
  }

  const dokumentstatus = (analyse as Record<string, unknown>)?.dokumentstatus as Record<string, DokumentStatus> | undefined;
  const complianceGap = (analyse as Record<string, unknown>)?.compliance_gap as ComplianceGap[] | undefined;
  const risikoVurdering = (analyse as Record<string, unknown>)?.risiko_vurdering as Record<string, unknown> | undefined;
  const anbefalinger = (analyse as Record<string, unknown>)?.anbefalinger as Record<string, string[]> | undefined;
  const tegningerListe = (tegninger as Record<string, unknown>)?.tegninger as Tegning[] | undefined;
  const mangler = (tegninger as Record<string, unknown>)?.tegningstyper_mangler as string[] | undefined;

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <section className="bg-gradient-to-br from-cyan-600 to-blue-700 text-white py-16 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="inline-flex items-center gap-2 mb-4 rounded-full bg-white/10 px-4 py-1.5 text-sm font-medium text-cyan-100">
            <FileSearch className="h-4 w-4" />
            nops.no / Dokumentanalyse
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mb-4">
            Godkjente tegninger og dokumentanalyse
          </h1>
          <p className="text-lg text-cyan-100 max-w-2xl mb-6">
            Hent godkjente byggetegninger gratis – og kjør AI-analyse av dokumentasjonsstatus,
            compliance-gap og risiko. Erstatter Norkart og Ambita.
          </p>
          <div className="flex flex-wrap gap-3">
            <div className="inline-flex items-center gap-1.5 rounded-full bg-green-500/20 border border-green-400/30 px-3 py-1 text-xs font-semibold text-green-100">
              <CheckCircle2 className="h-3.5 w-3.5" /> Gratis tegningshenting
            </div>
            <div className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs text-cyan-100">
              <Sparkles className="h-3.5 w-3.5" /> AI-risikovurdering
            </div>
            <div className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs text-cyan-100">
              <Upload className="h-3.5 w-3.5" /> Salgsoppgave-analyse
            </div>
          </div>
        </div>
      </section>

      <div className="max-w-5xl mx-auto px-4 py-10 space-y-8">
        {/* Søkeskjema */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
            <MapPin className="h-5 w-5 text-blue-600" />
            Søk opp eiendom
          </h2>
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Kommunenr.</label>
              <input type="text" placeholder="3212" value={knr} onChange={(e) => setKnr(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Gnr.</label>
              <input type="number" placeholder="1" value={gnr} onChange={(e) => setGnr(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Bnr.</label>
              <input type="number" placeholder="1" value={bnr} onChange={(e) => setBnr(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>

          {feil && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 mb-4">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {feil}
            </div>
          )}

          <div className="flex flex-wrap gap-3">
            <button type="button" onClick={hentTegninger} disabled={tegningerLoading}
              className="inline-flex items-center gap-2 rounded-xl bg-cyan-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-cyan-700 disabled:opacity-60 transition-colors">
              {tegningerLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
              Hent godkjente tegninger (gratis)
            </button>
            <button type="button" onClick={kjørDokumentanalyse} disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60 transition-colors">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              Kjør AI-dokumentanalyse
            </button>
          </div>
        </div>

        {/* Godkjente tegninger */}
        {tegninger && (
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
              <FileText className="h-5 w-5 text-cyan-600" />
              Godkjente tegninger
              <span className="ml-auto text-xs font-normal text-green-600 bg-green-50 border border-green-200 rounded-full px-2.5 py-0.5">
                Gratis via NOPS
              </span>
            </h2>

            {(tegningerListe?.length ?? 0) > 0 ? (
              <div className="space-y-2 mb-4">
                {tegningerListe?.map((t, i) => (
                  <div key={i} className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <FileText className="h-4 w-4 text-slate-400 shrink-0" />
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-slate-900 truncate">{t.tittel || 'Ukjent dokument'}</p>
                        <p className="text-xs text-slate-500">
                          {t.type} {t.vedtaksdato && `· ${t.vedtaksdato}`} {t.saksnummer && `· Sak ${t.saksnummer}`}
                        </p>
                      </div>
                    </div>
                    {t.url && (
                      <a href={t.url} target="_blank" rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:underline shrink-0">
                        Åpne <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500 mb-4">Ingen tegninger funnet i digitalt arkiv for denne eiendommen.</p>
            )}

            {(mangler?.length ?? 0) > 0 && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
                <p className="text-xs font-semibold text-amber-800 mb-1">Manglende tegningstyper:</p>
                <div className="flex flex-wrap gap-1.5">
                  {mangler?.map((m) => (
                    <span key={m} className="rounded-full bg-amber-100 border border-amber-200 px-2 py-0.5 text-xs text-amber-700">
                      {m}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* AI Dokumentanalyse */}
        {analyse && (
          <>
            {/* Risiko */}
            {risikoVurdering && (
              <div className={cn(
                'rounded-2xl border p-6 shadow-sm',
                (risikoVurdering.nivaa as string) === 'LAV' ? 'border-green-200 bg-green-50' :
                (risikoVurdering.nivaa as string) === 'MIDDELS' ? 'border-amber-200 bg-amber-50' :
                'border-red-200 bg-red-50'
              )}>
                <div className="flex items-center gap-3 mb-3">
                  <ShieldCheck className="h-6 w-6" />
                  <h2 className="text-lg font-bold">Risikovurdering: {risikoVurdering.nivaa as string}</h2>
                </div>
                <p className="text-sm leading-relaxed">{risikoVurdering.sammendrag as string}</p>
                {(risikoVurdering.hovedrisiko as string[])?.length > 0 && (
                  <ul className="mt-3 space-y-1">
                    {(risikoVurdering.hovedrisiko as string[]).map((r, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" /> {r}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {/* Dokumentstatus */}
            {dokumentstatus && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-lg font-bold text-slate-900 mb-4">Dokumentstatus</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {Object.entries(dokumentstatus).map(([key, val]) => (
                    <div key={key} className="flex items-start justify-between rounded-lg border border-slate-200 bg-slate-50 p-3">
                      <div>
                        <p className="text-sm font-medium text-slate-900 capitalize">{key.replace(/_/g, ' ')}</p>
                        <p className="text-xs text-slate-500 mt-0.5">{val.kommentar}</p>
                      </div>
                      <StatusBadge status={val.status} />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Compliance gap */}
            {complianceGap && complianceGap.length > 0 && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-lg font-bold text-slate-900 mb-4">Compliance gap-analyse</h2>
                <div className="space-y-3">
                  {complianceGap.map((gap, i) => (
                    <div key={i} className={cn(
                      'rounded-lg border p-4',
                      gap.alvorlighet === 'Kritisk' ? 'border-red-200 bg-red-50' :
                      gap.alvorlighet === 'Viktig' ? 'border-amber-200 bg-amber-50' :
                      'border-blue-200 bg-blue-50'
                    )}>
                      <div className="flex items-center gap-2 mb-1">
                        <span className={cn(
                          'rounded-full px-2 py-0.5 text-xs font-semibold',
                          gap.alvorlighet === 'Kritisk' ? 'bg-red-100 text-red-700' :
                          gap.alvorlighet === 'Viktig' ? 'bg-amber-100 text-amber-700' :
                          'bg-blue-100 text-blue-700'
                        )}>{gap.alvorlighet}</span>
                        <span className="text-sm font-semibold text-slate-900">{gap.dokument}</span>
                      </div>
                      <p className="text-xs text-slate-600">{gap.konsekvens}</p>
                      <p className="text-xs text-slate-700 font-medium mt-1">{gap.handling}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Anbefalinger */}
            {anbefalinger && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-lg font-bold text-slate-900 mb-4">Anbefalinger</h2>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {Object.entries(anbefalinger).map(([rolle, tips]) => (
                    <div key={rolle}>
                      <h3 className="text-sm font-semibold text-slate-700 capitalize mb-2">For {rolle}</h3>
                      <ul className="space-y-1.5">
                        {tips.map((t, i) => (
                          <li key={i} className="flex items-start gap-2 text-xs text-slate-600">
                            <CheckCircle2 className="h-3.5 w-3.5 text-green-500 mt-0.5 shrink-0" /> {t}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* Salgsoppgave-analyse */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900 mb-2 flex items-center gap-2">
            <Upload className="h-5 w-5 text-purple-600" />
            Salgsoppgave-analyse
          </h2>
          <p className="text-sm text-slate-500 mb-4">
            Last opp en salgsoppgave-PDF og få øyeblikkelig AI-analyse med risikopunkter og anbefalinger.
          </p>
          <div className="flex items-center gap-3 mb-4">
            <button type="button" onClick={() => fileRef.current?.click()}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors">
              <Upload className="h-4 w-4" />
              {salgsoppgaveFil ? salgsoppgaveFil.name : 'Velg PDF-fil'}
            </button>
            <input ref={fileRef} type="file" accept=".pdf,image/*" className="hidden"
              onChange={(e) => setSalgsoppgaveFil(e.target.files?.[0] ?? null)} />
            {salgsoppgaveFil && (
              <button type="button" onClick={analyserSalgsoppgave} disabled={salgsoppgaveLoading}
                className="inline-flex items-center gap-2 rounded-lg bg-purple-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-purple-700 disabled:opacity-60 transition-colors">
                {salgsoppgaveLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                Analyser
              </button>
            )}
          </div>

          {salgsoppgaveResultat && (
            <div className="rounded-lg border border-purple-200 bg-purple-50 p-4">
              <p className="text-sm font-semibold text-purple-900 mb-2">Analyse fullført</p>
              <pre className="text-xs text-purple-800 whitespace-pre-wrap overflow-auto max-h-96">
                {JSON.stringify((salgsoppgaveResultat as Record<string, unknown>).analyse, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="rounded-xl border border-blue-100 bg-blue-50 p-5 flex items-start gap-3">
          <Info className="h-5 w-5 text-blue-600 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-blue-900 mb-1">Gratis tegningshenting via NOPS</p>
            <p className="text-xs text-blue-700 leading-relaxed">
              Norkart og Ambita tar betalt for å innhente sist godkjente tegninger. NOPS tilbyr dette gratis
              for alle brukere via direkte oppkobling mot kommunale eByggesak-arkiver og Kartverket.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
