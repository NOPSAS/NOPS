'use client';

import * as React from 'react';
import {
  Layers,
  Loader2,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Palette,
  Package,
  Lightbulb,
  ShoppingBag,
  LayoutGrid,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// ─── Types ─────────────────────────────────────────────────────────────────────

interface Farge {
  navn: string;
  hex: string;
  bruk: string;
  tone?: string;
}

interface Materiale {
  type: string;
  anbefaling: string;
  grunn: string;
  pris_per_m2: number;
}

interface Budsjettpost {
  kategori: string;
  prosent: number;
  estimat_kr: number;
}

interface Produkt {
  produkt: string;
  butikk: string;
  estimert_pris: number;
  grunn: string;
  prioritet?: string;
}

interface RomPlan {
  planleggingsforslag: string;
  fargepalette: Farge[];
  materialer: Materiale[];
  belysning: string;
  budsjettfordeling: Budsjettpost[];
  produktanbefalinger: Produkt[];
  tips: string[];
}

interface AnalyseResultat {
  romtype: string;
  stil: string;
  budsjett: string;
  plan?: RomPlan;
  // Direkte felt (ny endpoint-struktur)
  planleggingsforslag?: string;
  fargepalette?: Farge[];
  materialer?: Materiale[];
  belysning?: string;
  budsjettfordeling?: Budsjettpost[];
  produktanbefalinger?: Produkt[];
  tips?: string[];
}

// ─── Konstanter ────────────────────────────────────────────────────────────────

const ROMTYPER = [
  { id: 'stue', label: 'Stue', emoji: '🛋️' },
  { id: 'kjøkken', label: 'Kjøkken', emoji: '🍳' },
  { id: 'soverom', label: 'Soverom', emoji: '🛏️' },
  { id: 'bad', label: 'Bad', emoji: '🚿' },
  { id: 'kontor', label: 'Kontor', emoji: '💻' },
  { id: 'barnerom', label: 'Barnerom', emoji: '🧸' },
  { id: 'terrasse', label: 'Terrasse', emoji: '🌿' },
];

const STØRRELSER = [
  { id: 'small', label: 'Lite', sub: '< 20 m²' },
  { id: 'medium', label: 'Middels', sub: '20–40 m²' },
  { id: 'large', label: 'Stort', sub: '> 40 m²' },
];

const STILER = [
  { id: 'Nordisk', label: 'Nordisk', desc: 'Minimalistisk, lyst tre' },
  { id: 'Moderne', label: 'Moderne', desc: 'Rene linjer, geometrisk' },
  { id: 'Industriell', label: 'Industriell', desc: 'Stål, betong, loft' },
  { id: 'Klassisk', label: 'Klassisk', desc: 'Tradisjonell eleganse' },
  { id: 'Japandi', label: 'Japandi', desc: 'Zen, naturmaterialer' },
  { id: 'Boho', label: 'Boho', desc: 'Fargerikt, tekstiler' },
];

const BUDSJETTER = [
  { id: 'under_50k', label: 'Under 50 000 kr', sub: 'Budsjett' },
  { id: '50_150k', label: '50–150 000 kr', sub: 'Mellom' },
  { id: '150_300k', label: '150–300 000 kr', sub: 'Premium' },
  { id: 'over_300k', label: 'Over 300 000 kr', sub: 'Luksus' },
];

function fmt(n: number): string {
  return new Intl.NumberFormat('nb-NO').format(Math.round(n));
}

// ─── Component ─────────────────────────────────────────────────────────────────

export default function RomplanleggerPage() {
  const [romtype, setRomtype] = React.useState('stue');
  const [størrelse, setStørrelse] = React.useState('medium');
  const [stil, setStil] = React.useState('Nordisk');
  const [budsjett, setBudsjett] = React.useState('50_150k');
  const [ønsker, setØnsker] = React.useState('');

  const [loading, setLoading] = React.useState(false);
  const [feil, setFeil] = React.useState<string | null>(null);
  const [resultat, setResultat] = React.useState<AnalyseResultat | null>(null);

  React.useEffect(() => {
    document.title = 'AI Romplanlegger \u2013 Farger, materialer og m\u00f8belplan | nops.no';
  }, []);

  // Utled plan uansett respons-format
  const plan: RomPlan | null = React.useMemo(() => {
    if (!resultat) return null;
    if (resultat.plan) return resultat.plan;
    if (resultat.planleggingsforslag) {
      return {
        planleggingsforslag: resultat.planleggingsforslag ?? '',
        fargepalette: resultat.fargepalette ?? [],
        materialer: resultat.materialer ?? [],
        belysning: resultat.belysning ?? '',
        budsjettfordeling: resultat.budsjettfordeling ?? [],
        produktanbefalinger: resultat.produktanbefalinger ?? [],
        tips: resultat.tips ?? [],
      };
    }
    return null;
  }, [resultat]);

  async function kjørAnalyse(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setFeil(null);
    setResultat(null);

    try {
      const form = new FormData();
      form.append('romtype', romtype);
      form.append('størrelse', størrelse);
      form.append('stil', stil);
      form.append('budsjett', budsjett);
      form.append('ønsker', ønsker);

      const res = await fetch('/api/v1/visualisering/analyser-rom', {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('token') || ''}` },
        body: form,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error((err as { detail?: string }).detail || 'Analyse feilet');
      }
      const data = await res.json() as AnalyseResultat;
      setResultat(data);
    } catch (err: unknown) {
      setFeil(err instanceof Error ? err.message : 'Ukjent feil');
    } finally {
      setLoading(false);
    }
  }

  function nullstill() {
    setResultat(null);
    setFeil(null);
  }

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <section className="bg-gradient-to-br from-violet-600 to-pink-600 text-white py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 mb-4 rounded-full bg-white/10 px-4 py-1.5 text-sm font-medium text-violet-100">
            <Layers className="h-4 w-4" />
            nops.no / AI Romplanlegger
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mb-3">AI Romplanlegger</h1>
          <p className="text-lg text-violet-100 max-w-2xl">
            Beskriv rommet ditt – AI planlegger det for deg. Farger, materialer, møbelplassering
            og produktanbefalinger fra norske butikker.
          </p>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-4 py-10 space-y-6">

        {!resultat && (
          <form onSubmit={kjørAnalyse} className="space-y-6">
            {/* Steg 1 – Romtype */}
            <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6 space-y-5">
              <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                <LayoutGrid className="h-4 w-4 text-violet-600" />
                Steg 1 – Romtype og preferanser
              </h2>

              {/* Romtype */}
              <div>
                <p className="text-sm font-medium text-slate-700 mb-3">Velg romtype</p>
                <div className="grid grid-cols-4 sm:grid-cols-7 gap-2">
                  {ROMTYPER.map((r) => (
                    <button
                      key={r.id}
                      type="button"
                      onClick={() => setRomtype(r.id)}
                      className={cn(
                        'flex flex-col items-center gap-1.5 rounded-xl border p-3 text-center transition-all',
                        romtype === r.id
                          ? 'border-violet-500 bg-violet-50 text-violet-700'
                          : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
                      )}
                    >
                      <span className="text-xl">{r.emoji}</span>
                      <span className="text-xs font-medium leading-tight">{r.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Størrelse */}
              <div>
                <p className="text-sm font-medium text-slate-700 mb-3">Romstørrelse</p>
                <div className="grid grid-cols-3 gap-3">
                  {STØRRELSER.map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => setStørrelse(s.id)}
                      className={cn(
                        'flex flex-col items-center rounded-xl border p-4 transition-all',
                        størrelse === s.id
                          ? 'border-violet-500 bg-violet-50 text-violet-700'
                          : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
                      )}
                    >
                      <span className="text-sm font-semibold">{s.label}</span>
                      <span className="text-xs text-slate-400 mt-0.5">{s.sub}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Stil */}
              <div>
                <p className="text-sm font-medium text-slate-700 mb-3">Ønsket stil</p>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {STILER.map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => setStil(s.id)}
                      className={cn(
                        'flex flex-col items-start rounded-xl border p-3 transition-all text-left',
                        stil === s.id
                          ? 'border-violet-500 bg-violet-50'
                          : 'border-slate-200 bg-white hover:border-slate-300'
                      )}
                    >
                      <span className={cn('text-sm font-semibold', stil === s.id ? 'text-violet-700' : 'text-slate-800')}>
                        {s.label}
                      </span>
                      <span className="text-xs text-slate-400 mt-0.5">{s.desc}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Budsjett */}
              <div>
                <p className="text-sm font-medium text-slate-700 mb-3">Budsjett</p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {BUDSJETTER.map((b) => (
                    <button
                      key={b.id}
                      type="button"
                      onClick={() => setBudsjett(b.id)}
                      className={cn(
                        'flex flex-col items-center rounded-xl border p-3 text-center transition-all',
                        budsjett === b.id
                          ? 'border-violet-500 bg-violet-50 text-violet-700'
                          : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
                      )}
                    >
                      <span className="text-xs font-semibold leading-tight">{b.label}</span>
                      <span className="text-xs text-slate-400 mt-0.5">{b.sub}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Steg 2 – Tilleggsinfo */}
            <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6">
              <h2 className="text-base font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-amber-500" />
                Steg 2 – Spesielle ønsker (valgfritt)
              </h2>
              <textarea
                value={ønsker}
                onChange={(e) => setØnsker(e.target.value)}
                placeholder='F.eks. "Vi trenger arbeidsplass for to, har to barn, ønsker mye oppbevaring og liker planter"'
                rows={4}
                className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-violet-500 resize-none"
              />
            </div>

            {feil && (
              <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {feil}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-6 py-3 text-sm font-semibold text-white hover:bg-violet-700 disabled:opacity-60 transition-colors"
            >
              {loading ? (
                <><Loader2 className="h-4 w-4 animate-spin" /> Planlegger rommet…</>
              ) : (
                <><Layers className="h-4 w-4" /> Generer romplan</>
              )}
            </button>
          </form>
        )}

        {/* Resultat */}
        {plan && resultat && (
          <div className="space-y-5">
            {/* Header badge */}
            <div className="flex items-center gap-3">
              <span className="inline-flex items-center gap-2 rounded-full border border-violet-300 bg-violet-50 px-4 py-2 text-sm font-semibold text-violet-700">
                <CheckCircle2 className="h-4 w-4" />
                {ROMTYPER.find((r) => r.id === resultat.romtype)?.emoji ?? ''}{' '}
                {ROMTYPER.find((r) => r.id === resultat.romtype)?.label ?? resultat.romtype} – {resultat.stil}
              </span>
              <span className="text-sm text-slate-500">
                {BUDSJETTER.find((b) => b.id === resultat.budsjett)?.label ?? resultat.budsjett}
              </span>
            </div>

            {/* Planleggingsforslag */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-900 mb-2 text-sm flex items-center gap-2">
                <LayoutGrid className="h-4 w-4 text-violet-600" />
                Planleggingsforslag
              </h3>
              <p className="text-sm text-slate-700 leading-relaxed">{plan.planleggingsforslag}</p>
            </div>

            {/* Fargepalette */}
            {(plan.fargepalette?.length ?? 0) > 0 && (
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-900 mb-4 text-sm flex items-center gap-2">
                  <Palette className="h-4 w-4 text-pink-500" />
                  Fargepalette
                </h3>
                <div className="flex flex-wrap gap-3">
                  {plan.fargepalette.map((f, i) => (
                    <div key={i} className="flex flex-col items-center gap-2">
                      <div
                        className="h-14 w-14 rounded-xl border border-slate-200 shadow-sm"
                        style={{ backgroundColor: f.hex }}
                        title={f.hex}
                      />
                      <div className="text-center">
                        <p className="text-xs font-medium text-slate-800 leading-tight">{f.navn}</p>
                        <p className="text-xs text-slate-400">{f.hex}</p>
                        <p className="text-xs text-slate-400">{f.bruk}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Materialer */}
            {(plan.materialer?.length ?? 0) > 0 && (
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-900 mb-4 text-sm flex items-center gap-2">
                  <Package className="h-4 w-4 text-emerald-600" />
                  Materialanbefalinger
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {plan.materialer.map((m, i) => (
                    <div key={i} className="rounded-lg bg-slate-50 border border-slate-200 p-4">
                      <div className="flex items-center justify-between mb-1">
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wide">{m.type}</p>
                        {m.pris_per_m2 > 0 && (
                          <span className="text-xs font-semibold text-slate-600">{fmt(m.pris_per_m2)} kr/m²</span>
                        )}
                      </div>
                      <p className="text-sm font-semibold text-slate-900">{m.anbefaling}</p>
                      <p className="text-xs text-slate-500 mt-1 leading-relaxed">{m.grunn}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Belysning */}
            {plan.belysning && (
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-900 mb-2 text-sm flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-amber-500" />
                  Belysningsplan
                </h3>
                <p className="text-sm text-slate-700 leading-relaxed">{plan.belysning}</p>
              </div>
            )}

            {/* Budsjettfordeling */}
            {(plan.budsjettfordeling?.length ?? 0) > 0 && (
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-900 mb-4 text-sm flex items-center gap-2">
                  <Package className="h-4 w-4 text-blue-600" />
                  Budsjettfordeling
                </h3>
                <div className="space-y-3">
                  {plan.budsjettfordeling.map((b, i) => (
                    <div key={i}>
                      <div className="flex justify-between text-xs text-slate-600 mb-1.5">
                        <span className="font-medium">{b.kategori}</span>
                        <span>{b.prosent}% – {fmt(b.estimat_kr)} kr</span>
                      </div>
                      <div className="h-2.5 w-full rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-violet-500 transition-all"
                          style={{ width: `${Math.min(100, b.prosent)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Produktanbefalinger */}
            {(plan.produktanbefalinger?.length ?? 0) > 0 && (
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-900 mb-4 text-sm flex items-center gap-2">
                  <ShoppingBag className="h-4 w-4 text-pink-500" />
                  Produktanbefalinger
                </h3>
                <div className="space-y-3">
                  {plan.produktanbefalinger.map((p, i) => (
                    <div key={i} className="flex items-start gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-violet-100">
                        <ShoppingBag className="h-4 w-4 text-violet-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-sm font-semibold text-slate-900">{p.produkt}</p>
                          <span className="shrink-0 text-sm font-bold text-slate-700">{fmt(p.estimert_pris)} kr</span>
                        </div>
                        <p className="text-xs text-violet-700 font-medium mt-0.5">{p.butikk}</p>
                        <p className="text-xs text-slate-500 mt-1 leading-relaxed">{p.grunn}</p>
                        {p.prioritet && (
                          <span className={cn(
                            'mt-1.5 inline-block rounded-full px-2 py-0.5 text-xs font-medium',
                            p.prioritet === 'Høy' || p.prioritet === 'Må ha'
                              ? 'bg-emerald-100 text-emerald-700'
                              : p.prioritet === 'Bør ha'
                              ? 'bg-amber-100 text-amber-700'
                              : 'bg-slate-100 text-slate-600'
                          )}>
                            {p.prioritet}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tips */}
            {(plan.tips?.length ?? 0) > 0 && (
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-900 mb-3 text-sm flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  Planleggingstips
                </h3>
                <ol className="space-y-2">
                  {plan.tips.map((t, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm text-slate-700">
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-violet-100 text-xs font-bold text-violet-700">
                        {i + 1}
                      </span>
                      {t}
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {feil && (
              <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {feil}
              </div>
            )}

            <div className="flex gap-3">
              <button
                type="button"
                onClick={nullstill}
                className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
              >
                Planlegg nytt rom
              </button>
              <a
                href="/tjenester"
                className="inline-flex items-center gap-2 rounded-lg bg-violet-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-violet-700 transition-colors"
              >
                Se alle tjenester
                <ArrowRight className="h-4 w-4" />
              </a>
            </div>

            {/* Info footer */}
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <p className="text-xs text-slate-500">
                <strong>Merk:</strong> AI-romplanleggeren gir inspirasjon og veiledning basert på beste praksis
                innen interiørdesign. For større prosjekter anbefales konsultasjon med en interiørarkitekt.
              </p>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
