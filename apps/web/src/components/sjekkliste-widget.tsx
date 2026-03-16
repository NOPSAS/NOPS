'use client';

import * as React from 'react';
import {
  ChevronDown,
  ChevronUp,
  Loader2,
  AlertTriangle,
  CheckSquare,
  Square,
  FileText,
  HardHat,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { fetchJSON } from '@/lib/utils';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Dokument {
  navn: string;
  beskrivelse: string;
  mal_url: string | null;
}

interface SjekklistePunkt {
  punkt: string;
  status: string;
  paragraf: string;
}

interface SjekklisteResult {
  soknadstype: string;
  soknadstype_begrunnelse: string;
  dokumenter: Dokument[];
  sjekkliste: SjekklistePunkt[];
  advarsler: string[];
  eiendom: {
    knr: string;
    gnr: number | string;
    bnr: number | string;
    adresse: string;
    kommunenavn: string;
  };
}

type Tiltakstype =
  | 'tilbygg'
  | 'garasje'
  | 'bruksendring'
  | 'riving'
  | 'nybygg'
  | 'terrasse'
  | 'carport';

interface SjekklisteWidgetProps {
  knr: string;
  gnr: string;
  bnr: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function soknadsTypeBadge(soknadstype: string) {
  const lower = soknadstype.toLowerCase();
  if (lower.includes('ikke')) {
    return (
      <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300">
        Ikke søknadspliktig
      </span>
    );
  }
  if (lower.includes('melding')) {
    return (
      <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-300">
        Meldingspliktig
      </span>
    );
  }
  return (
    <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300">
      Søknadspliktig
    </span>
  );
}

// ─── Component ────────────────────────────────────────────────────────────────

export function SjekklisteWidget({ knr, gnr, bnr }: SjekklisteWidgetProps) {
  const [expanded, setExpanded] = React.useState(false);
  const [tiltakstype, setTiltakstype] = React.useState<Tiltakstype>('tilbygg');
  const [arealM2, setArealM2] = React.useState<string>('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [upsell, setUpsell] = React.useState(false);
  const [result, setResult] = React.useState<SjekklisteResult | null>(null);

  async function handleGenerer() {
    setLoading(true);
    setError(null);
    setUpsell(false);
    setResult(null);

    const params = new URLSearchParams({ knr, gnr, bnr, tiltakstype });
    const parsedAreal = parseInt(arealM2, 10);
    if (!isNaN(parsedAreal) && parsedAreal > 0) {
      params.set('areal_m2', String(parsedAreal));
    }

    try {
      const data = await fetchJSON<SjekklisteResult>(
        `/api/v1/property/sjekkliste?${params.toString()}`,
        { method: 'POST' }
      );
      setResult(data);
    } catch (err: unknown) {
      const e = err as { status?: number; message?: string };
      if (e.status === 401 || e.status === 402) {
        setUpsell(true);
      } else {
        setError(e.message || 'Sjekkliste-generering feilet.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900 overflow-hidden">
      {/* Header / toggle */}
      <button
        className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-2">
          <HardHat className="h-4 w-4 text-orange-600 shrink-0" />
          <div>
            <p className="font-semibold text-slate-900 dark:text-white text-sm">
              Planlegger du å bygge?
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Generer en byggesøknad-sjekkliste basert på reguleringsplanen
            </p>
          </div>
        </div>
        {expanded ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground shrink-0" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
        )}
      </button>

      {/* Collapsible content */}
      {expanded && (
        <div className="border-t border-slate-200 dark:border-slate-700 px-5 py-5 space-y-5">
          {!result ? (
            <>
              <div className="grid gap-4 sm:grid-cols-2">
                {/* Tiltakstype */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    Tiltakstype
                  </label>
                  <div className="relative">
                    <select
                      value={tiltakstype}
                      onChange={(e) => setTiltakstype(e.target.value as Tiltakstype)}
                      className="w-full appearance-none rounded-lg border border-slate-200 bg-white px-3 py-2.5 pr-8 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-orange-500 dark:border-slate-600 dark:bg-slate-800 dark:text-white"
                    >
                      <option value="tilbygg">Tilbygg</option>
                      <option value="garasje">Garasje</option>
                      <option value="bruksendring">Bruksendring</option>
                      <option value="riving">Riving</option>
                      <option value="nybygg">Nybygg</option>
                      <option value="terrasse">Terrasse</option>
                      <option value="carport">Carport</option>
                    </select>
                    <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  </div>
                </div>

                {/* Areal */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    Areal (m²) – valgfritt
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={9999}
                    value={arealM2}
                    onChange={(e) => setArealM2(e.target.value)}
                    placeholder="F.eks. 25"
                    className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-orange-500 dark:border-slate-600 dark:bg-slate-800 dark:text-white"
                  />
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-400">
                  {error}
                </div>
              )}

              {/* Upsell */}
              {upsell && (
                <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 flex items-start gap-3 dark:border-amber-900 dark:bg-amber-950">
                  <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                      Starter-abonnement kreves
                    </p>
                    <p className="text-xs text-amber-700 dark:text-amber-300 mt-0.5">
                      Logg inn og oppgrader til Starter (499 kr/mnd) for sjekkliste.{' '}
                      <a href="/register" className="underline font-medium">
                        Registrer deg / logg inn
                      </a>
                    </p>
                  </div>
                </div>
              )}

              <div className="no-print">
                <Button
                  size="sm"
                  onClick={handleGenerer}
                  disabled={loading}
                  className="bg-orange-600 hover:bg-orange-700 text-white"
                >
                  {loading ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <HardHat className="h-3.5 w-3.5" />
                  )}
                  {loading ? 'Genererer…' : 'Generer sjekkliste'}
                </Button>
              </div>
            </>
          ) : (
            <div className="space-y-5">
              {/* Søknadstype badge */}
              <div className="flex items-start gap-3 flex-wrap">
                {soknadsTypeBadge(result.soknadstype)}
                {result.soknadstype_begrunnelse && (
                  <p className="text-sm text-slate-700 dark:text-slate-300">
                    {result.soknadstype_begrunnelse}
                  </p>
                )}
              </div>

              {/* Advarsler */}
              {result.advarsler.length > 0 && (
                <div className="rounded-lg border border-yellow-200 bg-yellow-50 px-4 py-3 space-y-1.5 dark:border-yellow-900 dark:bg-yellow-950">
                  <p className="text-xs font-semibold uppercase tracking-wide text-yellow-800 dark:text-yellow-300">
                    Advarsler
                  </p>
                  <ul className="space-y-1">
                    {result.advarsler.map((advarsel, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-yellow-800 dark:text-yellow-300">
                        <AlertTriangle className="h-3.5 w-3.5 mt-0.5 shrink-0 text-yellow-600" />
                        {advarsel}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Dokumenter */}
              {result.dokumenter.length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                    Dokumenter som kreves ({result.dokumenter.length})
                  </p>
                  <div className="space-y-2">
                    {result.dokumenter.map((doc, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-3 rounded-lg border border-slate-200 px-3 py-2.5 dark:border-slate-700"
                      >
                        <FileText className="h-4 w-4 mt-0.5 shrink-0 text-blue-600" />
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-slate-900 dark:text-white">
                            {doc.navn}
                          </p>
                          {doc.beskrivelse && (
                            <p className="text-xs text-muted-foreground mt-0.5">
                              {doc.beskrivelse}
                            </p>
                          )}
                          {doc.mal_url && (
                            <a
                              href={doc.mal_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-blue-600 hover:underline dark:text-blue-400 mt-0.5 inline-block"
                            >
                              Last ned mal
                            </a>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Sjekkliste */}
              {result.sjekkliste.length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                    Sjekkliste ({result.sjekkliste.length} punkter)
                  </p>
                  <ul className="space-y-1.5">
                    {result.sjekkliste.map((punkt, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-2.5"
                      >
                        <Square className="h-4 w-4 mt-0.5 shrink-0 text-slate-400" />
                        <div className="flex-1 min-w-0">
                          <span className="text-sm text-slate-800 dark:text-slate-200">
                            {punkt.punkt}
                          </span>
                          {punkt.paragraf && (
                            <span className="ml-2 inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-1.5 py-0 text-xs text-muted-foreground dark:border-slate-700 dark:bg-slate-800">
                              {punkt.paragraf}
                            </span>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <p className="text-xs text-muted-foreground italic border-t pt-3 dark:border-slate-700">
                Sjekklisten er generert av ByggSjekk AI og er kun ment som
                beslutningsstøtte. Ansvarlig arkitekt eller fagperson må alltid
                kvalitetssikre innholdet.
              </p>

              <Button
                variant="ghost"
                size="sm"
                className="text-xs"
                onClick={() => setResult(null)}
              >
                Generer ny sjekkliste
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
