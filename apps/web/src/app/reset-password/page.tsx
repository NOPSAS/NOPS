'use client';

import * as React from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Building2, KeyRound, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const schema = z
  .object({
    new_password: z.string().min(8, 'Passordet må være minst 8 tegn'),
    confirm_password: z.string().min(1, 'Bekreft passordet'),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    message: 'Passordene stemmer ikke overens',
    path: ['confirm_password'],
  });

type FormValues = z.infer<typeof schema>;

export default function ResetPasswordPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  const [success, setSuccess] = React.useState(false);
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
    if (!token) {
      setServerError('Ugyldig lenke – token mangler.');
      return;
    }
    try {
      const res = await fetch(
        `/api/v1/auth/reset-password?token=${encodeURIComponent(token)}&new_password=${encodeURIComponent(data.new_password)}`,
        { method: 'POST' }
      );
      const json = await res.json().catch(() => ({}));
      if (res.ok) {
        setSuccess(true);
      } else {
        setServerError(json.detail ?? 'Noe gikk galt. Prøv igjen.');
      }
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
          <h1 className="text-2xl font-bold">Nytt passord</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Velg et nytt passord for kontoen din
          </p>
        </div>

        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="text-base">Tilbakestill passord</CardTitle>
            <CardDescription>Passordet må være minst 8 tegn</CardDescription>
          </CardHeader>
          <CardContent>
            {success ? (
              <div className="flex flex-col items-center gap-4 text-center">
                <CheckCircle className="h-10 w-10 text-green-500" />
                <p className="text-sm text-muted-foreground">
                  Passordet er oppdatert. Du kan nå logge inn.
                </p>
                <Button asChild className="w-full">
                  <Link href="/login">Gå til innlogging</Link>
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
                {serverError && (
                  <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
                    {serverError}
                  </div>
                )}
                <div className="space-y-1.5">
                  <Label htmlFor="new_password">Nytt passord</Label>
                  <Input
                    id="new_password"
                    type="password"
                    autoComplete="new-password"
                    placeholder="••••••••"
                    error={errors.new_password?.message}
                    {...register('new_password')}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="confirm_password">Bekreft passord</Label>
                  <Input
                    id="confirm_password"
                    type="password"
                    autoComplete="new-password"
                    placeholder="••••••••"
                    error={errors.confirm_password?.message}
                    {...register('confirm_password')}
                  />
                </div>
                <Button type="submit" className="w-full" loading={isSubmitting}>
                  <KeyRound className="h-4 w-4" />
                  Lagre nytt passord
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
