"""
ByggSjekk – Document classification service.

Provides:
  DocumentClassifier          – classify filename + content preview → document_type
  SourceConfidenceClassifier  – derive ApprovalStatus from source metadata
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Document type definitions
# ---------------------------------------------------------------------------

# (pattern, document_type, priority)
# Higher priority wins when multiple patterns match.
_FILENAME_RULES: list[tuple[re.Pattern[str], str, int]] = [
    (re.compile(r"situasjonsplan", re.IGNORECASE), "situasjonsplan", 10),
    (re.compile(r"(plan|plantegning|floor.?plan)", re.IGNORECASE), "floor_plan", 9),
    (re.compile(r"snitt|section", re.IGNORECASE), "section_drawing", 8),
    (re.compile(r"fasade|facade|elevation", re.IGNORECASE), "facade_drawing", 8),
    (re.compile(r"(tegning|drawing)", re.IGNORECASE), "architectural_drawing", 5),
    (re.compile(r"rammetillatelse", re.IGNORECASE), "building_permit_framework", 10),
    (re.compile(r"igangsettingstillatelse|ig[- ]?tillatelse", re.IGNORECASE), "building_permit_start", 10),
    (re.compile(r"(brukstillatelse|ferdigattest)", re.IGNORECASE), "completion_certificate", 10),
    (re.compile(r"dispensasjon", re.IGNORECASE), "dispensation_application", 9),
    (re.compile(r"nabovarsel", re.IGNORECASE), "neighbour_notification", 8),
    (re.compile(r"reguleringsplan", re.IGNORECASE), "zoning_plan", 9),
    (re.compile(r"(rapport|report)", re.IGNORECASE), "report", 4),
    (re.compile(r"kontrakt|contract", re.IGNORECASE), "contract", 6),
    (re.compile(r"\.(pdf)$", re.IGNORECASE), "pdf_document", 1),
    (re.compile(r"\.(dwg|dxf)$", re.IGNORECASE), "cad_drawing", 7),
    (re.compile(r"\.(ifc)$", re.IGNORECASE), "bim_model", 8),
]

_CONTENT_RULES: list[tuple[re.Pattern[str], str, int]] = [
    (re.compile(r"situasjonsplan", re.IGNORECASE), "situasjonsplan", 10),
    (re.compile(r"etasjeplan|planløsning", re.IGNORECASE), "floor_plan", 9),
    (re.compile(r"snitt[tegning]*\s+[A-Z]-[A-Z]", re.IGNORECASE), "section_drawing", 8),
    (re.compile(r"(nord|syd|øst|vest)fasade", re.IGNORECASE), "facade_drawing", 8),
    (re.compile(r"rammetillatelse", re.IGNORECASE), "building_permit_framework", 10),
    (re.compile(r"igangsettingstillatelse", re.IGNORECASE), "building_permit_start", 10),
    (re.compile(r"(brukstillatelse|ferdigattest)", re.IGNORECASE), "completion_certificate", 10),
    (re.compile(r"dispensasjon.*§", re.IGNORECASE), "dispensation_application", 9),
    (re.compile(r"nabovarsel|nabo", re.IGNORECASE), "neighbour_notification", 7),
]


@dataclass
class ClassificationResult:
    document_type: str
    confidence: float
    method: str  # "rule_based" | "llm" | "fallback"


@dataclass
class ApprovalClassificationResult:
    status: str  # "VERIFIED_APPROVED" | "ASSUMED_APPROVED" | "RECEIVED" | "UNKNOWN"
    confidence: float


class DocumentClassifier:
    """Classify a document by filename and/or content preview.

    Strategy:
    1. Apply filename regex rules (highest priority).
    2. Apply content preview regex rules.
    3. Fall back to LLM if no confident rule-based match is found
       (LLM call is currently a stub – returns a low-confidence unknown).
    """

    def __init__(self, llm_confidence_threshold: float = 0.5) -> None:
        self._llm_threshold = llm_confidence_threshold

    def classify(
        self,
        filename: str,
        content_preview: str = "",
    ) -> ClassificationResult:
        """Classify a document and return a ClassificationResult."""
        result = self._rule_based(filename, content_preview)
        if result.confidence < self._llm_threshold:
            llm_result = self._llm_classify(filename, content_preview)
            if llm_result.confidence > result.confidence:
                result = llm_result

        logger.debug(
            "Classified '%s' as '%s' (confidence=%.2f, method=%s)",
            filename,
            result.document_type,
            result.confidence,
            result.method,
        )
        return result

    def _rule_based(
        self, filename: str, content_preview: str
    ) -> ClassificationResult:
        best_type = "unknown"
        best_score = 0
        best_priority = 0

        # Filename rules
        for pattern, doc_type, priority in _FILENAME_RULES:
            if pattern.search(filename):
                score = priority / 10.0
                if priority > best_priority or (
                    priority == best_priority and score > best_score
                ):
                    best_type = doc_type
                    best_score = score
                    best_priority = priority

        # Content rules (only applied if content is present)
        if content_preview:
            for pattern, doc_type, priority in _CONTENT_RULES:
                if pattern.search(content_preview):
                    score = (priority / 10.0) * 0.9  # slight penalty vs filename
                    if priority > best_priority or (
                        priority == best_priority and score > best_score
                    ):
                        best_type = doc_type
                        best_score = score
                        best_priority = priority

        return ClassificationResult(
            document_type=best_type,
            confidence=min(best_score, 1.0),
            method="rule_based",
        )

    def _llm_classify(self, filename: str, content_preview: str) -> ClassificationResult:
        """
        LLM-based classification using the configured LLMAdapter.
        Falls back to low-confidence 'other' if LLM is unavailable.
        """
        import asyncio
        try:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../apps/api"))
            from app.services.llm_adapter import get_llm_adapter
            adapter = get_llm_adapter()

            # Run async method in sync context
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(
                    adapter.classify_document(filename, content_preview)
                )
            finally:
                loop.close()

            return ClassificationResult(
                document_type=result.document_type,
                confidence=result.confidence,
                method="llm",
            )
        except Exception as exc:
            import logging
            logging.getLogger(__name__).debug("LLM classify failed, using stub: %s", exc)
            return ClassificationResult(
                document_type="other",
                confidence=0.1,
                method="llm_unavailable",
            )


# ---------------------------------------------------------------------------
# Approval-status classifier
# ---------------------------------------------------------------------------


class SourceConfidenceClassifier:
    """Infer the approval status and confidence of a source document.

    Rules (Norwegian building permit process):
    - If the source is a municipality fetch → VERIFIED_APPROVED (high confidence).
    - If the source is an email request → depends on metadata signals.
    - If the source is a user upload with a document_type indicating a permit
      with a date more than 3 months old → ASSUMED_APPROVED (medium confidence).
    - Otherwise → UNKNOWN.
    """

    def classify_source(
        self,
        source_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> ApprovalClassificationResult:
        """Return an ApprovalClassificationResult with status and confidence."""
        meta = metadata or {}

        if source_type == "FETCHED_MUNICIPALITY":
            return ApprovalClassificationResult(
                status="VERIFIED_APPROVED",
                confidence=0.95,
            )

        if source_type == "EMAIL_REQUEST":
            if meta.get("municipality_confirmed"):
                return ApprovalClassificationResult(
                    status="VERIFIED_APPROVED",
                    confidence=0.80,
                )
            return ApprovalClassificationResult(
                status="ASSUMED_APPROVED",
                confidence=0.55,
            )

        # UPLOADED – look for permit-type hints in metadata
        doc_type = meta.get("document_type", "")
        permit_types = {
            "building_permit_framework",
            "building_permit_start",
            "completion_certificate",
        }
        if doc_type in permit_types:
            return ApprovalClassificationResult(
                status="RECEIVED",
                confidence=0.60,
            )

        return ApprovalClassificationResult(
            status="UNKNOWN",
            confidence=0.20,
        )
