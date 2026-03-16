'use client';

import * as React from 'react';
import { Calculator, ChevronDown, Info, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface GebyrPost {
  navn: string;
  belop: number;
  beskrivelse: string;
  alltid_med: boolean;
}

interface GebyrResultat {
  kommunenavn: string;
  tiltakstype: string;
  total_gebyr: number;
  gebyrer: GebyrPost[];
  notat: string;
  kilde: string;
  disclaimer: string;
}

interface GebyrKalkulatorProps {
  knr: string;
  gnr: number;
  bnr: number;
  apiBaseUrl?: string;
}

const TILTAKSTYPER = [
  { value: 'tilbygg', label: 'Tilbygg' },
  { value: 'påbygg', label: 'Påbygg' },
  { value: 'garasje', label: 'Garasje' },
  { value: 'carport', label: 'Carport' },
  { value: 'uthus', label: 'Uthus / bod' },
  { value: 'nybygg', label: 'Nybygg (enebolig)' },
  { value: 'tomannsbolig', label: 'Tomannsbolig' },
  { value: 'bruksendring', label: 'Bruksendring' },
  { value: 'terrasse', label: 'Terrasse' },
  { value: 'fasadeendring', label: 'Fasadeendring' },
  { value: 'riving', label: 'Riving' },
];

function fmt(kr: number) {
  return kr.toLocaleString('no-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 });
}

export function GebyrKalkulator({ knr, gnr, bnr, apiBaseUrl = '/api' }: GebyrKalkulatorProps) {
  const [open, setOpen] = React.useState(false);
  const [tiltakstype, setTiltakstype] = React.useState('tilbygg');
  const [areal, setAreal] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [resultat, setResultat] = React.useState<GebyrResultat | null>(null);
  const [feil, setFeil] = React.useState<string | null>(null);

  async function beregnGebyrer() {
    setLoading(true);
    setFeil(null);
    setResultat(null);
    try {
      const params = new URLSearchParams({
        knr,
        gnr: String(gnr),
        bnr: String(bnr),
        tiltakstype,
      });
      if (areal) params.set('areal_m2', areal);

      const res = await fetch(`${apiBaseUrl}/v1/property/gebyrberegning?${params}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${typeof window !== 'undefined' ? localStorage.getItem('token') || '' : ''}`,
        },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Gebyrberegning feilet');
      }
      const data = await res.json();
      setResultat(data);
    } catch (e: unknown) {
      setFeil(e instanceof Error ? e.message : 'Ukjent feil');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      {/* Header toggle */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between p-5 text-left"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-100">
            <Calculator className="h-5 w-5 text-amber-600" aria-hidden="true" />
          </div>
          <div>
            <p className="font-semibold text-slate-900 text-sm">Gebyrberegning</p>
            <p className="text-xs text-slate-500">Estimer kommunale gebyrer for ditt tiltak</p>
          </div>
        </div>
        <ChevronDown
          className={cn(
            'h-4 w-4 text-slate-400 transition-transform duration-200',
            open && 'rotate-180'
          )}
        />
      </button>

      {open && (
        <div className="border-t border-slate-100 px-5 pb-5 pt-4">
          {/* Form */}
          <div className="flex flex-col sm:flex-row gap-3 mb-4">
            <div className="flex-1">
              <label className="block text-xs font-medium text-slate-600 mb-1.5">
                Tiltakstype
              </label>
              <select
                value={tiltakstype}
                onChange={(e) => setTiltakstype(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {TILTAKSTYPER.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div className="sm:w-36">
              <label className="block text-xs font-medium text-slate-600 mb-1.5">
                Areal (m²)
              </label>
              <input
                type="number"
                min={1}
                max={9999}
                placeholder="f.eks. 30"
                value={areal}
                onChange={(e) => setAreal(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-end">
              <button
                type="button"
                onClick={beregnGebyrer}
                disabled={loading}
                className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg bg-amber-600 px-4 text-sm font-semibold text-white hover:bg-amber-700 disabled:opacity-60 transition-colors"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Calculator className="h-4 w-4" />
                )}
                Beregn
              </button>
            </div>
          </div>

          {feil && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {feil}
            </div>
          )}

          {/* Resultat */}
          {resultat && (
            <div className="mt-2 space-y-3">
              <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 flex items-center justify-between">
                <div>
                  <p className="text-xs text-amber-700 font-medium uppercase tracking-wide">
                    Estimert totalt
                  </p>
                  <p className="text-2xl font-bold text-amber-900 mt-0.5">
                    {fmt(resultat.total_gebyr)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-amber-600">{resultat.kommunenavn}</p>
                  <p className="text-xs text-amber-600 mt-0.5">
                    {resultat.kilde === 'hardkodet' ? 'Faktiske satser 2026' : 'Estimert'}
                  </p>
                </div>
              </div>

              <div className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white overflow-hidden">
                {resultat.gebyrer.map((g) => (
                  <div key={g.navn} className="flex items-center justify-between px-4 py-2.5">
                    <div className="min-w-0 flex-1 pr-4">
                      <p className="text-sm font-medium text-slate-800 truncate">{g.navn}</p>
                      {g.beskrivelse && (
                        <p className="text-xs text-slate-500 truncate">{g.beskrivelse}</p>
                      )}
                    </div>
                    <p className="shrink-0 text-sm font-semibold text-slate-900">
                      {fmt(g.belop)}
                    </p>
                  </div>
                ))}
                <div className="flex items-center justify-between bg-slate-50 px-4 py-3">
                  <p className="text-sm font-bold text-slate-900">Sum ekskl. mva.</p>
                  <p className="text-sm font-bold text-slate-900">{fmt(resultat.total_gebyr)}</p>
                </div>
              </div>

              {resultat.notat && (
                <p className="text-xs text-slate-500">{resultat.notat}</p>
              )}

              <div className="flex items-start gap-2 rounded-lg bg-blue-50 border border-blue-100 px-3 py-2.5">
                <Info className="h-3.5 w-3.5 text-blue-500 mt-0.5 shrink-0" />
                <p className="text-xs text-blue-700 leading-relaxed">
                  {resultat.disclaimer}
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
