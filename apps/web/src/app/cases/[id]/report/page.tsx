'use client';

import * as React from 'react';
import { useParams } from 'next/navigation';
import useSWR from 'swr';
import {
  FileBarChart,
  AlertTriangle,
  CheckCircle2,
  Printer,
  ShieldCheck,
  Info,
  RefreshCw,
} from 'lucide-react';
import { getReport, getReview, approveReport, generateReport } from '@/lib/api';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { ReportType } from '@/lib/types';

// ─── Report content renderer ──────────────────────────────────────────────────

interface ReportContentProps {
  content: Record<string, unknown> | null;
  type: ReportType;
}

function ReportSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mb-6">
      <h3 className="mb-2 text-base font-semibold border-b pb-2">{title}</h3>
      {children}
    </section>
  );
}

function ReportContent({ content, type }: ReportContentProps) {
  if (!content) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <FileBarChart className="mb-3 h-10 w-10 text-slate-300" />
        <p className="font-medium text-slate-600 dark:text-slate-400">
          {type === 'INTERNAL'
            ? 'Intern rapport ikke tilgjengelig'
            : 'Kunderapport ikke tilgjengelig'}
        </p>
        <p className="mt-1 text-sm text-muted-foreground">
          Rapporten genereres automatisk etter at analysen er fullført
        </p>
      </div>
    );
  }

  // Generic JSON-to-readable render
  const sections = Object.entries(content);

  return (
    <div className="prose prose-sm max-w-none dark:prose-invert">
      {sections.map(([key, value]) => {
        const title = key
          .replace(/_/g, ' ')
          .replace(/\b\w/g, (c) => c.toUpperCase());

        if (typeof value === 'string') {
          return (
            <ReportSection key={key} title={title}>
              <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                {value}
              </p>
            </ReportSection>
          );
        }

        if (Array.isArray(value)) {
          return (
            <ReportSection key={key} title={title}>
              <ul className="space-y-1 list-disc list-inside">
                {value.map((item, i) => (
                  <li key={i} className="text-sm text-slate-700 dark:text-slate-300">
                    {typeof item === 'object' ? JSON.stringify(item) : String(item)}
                  </li>
                ))}
              </ul>
            </ReportSection>
          );
        }

        if (typeof value === 'object' && value !== null) {
          return (
            <ReportSection key={key} title={title}>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-2">
                {Object.entries(value as Record<string, unknown>).map(
                  ([k, v]) => (
                    <React.Fragment key={k}>
                      <dt className="text-xs font-medium text-muted-foreground capitalize">
                        {k.replace(/_/g, ' ')}
                      </dt>
                      <dd className="text-sm">{String(v)}</dd>
                    </React.Fragment>
                  )
                )}
              </dl>
            </ReportSection>
          );
        }

        return (
          <ReportSection key={key} title={title}>
            <p className="text-sm">{String(value)}</p>
          </ReportSection>
        );
      })}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ReportPage() {
  const params = useParams<{ id: string }>();
  const caseId = params?.id ?? '';

  const {
    data: report,
    isLoading: reportLoading,
    mutate: mutateReport,
  } = useSWR(`report-${caseId}`, () => getReport(caseId).catch(() => null));

  const { data: review } = useSWR(
    `review-report-${caseId}`,
    () => getReview(caseId).catch(() => null)
  );

  const [approving, setApproving] = React.useState(false);
  const [generating, setGenerating] = React.useState(false);
  const [activeTab, setActiveTab] = React.useState<ReportType>('INTERNAL');

  const reviewCompleted = review?.status === 'COMPLETED';
  const isApproved = !!report?.approved_at;

  const handleApprove = async () => {
    setApproving(true);
    try {
      await approveReport(caseId);
      mutateReport();
    } finally {
      setApproving(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await generateReport(caseId);
      mutateReport();
    } finally {
      setGenerating(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="page-container">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="section-title">Vurderingsrapport</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Generert analyserapport for byggesaken
          </p>
        </div>
        <div className="flex items-center gap-2 print:hidden">
          {!report && !reportLoading && (
            <Button
              variant="outline"
              onClick={handleGenerate}
              loading={generating}
            >
              <RefreshCw className="h-4 w-4" />
              Generer rapport
            </Button>
          )}
          <Button variant="outline" onClick={handlePrint}>
            <Printer className="h-4 w-4" />
            Skriv ut
          </Button>
          {report && reviewCompleted && !isApproved && (
            <Button onClick={handleApprove} loading={approving}>
              <ShieldCheck className="h-4 w-4" />
              Godkjenn rapport
            </Button>
          )}
        </div>
      </div>

      {/* Disclaimer banner */}
      <div className="mb-6 flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-900 dark:bg-amber-950">
        <Info className="mt-0.5 h-5 w-5 shrink-0 text-amber-600 dark:text-amber-400" />
        <p className="text-sm text-amber-800 dark:text-amber-200">
          <span className="font-semibold">Viktig merknad:</span> Arkitekt er
          siste kontrollinstans. Dette er et beslutningsstøtteverktøy og
          erstatter ikke faglig skjønn. Alle funn skal verifiseres av ansvarlig
          arkitekt før rapporten godkjennes.
        </p>
      </div>

      {/* Approval status */}
      {isApproved && report && (
        <div className="mb-6 flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 px-4 py-3 dark:border-green-900 dark:bg-green-950">
          <CheckCircle2 className="h-5 w-5 shrink-0 text-green-600" />
          <div>
            <p className="text-sm font-medium text-green-800 dark:text-green-200">
              Rapport godkjent
            </p>
            <p className="text-xs text-green-700 dark:text-green-300">
              Godkjent {formatDateTime(report.approved_at!)}
            </p>
          </div>
          <Badge variant="success" className="ml-auto">
            Godkjent
          </Badge>
        </div>
      )}

      {!reviewCompleted && !isApproved && (
        <div className="mb-6 flex items-center gap-3 rounded-lg border border-yellow-200 bg-yellow-50 px-4 py-3 dark:border-yellow-900 dark:bg-yellow-950">
          <AlertTriangle className="h-5 w-5 shrink-0 text-yellow-600" />
          <p className="text-sm text-yellow-800 dark:text-yellow-200">
            Rapporten kan ikke godkjennes før arkitektreviewet er fullført.
          </p>
        </div>
      )}

      {reportLoading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-20 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800"
            />
          ))}
        </div>
      )}

      {!reportLoading && report && (
        <>
          {/* Summary stats */}
          {report.summary && (
            <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Card>
                <CardContent className="pt-4 pb-3">
                  <p className="text-xs text-muted-foreground">Totale avvik</p>
                  <p className="text-2xl font-bold">
                    {report.summary.total_deviations}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4 pb-3">
                  <p className="text-xs text-muted-foreground">Kritiske</p>
                  <p className="text-2xl font-bold text-red-600">
                    {report.summary.critical_count}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4 pb-3">
                  <p className="text-xs text-muted-foreground">Alvorlige</p>
                  <p className="text-2xl font-bold text-yellow-600">
                    {report.summary.major_count}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4 pb-3">
                  <p className="text-xs text-muted-foreground">
                    Samlet konfidens
                  </p>
                  <p className="text-2xl font-bold">
                    {Math.round(report.summary.overall_confidence * 100)}%
                  </p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Report content tabs */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Rapportinnhold</CardTitle>
              <CardDescription>
                Veksle mellom intern rapport (for arkitekt) og kunderapport
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs
                value={activeTab}
                onValueChange={(v) => setActiveTab(v as ReportType)}
              >
                <TabsList className="mb-4">
                  <TabsTrigger value="INTERNAL">Intern rapport</TabsTrigger>
                  <TabsTrigger value="CUSTOMER">Kunderapport</TabsTrigger>
                </TabsList>

                <TabsContent value="INTERNAL">
                  <ReportContent
                    content={report.internal_report}
                    type="INTERNAL"
                  />
                </TabsContent>

                <TabsContent value="CUSTOMER">
                  <ReportContent
                    content={report.customer_report}
                    type="CUSTOMER"
                  />
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          <p className="mt-4 text-center text-xs text-muted-foreground print:block">
            Generert {formatDateTime(report.generated_at)} · ByggSjekk
            vurderingsverktøy · Endelig godkjenning av ansvarlig arkitekt
            påkrevd
          </p>
        </>
      )}

      {!reportLoading && !report && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <FileBarChart className="mb-3 h-10 w-10 text-slate-300" />
            <p className="font-medium text-slate-600 dark:text-slate-400">
              Ingen rapport tilgjengelig
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              Last opp dokumenter og vent på analyse, eller generer rapporten
              manuelt
            </p>
            <Button className="mt-4" onClick={handleGenerate} loading={generating}>
              <RefreshCw className="h-4 w-4" />
              Generer rapport
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
