'use client';

import * as React from 'react';

const STORAGE_KEY = 'byggsjekk_favoritter';

export interface Favoritt {
  knr: string;
  gnr: string;
  bnr: string;
  adresse: string;
  lagretDato: string; // ISO string
}

function lesFromStorage(): Favoritt[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as Favoritt[];
  } catch {
    return [];
  }
}

function skrivToStorage(favoritter: Favoritt[]): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(favoritter));
  } catch {
    // ignore quota errors
  }
}

export function useFavoritter() {
  const [favoritter, setFavoritter] = React.useState<Favoritt[]>([]);

  // Read from localStorage on mount (client-side only)
  React.useEffect(() => {
    setFavoritter(lesFromStorage());
  }, []);

  const erFavoritt = React.useCallback(
    (knr: string, gnr: string, bnr: string): boolean => {
      return favoritter.some(
        (f) => f.knr === knr && f.gnr === gnr && f.bnr === bnr
      );
    },
    [favoritter]
  );

  const toggleFavoritt = React.useCallback((favoritt: Favoritt) => {
    setFavoritter((prev) => {
      const eksisterer = prev.some(
        (f) =>
          f.knr === favoritt.knr &&
          f.gnr === favoritt.gnr &&
          f.bnr === favoritt.bnr
      );
      const oppdatert = eksisterer
        ? prev.filter(
            (f) =>
              !(
                f.knr === favoritt.knr &&
                f.gnr === favoritt.gnr &&
                f.bnr === favoritt.bnr
              )
          )
        : [...prev, favoritt];
      skrivToStorage(oppdatert);
      return oppdatert;
    });
  }, []);

  return { favoritter, toggleFavoritt, erFavoritt };
}
