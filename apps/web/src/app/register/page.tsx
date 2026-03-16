'use client';

import * as React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Building2, UserPlus } from 'lucide-react';
import { register as registerUser } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { useAuth } from '../auth-provider';

const registerSchema = z
  .object({
    full_name: z.string().min(2, 'Navn må ha minst 2 tegn').max(100),
    email: z.string().email('Ugyldig e-postadresse'),
    password: z
      .string()
      .min(8, 'Passord må ha minst 8 tegn')
      .max(128),
    confirm_password: z.string(),
  })
  .refine((d) => d.password === d.confirm_password, {
    message: 'Passordene stemmer ikke overens',
    path: ['confirm_password'],
  });

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const { setUser } = useAuth();
  const [serverError, setServerError] = React.useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormValues) => {
    setServerError(null);
    try {
      const response = await registerUser(
        data.email,
        data.password,
        data.full_name
      );
      setUser(response.user);
      router.push('/');
    } catch (err: unknown) {
      const message =
        (err as { message?: string })?.message ??
        'Registrering mislyktes. Prøv igjen.';
      setServerError(message);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 mb-3">
            <Building2 className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold">Opprett gratis konto</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            5 gratis eiendomsoppslag per måned – ingen kredittkort
          </p>
        </div>

        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="text-base">Registrering</CardTitle>
            <CardDescription>
              Fyll inn informasjonen nedenfor for å opprette konto
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form
              onSubmit={handleSubmit(onSubmit)}
              noValidate
              className="space-y-4"
            >
              {serverError && (
                <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
                  {serverError}
                </div>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="full_name">Fullt navn</Label>
                <Input
                  id="full_name"
                  autoComplete="name"
                  placeholder="Ola Nordmann"
                  error={errors.full_name?.message}
                  {...register('full_name')}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="email">E-post</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder="arkitekt@firma.no"
                  error={errors.email?.message}
                  {...register('email')}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="password">Passord</Label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="new-password"
                  placeholder="Minst 8 tegn"
                  error={errors.password?.message}
                  {...register('password')}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="confirm_password">Bekreft passord</Label>
                <Input
                  id="confirm_password"
                  type="password"
                  autoComplete="new-password"
                  placeholder="Gjenta passordet"
                  error={errors.confirm_password?.message}
                  {...register('confirm_password')}
                />
              </div>

              <Button
                type="submit"
                className="w-full"
                loading={isSubmitting}
              >
                <UserPlus className="h-4 w-4" />
                Opprett konto
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="mt-4 text-center text-sm text-muted-foreground">
          Har du allerede konto?{' '}
          <Link
            href="/login"
            className="font-medium text-blue-600 hover:underline"
          >
            Logg inn
          </Link>
        </p>
      </div>
    </div>
  );
}
