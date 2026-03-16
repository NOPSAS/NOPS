'use client';

import * as React from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { getMe } from '@/lib/api';
import { getAuthToken } from '@/lib/utils';
import type { User } from '@/lib/types';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  setUser: (user: User | null) => void;
}

const AuthContext = React.createContext<AuthContextValue>({
  user: null,
  loading: true,
  setUser: () => {},
});

const PUBLIC_PATHS = ['/login', '/register', '/landing', '/verify-email', '/forgot-password', '/reset-password', '/pricing', '/tjenester', '/visualisering', '/utbygging', '/pakke', '/investering', '/romplanlegger', '/nyheter', '/personvern', '/vilkar', '/kontakt', '/tomter', '/finn-analyse', '/dokumenter', '/juridisk', '/property', '/naboklage', '/situasjonsplan', '/dispensasjon', '/ferdigattest', '/energi', '/avvik'];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = React.useState<User | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      setLoading(false);
      if (!PUBLIC_PATHS.includes(pathname)) {
        if (pathname === '/') {
          router.replace('/landing');
        } else {
          router.replace('/login');
        }
      }
      return;
    }

    getMe()
      .then((me) => {
        setUser(me);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
        if (!PUBLIC_PATHS.includes(pathname)) {
          if (pathname === '/') {
            router.replace('/landing');
          } else {
            router.replace('/login');
          }
        }
      });
  }, [pathname, router]);

  return (
    <AuthContext.Provider value={{ user, loading, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  return React.useContext(AuthContext);
}
