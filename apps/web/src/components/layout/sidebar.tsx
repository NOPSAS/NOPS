'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutGrid,
  FileText,
  Map,
  AlertTriangle,
  ClipboardCheck,
  FileBarChart,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import type { CaseStatus, PropertyCase } from '@/lib/types';

interface SidebarProps {
  caseData: PropertyCase;
}

interface SidebarLinkDef {
  href: string;
  label: string;
  icon: React.ReactNode;
}

function caseStatusVariant(
  status: CaseStatus
): 'default' | 'success' | 'warning' | 'muted' | 'info' | 'destructive' | 'secondary' {
  switch (status) {
    case 'COMPLETED':
      return 'success';
    case 'REVIEW':
      return 'warning';
    case 'PROCESSING':
    case 'ANALYSIS':
      return 'info';
    case 'ARCHIVED':
      return 'muted';
    case 'DRAFT':
    case 'INTAKE':
      return 'secondary';
    default:
      return 'muted';
  }
}

function caseStatusLabel(status: CaseStatus): string {
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

export function CaseSidebar({ caseData }: SidebarProps) {
  const pathname = usePathname();
  const base = `/cases/${caseData.id}`;

  const links: SidebarLinkDef[] = [
    {
      href: base,
      label: 'Oversikt',
      icon: <LayoutGrid className="h-4 w-4" />,
    },
    {
      href: `${base}/documents`,
      label: 'Dokumenter',
      icon: <FileText className="h-4 w-4" />,
    },
    {
      href: `${base}/plan`,
      label: 'Plan',
      icon: <Map className="h-4 w-4" />,
    },
    {
      href: `${base}/deviations`,
      label: 'Avvik',
      icon: <AlertTriangle className="h-4 w-4" />,
    },
    {
      href: `${base}/review`,
      label: 'Review',
      icon: <ClipboardCheck className="h-4 w-4" />,
    },
    {
      href: `${base}/report`,
      label: 'Rapport',
      icon: <FileBarChart className="h-4 w-4" />,
    },
  ];

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
      {/* Case title + status */}
      <div className="border-b border-slate-200 p-4 dark:border-slate-700">
        <p className="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Sak
        </p>
        <h2 className="text-sm font-semibold text-slate-900 dark:text-white leading-tight break-words">
          {caseData.property.street_address}
        </h2>
        <p className="mt-0.5 text-xs text-muted-foreground">
          {caseData.property.postal_code} {caseData.property.municipality}
        </p>
        <div className="mt-2">
          <Badge variant={caseStatusVariant(caseData.status)}>
            {caseStatusLabel(caseData.status)}
          </Badge>
        </div>
      </div>

      {/* Nav links */}
      <nav className="flex flex-col gap-0.5 p-3" aria-label="Saksnavigasjon">
        {links.map((link) => {
          // Exact match for overview, prefix match for sub-pages
          const isActive =
            link.href === base
              ? pathname === base
              : pathname.startsWith(link.href);

          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                'flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100'
              )}
              aria-current={isActive ? 'page' : undefined}
            >
              <span
                className={cn(
                  'shrink-0',
                  isActive
                    ? 'text-blue-600 dark:text-blue-400'
                    : 'text-slate-400 dark:text-slate-500'
                )}
              >
                {link.icon}
              </span>
              {link.label}
            </Link>
          );
        })}
      </nav>

      {/* Case metadata footer */}
      <div className="mt-auto border-t border-slate-200 p-4 dark:border-slate-700">
        {caseData.property.gnr != null && (
          <p className="text-xs text-muted-foreground">
            Gnr/Bnr: {caseData.property.gnr}/{caseData.property.bnr}
          </p>
        )}
        {caseData.deviation_count !== undefined && (
          <p className="text-xs text-muted-foreground mt-0.5">
            {caseData.open_deviation_count ?? 0} åpne avvik
          </p>
        )}
      </div>
    </aside>
  );
}
