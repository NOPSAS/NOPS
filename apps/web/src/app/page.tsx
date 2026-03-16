'use client';

import * as React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Plus,
  FolderOpen,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  FileText,
  Search,
  MapPin,
  Star,
  Sparkles,
  BarChart3,
  TrendingUp,
  Camera,
  Package,
  Newspaper,
  Wrench,
} from 'lucide-react';
import useSWR from 'swr';
import { getCases } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import type { CaseStatus, PropertyCase } from '@/lib/types';
import { useSisteSøk } from '@/hooks/use-siste-sok';
import { useFavoritter } from '@/hooks/use-favoritter';
import { OnboardingBanner } from '@/components/onboarding-banner';

// ─── Status helpers ───────────────────────────────────────────────────────────

function statusLabel(status: CaseStatus): string {
  const labels: Record<CaseStatus, string> = {
    DRAFT: 'Utkast',
    INTAKE: 'Inntak',
    PROCESSING: 'Behandles',
    ANALYSIS: 'Analyse',
    REVIEW: 'Under review',
    COMPLETED: 'Fullført',
    ARCHIVED: 'Arkivert',
  };
  return labels[status] ?? status;
}

function statusVariant(
  status: CaseStatus
): 'default' | 'success' | 'warning' | 'info' | 'muted' | 'secondary' {
  switch (status) {
    case 'COMPLETED':
      return 'success';
    case 'REVIEW':
      return 'warning';
    case 'PROCESSING':
    case 'ANALYSIS':
      return 'info';
    case 'DRAFT':
    case 'INTAKE':
      return 'secondary';
    case 'ARCHIVED':
      return 'muted';
    default:
      return 'muted';
  }
}

// ─── Stats card ───────────────────────────────────────────────────────────────

interface StatCardProps {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  description?: string;
  color?: string;
}

function StatCard({ label, value, icon, description, color = 'text-blue-600' }: StatCardProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{label}</p>
            <p className="mt-1 text-3xl font-bold tabular-nums">{value}</p>
            {description && (
              <p className="mt-1 text-xs text-muted-foreground">{description}</p>
            )}
          </div>
          <div className={`p-2 rounded-lg bg-slate-100 dark:bg-slate-800 ${color}`}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Case row ─────────────────────────────────────────────────────────────────

function CaseRow({ c }: { c: PropertyCase }) {
  return (
    <Link
      href={`/cases/${c.id}`}
      className="group flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 transition-all hover:border-blue-300 hover:shadow-sm dark:border-slate-700 dark:bg-slate-900"
    >
      <div className="flex items-start gap-3 min-w-0">
        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-slate-100 dark:bg-slate-800">
          <FolderOpen className="h-4 w-4 text-slate-500" />
        </div>
        <div className="min-w-0">
          <p className="truncate font-medium text-slate-900 dark:text-white">
            {c.property.street_address}
          </p>
          <p className="truncate text-xs text-muted-foreground">
            {c.property.postal_code} {c.property.municipality}
            {c.property.gnr != null && ` · Gnr/Bnr: ${c.property.gnr}/${c.property.bnr}`}
          </p>
        </div>
      </div>

      <div className="ml-4 flex shrink-0 items-center gap-4">
        <div className="hidden sm:flex items-center gap-3 text-xs text-muted-foreground">
          {c.document_count !== undefined && (
            <span className="flex items-center gap-1">
              <FileText className="h-3.5 w-3.5" />
              {c.document_count} dok.
            </span>
          )}
          {c.open_deviation_count !== undefined && c.open_deviation_count > 0 && (
            <span className="flex items-center gap-1 text-orange-600">
              <AlertTriangle className="h-3.5 w-3.5" />
              {c.open_deviation_count} avvik
            </span>
          )}
          <span>{formatDate(c.updated_at)}</span>
        </div>
        <Badge variant={statusVariant(c.status)}>{statusLabel(c.status)}</Badge>
        <ArrowRight className="h-4 w-4 text-slate-400 transition-transform group-hover:translate-x-0.5" />
      </div>
    </Link>
  );
}

// ─── Dashboard page ───────────────────────────────────────────────────────────

export default function DashboardPage() {
  const router = useRouter();
  const { data: cases, error, isLoading } = useSWR('cases', getCases);
  const { søk: sisteSøk } = useSisteSøk();
  const { favoritter } = useFavoritter();

  // Computed stats
  const stats = React.useMemo(() => {
    if (!cases) return null;
    return {
      total: cases.length,
      inProgress: cases.filter((c) =>
        ['INTAKE', 'PROCESSING', 'ANALYSIS', 'REVIEW'].includes(c.status)
      ).length,
      completed: cases.filter((c) => c.status === 'COMPLETED').length,
      openDeviations: cases.reduce(
        (sum, c) => sum + (c.open_deviation_count ?? 0),
        0
      ),
    };
  }, [cases]);

  const recentCases = React.useMemo(
    () =>
      cases
        ? [...cases]
            .sort(
              (a, b) =>
                new Date(b.updated_at).getTime() -
                new Date(a.updated_at).getTime()
            )
            .slice(0, 10)
        : [],
    [cases]
  );

  return (
    <div className="page-container">
      <OnboardingBanner />
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="section-title">Dashboard</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Oversikt over alle dine saker
          </p>
        </div>
        <Button onClick={() => router.push('/cases/new')}>
          <Plus className="h-4 w-4" />
          Ny sak
        </Button>
      </div>

      {/* Quick property search */}
      <Card className="mb-6 border-blue-100 bg-blue-50 dark:border-blue-900 dark:bg-blue-950">
        <CardContent className="pt-5 pb-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600">
                <MapPin className="h-4 w-4 text-white" />
              </div>
              <div>
                <p className="font-semibold text-blue-900 dark:text-blue-100">Raskt eiendomsoppslag</p>
                <p className="text-xs text-blue-700 dark:text-blue-300">
                  Hent byggesaker, arealplaner og AI-analyse for enhver norsk eiendom
                </p>
              </div>
            </div>
            <Button asChild variant="default" size="sm" className="bg-blue-600 hover:bg-blue-700">
              <Link href="/property">
                <Search className="h-3.5 w-3.5" />
                Søk opp eiendom
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Siste søk */}
      {sisteSøk.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">Siste søk</h2>
          <div className="flex flex-wrap gap-2">
            {sisteSøk.slice(0, 6).map((s) => (
              <Link
                key={`${s.knr}-${s.gnr}-${s.bnr}`}
                href={`/property?knr=${s.knr}&gnr=${s.gnr}&bnr=${s.bnr}`}
                className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 hover:border-blue-300 hover:bg-blue-50 transition-colors shadow-sm"
              >
                <MapPin className="h-3.5 w-3.5 text-slate-400" />
                {s.adresse || `Gnr. ${s.gnr} / Bnr. ${s.bnr}`}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Lagrede eiendommer */}
      {favoritter.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">Lagrede eiendommer</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {favoritter.slice(0, 4).map((f) => (
              <Link
                key={`${f.knr}-${f.gnr}-${f.bnr}`}
                href={`/property?knr=${f.knr}&gnr=${f.gnr}&bnr=${f.bnr}`}
                className="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm hover:bg-amber-100 transition-colors"
              >
                <Star className="h-4 w-4 fill-amber-400 text-amber-400 shrink-0" />
                <div className="min-w-0">
                  <p className="font-medium text-slate-900 truncate">{f.adresse || `${f.gnr}/${f.bnr}`}</p>
                  <p className="text-xs text-slate-500">Gnr. {f.gnr} / Bnr. {f.bnr}</p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Stats */}
      {stats && (
        <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard
            label="Totalt saker"
            value={stats.total}
            icon={<FolderOpen className="h-5 w-5" />}
            color="text-blue-600"
          />
          <StatCard
            label="Under arbeid"
            value={stats.inProgress}
            icon={<Clock className="h-5 w-5" />}
            color="text-yellow-600"
            description="Inntak, behandling og review"
          />
          <StatCard
            label="Fullførte"
            value={stats.completed}
            icon={<CheckCircle2 className="h-5 w-5" />}
            color="text-green-600"
          />
          <StatCard
            label="Åpne avvik"
            value={stats.openDeviations}
            icon={<AlertTriangle className="h-5 w-5" />}
            color="text-orange-600"
            description="På tvers av alle saker"
          />
        </div>
      )}

      {/* Tjenester hurtigtilgang */}
      <div className="mb-8">
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">Verktøy</h2>
        <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-7 gap-2">
          {[
            { href: '/property', icon: <MapPin className="h-5 w-5" />, label: 'Eiendomssøk', farge: 'text-blue-600 bg-blue-50' },
            { href: '/visualisering', icon: <Camera className="h-5 w-5" />, label: 'Visualisering', farge: 'text-purple-600 bg-purple-50' },
            { href: '/utbygging', icon: <BarChart3 className="h-5 w-5" />, label: 'Utbygging', farge: 'text-green-600 bg-green-50' },
            { href: '/investering', icon: <TrendingUp className="h-5 w-5" />, label: 'Investering', farge: 'text-indigo-600 bg-indigo-50' },
            { href: '/romplanlegger', icon: <Sparkles className="h-5 w-5" />, label: 'Romplan', farge: 'text-pink-600 bg-pink-50' },
            { href: '/pakke', icon: <Package className="h-5 w-5" />, label: 'Pakke', farge: 'text-amber-600 bg-amber-50' },
            { href: '/nyheter', icon: <Newspaper className="h-5 w-5" />, label: 'Nyheter', farge: 'text-red-600 bg-red-50' },
          ].map((t) => (
            <Link
              key={t.href}
              href={t.href}
              className="flex flex-col items-center gap-1.5 rounded-xl border border-slate-200 bg-white p-3 hover:border-slate-300 hover:shadow-sm transition-all text-center"
            >
              <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${t.farge}`}>
                {t.icon}
              </div>
              <span className="text-[11px] font-medium text-slate-700 leading-tight">{t.label}</span>
            </Link>
          ))}
        </div>
      </div>

      {/* Case list */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle className="text-lg">Siste saker</CardTitle>
            <CardDescription>
              Dine sist oppdaterte byggesaker
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" asChild>
            <Link href="/cases">Se alle</Link>
          </Button>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-14 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800"
                />
              ))}
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
              Kunne ikke hente saker. Sjekk tilkoblingen og prøv igjen.
            </div>
          )}

          {!isLoading && !error && recentCases.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FolderOpen className="mb-3 h-10 w-10 text-slate-300" />
              <p className="font-medium text-slate-600 dark:text-slate-400">
                Ingen saker ennå
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                Kom i gang ved å opprette din første sak
              </p>
              <Button className="mt-4" onClick={() => router.push('/cases/new')}>
                <Plus className="h-4 w-4" />
                Opprett sak
              </Button>
            </div>
          )}

          {!isLoading && !error && recentCases.length > 0 && (
            <div className="space-y-2">
              {recentCases.map((c) => (
                <CaseRow key={c.id} c={c} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
