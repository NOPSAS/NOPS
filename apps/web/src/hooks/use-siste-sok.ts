'use client';

import * as React from 'react';

const STORAGE_KEY = 'byggsjekk_siste_sok';
const MAX_SOK = 8;

export interface SisteSøk {
  knr: string;
  gnr: string;
  bnr: string;
  adresse: string;
  timestamp: number;
}

function lesFromStorage(): SisteSøk[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as SisteSøk[];
  } catch {
    return [];
  }
}

function skrivToStorage(søk: SisteSøk[]): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(søk));
  } catch {
    // ignore quota errors
  }
}

export function useSisteSøk() {
  const [søk, setSøk] = React.useState<SisteSøk[]>([]);

  // Read from localStorage on mount (client-side only)
  React.useEffect(() => {
    setSøk(lesFromStorage());
  }, []);

  const leggTil = React.useCallback((nyttSøk: SisteSøk) => {
    setSøk((prev) => {
      // Deduplicate on knr+gnr+bnr, remove existing match
      const filtrert = prev.filter(
        (s) => !(s.knr === nyttSøk.knr && s.gnr === nyttSøk.gnr && s.bnr === nyttSøk.bnr)
      );
      // Newest first, cap at MAX_SOK
      const oppdatert = [nyttSøk, ...filtrert].slice(0, MAX_SOK);
      skrivToStorage(oppdatert);
      return oppdatert;
    });
  }, []);

  const fjern = React.useCallback((knr: string, gnr: string, bnr: string) => {
    setSøk((prev) => {
      const oppdatert = prev.filter(
        (s) => !(s.knr === knr && s.gnr === gnr && s.bnr === bnr)
      );
      skrivToStorage(oppdatert);
      return oppdatert;
    });
  }, []);

  const tøm = React.useCallback(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem(STORAGE_KEY);
    }
    setSøk([]);
  }, []);

  return { søk, leggTil, fjern, tøm };
}
