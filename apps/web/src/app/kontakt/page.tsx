import type { Metadata } from 'next';
import Link from 'next/link';
import { Mail, Building2, Globe, ArrowRight } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Kontakt – nops.no',
};

export default function KontaktPage() {
  return (
    <main className="min-h-screen bg-slate-50">
      {/* Hero */}
      <section className="bg-gradient-to-br from-blue-600 to-indigo-700 py-16 px-4 text-center text-white">
        <h1 className="text-3xl sm:text-4xl font-bold mb-3">Kontakt oss</h1>
        <p className="text-blue-100 max-w-xl mx-auto">
          Har du spørsmål om nops.no eller trenger hjelp? Vi er her for deg.
        </p>
      </section>

      {/* Kontaktkort */}
      <section className="px-4 -mt-8">
        <div className="max-w-lg mx-auto rounded-2xl border border-slate-200 bg-white shadow-sm p-8">
          <div className="space-y-6">
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 text-blue-600 shrink-0">
                <Mail className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">E-post</h3>
                <a
                  href="mailto:hey@nops.no"
                  className="text-blue-600 hover:underline text-sm"
                >
                  hey@nops.no
                </a>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 text-blue-600 shrink-0">
                <Building2 className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Firma</h3>
                <p className="text-sm text-slate-700">Konsepthus AS</p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 text-blue-600 shrink-0">
                <Globe className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Nettside</h3>
                <a
                  href="https://www.nops.no"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline text-sm"
                >
                  nops.no
                </a>
              </div>
            </div>
          </div>

          <div className="mt-8 rounded-xl bg-slate-50 border border-slate-200 px-5 py-4">
            <p className="text-sm text-slate-600">
              Vi svarer normalt innen 24 timer på hverdager.
            </p>
          </div>
        </div>
      </section>

      {/* Link tilbake */}
      <section className="px-4 py-12 text-center">
        <Link
          href="/tjenester"
          className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
        >
          Se alle tjenester
          <ArrowRight className="h-4 w-4" />
        </Link>
      </section>
    </main>
  );
}
