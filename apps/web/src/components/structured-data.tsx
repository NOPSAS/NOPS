export function StructuredData() {
  const orgSchema = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "nops.no",
    "alternateName": ["NOPS", "ByggSjekk", "Konsepthus AS"],
    "url": "https://nops.no",
    "logo": "https://nops.no/og-image.svg",
    "email": "hey@nops.no",
    "description": "Norges ledende plattform for digitale eiendomstjenester. Avviksdeteksjon, byggesøknad, 2D til 3D, energirådgivning og 20+ tjenester.",
    "foundingDate": "2020",
    "address": {
      "@type": "PostalAddress",
      "addressCountry": "NO"
    },
    "sameAs": [
      "https://www.situasjonsplan.no",
      "https://www.dispensasjonen.no",
      "https://www.naboklagen.no",
      "https://www.ferdigattesten.no",
      "https://www.minni.no"
    ]
  };

  const softwareSchema = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "nops.no",
    "alternateName": "ByggSjekk",
    "applicationCategory": "BusinessApplication",
    "operatingSystem": "Web",
    "url": "https://nops.no",
    "description": "Norges smarteste eiendomsverktøy. Sjekk eiendommen din gratis – avviksdeteksjon, reguleringsplan, byggesaker, energimerke og AI-analyse på sekunder.",
    "offers": {
      "@type": "AggregateOffer",
      "lowPrice": "0",
      "highPrice": "999",
      "priceCurrency": "NOK",
      "offerCount": "3"
    },
    "aggregateRating": {
      "@type": "AggregateRating",
      "ratingValue": "4.8",
      "reviewCount": "127"
    }
  };

  const websiteSchema = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "nops.no",
    "url": "https://nops.no",
    "description": "Norges ledende plattform for digitale eiendomstjenester",
    "potentialAction": {
      "@type": "SearchAction",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": "https://nops.no/property?q={search_term_string}"
      },
      "query-input": "required name=search_term_string"
    }
  };

  const faqSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {
        "@type": "Question",
        "name": "Hva er nops.no?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "nops.no er Norges ledende plattform for digitale eiendomstjenester. Vi tilbyr avviksdeteksjon, byggesøknad, 2D til 3D-konvertering, energirådgivning, dispensasjonssøknader og 20+ andre tjenester for eiendom, byggesak og arkitektur."
        }
      },
      {
        "@type": "Question",
        "name": "Kan jeg sjekke eiendommen min gratis?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Ja, nops.no tilbyr gratis eiendomssjekk for alle norske eiendommer. Du får matrikkeldata, byggesaker, reguleringsplan, DOK-analyse og ferdigattest-status uten å betale. AI-analyse og PDF-rapporter krever Starter-abonnement (499 kr/mnd)."
        }
      },
      {
        "@type": "Question",
        "name": "Hva er avviksdeteksjon?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Avviksdeteksjon er nops.no sin flaggskiptjeneste som automatisk sammenligner offentlige registre, byggetegninger og Finn.no-annonser for å finne avvik som ulovlige tilbygg, manglende ferdigattester og feil i plantegninger."
        }
      },
      {
        "@type": "Question",
        "name": "Hva koster byggesøknad via nops.no?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Byggesøknad via nops.no koster fra 15 000 kr og inkluderer tegninger, søknad, nabovarsel og all dokumentasjon. Vi håndterer tilbygg, påbygg, bruksendring, garasje, tomtedeling og dispensasjonssøknader."
        }
      },
      {
        "@type": "Question",
        "name": "Hva er 2D til 3D-konvertering?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "2D til 3D er en tjeneste der vi konverterer plantegninger og fasadetegninger til komplette 3D-modeller. Leveres som IFC, SketchUp eller Revit – klar for prosjektering, byggesak og fotorealistisk visualisering."
        }
      },
      {
        "@type": "Question",
        "name": "Kan nops.no hjelpe med energirådgivning?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Ja, nops.no tilbyr gratis energianalyse med estimert energimerke (A-G), anbefalte tiltak, Enova-støtte beregning og TEK17-sjekk. Vi kan også lage 3D-modeller for presis energiberegning."
        }
      },
      {
        "@type": "Question",
        "name": "Tilbyr nops.no gratis godkjente tegninger?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Ja, i motsetning til Norkart og Ambita som tar betalt, tilbyr nops.no gratis innhenting av sist godkjente tegninger fra kommunen. Vi sender automatisk innsynsbegjæring til kommunens postmottak."
        }
      }
    ]
  };

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(orgSchema) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(softwareSchema) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteSchema) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }} />
    </>
  );
}
