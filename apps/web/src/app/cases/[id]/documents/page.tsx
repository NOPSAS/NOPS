'use client';

import * as React from 'react';
import { useParams } from 'next/navigation';
import useSWR from 'swr';
import {
  Upload,
  FileText,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Clock,
  HelpCircle,
  X,
  File,
} from 'lucide-react';
import { getDocuments, uploadDocument, deleteDocument } from '@/lib/api';
import { formatDate, formatFileSize } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import type { ApprovalStatus, ProcessingStatus, SourceDocument } from '@/lib/types';

// ─── Status helpers ───────────────────────────────────────────────────────────

function approvalBadgeVariant(
  status: ApprovalStatus
): 'success' | 'warning' | 'info' | 'muted' {
  switch (status) {
    case 'VERIFIED_APPROVED': return 'success';
    case 'ASSUMED_APPROVED': return 'warning';
    case 'RECEIVED': return 'info';
    default: return 'muted';
  }
}

function approvalLabel(status: ApprovalStatus): string {
  switch (status) {
    case 'VERIFIED_APPROVED': return 'Bekreftet godkjent';
    case 'ASSUMED_APPROVED': return 'Antatt godkjent';
    case 'RECEIVED': return 'Mottatt';
    default: return 'Ukjent';
  }
}

function ApprovalIcon({ status }: { status: ApprovalStatus }) {
  switch (status) {
    case 'VERIFIED_APPROVED':
      return <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />;
    case 'ASSUMED_APPROVED':
      return <AlertCircle className="h-3.5 w-3.5 text-yellow-600" />;
    case 'RECEIVED':
      return <Clock className="h-3.5 w-3.5 text-blue-600" />;
    default:
      return <HelpCircle className="h-3.5 w-3.5 text-slate-400" />;
  }
}

function processingLabel(status: ProcessingStatus): string {
  switch (status) {
    case 'PENDING': return 'Venter';
    case 'PROCESSING': return 'Behandles';
    case 'COMPLETED': return 'Ferdig';
    case 'FAILED': return 'Feilet';
    default: return status;
  }
}

function ProcessingBadge({ status }: { status: ProcessingStatus }) {
  if (status === 'COMPLETED') return null;
  const variant =
    status === 'FAILED'
      ? ('destructive' as const)
      : status === 'PROCESSING'
      ? ('info' as const)
      : ('muted' as const);
  return (
    <Badge variant={variant} className="text-[10px] px-1.5 py-0">
      {processingLabel(status)}
    </Badge>
  );
}

// ─── Upload zone ──────────────────────────────────────────────────────────────

interface UploadZoneProps {
  onFilesSelected: (files: File[]) => void;
  uploading: boolean;
}

function UploadZone({ onFilesSelected, uploading }: UploadZoneProps) {
  const [dragging, setDragging] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const files = Array.from(e.dataTransfer.files).filter(
      (f) =>
        f.type === 'application/pdf' ||
        f.type.startsWith('image/')
    );
    if (files.length > 0) onFilesSelected(files);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    if (files.length > 0) onFilesSelected(files);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => !uploading && inputRef.current?.click()}
      className={`
        flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed
        p-10 text-center cursor-pointer transition-colors select-none
        ${dragging
          ? 'border-blue-400 bg-blue-50 dark:border-blue-600 dark:bg-blue-950'
          : 'border-slate-300 hover:border-blue-300 hover:bg-slate-50 dark:border-slate-600 dark:hover:bg-slate-800'
        }
        ${uploading ? 'opacity-60 cursor-not-allowed' : ''}
      `}
      role="button"
      tabIndex={0}
      aria-label="Last opp dokumenter"
      onKeyDown={(e) => e.key === 'Enter' && !uploading && inputRef.current?.click()}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900">
        <Upload className="h-6 w-6 text-blue-600 dark:text-blue-400" />
      </div>
      <div>
        <p className="font-medium text-slate-700 dark:text-slate-300">
          {uploading ? 'Laster opp...' : 'Dra og slipp filer hit'}
        </p>
        <p className="mt-0.5 text-sm text-muted-foreground">
          eller klikk for å velge fra filsystemet
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Støtter PDF og bildefiler (JPG, PNG, TIFF)
        </p>
      </div>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,image/*"
        className="hidden"
        onChange={handleChange}
        disabled={uploading}
      />
    </div>
  );
}

// ─── Document row ─────────────────────────────────────────────────────────────

interface DocumentRowProps {
  doc: SourceDocument;
  onDelete: (id: string) => void;
}

function DocumentRow({ doc, onDelete }: DocumentRowProps) {
  return (
    <div className="flex items-center gap-4 rounded-lg border border-slate-200 bg-white px-4 py-3 dark:border-slate-700 dark:bg-slate-900">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-slate-100 dark:bg-slate-800">
        <File className="h-5 w-5 text-slate-500" />
      </div>

      <div className="flex-1 min-w-0">
        <p className="truncate text-sm font-medium text-slate-900 dark:text-white">
          {doc.filename}
        </p>
        <div className="mt-0.5 flex flex-wrap items-center gap-2">
          <span className="text-xs text-muted-foreground">
            {formatFileSize(doc.file_size)}
          </span>
          <span className="text-xs text-muted-foreground">·</span>
          <span className="text-xs text-muted-foreground">
            {formatDate(doc.uploaded_at)}
          </span>
          <ProcessingBadge status={doc.processing_status} />
        </div>
      </div>

      <div className="shrink-0 flex items-center gap-2">
        <div className="flex items-center gap-1">
          <ApprovalIcon status={doc.approval_status} />
          <Badge variant={approvalBadgeVariant(doc.approval_status)}>
            {approvalLabel(doc.approval_status)}
          </Badge>
        </div>
        <Button
          variant="ghost"
          size="icon-sm"
          className="text-slate-400 hover:text-red-600"
          onClick={() => onDelete(doc.id)}
          aria-label={`Slett ${doc.filename}`}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function DocumentsPage() {
  const params = useParams<{ id: string }>();
  const caseId = params?.id ?? '';

  const { data: documents, isLoading, mutate } = useSWR(
    `documents-${caseId}`,
    () => getDocuments(caseId)
  );

  const [uploading, setUploading] = React.useState(false);
  const [uploadErrors, setUploadErrors] = React.useState<string[]>([]);
  const [deleteTarget, setDeleteTarget] = React.useState<SourceDocument | null>(null);
  const [deleting, setDeleting] = React.useState(false);

  const handleFilesSelected = async (files: File[]) => {
    setUploading(true);
    setUploadErrors([]);
    const errors: string[] = [];

    for (const file of files) {
      try {
        await uploadDocument(caseId, file);
      } catch {
        errors.push(`Kunne ikke laste opp «${file.name}»`);
      }
    }

    setUploadErrors(errors);
    setUploading(false);
    mutate();
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteDocument(caseId, deleteTarget.id);
      mutate();
    } catch {
      // ignore
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
    }
  };

  return (
    <div className="page-container">
      <div className="mb-6">
        <h1 className="section-title">Dokumenter</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Last opp godkjente tegninger, som-bygget-tegninger og bilder
        </p>
      </div>

      {/* Upload zone */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">Last opp dokumenter</CardTitle>
          <CardDescription>
            Tegninger og bilder brukes til å oppdage avvik mellom godkjent plan og nåværende tilstand
          </CardDescription>
        </CardHeader>
        <CardContent>
          <UploadZone
            onFilesSelected={handleFilesSelected}
            uploading={uploading}
          />
          {uploadErrors.length > 0 && (
            <div className="mt-3 space-y-1">
              {uploadErrors.map((e, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300"
                >
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  {e}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Document list */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Opplastede dokumenter
            {documents && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                ({documents.length})
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-14 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800"
                />
              ))}
            </div>
          )}

          {!isLoading && (!documents || documents.length === 0) && (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <FileText className="mb-2 h-8 w-8 text-slate-300" />
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                Ingen dokumenter lastet opp ennå
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Bruk opplastingssonen over for å legge til filer
              </p>
            </div>
          )}

          {documents && documents.length > 0 && (
            <div className="space-y-2">
              {documents.map((doc) => (
                <DocumentRow
                  key={doc.id}
                  doc={doc}
                  onDelete={() => setDeleteTarget(doc)}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Approval status legend */}
      <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
        <span className="font-medium">Godkjenningsstatus:</span>
        <span className="flex items-center gap-1">
          <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />
          Bekreftet godkjent
        </span>
        <span className="flex items-center gap-1">
          <AlertCircle className="h-3.5 w-3.5 text-yellow-600" />
          Antatt godkjent
        </span>
        <span className="flex items-center gap-1">
          <Clock className="h-3.5 w-3.5 text-blue-600" />
          Mottatt
        </span>
        <span className="flex items-center gap-1">
          <HelpCircle className="h-3.5 w-3.5 text-slate-400" />
          Ukjent
        </span>
      </div>

      {/* Delete confirmation dialog */}
      <Dialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Slett dokument</DialogTitle>
            <DialogDescription>
              Er du sikker på at du vil slette{' '}
              <span className="font-medium">«{deleteTarget?.filename}»</span>?
              Dette kan ikke angres.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteTarget(null)}
              disabled={deleting}
            >
              Avbryt
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
              loading={deleting}
            >
              Slett
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
