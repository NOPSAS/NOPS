import Link from 'next/link';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Side ikke funnet – nops.no',
};

export default function NotFound() {
  return (
    <main className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
      <h1 className="mb-4 text-6xl font-extrabold text-slate-900">404</h1>
      <p className="mb-8 text-lg text-slate-500">Beklager, denne siden finnes ikke.</p>
      <div className="flex gap-4">
        <Link href="/landing" className="rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-700 transition-colors">
          Gå til forsiden
        </Link>
        <Link href="/property" className="rounded-xl border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors">
          Søk opp eiendom
        </Link>
      </div>
    </main>
  );
}
