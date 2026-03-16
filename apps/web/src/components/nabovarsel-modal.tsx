'use client';

import * as React from 'react';
import {
  Scale,
  X,
  Loader2,
  Copy,
  Download,
  Check,
  ChevronDown,
  AlertTriangle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { fetchJSON } from '@/lib/utils';

// ─── Types ────────────────────────────────────────────────────────────────────

interface NabovarselResult {
  nabovarsel_tekst: string;
  paragraf_referanser: string[];
  tips: string[];
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
  | 'terrasse'
  | 'carport'
  | 'nybygg';

interface NabovarselModalProps {
  knr: string;
  gnr: string;
  bnr: string;
  disabled?: boolean;
}

// ─── Component ────────────────────────────────────────────────────────────────

export function NabovarselModal({ knr, gnr, bnr, disabled }: NabovarselModalProps) {
  const [open, setOpen] = React.useState(false);
  const [tiltakstype, setTiltakstype] = React.useState<Tiltakstype>('tilbygg');
  const [tiltaksbeskrivelse, setTiltaksbeskrivelse] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [upsell, setUpsell] = React.useState(false);
  const [result, setResult] = React.useState<NabovarselResult | null>(null);
  const [copied, setCopied] = React.useState(false);

  function handleOpen() {
    setOpen(true);
    setError(null);
    setUpsell(false);
    setResult(null);
  }

  function handleClose() {
    setOpen(false);
  }

  async function handleGenerer() {
    if (!tiltaksbeskrivelse.trim()) {
      setError('Du må beskrive hva du planlegger å bygge.');
      return;
    }
    setLoading(true);
    setError(null);
    setUpsell(false);
    setResult(null);

    const params = new URLSearchParams({
      knr,
      gnr,
      bnr,
      tiltakstype,
      tiltaksbeskrivelse: tiltaksbeskrivelse.trim(),
    });

    try {
      const data = await fetchJSON<NabovarselResult>(
        `/api/v1/property/nabovarsel?${params.toString()}`,
        { method: 'POST' }
      );
      setResult(data);
    } catch (err: unknown) {
      const e = err as { status?: number; message?: string };
      if (e.status === 402) {
        setUpsell(true);
      } else {
        setError(e.message || 'Nabovarsel-generering feilet.');
      }
    } finally {
      setLoading(false);
    }
  }

  function handleCopy() {
    if (!result) return;
    navigator.clipboard.writeText(result.nabovarsel_tekst).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  function handleDownload() {
    if (!result) return;
    const blob = new Blob([result.nabovarsel_tekst], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nabovarsel_${gnr}_${bnr}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <>
      {/* Trigger-knapp */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
              <Scale className="h-4 w-4 text-indigo-600" />
              Nabovarsel
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Generer et komplett nabovarsel-brev etter PBL §21-3 og SAK10 §6-2
            </p>
          </div>
          <div className="no-print">
            <Button
              variant="outline"
              size="sm"
              onClick={handleOpen}
              disabled={disabled}
            >
              <Scale className="h-3.5 w-3.5 text-indigo-600" />
              Generer nabovarsel
            </Button>
          </div>
        </div>
      </div>

      {/* Modal */}
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50"
            onClick={handleClose}
            aria-hidden="true"
          />

          {/* Dialog */}
          <div className="relative z-10 w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white shadow-2xl dark:bg-slate-900">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-700">
              <div className="flex items-center gap-2">
                <Scale className="h-5 w-5 text-indigo-600" />
                <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                  Generer nabovarsel
                </h2>
              </div>
              <button
                onClick={handleClose}
                className="rounded-md p-1 text-muted-foreground hover:text-slate-900 dark:hover:text-white"
                aria-label="Lukk"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Body */}
            <div className="px-6 py-5 space-y-5">
              {!result ? (
                <>
                  <p className="text-sm text-muted-foreground">
                    Fyll inn informasjon om tiltaket. ByggSjekk AI skriver et ferdig
                    nabovarsel-brev med korrekte lovhenvisninger. Dette er
                    beslutningsstøtte – ikke juridisk rådgivning.
                  </p>

                  {/* Tiltakstype */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                      Tiltakstype
                    </label>
                    <div className="relative">
                      <select
                        value={tiltakstype}
                        onChange={(e) => setTiltakstype(e.target.value as Tiltakstype)}
                        className="w-full appearance-none rounded-lg border border-slate-200 bg-white px-3 py-2.5 pr-8 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-800 dark:text-white"
                      >
                        <option value="tilbygg">Tilbygg</option>
                        <option value="garasje">Garasje</option>
                        <option value="bruksendring">Bruksendring</option>
                        <option value="terrasse">Terrasse</option>
                        <option value="carport">Carport</option>
                        <option value="nybygg">Nybygg</option>
                      </select>
                      <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    </div>
                  </div>

                  {/* Tiltaksbeskrivelse */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                      Beskriv tiltaket
                    </label>
                    <textarea
                      value={tiltaksbeskrivelse}
                      onChange={(e) => setTiltaksbeskrivelse(e.target.value)}
                      placeholder="F.eks.: Tilbygg på 20 m² BRA i én etasje på baksiden av boligen, med ny stue og bod. Tilbygget plasseres inntil eksisterende vegg og bygges i samme stil som eksisterende bebyggelse."
                      rows={5}
                      className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-800 dark:text-white"
                    />
                    <p className="mt-1 text-xs text-muted-foreground">
                      Jo mer detaljert beskrivelse, desto bedre brev.
                    </p>
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
                          AI-genererte nabovarsel er tilgjengelig fra Starter (499 kr/mnd).{' '}
                          <a href="/pricing" className="underline font-medium">
                            Se priser
                          </a>
                        </p>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <>
                  {/* Resultat */}
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                      Nabovarsel-brev generert
                    </p>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm" onClick={handleCopy}>
                        {copied ? (
                          <Check className="h-3.5 w-3.5 text-green-600" />
                        ) : (
                          <Copy className="h-3.5 w-3.5" />
                        )}
                        {copied ? 'Kopiert!' : 'Kopier'}
                      </Button>
                      <Button variant="outline" size="sm" onClick={handleDownload}>
                        <Download className="h-3.5 w-3.5" />
                        Last ned .txt
                      </Button>
                    </div>
                  </div>

                  <pre className="whitespace-pre-wrap rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-800 font-mono leading-relaxed dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200">
                    {result.nabovarsel_tekst}
                  </pre>

                  {/* Paragrafhenvisninger */}
                  {result.paragraf_referanser.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                        Lovhenvisninger
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {result.paragraf_referanser.map((ref, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-800 dark:border-indigo-900 dark:bg-indigo-950 dark:text-indigo-300"
                          >
                            {ref}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tips */}
                  {result.tips.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                        Tips om nabovarslingsprosessen
                      </p>
                      <ul className="space-y-1.5">
                        {result.tips.map((tip, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-slate-700 dark:text-slate-300">
                            <Check className="h-3.5 w-3.5 mt-0.5 shrink-0 text-indigo-500" />
                            {tip}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <p className="text-xs text-muted-foreground italic border-t pt-3 dark:border-slate-700">
                    Dette nabovarselet er generert av ByggSjekk AI og er kun ment som
                    beslutningsstøtte. Ansvarlig arkitekt eller fagperson må alltid
                    kvalitetssikre innholdet. Brevet er ikke juridisk rådgivning.
                  </p>

                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs"
                    onClick={() => setResult(null)}
                  >
                    Generer nytt nabovarsel
                  </Button>
                </>
              )}
            </div>

            {/* Footer */}
            {!result && (
              <div className="border-t border-slate-200 px-6 py-4 flex items-center justify-end gap-3 dark:border-slate-700">
                <Button variant="ghost" size="sm" onClick={handleClose}>
                  Avbryt
                </Button>
                <Button
                  size="sm"
                  onClick={handleGenerer}
                  disabled={loading || !tiltaksbeskrivelse.trim()}
                >
                  {loading ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Scale className="h-3.5 w-3.5" />
                  )}
                  {loading ? 'Genererer…' : 'Generer nabovarsel'}
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
