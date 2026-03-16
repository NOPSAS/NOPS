'use client';

import * as React from 'react';
import { useParams } from 'next/navigation';
import useSWR from 'swr';
import { getCase } from '@/lib/api';
import { CaseSidebar } from '@/components/layout/sidebar';
import type { PropertyCase } from '@/lib/types';

// Context so child pages can consume the case without re-fetching
interface CaseContextValue {
  caseData: PropertyCase | null;
  isLoading: boolean;
  mutate: () => void;
}

export const CaseContext = React.createContext<CaseContextValue>({
  caseData: null,
  isLoading: true,
  mutate: () => {},
});

export function useCaseContext(): CaseContextValue {
  return React.useContext(CaseContext);
}

export default function CaseDetailLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams<{ id: string }>();
  const id = params?.id;

  const {
    data: caseData,
    isLoading,
    mutate,
  } = useSWR(id ? `case-${id}` : null, () => getCase(id!));

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-4rem)]">
        {/* Skeleton sidebar */}
        <div className="w-64 shrink-0 border-r border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900 animate-pulse">
          <div className="p-4 space-y-3">
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
            <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded w-1/2" />
            <div className="h-6 bg-slate-100 dark:bg-slate-800 rounded w-20 mt-2" />
          </div>
          <div className="px-3 space-y-1">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div
                key={i}
                className="h-9 bg-slate-100 dark:bg-slate-800 rounded-md"
              />
            ))}
          </div>
        </div>
        {/* Skeleton content */}
        <div className="flex-1 overflow-y-auto p-8 space-y-4">
          <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-1/3" />
          <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded w-2/3" />
          <div className="grid grid-cols-3 gap-4 mt-6">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-28 bg-slate-100 dark:bg-slate-800 rounded-lg"
              />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <div className="text-center">
          <p className="text-lg font-medium text-slate-900 dark:text-white">
            Sak ikke funnet
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            Saken finnes ikke eller du har ikke tilgang.
          </p>
        </div>
      </div>
    );
  }

  return (
    <CaseContext.Provider value={{ caseData, isLoading, mutate }}>
      <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
        <CaseSidebar caseData={caseData} />
        <div className="flex-1 overflow-y-auto">{children}</div>
      </div>
    </CaseContext.Provider>
  );
}
