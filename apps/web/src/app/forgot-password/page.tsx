'use client';

import * as React from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Building2, Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const schema = z.object({
  email: z.string().email('Ugyldig e-postadresse'),
});

type FormValues = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  const [sent, setSent] = React.useState(false);
  const [serverError, setServerError] = React.useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormValues) => {
    setServerError(null);
    try {
      const res = await fetch(
        `/api/v1/auth/forgot-password?email=${encodeURIComponent(data.email)}`,
        { method: 'POST' }
      );
      if (!res.ok) {
        const json = await res.json().catch(() => ({}));
        setServerError(json.detail ?? 'Noe gikk galt. Prøv igjen.');
        return;
      }
      setSent(true);
    } catch {
      setServerError('Nettverksfeil. Prøv igjen senere.');
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 mb-3">
            <Building2 className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold">Glemt passord?</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Vi sender deg en lenke for å tilbakestille passordet
          </p>
        </div>

        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="text-base">Tilbakestill passord</CardTitle>
            <CardDescription>
              Skriv inn e-postadressen knyttet til kontoen din
            </CardDescription>
          </CardHeader>
          <CardContent>
            {sent ? (
              <div className="rounded-md border border-green-200 bg-green-50 p-4 text-sm text-green-700 dark:border-green-900 dark:bg-green-950 dark:text-green-300">
                Hvis e-postadressen finnes, har vi sendt instruksjoner for tilbakestilling.
              </div>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
                {serverError && (
                  <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
                    {serverError}
                  </div>
                )}
                <div className="space-y-1.5">
                  <Label htmlFor="email">E-post</Label>
                  <Input
                    id="email"
                    type="email"
                    autoComplete="email"
                    placeholder="din@epost.no"
                    error={errors.email?.message}
                    {...register('email')}
                  />
                </div>
                <Button type="submit" className="w-full" loading={isSubmitting}>
                  <Send className="h-4 w-4" />
                  Send tilbakestillingslenke
                </Button>
              </form>
            )}
          </CardContent>
        </Card>

        <p className="mt-4 text-center text-sm text-muted-foreground">
          <Link href="/login" className="font-medium text-blue-600 hover:underline">
            Tilbake til innlogging
          </Link>
        </p>
      </div>
    </div>
  );
}
