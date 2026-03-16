'use client';

import * as React from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Building2, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  const [status, setStatus] = React.useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = React.useState('');

  React.useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage('Ugyldig bekreftelseslenke – token mangler.');
      return;
    }

    fetch(`/api/v1/auth/verify-email?token=${encodeURIComponent(token)}`)
      .then(async (res) => {
        const data = await res.json();
        if (res.ok) {
          setStatus('success');
          setMessage(data.message ?? 'E-postadresse bekreftet!');
        } else {
          setStatus('error');
          setMessage(data.detail ?? 'Bekreftelse mislyktes.');
        }
      })
      .catch(() => {
        setStatus('error');
        setMessage('Nettverksfeil. Prøv igjen senere.');
      });
  }, [token]);

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 mb-3">
            <Building2 className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold">E-postbekreftelse</h1>
        </div>

        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="text-base text-center">
              {status === 'loading' && 'Bekrefter…'}
              {status === 'success' && 'Bekreftet!'}
              {status === 'error' && 'Noe gikk galt'}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center gap-4 text-center">
            {status === 'loading' && (
              <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
            )}
            {status === 'success' && (
              <>
                <CheckCircle className="h-10 w-10 text-green-500" />
                <p className="text-sm text-muted-foreground">{message}</p>
                <Button asChild className="w-full">
                  <Link href="/login">Gå til innlogging</Link>
                </Button>
              </>
            )}
            {status === 'error' && (
              <>
                <XCircle className="h-10 w-10 text-red-500" />
                <p className="text-sm text-muted-foreground">{message}</p>
                <Button asChild variant="outline" className="w-full">
                  <Link href="/login">Tilbake til innlogging</Link>
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
