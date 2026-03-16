// ─── Enums ────────────────────────────────────────────────────────────────────

export type CaseStatus =
  | 'DRAFT'
  | 'INTAKE'
  | 'PROCESSING'
  | 'ANALYSIS'
  | 'REVIEW'
  | 'COMPLETED'
  | 'ARCHIVED';

export type CustomerType = 'PRIVATE' | 'PROFESSIONAL' | 'MUNICIPALITY';

export type SourceType =
  | 'APPROVED_DRAWING'
  | 'AS_BUILT'
  | 'SITE_PHOTO'
  | 'SURVEY'
  | 'OTHER';

export type ApprovalStatus =
  | 'VERIFIED_APPROVED'
  | 'ASSUMED_APPROVED'
  | 'RECEIVED'
  | 'UNKNOWN';

export type ProcessingStatus =
  | 'PENDING'
  | 'PROCESSING'
  | 'COMPLETED'
  | 'FAILED';

export enum DeviationCategory {
  ROOM_DEFINITION_CHANGE = 'ROOM_DEFINITION_CHANGE',
  BEDROOM_UTILITY_DISCREPANCY = 'BEDROOM_UTILITY_DISCREPANCY',
  DOOR_PLACEMENT_CHANGE = 'DOOR_PLACEMENT_CHANGE',
  WINDOW_PLACEMENT_CHANGE = 'WINDOW_PLACEMENT_CHANGE',
  BALCONY_TERRACE_DISCREPANCY = 'BALCONY_TERRACE_DISCREPANCY',
  ADDITION_DETECTED = 'ADDITION_DETECTED',
  UNDERBUILDING_DETECTED = 'UNDERBUILDING_DETECTED',
  UNINSPECTED_AREA = 'UNINSPECTED_AREA',
  USE_CHANGE_INDICATION = 'USE_CHANGE_INDICATION',
  MARKETED_FUNCTION_DISCREPANCY = 'MARKETED_FUNCTION_DISCREPANCY',
}

export type DeviationSeverity = 'CRITICAL' | 'MAJOR' | 'MINOR' | 'INFO';

export type DeviationStatus =
  | 'OPEN'
  | 'ACKNOWLEDGED'
  | 'DISMISSED'
  | 'RESOLVED';

export type ReviewStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED';

export type ReportType = 'INTERNAL' | 'CUSTOMER';

// ─── Core Domain Types ────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'ARCHITECT' | 'ADMIN' | 'VIEWER';
  created_at: string;
  updated_at: string;
}

export interface Property {
  street_address: string;
  postal_code: string;
  municipality: string;
  gnr: number | null;
  bnr: number | null;
  snr?: number | null;
  fnr?: number | null;
  kommunenummer?: string | null;
}

export interface PropertyCase {
  id: string;
  title: string;
  status: CaseStatus;
  customer_type: CustomerType;
  intake_source: string | null;
  property: Property;
  architect_id: string;
  created_at: string;
  updated_at: string;
  document_count?: number;
  deviation_count?: number;
  open_deviation_count?: number;
}

export interface SourceDocument {
  id: string;
  case_id: string;
  filename: string;
  file_size: number;
  mime_type: string;
  source_type: SourceType;
  approval_status: ApprovalStatus;
  processing_status: ProcessingStatus;
  storage_path: string;
  uploaded_at: string;
  processed_at: string | null;
  metadata: Record<string, unknown> | null;
}

// ─── Deviation ────────────────────────────────────────────────────────────────

export interface RuleMatch {
  rule_id: string;
  rule_code: string;
  description: string;
  reference: string;
  matched: boolean;
  details: string | null;
}

export interface Deviation {
  id: string;
  case_id: string;
  category: DeviationCategory;
  severity: DeviationSeverity;
  status: DeviationStatus;
  description: string;
  location: string | null;
  confidence: number;
  source_document_ids: string[];
  rule_matches: RuleMatch[];
  architect_note: string | null;
  reviewed_at: string | null;
  reviewed_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface Rule {
  id: string;
  code: string;
  title: string;
  description: string;
  category: DeviationCategory;
  reference_document: string;
  is_active: boolean;
}

// ─── Assessment Report ────────────────────────────────────────────────────────

export interface SpaceRecord {
  name: string;
  type: string;
  area_m2: number | null;
  floor: string | null;
  confidence: number;
  source_document_id: string | null;
}

export interface FloorPlan {
  floor: string;
  spaces: SpaceRecord[];
  total_area_m2: number | null;
}

export interface AssessmentReport {
  id: string;
  case_id: string;
  floor_plans: FloorPlan[];
  summary: {
    total_deviations: number;
    critical_count: number;
    major_count: number;
    minor_count: number;
    info_count: number;
    overall_confidence: number;
  };
  internal_report: Record<string, unknown> | null;
  customer_report: Record<string, unknown> | null;
  generated_at: string;
  approved_at: string | null;
  approved_by: string | null;
}

// ─── Architect Review ─────────────────────────────────────────────────────────

export interface AuditLogEntry {
  timestamp: string;
  action: string;
  user_id: string;
  user_name: string;
  details: string | null;
}

export interface ArchitectReview {
  id: string;
  case_id: string;
  status: ReviewStatus;
  comments: string | null;
  audit_log: AuditLogEntry[];
  started_at: string | null;
  completed_at: string | null;
  architect_id: string;
  created_at: string;
  updated_at: string;
}

// ─── API Request/Response types ────────────────────────────────────────────────

export interface ApiError {
  detail: string;
  status?: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface CreateCasePayload {
  property: Property;
  customer_type: CustomerType;
  intake_source?: string;
}

export interface UpdateCasePayload {
  status?: CaseStatus;
  property?: Partial<Property>;
  customer_type?: CustomerType;
  intake_source?: string;
}

export interface UpdateDeviationPayload {
  status?: DeviationStatus;
  architect_note?: string;
}

export interface UpdateReviewPayload {
  status?: ReviewStatus;
  comments?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// ─── Structured Plans ─────────────────────────────────────────────────────────

export interface Space {
  id: string;
  name: string;
  space_type: string;
  floor_number: number | null;
  area: number | null;
  confidence: number;
  attributes: Record<string, unknown>;
}

export interface StructuredPlan {
  id: string;
  document_id: string;
  case_id: string;
  document_filename: string | null;
  document_type: string | null;
  approval_status: ApprovalStatus | null;
  total_area: number | null;
  room_count: number | null;
  version: number;
  created_at: string | null;
  spaces: Space[];
  plan_data: Record<string, unknown> | null;
}

export interface MunicipalityRequest {
  id: string;
  case_id: string;
  municipality: string;
  request_type: string;
  request_method: string;
  status: string;
  request_payload: Record<string, unknown> | null;
  response_payload: Record<string, unknown> | null;
  sent_at: string | null;
  received_at: string | null;
  created_at: string | null;
}

// ─── Property Lookup (DOK-analyse + Arealplaner) ───────────────────────────

export interface DokDataset {
  datasetId: string;
  datasetName: string;
  theme: string;
  description?: string | null;
  url?: string | null;
}

export interface DokAnalyseResult {
  knr: string;
  gnr: string;
  bnr: string;
  datasets_touched: DokDataset[];
  datasets_untouched: DokDataset[];
  report_url: string | null;
  error: string | null;
  source: string;
  mock: boolean;
}

export interface ArealplanResult {
  plan_id: string;
  plan_name: string;
  plan_type: string;
  plan_status: string;
  municipality_number: string;
  vedtak_date: string | null;
  ikrafttredelse_date: string | null;
  url: string | null;
}

export interface PlanrapportResult {
  knr: string;
  gnr: string;
  bnr: string;
  planrapport_url: string | null;
  plans: Record<string, unknown>[];
  error: string | null;
  source: string;
}

export interface DispensasjonResult {
  reference: string;
  description: string;
  status: string;
  granted_date: string | null;
  plan_reference: string | null;
}

export interface PropertyLookupResult {
  knr: string;
  gnr: string;
  bnr: string;
  planrapport: PlanrapportResult | null;
  dok_analyse: DokAnalyseResult | null;
  dispensasjoner: DispensasjonResult[];
  arealplaner: ArealplanResult[];
  errors: string[];
  data_sources: string[];
}

// ─── Kartverket / Matrikkel types ─────────────────────────────────────────────

export interface MatrikkelEiendomData {
  adresse: string;
  postnummer: string;
  poststed: string;
  areal_m2: number | null;
  koordinat_nord: number | null;
  koordinat_ost: number | null;
  eierform: string;
  matrikkel_id: string;
}

export interface MatrikkelBygningData {
  bygningsnummer: number;
  bygningstype: string;
  bygningstype_kode: string;
  byggeaar: number | null;
  bruksareal: number | null;
  bygningstatus: string;
  etasjer: Record<string, unknown>[];
  bruksenheter: Record<string, unknown>[];
  koordinat_nord: number | null;
  koordinat_ost: number | null;
}

export interface ByggesakData {
  saksnummer: string;
  sakstype: string;
  tittel: string;
  status: string;
  vedtaksdato: string | null;
  innsendtdato: string | null;
  tiltakstype: string;
  tiltakshaver: string;
  ansvarlig_soeker: string;
  beskrivelse: string;
  dokumenter: Record<string, unknown>[];
  kilde: string;
}

export interface KommuneData {
  kommunenummer: string;
  kommunenavn: string;
  innsyn_url: string | null;
}

export interface PropertyAIAnalysis {
  eiendom_id: string;
  risiko_nivaa: 'LAV' | 'MIDDELS' | 'HØY' | 'KRITISK';
  risiko_score: number;
  sammendrag: string;
  nøkkelfinninger: string[];
  anbefalinger: string[];
  avviksvurdering: string;
  dispensasjonsgrunnlag: string;
  reguleringsplan_vurdering: string;
  dok_analyse_vurdering: string;
  fraskrivelse: string;
  model_used: string;
}

export interface VerdiestimatorData {
  estimert_verdi: number | null;
  konfidensintervall: [number, number] | null;
  estimat_metode: string;
  pris_per_kvm: number | null;
  kommune_median_pris: number | null;
  kommune_prisvekst_prosent: number | null;
  statistikk_aar: number | null;
  boligtype: string;
  byggeaar: number | null;
}

export interface NaboEiendomData {
  gnr: number;
  bnr: number;
  avstand_meter: number | null;
  adresse: string;
  se_eiendom_url: string;
}

export interface NaboAnalyseResult {
  kommunenummer: string;
  gnr: number;
  bnr: number;
  antall_naboer: number;
  naboer: NaboEiendomData[];
  feilmelding: string | null;
}

// ─── Planslurpen (DiBK) – AI-strukturerte planbestemmelser ────────────────────

export interface Planbestemmelse {
  kode: string;
  tittel: string;
  tekst: string;
  verdi: string | null;
  kategori: string;
}

export interface PlanslurpenPlanData {
  plan_id: string;
  plan_navn: string;
  plantype: string;
  maks_hoyde: string | null;
  maks_utnyttelse: string | null;
  tillatt_bruk: string[];
  droemmeplan_url: string | null;
  antall_bestemmelser: number;
  bestemmelser: Planbestemmelse[];
}

export interface PlanslurpenData {
  antall_planer: number;
  feilmelding: string | null;
  planer: PlanslurpenPlanData[];
}

export interface FullPropertyResult {
  kommunenummer: string;
  gnr: number;
  bnr: number;
  fnr: number | null;
  snr: number | null;
  se_eiendom_url: string;
  eiendom: MatrikkelEiendomData | null;
  bygninger: MatrikkelBygningData[];
  byggesaker: ByggesakData[];
  kommune: KommuneData | null;
  eiendomskart_wms_url: string;
  kommuneplan_wms_url: string;
  kartverket_feilmeldinger: string[];
  // Arealplaner-data (fra /lookup)
  planrapport: {
    gjeldende_planer: {
      plan_id: string;
      plan_navn: string;
      plan_type: string;
      status: string;
      vedtaksdato: string | null;
      arealformål: string;
      url: string;
    }[];
    dispensasjoner: {
      saks_id: string;
      saks_type: string;
      vedtaksdato: string | null;
      status: string;
      beskrivelse: string;
      paragraf: string;
    }[];
    planrapport_url: string | null;
    feilmelding: string | null;
  } | null;
  dok_analyse: {
    berørte_datasett: { uuid: string; navn: string; tema: string; url: string }[];
    antall_berørt: number;
    antall_ikke_berørt: number;
    rapport_url: string | null;
    feilmelding: string | null;
  } | null;
  feilmeldinger: string[];
  verdiestimator: VerdiestimatorData | null;
  planslurpen?: PlanslurpenData | null;
}
