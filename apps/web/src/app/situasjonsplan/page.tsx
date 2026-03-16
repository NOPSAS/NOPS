'use client';

import * as React from 'react';
import {
  Map,
  CheckCircle2,
  MapPin,
  Ruler,
  Home,
  Droplets,
  Car,
  Layers,
  ArrowRight,
  Mail,
} from 'lucide-react';

const INKLUDERT = [
  { icon: <Layers className="h-5 w-5" />, tittel: 'Digitalt situasjonskart fra kommunen', desc: 'Oppdatert kartgrunnlag med eiendomsgrenser og hoydekurver' },
  { icon: <Home className="h-5 w-5" />, tittel: 'Eksisterende bebyggelse tegnet inn', desc: 'Alle eksisterende bygninger pa tomten med korrekte mal' },
  { icon: <MapPin className="h-5 w-5" />, tittel: 'Ny bebyggelse med mal og avstander', desc: 'Planlagt bygg tegnet inn med presise dimensjoner' },
  { icon: <Ruler className="h-5 w-5" />, tittel: 'Avstand til nabogrense (min. 4m)', desc: 'Maling til alle relevante grenser iht. PBL §29-4' },
  { icon: <Droplets className="h-5 w-5" />, tittel: 'Vann- og avlopsledninger', desc: 'VA-anlegg tegnet inn med tilkoblingspunkter' },
  { icon: <Car className="h-5 w-5" />, tittel: 'Parkering og adkomst', desc: 'Innkjorsel, parkeringsplasser og snuplass' },
];

const BYGGETYPER = [
  'Tilbygg',
  'Garasje / carport',
  'Nybygg',
  'Paabygg',
  'Terrasse / platting',
  'Bod / uthus',
  'Annet',
];

export default function SituasjonsplanPage() {
  const [adresse, setAdresse] = React.useState('');
  const [knr, setKnr] = React.useState('');
  const [gnr, setGnr] = React.useState('');
  const [bnr, setBnr] = React.useState('');
  const [byggeType, setByggeType] = React.useState('');
  const [tilleggsinfo, setTilleggsinfo] = React.useState('');

  React.useEffect(() => {
    document.title = 'Situasjonsplan til byggesoeknad | nops.no';
  }, []);

  function sendBestilling() {
    const subject = encodeURIComponent('Bestilling situasjonsplan');
    const body = encodeURIComponent(
      `Bestilling av situasjonsplan\n\n` +
      `Adresse: ${adresse}\n` +
      `Kommunenr: ${knr}, Gnr: ${gnr}, Bnr: ${bnr}\n` +
      `Hva skal bygges: ${byggeType}\n` +
      `Tilleggsinfo: ${tilleggsinfo || 'Ingen'}\n`
    );
    window.location.href = `mailto:hey@nops.no?subject=${subject}&body=${body}`;
  }

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <section className="bg-gradient-to-br from-green-600 to-emerald-700 text-white py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 mb-4 rounded-full bg-white/10 px-4 py-1.5 text-sm font-medium text-green-200">
            <Map className="h-4 w-4" /> nops.no / Situasjonsplan
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mb-4">
            Situasjonsplan til byggesoeknad
          </h1>
          <p className="text-lg text-green-100 max-w-2xl">
            Profesjonell situasjonsplan som kommunen godtar. Dekker hele Norge.
          </p>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-4 py-10 space-y-12">
        {/* Hva er en situasjonsplan */}
        <section>
          <h2 className="text-xl font-bold text-slate-900 mb-4">Hva er en situasjonsplan?</h2>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-sm text-slate-700 leading-relaxed">
              Situasjonsplan er et kart som viser tomten med eksisterende og planlagt bebyggelse,
              avstand til nabogrenser, vei, VA-anlegg med mer. Situasjonsplanen er et obligatorisk
              vedlegg til byggesoeknad og kreves ved alle soeknadspliktige tiltak etter PBL §20-1.
              Kommunen bruker situasjonsplanen til a vurdere om tiltaket er i samsvar med
              reguleringsplan, avstandskrav og andre bestemmelser.
            </p>
          </div>
        </section>

        {/* Hva inkluderer */}
        <section>
          <h2 className="text-xl font-bold text-slate-900 mb-4">Hva inkluderer var situasjonsplan?</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {INKLUDERT.map((item) => (
              <div
                key={item.tittel}
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-green-100 text-green-600">
                  {item.icon}
                </div>
                <h3 className="text-sm font-semibold text-slate-900 mb-1">{item.tittel}</h3>
                <p className="text-xs text-slate-500 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Priser */}
        <section>
          <h2 className="text-xl font-bold text-slate-900 mb-4">Pris</h2>
          <div className="rounded-2xl border border-green-200 bg-white p-8 shadow-sm text-center">
            <p className="text-4xl font-bold text-slate-900 mb-2">Fra 3 000 kr <span className="text-lg font-normal text-slate-500">+ mva</span></p>
            <div className="mt-6 space-y-2 text-sm text-slate-700">
              <div className="flex items-center justify-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" /> Situasjonskart fra kommunen
              </div>
              <div className="flex items-center justify-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" /> Inntegning av eksisterende og ny bebyggelse
              </div>
              <div className="flex items-center justify-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" /> Nabogrenser og malsetting
              </div>
              <div className="flex items-center justify-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" /> VA-ledninger og adkomst
              </div>
            </div>
            <p className="mt-6 text-sm text-slate-500">Leveringstid: 2-5 virkedager</p>
            <a
              href="mailto:hey@nops.no?subject=Bestilling%20situasjonsplan"
              className="mt-6 inline-flex items-center gap-2 rounded-xl bg-green-600 px-6 py-3 text-sm font-semibold text-white hover:bg-green-700 transition-colors"
            >
              <Mail className="h-4 w-4" />
              Bestill situasjonsplan
            </a>
          </div>
        </section>

        {/* Bestillingsskjema */}
        <section>
          <h2 className="text-xl font-bold text-slate-900 mb-4">Bestillingsskjema</h2>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">Adresse</label>
              <input
                type="text"
                placeholder="Gateadresse, postnummer og sted"
                value={adresse}
                onChange={(e) => setAdresse(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1">Kommunenr.</label>
                <input
                  type="text"
                  placeholder="F.eks. 0301"
                  value={knr}
                  onChange={(e) => setKnr(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1">Gnr.</label>
                <input
                  type="number"
                  placeholder="Gardsnr."
                  value={gnr}
                  onChange={(e) => setGnr(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1">Bnr.</label>
                <input
                  type="number"
                  placeholder="Bruksnr."
                  value={bnr}
                  onChange={(e) => setBnr(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">Hva skal bygges?</label>
              <select
                value={byggeType}
                onChange={(e) => setByggeType(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                <option value="">Velg type...</option>
                {BYGGETYPER.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Tilleggsinfo <span className="text-slate-400 font-normal">(valgfritt)</span>
              </label>
              <textarea
                value={tilleggsinfo}
                onChange={(e) => setTilleggsinfo(e.target.value)}
                rows={3}
                placeholder="Beskriv gjerne prosjektet naermere..."
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 resize-none"
              />
            </div>
            <button
              type="button"
              onClick={sendBestilling}
              className="inline-flex items-center gap-2 rounded-xl bg-green-600 px-6 py-3 text-sm font-semibold text-white hover:bg-green-700 transition-colors"
            >
              <Mail className="h-4 w-4" />
              Send bestilling
            </button>
          </div>
        </section>
      </div>

      {/* CTA bunn */}
      <section className="bg-gradient-to-br from-green-600 to-emerald-700 py-16 px-4 text-center text-white">
        <h2 className="text-2xl font-bold mb-3">Usikker pa hva du trenger?</h2>
        <p className="text-green-100 mb-6">
          Kontakt oss pa hey@nops.no sa hjelper vi deg videre.
        </p>
        <a
          href="mailto:hey@nops.no"
          className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-sm font-semibold text-green-700 hover:bg-green-50 transition-colors"
        >
          <Mail className="h-4 w-4" />
          Kontakt oss
        </a>
      </section>
    </main>
  );
}
