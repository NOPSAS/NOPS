'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft, Search, CheckCircle2 } from 'lucide-react';
import Link from 'next/link';
import { createCase, getFullPropertyData } from '@/lib/api';
import { AddressAutocomplete } from '@/components/address-autocomplete';
import type { AddressSuggestion } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import type { CustomerType } from '@/lib/types';

// ─── Validation schema ────────────────────────────────────────────────────────

const newCaseSchema = z.object({
  kommunenummer: z
    .string()
    .regex(/^\d{4}$/, 'Kommunenummer må være 4 siffer')
    .optional()
    .or(z.literal('')),
  street_address: z
    .string()
    .min(3, 'Gateadresse er for kort')
    .max(200, 'Gateadresse er for lang'),
  postal_code: z
    .string()
    .regex(/^\d{4}$/, 'Postnummer må være 4 siffer'),
  municipality: z
    .string()
    .min(2, 'Kommune er påkrevd')
    .max(100, 'Kommunenavn er for langt'),
  gnr: z
    .string()
    .optional()
    .refine(
      (v) => v === undefined || v === '' || /^\d+$/.test(v),
      'Gnr må være et tall'
    ),
  bnr: z
    .string()
    .optional()
    .refine(
      (v) => v === undefined || v === '' || /^\d+$/.test(v),
      'Bnr må være et tall'
    ),
  customer_type: z.enum(['PRIVATE', 'PROFESSIONAL', 'MUNICIPALITY'], {
    required_error: 'Velg kundetype',
  }),
  intake_source: z.string().optional(),
});

type NewCaseFormValues = z.infer<typeof newCaseSchema>;

const customerTypeLabels: Record<CustomerType, string> = {
  PRIVATE: 'Privat',
  PROFESSIONAL: 'Næringsliv',
  MUNICIPALITY: 'Kommune',
};

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function NewCasePage() {
  const router = useRouter();
  const [serverError, setServerError] = React.useState<string | null>(null);
  const [matrikkelLookup, setMatrikkelLookup] = React.useState<{
    loading: boolean;
    done: boolean;
    error: string | null;
  }>({ loading: false, done: false, error: null });

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<NewCaseFormValues>({
    resolver: zodResolver(newCaseSchema),
    defaultValues: {
      customer_type: 'PRIVATE',
      kommunenummer: '3212',
    },
  });

  const customerType = watch('customer_type');
  const knr = watch('kommunenummer');
  const gnrVal = watch('gnr');
  const bnrVal = watch('bnr');

  const handleMatrikkelLookup = async () => {
    if (!knr || !gnrVal || !bnrVal) return;
    setMatrikkelLookup({ loading: true, done: false, error: null });
    try {
      const data = await getFullPropertyData(knr, gnrVal, bnrVal);
      if (data.eiendom) {
        if (data.eiendom.adresse) {
          setValue('street_address', data.eiendom.adresse, { shouldValidate: true });
        }
        if (data.eiendom.postnummer) {
          setValue('postal_code', data.eiendom.postnummer, { shouldValidate: true });
        }
        if (data.eiendom.poststed) {
          setValue('municipality', data.eiendom.poststed, { shouldValidate: true });
        } else if (data.kommune?.kommunenavn) {
          setValue('municipality', data.kommune.kommunenavn, { shouldValidate: true });
        }
        setMatrikkelLookup({ loading: false, done: true, error: null });
      } else {
        setMatrikkelLookup({ loading: false, done: false, error: 'Eiendom ikke funnet i Matrikkel' });
      }
    } catch {
      setMatrikkelLookup({ loading: false, done: false, error: 'Matrikkel-oppslag feilet' });
    }
  };

  const onSubmit = async (data: NewCaseFormValues) => {
    setServerError(null);
    try {
      const created = await createCase({
        customer_type: data.customer_type,
        intake_source: data.intake_source || undefined,
        property: {
          street_address: data.street_address,
          postal_code: data.postal_code,
          municipality: data.municipality,
          gnr: data.gnr ? parseInt(data.gnr, 10) : null,
          bnr: data.bnr ? parseInt(data.bnr, 10) : null,
          kommunenummer: data.kommunenummer || undefined,
        },
      });
      router.push(`/cases/${created.id}`);
    } catch (err: unknown) {
      const message =
        (err as { message?: string })?.message ??
        'Kunne ikke opprette sak. Prøv igjen.';
      setServerError(message);
    }
  };

  return (
    <div className="page-container max-w-2xl">
      {/* Back link */}
      <div className="mb-6">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Tilbake til dashboard
        </Link>
      </div>

      <div className="mb-6">
        <h1 className="section-title">Opprett ny sak</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Fyll inn eiendomsinformasjon for å starte en ny byggesjekk
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-6">
        {serverError && (
          <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
            {serverError}
          </div>
        )}

        {/* Adresse */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Eiendomsadresse</CardTitle>
            <CardDescription>
              Søk opp adressen eller skriv inn manuelt. Adressesøket henter gnr/bnr automatisk.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Address autocomplete */}
            <div className="space-y-1.5">
              <Label>Søk adresse (Geonorge)</Label>
              <AddressAutocomplete
                placeholder="Skriv adresse for å søke..."
                onSelect={(s: AddressSuggestion) => {
                  setValue('street_address', s.adressetekst, { shouldValidate: true });
                  setValue('postal_code', s.postnummer, { shouldValidate: true });
                  setValue('municipality', s.poststed || s.kommunenavn, { shouldValidate: true });
                  if (s.gnr) setValue('gnr', String(s.gnr), { shouldValidate: true });
                  if (s.bnr) setValue('bnr', String(s.bnr), { shouldValidate: true });
                  if (s.kommunenummer) setValue('kommunenummer', s.kommunenummer, { shouldValidate: true });
                }}
              />
              <p className="text-xs text-muted-foreground">
                Valgfritt — fyller ut feltene nedenfor automatisk
              </p>
            </div>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t dark:border-slate-700" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-2 text-muted-foreground dark:bg-card">
                  eller fyll inn manuelt
                </span>
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="street_address">Gateadresse *</Label>
              <Input
                id="street_address"
                placeholder="Eksempelveien 12"
                error={errors.street_address?.message}
                {...register('street_address')}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="postal_code">Postnummer *</Label>
                <Input
                  id="postal_code"
                  placeholder="0000"
                  maxLength={4}
                  error={errors.postal_code?.message}
                  {...register('postal_code')}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="municipality">Kommune *</Label>
                <Input
                  id="municipality"
                  placeholder="Oslo"
                  error={errors.municipality?.message}
                  {...register('municipality')}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Matrikkelinformasjon */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Matrikkelinformasjon</CardTitle>
            <CardDescription>
              Fyll inn kommunenummer og gnr/bnr for å hente adresse automatisk fra Kartverket
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="kommunenummer">Kommunenummer</Label>
                <Input
                  id="kommunenummer"
                  placeholder="3212"
                  maxLength={4}
                  inputMode="numeric"
                  {...register('kommunenummer')}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="gnr">Gårdsnummer (Gnr)</Label>
                <Input
                  id="gnr"
                  placeholder="1"
                  inputMode="numeric"
                  error={errors.gnr?.message}
                  {...register('gnr')}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="bnr">Bruksnummer (Bnr)</Label>
                <Input
                  id="bnr"
                  placeholder="100"
                  inputMode="numeric"
                  error={errors.bnr?.message}
                  {...register('bnr')}
                />
              </div>
            </div>

            {/* Matrikkel lookup button */}
            {knr && gnrVal && bnrVal && (
              <div className="flex items-center gap-3">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleMatrikkelLookup}
                  loading={matrikkelLookup.loading}
                >
                  <Search className="h-3.5 w-3.5" />
                  Hent adresse fra Kartverket
                </Button>
                {matrikkelLookup.done && (
                  <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Adresse hentet
                  </span>
                )}
                {matrikkelLookup.error && (
                  <span className="text-xs text-red-600 dark:text-red-400">
                    {matrikkelLookup.error}
                  </span>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Saksinformasjon */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Saksinformasjon</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="customer_type">Kundetype *</Label>
              <Select
                value={customerType}
                onValueChange={(val) =>
                  setValue('customer_type', val as CustomerType, {
                    shouldValidate: true,
                  })
                }
              >
                <SelectTrigger id="customer_type">
                  <SelectValue placeholder="Velg kundetype" />
                </SelectTrigger>
                <SelectContent>
                  {(
                    Object.entries(customerTypeLabels) as [
                      CustomerType,
                      string
                    ][]
                  ).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.customer_type && (
                <p className="text-xs text-destructive" role="alert">
                  {errors.customer_type.message}
                </p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="intake_source">Inntakskilde</Label>
              <Input
                id="intake_source"
                placeholder="f.eks. Direkte henvendelse, Nettside, Samarbeidspartner"
                {...register('intake_source')}
              />
              <p className="text-xs text-muted-foreground">
                Valgfritt — hvordan kom denne saken inn?
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.back()}
          >
            Avbryt
          </Button>
          <Button type="submit" loading={isSubmitting}>
            Opprett sak
          </Button>
        </div>
      </form>
    </div>
  );
}
