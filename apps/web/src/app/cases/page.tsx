'use client';

import * as React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import useSWR from 'swr';
import {
  Plus,
  FolderOpen,
  Search,
  AlertTriangle,
  FileText,
  ArrowRight,
  MapPin,
} from 'lucide-react';
import { getCases } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import type { CaseStatus, PropertyCase } from '@/lib/types';

const allStatuses: CaseStatus[] = [
  'DRAFT',
  'INTAKE',
  'PROCESSING',
  'ANALYSIS',
  'REVIEW',
  'COMPLETED',
  'ARCHIVED',
];

const statusLabels: Record<CaseStatus, string> = {
  DRAFT: 'Utkast',
  INTAKE: 'Inntak',
  PROCESSING: 'Behandles',
  ANALYSIS: 'Analyse',
  REVIEW: 'Under review',
  COMPLETED: 'Fullført',
  ARCHIVED: 'Arkivert',
};

function statusVariant(
  s: CaseStatus
): 'default' | 'success' | 'warning' | 'info' | 'muted' | 'secondary' {
  switch (s) {
    case 'COMPLETED': return 'success';
    case 'REVIEW': return 'warning';
    case 'PROCESSING':
    case 'ANALYSIS': return 'info';
    case 'DRAFT':
    case 'INTAKE': return 'secondary';
    default: return 'muted';
  }
}

function CaseCard({ c }: { c: PropertyCase }) {
  return (
    <Link
      href={`/cases/${c.id}`}
      className="group flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 transition-all hover:border-blue-300 hover:shadow-sm dark:border-slate-700 dark:bg-slate-900"
    >
      <div className="flex items-start gap-3 min-w-0">
        <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-slate-100 dark:bg-slate-800">
          <FolderOpen className="h-4 w-4 text-slate-500" />
        </div>
        <div className="min-w-0">
          <p className="truncate font-medium text-slate-900 dark:text-white">
            {c.property.street_address}
          </p>
          <p className="truncate text-xs text-muted-foreground">
            {c.property.postal_code} {c.property.municipality}
            {c.property.gnr != null
              ? ` · Gnr/Bnr: ${c.property.gnr}/${c.property.bnr}`
              : ''}
          </p>
        </div>
      </div>

      <div className="ml-4 flex shrink-0 items-center gap-4">
        <div className="hidden sm:flex items-center gap-3 text-xs text-muted-foreground">
          {c.document_count !== undefined && (
            <span className="flex items-center gap-1">
              <FileText className="h-3.5 w-3.5" />
              {c.document_count}
            </span>
          )}
          {c.open_deviation_count !== undefined &&
            c.open_deviation_count > 0 && (
              <span className="flex items-center gap-1 text-orange-600">
                <AlertTriangle className="h-3.5 w-3.5" />
                {c.open_deviation_count}
              </span>
            )}
          <span>{formatDate(c.updated_at)}</span>
        </div>
        {c.property.kommunenummer && c.property.gnr != null && c.property.bnr != null && (
          <a
            href={`/property?knr=${c.property.kommunenummer}&gnr=${c.property.gnr}&bnr=${c.property.bnr}`}
            onClick={(e) => e.stopPropagation()}
            title="Eiendomsoppslag"
            className="flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-600 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 transition-colors dark:border-slate-700 dark:text-slate-400"
          >
            <MapPin className="h-3 w-3" />
            Eiendom
          </a>
        )}
        <Badge variant={statusVariant(c.status)}>
          {statusLabels[c.status]}
        </Badge>
        <ArrowRight className="h-4 w-4 text-slate-400 transition-transform group-hover:translate-x-0.5" />
      </div>
    </Link>
  );
}

export default function CasesPage() {
  const router = useRouter();
  const { data: cases, isLoading, error } = useSWR('cases-list', getCases);

  const [search, setSearch] = React.useState('');
  const [filterStatus, setFilterStatus] = React.useState<'ALL' | CaseStatus>('ALL');

  const filtered = React.useMemo(() => {
    if (!cases) return [];
    return cases
      .filter((c) => {
        if (filterStatus !== 'ALL' && c.status !== filterStatus) return false;
        if (search.trim()) {
          const q = search.toLowerCase();
          return (
            c.property.street_address.toLowerCase().includes(q) ||
            c.property.municipality.toLowerCase().includes(q) ||
            c.property.postal_code.includes(q)
          );
        }
        return true;
      })
      .sort(
        (a, b) =>
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      );
  }, [cases, search, filterStatus]);

  return (
    <div className="page-container">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="section-title">Alle saker</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {cases ? `${cases.length} saker totalt` : 'Laster...'}
          </p>
        </div>
        <Button onClick={() => router.push('/cases/new')}>
          <Plus className="h-4 w-4" />
          Ny sak
        </Button>
      </div>

      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-48 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Søk på adresse eller kommune..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select
          value={filterStatus}
          onValueChange={(v) => setFilterStatus(v as 'ALL' | CaseStatus)}
        >
          <SelectTrigger className="w-40 h-10">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">Alle statuser</SelectItem>
            {allStatuses.map((s) => (
              <SelectItem key={s} value={s}>
                {statusLabels[s]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">
            Saker
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              ({filtered.length})
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="space-y-2">
              {[1, 2, 3, 4, 5].map((i) => (
                <div
                  key={i}
                  className="h-14 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800"
                />
              ))}
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              Kunne ikke hente saker. Sjekk tilkoblingen og prøv igjen.
            </div>
          )}

          {!isLoading && !error && filtered.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FolderOpen className="mb-3 h-10 w-10 text-slate-300" />
              <p className="font-medium text-slate-600 dark:text-slate-400">
                {cases?.length === 0 ? 'Ingen saker ennå' : 'Ingen saker matcher søket'}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                {cases?.length === 0
                  ? 'Opprett din første sak for å komme i gang'
                  : 'Prøv å endre søket eller filteret'}
              </p>
              {cases?.length === 0 && (
                <Button className="mt-4" onClick={() => router.push('/cases/new')}>
                  <Plus className="h-4 w-4" />
                  Opprett sak
                </Button>
              )}
            </div>
          )}

          {!isLoading && !error && filtered.length > 0 && (
            <div className="space-y-2">
              {filtered.map((c) => (
                <CaseCard key={c.id} c={c} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
