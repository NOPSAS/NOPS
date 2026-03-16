'use client';

import * as React from 'react';
import { useParams } from 'next/navigation';
import useSWR from 'swr';
import { AlertTriangle, Filter, Save, X, ChevronDown } from 'lucide-react';
import { getDeviations, updateDeviation } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ConfidenceIndicator } from '@/components/confidence-indicator';
import type {
  Deviation,
  DeviationCategory,
  DeviationSeverity,
  DeviationStatus,
} from '@/lib/types';

// ─── Label maps ───────────────────────────────────────────────────────────────

const categoryLabels: Record<DeviationCategory, string> = {
  [DeviationCategory.ROOM_DEFINITION_CHANGE]: 'Romdefinisjon endret',
  [DeviationCategory.BEDROOM_UTILITY_DISCREPANCY]: 'Soverom/bruksrom-avvik',
  [DeviationCategory.DOOR_PLACEMENT_CHANGE]: 'Dørplassering endret',
  [DeviationCategory.WINDOW_PLACEMENT_CHANGE]: 'Vindusplassering endret',
  [DeviationCategory.BALCONY_TERRACE_DISCREPANCY]: 'Balkong/terrasse-avvik',
  [DeviationCategory.ADDITION_DETECTED]: 'Tilbygg oppdaget',
  [DeviationCategory.UNDERBUILDING_DETECTED]: 'Underbygging oppdaget',
  [DeviationCategory.UNINSPECTED_AREA]: 'Udokumentert areal',
  [DeviationCategory.USE_CHANGE_INDICATION]: 'Bruksendring indikert',
  [DeviationCategory.MARKETED_FUNCTION_DISCREPANCY]: 'Markedsført funksjon avviker',
};

const severityLabels: Record<DeviationSeverity, string> = {
  CRITICAL: 'Kritisk',
  MAJOR: 'Alvorlig',
  MINOR: 'Mindre',
  INFO: 'Info',
};

const statusLabels: Record<DeviationStatus, string> = {
  OPEN: 'Åpen',
  ACKNOWLEDGED: 'Bekreftet',
  DISMISSED: 'Avvist',
  RESOLVED: 'Løst',
};

function severityVariant(
  s: DeviationSeverity
): 'destructive' | 'warning' | 'secondary' | 'muted' {
  switch (s) {
    case 'CRITICAL': return 'destructive';
    case 'MAJOR': return 'warning';
    case 'MINOR': return 'secondary';
    default: return 'muted';
  }
}

function statusVariant(
  s: DeviationStatus
): 'destructive' | 'warning' | 'success' | 'muted' {
  switch (s) {
    case 'OPEN': return 'destructive';
    case 'ACKNOWLEDGED': return 'warning';
    case 'RESOLVED': return 'success';
    default: return 'muted';
  }
}

// ─── Inline-edit card ─────────────────────────────────────────────────────────

interface DeviationCardProps {
  deviation: Deviation;
  onSave: (id: string, note: string, status: DeviationStatus) => Promise<void>;
}

function DeviationCard({ deviation, onSave }: DeviationCardProps) {
  const [editing, setEditing] = React.useState(false);
  const [note, setNote] = React.useState(deviation.architect_note ?? '');
  const [status, setStatus] = React.useState<DeviationStatus>(deviation.status);
  const [saving, setSaving] = React.useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(deviation.id, note, status);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setNote(deviation.architect_note ?? '');
    setStatus(deviation.status);
    setEditing(false);
  };

  return (
    <Card
      className={`transition-shadow ${
        editing ? 'shadow-md border-blue-200 dark:border-blue-800' : ''
      }`}
    >
      <CardContent className="pt-4">
        {/* Top row */}
        <div className="flex flex-wrap items-start justify-between gap-2 mb-3">
          <div className="flex flex-wrap gap-1.5">
            <Badge variant="outline" className="text-xs">
              {categoryLabels[deviation.category] ?? deviation.category}
            </Badge>
            <Badge variant={severityVariant(deviation.severity)}>
              {severityLabels[deviation.severity]}
            </Badge>
            <Badge variant={statusVariant(deviation.status)}>
              {statusLabels[deviation.status]}
            </Badge>
          </div>
          <ConfidenceIndicator
            confidence={deviation.confidence}
            showLabel
          />
        </div>

        {/* Description */}
        <p className="text-sm text-slate-800 dark:text-slate-200 mb-2 leading-relaxed">
          {deviation.description}
        </p>

        {deviation.location && (
          <p className="text-xs text-muted-foreground mb-3">
            <span className="font-medium">Lokasjon:</span> {deviation.location}
          </p>
        )}

        {/* Edit section */}
        {editing ? (
          <div className="space-y-3 mt-3 border-t pt-3">
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">
                Arkitektnotat
              </label>
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                rows={3}
                placeholder="Legg til notat om dette avviket..."
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">
                Status
              </label>
              <Select
                value={status}
                onValueChange={(v) => setStatus(v as DeviationStatus)}
              >
                <SelectTrigger className="h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(Object.entries(statusLabels) as [DeviationStatus, string][]).map(
                    ([v, l]) => (
                      <SelectItem key={v} value={v}>
                        {l}
                      </SelectItem>
                    )
                  )}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <Button size="sm" onClick={handleSave} loading={saving}>
                <Save className="h-3.5 w-3.5" />
                Lagre
              </Button>
              <Button size="sm" variant="outline" onClick={handleCancel}>
                <X className="h-3.5 w-3.5" />
                Avbryt
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex items-start justify-between mt-3 border-t pt-3">
            <div className="flex-1 min-w-0">
              {deviation.architect_note ? (
                <p className="text-xs text-muted-foreground">
                  <span className="font-medium">Notat:</span>{' '}
                  {deviation.architect_note}
                </p>
              ) : (
                <p className="text-xs text-muted-foreground italic">
                  Ingen arkitektnotat
                </p>
              )}
            </div>
            <Button
              size="sm"
              variant="ghost"
              className="text-xs ml-2 shrink-0"
              onClick={() => setEditing(true)}
            >
              Rediger
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

type FilterSeverity = 'ALL' | DeviationSeverity;
type FilterCategory = 'ALL' | DeviationCategory;
type FilterStatus = 'ALL' | DeviationStatus;

export default function DeviationsPage() {
  const params = useParams<{ id: string }>();
  const caseId = params?.id ?? '';

  const { data: deviations, isLoading, mutate } = useSWR(
    `deviations-${caseId}`,
    () => getDeviations(caseId)
  );

  const [filterSeverity, setFilterSeverity] =
    React.useState<FilterSeverity>('ALL');
  const [filterCategory, setFilterCategory] =
    React.useState<FilterCategory>('ALL');
  const [filterStatus, setFilterStatus] = React.useState<FilterStatus>('ALL');

  const filtered = React.useMemo(() => {
    if (!deviations) return [];
    return deviations.filter((d) => {
      if (filterSeverity !== 'ALL' && d.severity !== filterSeverity)
        return false;
      if (filterCategory !== 'ALL' && d.category !== filterCategory)
        return false;
      if (filterStatus !== 'ALL' && d.status !== filterStatus) return false;
      return true;
    });
  }, [deviations, filterSeverity, filterCategory, filterStatus]);

  const handleSave = async (
    id: string,
    note: string,
    status: DeviationStatus
  ) => {
    await updateDeviation(caseId, id, { architect_note: note, status });
    mutate();
  };

  const stats = React.useMemo(() => {
    if (!deviations) return null;
    return {
      critical: deviations.filter((d) => d.severity === 'CRITICAL').length,
      major: deviations.filter((d) => d.severity === 'MAJOR').length,
      minor: deviations.filter((d) => d.severity === 'MINOR').length,
      open: deviations.filter((d) => d.status === 'OPEN').length,
    };
  }, [deviations]);

  return (
    <div className="page-container">
      <div className="mb-6">
        <h1 className="section-title">Avvik</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Oppdagede avvik mellom godkjente tegninger og nåværende tilstand
        </p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="mb-6 flex flex-wrap gap-3">
          <div className="flex items-center gap-1.5 rounded-full border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-medium text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
            <AlertTriangle className="h-3.5 w-3.5" />
            {stats.critical} kritiske
          </div>
          <div className="flex items-center gap-1.5 rounded-full border border-yellow-200 bg-yellow-50 px-3 py-1.5 text-xs font-medium text-yellow-700 dark:border-yellow-900 dark:bg-yellow-950 dark:text-yellow-300">
            {stats.major} alvorlige
          </div>
          <div className="flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
            {stats.minor} mindre
          </div>
          <div className="flex items-center gap-1.5 rounded-full border border-orange-200 bg-orange-50 px-3 py-1.5 text-xs font-medium text-orange-700 dark:border-orange-900 dark:bg-orange-950 dark:text-orange-300">
            {stats.open} åpne
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <Filter className="h-4 w-4" />
          <span>Filter:</span>
        </div>

        <Select
          value={filterSeverity}
          onValueChange={(v) => setFilterSeverity(v as FilterSeverity)}
        >
          <SelectTrigger className="h-8 w-36">
            <SelectValue placeholder="Alvorlighet" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">Alle alvorligheter</SelectItem>
            {(Object.entries(severityLabels) as [DeviationSeverity, string][]).map(
              ([v, l]) => (
                <SelectItem key={v} value={v}>{l}</SelectItem>
              )
            )}
          </SelectContent>
        </Select>

        <Select
          value={filterCategory}
          onValueChange={(v) => setFilterCategory(v as FilterCategory)}
        >
          <SelectTrigger className="h-8 w-44">
            <SelectValue placeholder="Kategori" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">Alle kategorier</SelectItem>
            {(Object.entries(categoryLabels) as [DeviationCategory, string][]).map(
              ([v, l]) => (
                <SelectItem key={v} value={v}>{l}</SelectItem>
              )
            )}
          </SelectContent>
        </Select>

        <Select
          value={filterStatus}
          onValueChange={(v) => setFilterStatus(v as FilterStatus)}
        >
          <SelectTrigger className="h-8 w-36">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">Alle statuser</SelectItem>
            {(Object.entries(statusLabels) as [DeviationStatus, string][]).map(
              ([v, l]) => (
                <SelectItem key={v} value={v}>{l}</SelectItem>
              )
            )}
          </SelectContent>
        </Select>

        {(filterSeverity !== 'ALL' ||
          filterCategory !== 'ALL' ||
          filterStatus !== 'ALL') && (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 text-xs"
            onClick={() => {
              setFilterSeverity('ALL');
              setFilterCategory('ALL');
              setFilterStatus('ALL');
            }}
          >
            <X className="h-3.5 w-3.5" />
            Fjern filter
          </Button>
        )}

        <span className="ml-auto text-xs text-muted-foreground">
          {filtered.length} av {deviations?.length ?? 0} avvik
        </span>
      </div>

      {/* List */}
      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-32 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800"
            />
          ))}
        </div>
      )}

      {!isLoading && filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <AlertTriangle className="mb-3 h-10 w-10 text-slate-300" />
          <p className="font-medium text-slate-600 dark:text-slate-400">
            {deviations?.length === 0
              ? 'Ingen avvik oppdaget'
              : 'Ingen avvik matcher filteret'}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            {deviations?.length === 0
              ? 'Avvik oppdages automatisk etter at dokumenter er behandlet'
              : 'Prøv å endre filterinnstillingene'}
          </p>
        </div>
      )}

      {!isLoading && filtered.length > 0 && (
        <div className="space-y-3">
          {filtered.map((d) => (
            <DeviationCard key={d.id} deviation={d} onSave={handleSave} />
          ))}
        </div>
      )}
    </div>
  );
}
