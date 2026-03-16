'use client';

import * as React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  FileText,
  AlertTriangle,
  MapPin,
  Building,
  ArrowRight,
  Upload,
  ClipboardCheck,
  Clock,
  ExternalLink,
} from 'lucide-react';
import { useCaseContext } from './layout';
import { formatDate } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import type { CaseStatus, CustomerType } from '@/lib/types';

function statusLabel(s: CaseStatus): string {
  const m: Record<CaseStatus, string> = {
    DRAFT: 'Utkast',
    INTAKE: 'Inntak',
    PROCESSING: 'Behandles',
    ANALYSIS: 'Analyse',
    REVIEW: 'Under review',
    COMPLETED: 'Fullført',
    ARCHIVED: 'Arkivert',
  };
  return m[s] ?? s;
}

function statusVariant(s: CaseStatus) {
  switch (s) {
    case 'COMPLETED': return 'success' as const;
    case 'REVIEW': return 'warning' as const;
    case 'PROCESSING':
    case 'ANALYSIS': return 'info' as const;
    case 'DRAFT':
    case 'INTAKE': return 'secondary' as const;
    default: return 'muted' as const;
  }
}

function customerTypeLabel(t: CustomerType): string {
  const m: Record<CustomerType, string> = {
    PRIVATE: 'Privat',
    PROFESSIONAL: 'Næringsliv',
    MUNICIPALITY: 'Kommune',
  };
  return m[t] ?? t;
}

interface QuickActionProps {
  href: string;
  icon: React.ReactNode;
  label: string;
  description: string;
}

function QuickAction({ href, icon, label, description }: QuickActionProps) {
  return (
    <Link
      href={href}
      className="group flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-4 transition-all hover:border-blue-300 hover:shadow-sm dark:border-slate-700 dark:bg-slate-900"
    >
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400">
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground truncate">{description}</p>
      </div>
      <ArrowRight className="h-4 w-4 text-slate-400 transition-transform group-hover:translate-x-0.5 shrink-0" />
    </Link>
  );
}

export default function CaseOverviewPage() {
  const router = useRouter();
  const { caseData } = useCaseContext();

  if (!caseData) return null;

  const base = `/cases/${caseData.id}`;
  const { property } = caseData;

  return (
    <div className="page-container">
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="section-title">{property.street_address}</h1>
            <Badge variant={statusVariant(caseData.status)}>
              {statusLabel(caseData.status)}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground flex items-center gap-1.5">
            <MapPin className="h-3.5 w-3.5" />
            {property.postal_code} {property.municipality}
          </p>
        </div>
        <p className="text-xs text-muted-foreground self-end">
          Oppdatert {formatDate(caseData.updated_at)}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Property info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Building className="h-4 w-4 text-muted-foreground" />
                Eiendomsinformasjon
              </CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
                <div>
                  <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Adresse
                  </dt>
                  <dd className="mt-0.5 font-medium">{property.street_address}</dd>
                </div>
                <div>
                  <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Kommune
                  </dt>
                  <dd className="mt-0.5">{property.municipality}</dd>
                </div>
                <div>
                  <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Postnummer
                  </dt>
                  <dd className="mt-0.5">{property.postal_code}</dd>
                </div>
                {property.gnr != null && (
                  <div>
                    <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                      Gnr/Bnr
                    </dt>
                    <dd className="mt-0.5 flex items-center gap-2">
                      {property.gnr}/{property.bnr}
                      {(property as { kommunenummer?: string }).kommunenummer && (
                        <Link
                          href={`/property?knr=${(property as { kommunenummer?: string }).kommunenummer}&gnr=${property.gnr}&bnr=${property.bnr}`}
                          className="inline-flex items-center gap-0.5 text-xs text-blue-600 hover:underline dark:text-blue-400"
                        >
                          <ExternalLink className="h-3 w-3" />
                          Eiendomsoppslag
                        </Link>
                      )}
                    </dd>
                  </div>
                )}
                <div>
                  <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Kundetype
                  </dt>
                  <dd className="mt-0.5">
                    {customerTypeLabel(caseData.customer_type)}
                  </dd>
                </div>
                {caseData.intake_source && (
                  <div>
                    <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                      Inntakskilde
                    </dt>
                    <dd className="mt-0.5">{caseData.intake_source}</dd>
                  </div>
                )}
              </dl>
            </CardContent>
          </Card>

          {/* Quick actions */}
          <div>
            <h2 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
              Hurtighandlinger
            </h2>
            <div className="grid gap-2 sm:grid-cols-2">
              <QuickAction
                href={`${base}/documents`}
                icon={<Upload className="h-5 w-5" />}
                label="Last opp dokumenter"
                description="Legg til tegninger og bilder"
              />
              <QuickAction
                href={`${base}/deviations`}
                icon={<AlertTriangle className="h-5 w-5" />}
                label="Se avvik"
                description="Gjennomgå oppdagede avvik"
              />
              <QuickAction
                href={`${base}/review`}
                icon={<ClipboardCheck className="h-5 w-5" />}
                label="Start review"
                description="Arkitektgjennomgang av saken"
              />
              <QuickAction
                href={`${base}/report`}
                icon={<FileText className="h-5 w-5" />}
                label="Se rapport"
                description="Vurderingsrapport for saken"
              />
            </div>
          </div>
        </div>

        {/* Right column — stats */}
        <div className="space-y-4">
          <Card>
            <CardContent className="pt-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-slate-400" />
                  <span className="text-sm font-medium">Dokumenter</span>
                </div>
                <span className="text-2xl font-bold tabular-nums">
                  {caseData.document_count ?? 0}
                </span>
              </div>
              <div className="h-px bg-border" />
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-orange-400" />
                  <span className="text-sm font-medium">Totale avvik</span>
                </div>
                <span className="text-2xl font-bold tabular-nums">
                  {caseData.deviation_count ?? 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-red-400" />
                  <span className="text-sm font-medium">Åpne avvik</span>
                </div>
                <span className="text-2xl font-bold tabular-nums text-red-600">
                  {caseData.open_deviation_count ?? 0}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                Tidslinje
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between text-muted-foreground">
                <span>Opprettet</span>
                <span>{formatDate(caseData.created_at)}</span>
              </div>
              <div className="flex justify-between text-muted-foreground">
                <span>Sist oppdatert</span>
                <span>{formatDate(caseData.updated_at)}</span>
              </div>
            </CardContent>
          </Card>

          <Button
            className="w-full"
            variant="outline"
            onClick={() => router.push(`${base}/documents`)}
          >
            <Upload className="h-4 w-4" />
            Last opp tegninger
          </Button>
        </div>
      </div>
    </div>
  );
}
