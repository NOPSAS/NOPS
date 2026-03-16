'use client';

import * as React from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { CreditCard, CheckCircle2, ArrowRight, ExternalLink } from 'lucide-react';
import { getBillingSubscription, createBillingPortal } from '@/lib/api';

interface Subscription {
  plan: string;
  plan_label: string;
  status: string;
  cancel_at_period_end: boolean;
  current_period_end: string | null;
  limits: {
    eiendomsoppslag: number;
    ai_analyser: number;
    pdf_rapporter: number;
  };
  has_stripe: boolean;
}

function formatLimit(value: number): string {
  return value === -1 ? 'Ubegrenset' : String(value);
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; className: string }> = {
    active: { label: 'Aktiv', className: 'bg-green-100 text-green-700' },
    trialing: { label: 'Prøveperiode', className: 'bg-blue-100 text-blue-700' },
    past_due: { label: 'Forfalt', className: 'bg-yellow-100 text-yellow-700' },
    canceled: { label: 'Kansellert', className: 'bg-red-100 text-red-700' },
  };
  const s = map[status] ?? { label: status, className: 'bg-slate-100 text-slate-700' };
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${s.className}`}>
      {s.label}
    </span>
  );
}

export default function BillingPage() {
  const searchParams = useSearchParams();
  const success = searchParams.get('success') === '1';

  const [sub, setSub] = React.useState<Subscription | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [portalLoading, setPortalLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    getBillingSubscription()
      .then((data) => {
        setSub(data as Subscription);
        setLoading(false);
      })
      .catch(() => {
        setError('Kunne ikke laste abonnementsinformasjon.');
        setLoading(false);
      });
  }, []);

  const handlePortal = async () => {
    setPortalLoading(true);
    try {
      const result = await createBillingPortal();
      window.location.href = (result as { portal_url: string }).portal_url;
    } catch {
      setError('Kunne ikke åpne kundeportalen. Prøv igjen.');
      setPortalLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-2xl mx-auto px-4 py-12">
        <div className="flex items-center gap-3 mb-8">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100">
            <CreditCard className="h-5 w-5 text-blue-600" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Abonnement og fakturering</h1>
            <p className="text-sm text-slate-500">Administrer ditt nops.no-abonnement</p>
          </div>
        </div>

        {/* Success banner */}
        {success && (
          <div className="mb-6 flex items-center gap-3 rounded-xl bg-green-50 border border-green-200 px-4 py-3">
            <CheckCircle2 className="h-5 w-5 text-green-600 shrink-0" aria-hidden="true" />
            <p className="text-sm text-green-700 font-medium">
              Betalingen ble gjennomfort. Abonnementet ditt er nå aktivt.
            </p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-6 rounded-xl bg-red-50 border border-red-200 px-4 py-3">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="rounded-2xl bg-white border border-slate-200 p-8 text-center">
            <p className="text-slate-400 text-sm">Laster abonnement...</p>
          </div>
        ) : sub ? (
          <>
            {/* Current plan card */}
            <div className="rounded-2xl bg-white border border-slate-200 shadow-sm p-6 mb-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wide font-medium mb-1">Gjeldende plan</p>
                  <h2 className="text-2xl font-bold text-slate-900">{sub.plan_label}</h2>
                </div>
                <StatusBadge status={sub.status} />
              </div>

              {sub.current_period_end && (
                <p className="text-sm text-slate-500 mb-4">
                  {sub.cancel_at_period_end
                    ? `Abonnementet avsluttes `
                    : `Neste fornyelse `}
                  <span className="font-medium text-slate-700">
                    {new Date(sub.current_period_end).toLocaleDateString('no-NO', {
                      day: 'numeric',
                      month: 'long',
                      year: 'numeric',
                    })}
                  </span>
                </p>
              )}

              {sub.cancel_at_period_end && (
                <div className="rounded-lg bg-yellow-50 border border-yellow-200 px-3 py-2 mb-4">
                  <p className="text-xs text-yellow-700">
                    Abonnementet ditt vil ikke fornyes automatisk.
                  </p>
                </div>
              )}

              {/* Limits */}
              <div className="grid grid-cols-3 gap-3 mb-6">
                {[
                  { label: 'Eiendomsoppslag', value: sub.limits.eiendomsoppslag },
                  { label: 'AI-analyser', value: sub.limits.ai_analyser },
                  { label: 'PDF-rapporter', value: sub.limits.pdf_rapporter },
                ].map(({ label, value }) => (
                  <div key={label} className="rounded-xl bg-slate-50 border border-slate-100 p-3 text-center">
                    <p className="text-lg font-bold text-slate-900">{formatLimit(value)}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{label}</p>
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div className="flex flex-col sm:flex-row gap-3">
                {sub.has_stripe ? (
                  <button
                    type="button"
                    onClick={handlePortal}
                    disabled={portalLoading}
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60 transition-colors"
                  >
                    <ExternalLink className="h-4 w-4" aria-hidden="true" />
                    {portalLoading ? 'Laster...' : 'Administrer abonnement'}
                  </button>
                ) : null}
                <Link
                  href="/pricing"
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-100 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-200 transition-colors"
                >
                  Oppgrader abonnement
                  <ArrowRight className="h-4 w-4" aria-hidden="true" />
                </Link>
              </div>
            </div>

            {/* Info box */}
            <div className="rounded-2xl bg-white border border-slate-200 shadow-sm p-6">
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Alle planer inkluderer</h3>
              <p className="text-sm text-slate-500 leading-relaxed">
                Matrikkeldata · Byggesaker · Arealplaner · Planslurpen · Verdiestimator · Kartvisualisering
              </p>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
