'use client';

import * as React from 'react';
import { useParams } from 'next/navigation';
import useSWR from 'swr';
import {
  ClipboardCheck,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Save,
  Plus,
  User,
} from 'lucide-react';
import { getReview, getDeviations, createReview, updateReview, updateDeviation } from '@/lib/api';
import { formatDateTime } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { ConfidenceIndicator } from '@/components/confidence-indicator';
import type { Deviation, DeviationSeverity, DeviationStatus, ReviewStatus } from '@/lib/types';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function reviewStatusLabel(s: ReviewStatus): string {
  switch (s) {
    case 'PENDING': return 'Venter';
    case 'IN_PROGRESS': return 'Pågår';
    case 'COMPLETED': return 'Fullført';
    default: return s;
  }
}

function reviewStatusVariant(
  s: ReviewStatus
): 'muted' | 'warning' | 'success' {
  switch (s) {
    case 'PENDING': return 'muted';
    case 'IN_PROGRESS': return 'warning';
    case 'COMPLETED': return 'success';
    default: return 'muted';
  }
}

function severityLabel(s: DeviationSeverity): string {
  const m: Record<DeviationSeverity, string> = {
    CRITICAL: 'Kritisk',
    MAJOR: 'Alvorlig',
    MINOR: 'Mindre',
    INFO: 'Info',
  };
  return m[s];
}

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

// ─── Deviation review row ─────────────────────────────────────────────────────

interface ReviewDeviationRowProps {
  deviation: Deviation;
  onApprove: (id: string) => Promise<void>;
  onDismiss: (id: string) => Promise<void>;
  disabled: boolean;
}

function ReviewDeviationRow({
  deviation,
  onApprove,
  onDismiss,
  disabled,
}: ReviewDeviationRowProps) {
  const [loading, setLoading] = React.useState<'approve' | 'dismiss' | null>(null);

  const handleApprove = async () => {
    setLoading('approve');
    try { await onApprove(deviation.id); } finally { setLoading(null); }
  };

  const handleDismiss = async () => {
    setLoading('dismiss');
    try { await onDismiss(deviation.id); } finally { setLoading(null); }
  };

  const isResolved =
    deviation.status === 'RESOLVED' || deviation.status === 'DISMISSED';

  return (
    <div
      className={`flex items-start gap-4 rounded-lg border p-4 transition-colors ${
        isResolved
          ? 'border-slate-200 bg-slate-50 opacity-70 dark:border-slate-700 dark:bg-slate-800/50'
          : 'border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900'
      }`}
    >
      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex flex-wrap gap-1.5">
          <Badge variant={severityVariant(deviation.severity)}>
            {severityLabel(deviation.severity)}
          </Badge>
          {isResolved && (
            <Badge variant={deviation.status === 'RESOLVED' ? 'success' : 'muted'}>
              {deviation.status === 'RESOLVED' ? 'Godkjent' : 'Avvist'}
            </Badge>
          )}
        </div>
        <p className="text-sm leading-relaxed">{deviation.description}</p>
        {deviation.location && (
          <p className="text-xs text-muted-foreground">
            Lokasjon: {deviation.location}
          </p>
        )}
        <ConfidenceIndicator confidence={deviation.confidence} showLabel />
        {deviation.architect_note && (
          <p className="text-xs text-muted-foreground mt-1">
            <span className="font-medium">Notat:</span> {deviation.architect_note}
          </p>
        )}
      </div>

      {!isResolved && (
        <div className="flex shrink-0 flex-col gap-2">
          <Button
            size="sm"
            variant="success"
            onClick={handleApprove}
            disabled={disabled || loading !== null}
            loading={loading === 'approve'}
            className="text-xs"
          >
            <CheckCircle2 className="h-3.5 w-3.5" />
            Godkjenn
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleDismiss}
            disabled={disabled || loading !== null}
            loading={loading === 'dismiss'}
            className="text-xs"
          >
            <XCircle className="h-3.5 w-3.5" />
            Avvis
          </Button>
        </div>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ReviewPage() {
  const params = useParams<{ id: string }>();
  const caseId = params?.id ?? '';

  const {
    data: review,
    isLoading: reviewLoading,
    mutate: mutateReview,
  } = useSWR(`review-${caseId}`, () => getReview(caseId).catch(() => null));

  const {
    data: deviations,
    isLoading: deviationsLoading,
    mutate: mutateDeviations,
  } = useSWR(`deviations-review-${caseId}`, () => getDeviations(caseId));

  const [comments, setComments] = React.useState('');
  const [savingComments, setSavingComments] = React.useState(false);
  const [completing, setCompleting] = React.useState(false);
  const [starting, setStarting] = React.useState(false);

  // Sync comments from fetched review
  React.useEffect(() => {
    if (review?.comments) setComments(review.comments);
  }, [review?.comments]);

  const handleStartReview = async () => {
    setStarting(true);
    try {
      await createReview(caseId);
      mutateReview();
    } finally {
      setStarting(false);
    }
  };

  const handleSaveComments = async () => {
    setSavingComments(true);
    try {
      await updateReview(caseId, { comments, status: 'IN_PROGRESS' });
      mutateReview();
    } finally {
      setSavingComments(false);
    }
  };

  const handleComplete = async () => {
    setCompleting(true);
    try {
      await updateReview(caseId, { status: 'COMPLETED', comments });
      mutateReview();
    } finally {
      setCompleting(false);
    }
  };

  const handleApprove = async (devId: string) => {
    await updateDeviation(caseId, devId, { status: 'RESOLVED' });
    mutateDeviations();
  };

  const handleDismiss = async (devId: string) => {
    await updateDeviation(caseId, devId, { status: 'DISMISSED' });
    mutateDeviations();
  };

  const isLoading = reviewLoading || deviationsLoading;
  const isCompleted = review?.status === 'COMPLETED';
  const openDeviations = deviations?.filter(
    (d) => d.status === 'OPEN' || d.status === 'ACKNOWLEDGED'
  ) ?? [];
  const resolvedDeviations = deviations?.filter(
    (d) => d.status === 'RESOLVED' || d.status === 'DISMISSED'
  ) ?? [];

  return (
    <div className="page-container">
      <div className="mb-6">
        <h1 className="section-title">Arkitektreview</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Gjennomgå og godkjenn oppdagede avvik
        </p>
      </div>

      {isLoading && (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div
              key={i}
              className="h-24 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800"
            />
          ))}
        </div>
      )}

      {!isLoading && !review && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <ClipboardCheck className="mb-3 h-10 w-10 text-slate-300" />
            <p className="font-medium">Ingen review startet</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Start en review for å gjennomgå avvikene i denne saken
            </p>
            <Button className="mt-4" onClick={handleStartReview} loading={starting}>
              <Plus className="h-4 w-4" />
              Start review
            </Button>
          </CardContent>
        </Card>
      )}

      {!isLoading && review && (
        <div className="space-y-6">
          {/* Review status card */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Review-status</CardTitle>
                <Badge variant={reviewStatusVariant(review.status)}>
                  {reviewStatusLabel(review.status)}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Startet
                  </p>
                  <p className="mt-0.5">
                    {review.started_at
                      ? formatDateTime(review.started_at)
                      : '—'}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Fullført
                  </p>
                  <p className="mt-0.5">
                    {review.completed_at
                      ? formatDateTime(review.completed_at)
                      : '—'}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Gjenstående
                  </p>
                  <p className="mt-0.5 font-semibold">
                    {openDeviations.length} åpne avvik
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Deviation review list */}
          <div>
            <h2 className="mb-3 text-sm font-semibold flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-orange-500" />
              Åpne avvik ({openDeviations.length})
            </h2>
            {openDeviations.length === 0 ? (
              <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-muted-foreground dark:border-slate-700 dark:bg-slate-800">
                Alle avvik er gjennomgått
              </div>
            ) : (
              <div className="space-y-2">
                {openDeviations.map((d) => (
                  <ReviewDeviationRow
                    key={d.id}
                    deviation={d}
                    onApprove={handleApprove}
                    onDismiss={handleDismiss}
                    disabled={isCompleted}
                  />
                ))}
              </div>
            )}
          </div>

          {resolvedDeviations.length > 0 && (
            <div>
              <h2 className="mb-3 text-sm font-semibold flex items-center gap-2 text-muted-foreground">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Gjennomgåtte avvik ({resolvedDeviations.length})
              </h2>
              <div className="space-y-2">
                {resolvedDeviations.map((d) => (
                  <ReviewDeviationRow
                    key={d.id}
                    deviation={d}
                    onApprove={handleApprove}
                    onDismiss={handleDismiss}
                    disabled={true}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Comments */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Arkitektkommentarer</CardTitle>
              <CardDescription>
                Samlet vurdering og merknader til rapporten
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <textarea
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                disabled={isCompleted}
                rows={4}
                placeholder="Skriv inn overordnet vurdering og kommentarer..."
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60 disabled:cursor-not-allowed"
              />
              {!isCompleted && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleSaveComments}
                  loading={savingComments}
                >
                  <Save className="h-3.5 w-3.5" />
                  Lagre kommentarer
                </Button>
              )}
            </CardContent>
          </Card>

          {/* Complete button */}
          {!isCompleted && (
            <div className="flex items-center justify-between rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 dark:border-blue-900 dark:bg-blue-950">
              <div>
                <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                  Klar til å fullføre?
                </p>
                <p className="text-xs text-blue-700 dark:text-blue-300">
                  {openDeviations.length > 0
                    ? `${openDeviations.length} avvik gjenstår å gjennomgå`
                    : 'Alle avvik er gjennomgått'}
                </p>
              </div>
              <Button
                onClick={handleComplete}
                loading={completing}
                disabled={openDeviations.length > 0}
              >
                <ClipboardCheck className="h-4 w-4" />
                Fullfør review
              </Button>
            </div>
          )}

          {/* Audit log */}
          {review.audit_log && review.audit_log.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  Revisjonslogg
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="space-y-3">
                  {review.audit_log.map((entry, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm">
                      <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800">
                        <User className="h-3.5 w-3.5 text-slate-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
                          <span className="font-medium">{entry.user_name}</span>
                          <span className="text-xs text-muted-foreground">
                            {entry.action}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {formatDateTime(entry.timestamp)}
                          </span>
                        </div>
                        {entry.details && (
                          <p className="mt-0.5 text-xs text-muted-foreground">
                            {entry.details}
                          </p>
                        )}
                      </div>
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
