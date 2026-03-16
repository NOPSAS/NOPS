import { fetchJSON, fetchUpload, setAuthToken, clearAuthToken } from './utils';
import type {
  AuthResponse,
  User,
  PropertyCase,
  CreateCasePayload,
  UpdateCasePayload,
  SourceDocument,
  Deviation,
  UpdateDeviationPayload,
  ArchitectReview,
  UpdateReviewPayload,
  AssessmentReport,
  StructuredPlan,
  MunicipalityRequest,
  Rule,
  PropertyLookupResult,
  DokAnalyseResult,
  PlanrapportResult,
  FullPropertyResult,
  ByggesakData,
  PropertyAIAnalysis,
  NaboAnalyseResult,
} from './types';

// ─── Auth ─────────────────────────────────────────────────────────────────────

/**
 * Authenticate with email + password. Stores the returned token.
 */
export async function login(
  email: string,
  password: string
): Promise<AuthResponse> {
  // OAuth2 password flow — form-encoded body
  const body = new URLSearchParams({ username: email, password });
  const response = await fetchJSON<AuthResponse>('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: body.toString(),
    skipAuth: true,
  });
  setAuthToken(response.access_token);
  return response;
}

/**
 * Register a new architect account.
 */
export async function register(
  email: string,
  password: string,
  fullName: string
): Promise<AuthResponse> {
  const response = await fetchJSON<AuthResponse>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, full_name: fullName }),
    skipAuth: true,
  });
  setAuthToken(response.access_token);
  return response;
}

/**
 * Fetch the currently authenticated user's profile.
 */
export async function getMe(): Promise<User> {
  return fetchJSON<User>('/api/v1/auth/me');
}

/**
 * Log the current user out by clearing the stored token.
 */
export function logout(): void {
  clearAuthToken();
}

// ─── Cases ────────────────────────────────────────────────────────────────────

/**
 * Retrieve all cases for the authenticated architect.
 */
export async function getCases(): Promise<PropertyCase[]> {
  return fetchJSON<PropertyCase[]>('/api/v1/cases');
}

/**
 * Retrieve a single case by ID.
 */
export async function getCase(id: string): Promise<PropertyCase> {
  return fetchJSON<PropertyCase>(`/api/v1/cases/${id}`);
}

/**
 * Create a new property case.
 */
export async function createCase(
  data: CreateCasePayload
): Promise<PropertyCase> {
  return fetchJSON<PropertyCase>('/api/v1/cases', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Update an existing case (status, property info, etc.).
 */
export async function updateCase(
  id: string,
  data: UpdateCasePayload
): Promise<PropertyCase> {
  return fetchJSON<PropertyCase>(`/api/v1/cases/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

/**
 * Delete a case permanently.
 */
export async function deleteCase(id: string): Promise<void> {
  return fetchJSON<void>(`/api/v1/cases/${id}`, { method: 'DELETE' });
}

// ─── Documents ────────────────────────────────────────────────────────────────

/**
 * List all source documents belonging to a case.
 */
export async function getDocuments(caseId: string): Promise<SourceDocument[]> {
  return fetchJSON<SourceDocument[]>(`/api/v1/cases/${caseId}/documents`);
}

/**
 * Upload a document (PDF, image) to a case using multipart/form-data.
 */
export async function uploadDocument(
  caseId: string,
  file: File,
  sourceType?: string
): Promise<SourceDocument> {
  const formData = new FormData();
  formData.append('file', file);
  if (sourceType) {
    formData.append('source_type', sourceType);
  }
  return fetchUpload<SourceDocument>(
    `/api/v1/cases/${caseId}/documents`,
    formData
  );
}

/**
 * Delete a document from a case.
 */
export async function deleteDocument(
  caseId: string,
  docId: string
): Promise<void> {
  return fetchJSON<void>(`/api/v1/cases/${caseId}/documents/${docId}`, {
    method: 'DELETE',
  });
}

// ─── Deviations ───────────────────────────────────────────────────────────────

/**
 * Retrieve all detected deviations for a case.
 */
export async function getDeviations(caseId: string): Promise<Deviation[]> {
  return fetchJSON<Deviation[]>(`/api/v1/cases/${caseId}/deviations`);
}

/**
 * Update a deviation (architect note, status change).
 */
export async function updateDeviation(
  caseId: string,
  devId: string,
  data: UpdateDeviationPayload
): Promise<Deviation> {
  return fetchJSON<Deviation>(
    `/api/v1/cases/${caseId}/deviations/${devId}`,
    {
      method: 'PATCH',
      body: JSON.stringify(data),
    }
  );
}

// ─── Reviews ──────────────────────────────────────────────────────────────────

/**
 * Fetch the architect review for a case.
 */
export async function getReview(caseId: string): Promise<ArchitectReview> {
  return fetchJSON<ArchitectReview>(`/api/v1/cases/${caseId}/review`);
}

/**
 * Create a new review for a case (starts the review workflow).
 */
export async function createReview(
  caseId: string
): Promise<ArchitectReview> {
  return fetchJSON<ArchitectReview>(`/api/v1/cases/${caseId}/review`, {
    method: 'POST',
  });
}

/**
 * Update the architect review (comments, status transitions).
 */
export async function updateReview(
  caseId: string,
  data: UpdateReviewPayload
): Promise<ArchitectReview> {
  return fetchJSON<ArchitectReview>(`/api/v1/cases/${caseId}/review`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

/**
 * Mark the assessment report as approved by the architect.
 */
export async function approveReport(
  caseId: string
): Promise<AssessmentReport> {
  return fetchJSON<AssessmentReport>(
    `/api/v1/cases/${caseId}/report/approve`,
    { method: 'POST' }
  );
}

// ─── Assessment Report ────────────────────────────────────────────────────────

/**
 * Fetch the generated assessment report for a case.
 */
export async function getReport(caseId: string): Promise<AssessmentReport> {
  return fetchJSON<AssessmentReport>(`/api/v1/cases/${caseId}/report`);
}

/**
 * Trigger report generation for a case.
 */
export async function generateReport(
  caseId: string
): Promise<AssessmentReport> {
  return fetchJSON<AssessmentReport>(`/api/v1/cases/${caseId}/report/generate`, {
    method: 'POST',
  });
}

// ---- Plans ----
export async function getPlans(caseId: string): Promise<StructuredPlan[]> {
  return fetchJSON<StructuredPlan[]>(`/api/v1/cases/${caseId}/plans`);
}

export async function getPlan(caseId: string, planId: string): Promise<StructuredPlan> {
  return fetchJSON<StructuredPlan>(`/api/v1/cases/${caseId}/plans/${planId}`);
}

// ---- Municipality Requests ----
export async function getMunicipalityRequests(caseId: string): Promise<MunicipalityRequest[]> {
  return fetchJSON<MunicipalityRequest[]>(`/api/v1/cases/${caseId}/municipality-requests`);
}

export async function createMunicipalityRequest(
  caseId: string,
  data: { request_type?: string; request_method?: string }
): Promise<MunicipalityRequest> {
  return fetchJSON<MunicipalityRequest>(`/api/v1/cases/${caseId}/municipality-requests`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ---- Rules ----
export async function getRules(source?: string): Promise<Rule[]> {
  const params = source ? `?source=${source}` : '';
  return fetchJSON<Rule[]>(`/api/v1/rules${params}`);
}

// ---- Property Lookup (DOK-analyse + Arealplaner) ----

/**
 * Komplett eiendomsoppslag – planrapport, DOK-analyse, dispensasjoner og arealplaner.
 */
export async function propertyLookup(
  knr: string,
  gnr: string,
  bnr: string,
  options?: { includeDok?: boolean; includeDispensasjoner?: boolean }
): Promise<PropertyLookupResult> {
  const params = new URLSearchParams({ knr, gnr, bnr });
  if (options?.includeDok === false) params.set('include_dok', 'false');
  if (options?.includeDispensasjoner === false) params.set('include_dispensasjoner', 'false');
  return fetchJSON<PropertyLookupResult>(`/api/v1/property/lookup?${params.toString()}`);
}

/**
 * Hent planrapport for en eiendom.
 */
export async function getPlanrapport(
  knr: string,
  gnr: string,
  bnr: string
): Promise<PlanrapportResult> {
  const params = new URLSearchParams({ knr, gnr, bnr });
  return fetchJSON<PlanrapportResult>(`/api/v1/property/planrapport?${params.toString()}`);
}

/**
 * Hent DOK-analyse for en eiendom.
 */
export async function getDokAnalyse(
  knr: string,
  gnr: string,
  bnr: string
): Promise<DokAnalyseResult> {
  const params = new URLSearchParams({ knr, gnr, bnr });
  return fetchJSON<DokAnalyseResult>(`/api/v1/property/dok-analyse?${params.toString()}`);
}

/**
 * Hent komplett eiendomsdata fra alle datakilder (Kartverket + Arealplaner).
 */
export async function getFullPropertyData(
  knr: string,
  gnr: string,
  bnr: string,
  fnr?: string,
  snr?: string,
): Promise<FullPropertyResult> {
  const params = new URLSearchParams({ knr, gnr, bnr });
  if (fnr) params.set('fnr', fnr);
  if (snr) params.set('snr', snr);
  return fetchJSON<FullPropertyResult>(`/api/v1/property/full?${params.toString()}`);
}

/**
 * Hent byggesaker for en eiendom fra kommunalt arkiv.
 */
export async function getByggesaker(
  knr: string,
  gnr: string,
  bnr: string,
): Promise<{ antall_saker: number; byggesaker: ByggesakData[] }> {
  const params = new URLSearchParams({ knr, gnr, bnr });
  return fetchJSON(`/api/v1/property/byggesaker?${params.toString()}`);
}

// ─── Address search ───────────────────────────────────────────────────────────

export interface AddressSuggestion {
  adressetekst: string;
  adressenavn: string;
  husnummer: number | null;
  bokstav: string;
  postnummer: string;
  poststed: string;
  kommunenummer: string;
  kommunenavn: string;
  gnr: number | null;
  bnr: number | null;
  fnr: number | null;
  snr: number | null;
  lat: number | null;
  lon: number | null;
}

/**
 * Hent adresseforslag for autocomplete.
 */
export async function getAddressSuggestions(q: string): Promise<AddressSuggestion[]> {
  if (q.length < 3) return [];
  const params = new URLSearchParams({ q });
  return fetchJSON<AddressSuggestion[]>(`/api/v1/search/suggest?${params.toString()}`);
}

/**
 * Slå opp gnr/bnr fra adresse.
 */
export async function lookupAddress(adresse: string): Promise<{
  funnet: boolean;
  adressetekst?: string;
  postnummer?: string;
  poststed?: string;
  kommunenummer?: string;
  kommunenavn?: string;
  gnr?: number;
  bnr?: number;
  lat?: number;
  lon?: number;
}> {
  const params = new URLSearchParams({ adresse });
  return fetchJSON(`/api/v1/search/address?${params.toString()}`);
}

export async function getNaboer(knr: string, gnr: string, bnr: string): Promise<NaboAnalyseResult> {
  return fetchJSON<NaboAnalyseResult>(`/api/v1/property/naboer?knr=${encodeURIComponent(knr)}&gnr=${encodeURIComponent(gnr)}&bnr=${encodeURIComponent(bnr)}`);
}

// ─── Billing ──────────────────────────────────────────────────────────────────

export async function getBillingSubscription() {
  return fetchJSON('/api/v1/billing/subscription');
}

export async function createCheckout(priceId: string) {
  return fetchJSON<{ checkout_url: string }>(
    `/api/v1/billing/checkout?price_id=${encodeURIComponent(priceId)}`,
    { method: 'POST' }
  );
}

export async function createBillingPortal() {
  return fetchJSON<{ portal_url: string }>('/api/v1/billing/portal', { method: 'POST' });
}

/**
 * Kjør AI-analyse av en eiendom.
 */
export async function getPropertyAIAnalysis(
  knr: string,
  gnr: string,
  bnr: string,
): Promise<PropertyAIAnalysis> {
  const params = new URLSearchParams({ knr, gnr, bnr });
  return fetchJSON<PropertyAIAnalysis>(`/api/v1/property/analyse?${params.toString()}`, {
    method: 'POST',
  });
}
