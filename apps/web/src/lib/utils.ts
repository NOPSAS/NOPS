import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge Tailwind CSS class names, handling conflicts intelligently.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Base URL for the ByggSjekk API, read from environment.
 */
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * Retrieve the stored auth token from localStorage (client-side only).
 */
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('byggsjekk_token');
}

/**
 * Store auth token in localStorage.
 */
export function setAuthToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('byggsjekk_token', token);
}

/**
 * Remove auth token from localStorage.
 */
export function clearAuthToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('byggsjekk_token');
}

export interface FetchOptions extends RequestInit {
  skipAuth?: boolean;
}

/**
 * Generic fetch wrapper that:
 * - Prepends the API base URL
 * - Injects Authorization header with bearer token
 * - Parses JSON response
 * - Throws structured errors on non-2xx responses
 */
export async function fetchJSON<T = unknown>(
  path: string,
  options: FetchOptions = {}
): Promise<T> {
  const { skipAuth = false, headers: extraHeaders, ...rest } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(extraHeaders as Record<string, string>),
  };

  if (!skipAuth) {
    const token = getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  const url = path.startsWith('http') ? path : `${API_BASE_URL}${path}`;

  const response = await fetch(url, {
    ...rest,
    headers,
  });

  if (!response.ok) {
    let errorBody: unknown;
    try {
      errorBody = await response.json();
    } catch {
      errorBody = { detail: response.statusText };
    }
    const error = new Error(
      (errorBody as { detail?: string })?.detail ||
        `HTTP ${response.status}: ${response.statusText}`
    ) as Error & { status: number; body: unknown };
    error.status = response.status;
    error.body = errorBody;
    throw error;
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

/**
 * Upload a file using multipart/form-data (no Content-Type header so browser sets boundary).
 */
export async function fetchUpload<T = unknown>(
  path: string,
  formData: FormData,
  options: FetchOptions = {}
): Promise<T> {
  const { skipAuth = false, headers: extraHeaders, ...rest } = options;

  const headers: Record<string, string> = {
    ...(extraHeaders as Record<string, string>),
  };

  if (!skipAuth) {
    const token = getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  const url = path.startsWith('http') ? path : `${API_BASE_URL}${path}`;

  const response = await fetch(url, {
    method: 'POST',
    ...rest,
    headers,
    body: formData,
  });

  if (!response.ok) {
    let errorBody: unknown;
    try {
      errorBody = await response.json();
    } catch {
      errorBody = { detail: response.statusText };
    }
    const error = new Error(
      (errorBody as { detail?: string })?.detail ||
        `HTTP ${response.status}: ${response.statusText}`
    ) as Error & { status: number; body: unknown };
    error.status = response.status;
    error.body = errorBody;
    throw error;
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

/**
 * Format a Date or ISO string to a Norwegian locale date string.
 */
export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('nb-NO', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

/**
 * Format a Date or ISO string to a Norwegian locale datetime string.
 */
export function formatDateTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleString('nb-NO', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Return a human-readable file size string.
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
