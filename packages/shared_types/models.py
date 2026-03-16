"""
packages/shared_types/models.py

Kanoniske Pydantic-modeller og enums for ByggSjekk.

Disse definisjonene er kilden til sannhet for alle statuser, kategorier og typer
som brukes på tvers av API, tjenester og (via kodegenerering) frontend.

TypeScript-typer kan genereres med:
    datamodel-codegen --input packages/shared_types/models.py --output apps/web/src/types/generated.ts

Importeres fra apps/api/ slik:
    from packages.shared_types import CaseStatus, DeviationCategory
"""

from enum import Enum


# =============================================================================
# Sak-enums
# =============================================================================

class CaseStatus(str, Enum):
    """Livssyklus for en avviksvurderingssak."""

    DRAFT = "DRAFT"
    """Saken er opprettet, men ikke alle dokumenter er lastet opp."""

    ACTIVE = "ACTIVE"
    """Saken er under behandling – dokumenter er lastet opp og analyse pågår eller er fullfort."""

    IN_REVIEW = "IN_REVIEW"
    """Arkitekt gjennomgår avvik og AI-vurderinger."""

    COMPLETED = "COMPLETED"
    """Saken er ferdigbehandlet og rapport er generert."""

    ARCHIVED = "ARCHIVED"
    """Saken er arkivert (ingen videre behandling)."""

    CANCELLED = "CANCELLED"
    """Saken er kansellert av bruker eller administrator."""


class CustomerType(str, Enum):
    """Type kunde / bruker som har opprettet saken."""

    ARCHITECT_FIRM = "ARCHITECT_FIRM"
    """Arkitektfirma som behandler saker på vegne av sine klienter."""

    INDEPENDENT_ARCHITECT = "INDEPENDENT_ARCHITECT"
    """Enkeltpraktiserende arkitekt."""

    MUNICIPALITY = "MUNICIPALITY"
    """Kommune som bruker systemet for intern saksbehandling."""

    PROPERTY_OWNER = "PROPERTY_OWNER"
    """Eiendomseier (begrenset tilgang – kun lesing av rapporter)."""


# =============================================================================
# Godkjenningsstatus
# =============================================================================

class ApprovalStatus(str, Enum):
    """
    Godkjenningsstatus for et kildedokument (tegning / tillatelse).

    Modellen unngår binær godkjent / ikke-godkjent fordi historiske dokumenter
    sjelden har maskinlesbar godkjenningsstatus. Se ADR-005 for begrunnelse.
    """

    RECEIVED = "RECEIVED"
    """
    Dokumentet er mottatt og registrert i systemet.
    Ingen vurdering av godkjenningsstatus er gjort enda.
    """

    ASSUMED_APPROVED = "ASSUMED_APPROVED"
    """
    Dokumentet antas å være godkjent basert på kontekst (f.eks. kommunalt arkiv,
    alder, referansenummer), men det er ikke maskinelt verifisert.
    Tillitsgrad: MEDIUM. Krever arkitvurdering ved tvil.
    """

    VERIFIED_APPROVED = "VERIFIED_APPROVED"
    """
    Godkjenning er verifisert via kommunekobling (eByggSak, SEFRAK eller tilsvarende)
    eller manuelt bekreftet av arkitekt i systemet.
    Tillitsgrad: HIGH.
    """

    UNKNOWN = "UNKNOWN"
    """
    Godkjenningsstatus kan ikke fastslås. Dokumentet mangler referansenummer,
    avsender er ukjent, eller kommunekobling returnerte ingen treff.
    Tillitsgrad: LOW. Avvik basert på dette dokumentet bør vektes lavere.
    """


# =============================================================================
# Avvikskategorier
# =============================================================================

class DeviationCategory(str, Enum):
    """
    Kategori for et oppdaget avvik mellom godkjent plan og dagens tilstand.

    Kategoriene dekker de vanligste avvikstypene arkitekter møter ved
    tilstandsvurdering av norsk boligmasse.
    """

    ROOM_DEFINITION_CHANGE = "ROOM_DEFINITION_CHANGE"
    """
    Et rom er omdefinert uten at dette fremgår av godkjente tegninger.
    Eksempel: kjøkken er slått sammen med stue, eller bod er gjort om til soverom.
    """

    BEDROOM_UTILITY_DISCREPANCY = "BEDROOM_UTILITY_DISCREPANCY"
    """
    Soverom i godkjent plan er omgjort til ikke-varig-oppholdsrom (kontor, lager)
    eller omvendt. Relevant for TEK17 § 12-2 (krav til rom for varig opphold).
    """

    DOOR_PLACEMENT_CHANGE = "DOOR_PLACEMENT_CHANGE"
    """
    Dørplassering er endret. Kan påvirke rømningsveier og branncelleinndeling.
    """

    WINDOW_PLACEMENT_CHANGE = "WINDOW_PLACEMENT_CHANGE"
    """
    Vindusplassering eller -størrelse er endret. Kan påvirke lysflate (TEK17 § 12-6)
    og rømningsvei krav.
    """

    BALCONY_TERRACE_DISCREPANCY = "BALCONY_TERRACE_DISCREPANCY"
    """
    Balkong eller terrasse er lagt til, fjernet eller endret i størrelse.
    Kan indikere innbygging av balkong uten tillatelse.
    """

    ADDITION_DETECTED = "ADDITION_DETECTED"
    """
    Et tilbygg, påbygg eller ny konstruksjon er synlig i dagens plan som ikke
    finnes i godkjent tegning. Typisk søknadspliktig etter PBL § 20-1.
    """

    UNDERBUILDING_DETECTED = "UNDERBUILDING_DETECTED"
    """
    Underbygging (kjeller, lavere etasje) er synlig i dagens plan, men mangler
    i godkjent tegning. Kan indikere ulovlig underbygging.
    """

    UNINSPECTED_AREA = "UNINSPECTED_AREA"
    """
    Et område (rom, etasje, uthus) er synlig i dagens plan, men mangler
    dokumentasjon i form av ferdigattest eller godkjent tegning.
    """

    USE_CHANGE_INDICATION = "USE_CHANGE_INDICATION"
    """
    Indikasjoner på at bygget brukes til noe annet enn godkjent formål.
    Eksempel: bolig brukt som næringslokale.
    """

    MARKETED_FUNCTION_DISCREPANCY = "MARKETED_FUNCTION_DISCREPANCY"
    """
    Rommet er markedsfort med en funksjon (f.eks. "soverom") som avviker fra
    hva godkjent tegning viser (f.eks. "stue" eller "bod").
    Relevant ved eiendomssalg og takstvurderinger.
    """


# =============================================================================
# Alvorlighetsgrad for avvik
# =============================================================================

class DeviationSeverity(str, Enum):
    """Alvorlighetsgrad for et avvik, basert på potensielle konsekvenser."""

    CRITICAL = "CRITICAL"
    """
    Avviket kan indikere brannsikkerhets- eller rømningsveiproblem.
    Krever umiddelbar arkitektvurdering.
    """

    HIGH = "HIGH"
    """
    Avviket er sannsynlig søknadspliktig eller bryter materielle krav i TEK17/PBL.
    """

    MEDIUM = "MEDIUM"
    """
    Avviket er en merkbar endring som bør dokumenteres, men konsekvensene er usikre.
    """

    LOW = "LOW"
    """
    Avviket er en mindre endring (f.eks. dørretning) med begrenset juridisk betydning.
    """

    INFORMATIONAL = "INFORMATIONAL"
    """
    Observasjon uten klar avvikskarakter – for dokumentasjonsformål.
    """


# =============================================================================
# Avviksstatus (saksbehandling)
# =============================================================================

class DeviationStatus(str, Enum):
    """Status for behandlingen av et enkeltavvik."""

    PENDING_REVIEW = "PENDING_REVIEW"
    """Avviket er oppdaget og venter på arkitvurdering."""

    UNDER_REVIEW = "UNDER_REVIEW"
    """Arkitekt har åpnet avviket og vurderer det aktivt."""

    CONFIRMED = "CONFIRMED"
    """Arkitekt har bekreftet at avviket er reelt og skal følges opp."""

    DISMISSED = "DISMISSED"
    """Arkitekt har avvist avviket (f.eks. tegningsfeil, allerede godkjent)."""

    DISPENSATION_APPLIED = "DISPENSATION_APPLIED"
    """Dispensasjon er søkt hos kommunen for dette avviket."""

    RESOLVED = "RESOLVED"
    """Avviket er løst (enten gjennom dispensasjon, korrigering eller dokumentasjon)."""


# =============================================================================
# Prosesseringsstatus (dokumentprosessering)
# =============================================================================

class ProcessingStatus(str, Enum):
    """Status for maskinell prosessering av et kildedokument."""

    QUEUED = "QUEUED"
    """Dokumentet er lastet opp og venter i jobbkøen."""

    PROCESSING = "PROCESSING"
    """Dokumentet prosesseres aktivt (OCR, parsing, AI-analyse)."""

    COMPLETED = "COMPLETED"
    """Prosessering er fullfort uten feil."""

    FAILED = "FAILED"
    """Prosessering feilet. Se error_message-feltet for detaljer."""

    PARTIAL = "PARTIAL"
    """Prosessering er delvis fullfort (f.eks. noen sider parsert, andre ikke)."""


# =============================================================================
# Kildetype for dokumenter
# =============================================================================

class SourceType(str, Enum):
    """Hvor et kildedokument kommer fra."""

    CUSTOMER_UPLOAD = "CUSTOMER_UPLOAD"
    """Lastet opp direkte av kunden via webgrensesnittet."""

    MUNICIPALITY_ARCHIVE = "MUNICIPALITY_ARCHIVE"
    """Hentet fra kommunalt byggesaksarkiv (eByggSak / kommunekobling)."""

    SEFRAK_REGISTRY = "SEFRAK_REGISTRY"
    """Hentet fra SEFRAK (Statens register over fredete og vernete anlegg)."""

    MATRIKKEL = "MATRIKKEL"
    """Hentet fra Matrikkelen (Kartverket)."""

    MANUAL_ENTRY = "MANUAL_ENTRY"
    """Manuelt registrert av arkitekt i systemet."""


# =============================================================================
# Rapporttyper
# =============================================================================

class ReportType(str, Enum):
    """Type rapport som kan genereres for en sak."""

    INTERNAL = "INTERNAL"
    """
    Intern arkitektrapport med full detaljeringsgrad:
    confidence-scorer, AI-evidens, regelreferanser.
    """

    CUSTOMER = "CUSTOMER"
    """
    Kunderapport (eier / kjøper) med høynivå-sammendrag.
    Unngår juridisk terminologi.
    """

    MUNICIPALITY = "MUNICIPALITY"
    """
    Rapport til kommune for søknadsdokumentasjon eller avviksdialog.
    Formelt språk med alle referanser.
    """

    VALUATION = "VALUATION"
    """
    Rapport til takstmann / megler med fokus på areal og funksjonsavvik.
    """
