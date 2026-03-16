"""
Document processing pipeline — called by the ARQ background job.

Separated from jobs.py for testability.
"""
from __future__ import annotations

import logging
import sys
import os
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root and services to path (works both locally and in Docker /app context)
_here = os.path.dirname(os.path.abspath(__file__))
_api_root = os.path.join(_here, "../../..")  # apps/api/
_project_root = os.path.join(_api_root, "../..")  # project root (local dev)
_services_local = os.path.join(_project_root, "services")
_services_docker = "/app/services"

for _path in [_api_root, _project_root, _services_local, _services_docker]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    document_id: str
    success: bool
    document_type: str | None = None
    structured_plan_id: str | None = None
    deviations_found: int = 0
    rule_matches_found: int = 0
    error: str | None = None
    steps_completed: list[str] = field(default_factory=list)


async def run_document_pipeline(
    db: AsyncSession,
    storage_adapter: Any,
    document_id: str,
) -> PipelineResult:
    """
    Full document processing pipeline:
    1. Download from storage
    2. Classify document
    3. Parse plan (if floor_plan / situasjonsplan)
    4. Persist StructuredPlan + Spaces
    5. Find reference plan for this case
    6. Run DeviationEngine (if reference plan exists)
    7. Persist Deviations
    8. Run RuleMatcher for each deviation
    9. Persist RuleMatches
    10. Update case status

    Returns a PipelineResult describing what happened.
    """
    from app.models.property_case import (
        SourceDocument, StructuredPlan, Space, Deviation, RuleMatch,
        ProcessingStatus, DeviationCategory, Severity, DeviationStatus,
        ApprovalStatus,
    )

    result = PipelineResult(document_id=document_id, success=False)

    # ------------------------------------------------------------------
    # Fetch document
    # ------------------------------------------------------------------
    doc_result = await db.execute(
        select(SourceDocument).where(SourceDocument.id == document_id)
    )
    doc = doc_result.scalar_one_or_none()
    if doc is None:
        result.error = f"Document {document_id} not found"
        return result

    # ------------------------------------------------------------------
    # Step 1: Download
    # ------------------------------------------------------------------
    try:
        file_bytes = await storage_adapter.download(doc.storage_key)
        result.steps_completed.append("download")
    except Exception as exc:
        result.error = f"Download failed: {exc}"
        return result

    # ------------------------------------------------------------------
    # Step 2: Classify
    # ------------------------------------------------------------------
    try:
        from services.document_ingestion.classifier import DocumentClassifier, SourceConfidenceClassifier
        classifier = DocumentClassifier()
        content_preview = ""
        # Try to decode text for content-based classification (PDFs may not decode)
        try:
            content_preview = file_bytes[:2000].decode("utf-8", errors="ignore")
        except Exception:
            pass

        classification = classifier.classify(doc.original_filename or doc.filename, content_preview)
        doc.document_type = classification.document_type
        doc.document_type_confidence = classification.confidence

        # Classify approval status based on source
        source_classifier = SourceConfidenceClassifier()
        approval_result = source_classifier.classify_source(
            str(doc.source_type.value) if hasattr(doc.source_type, "value") else str(doc.source_type),
            {}
        )
        doc.approval_status = approval_result.status
        doc.approval_status_confidence = approval_result.confidence

        await db.flush()
        result.document_type = classification.document_type
        result.steps_completed.append("classify")
        logger.info("Document %s classified as %s (conf=%.2f)", document_id, classification.document_type, classification.confidence)
    except Exception as exc:
        logger.warning("Classification failed for %s: %s", document_id, exc)
        result.steps_completed.append("classify_failed")

    # ------------------------------------------------------------------
    # Step 3: Parse plan (only for plan documents)
    # ------------------------------------------------------------------
    plan_types = {"floor_plan", "situasjonsplan", "plantegning", "plan"}
    if doc.document_type not in plan_types:
        logger.info("Document %s is not a plan document (%s), skipping plan parsing", document_id, doc.document_type)
        result.success = True
        result.steps_completed.append("parse_skipped")
        return result

    try:
        from services.plan_parser.parser import MockPlanParser
        parser = MockPlanParser()
        plan_data = await parser.parse(str(doc.id), doc.storage_key)
        result.steps_completed.append("parse")
        logger.info("Parsed plan for %s: %d floors, %d rooms", document_id, len(plan_data.floors), plan_data.room_count or 0)
    except Exception as exc:
        result.error = f"Plan parsing failed: {exc}"
        logger.error("Plan parsing failed for %s: %s", document_id, exc)
        return result

    # ------------------------------------------------------------------
    # Step 4: Persist StructuredPlan + Spaces
    # ------------------------------------------------------------------
    try:
        import uuid
        structured_plan = StructuredPlan(
            id=str(uuid.uuid4()),
            document_id=str(doc.id),
            case_id=str(doc.case_id),
            plan_data=plan_data.model_dump(),
            total_area=plan_data.total_area,
            room_count=plan_data.room_count,
            version=1,
        )
        db.add(structured_plan)
        await db.flush()

        # Persist spaces
        for floor in plan_data.floors:
            for space in floor.spaces:
                space_record = Space(
                    id=str(uuid.uuid4()),
                    plan_id=str(structured_plan.id),
                    name=space.name,
                    space_type=space.space_type,
                    floor_number=space.floor_number,
                    area=space.area,
                    confidence=space.confidence,
                    attributes=space.attributes or {},
                )
                db.add(space_record)

        await db.flush()
        result.structured_plan_id = str(structured_plan.id)
        result.steps_completed.append("persist_plan")
        logger.info("Persisted StructuredPlan %s", structured_plan.id)
    except Exception as exc:
        result.error = f"Plan persistence failed: {exc}"
        logger.error("Plan persistence failed for %s: %s", document_id, exc)
        return result

    # ------------------------------------------------------------------
    # Step 5: Find reference plan (most recent approved plan, not this doc)
    # ------------------------------------------------------------------
    try:
        from sqlalchemy import and_
        from app.models.property_case import SourceDocument as SD

        # Look for other documents in this case with approved status
        ref_plan_result = await db.execute(
            select(StructuredPlan)
            .join(SD, StructuredPlan.document_id == SD.id)
            .where(
                and_(
                    SD.case_id == doc.case_id,
                    SD.id != doc.id,
                    SD.approval_status.in_([
                        ApprovalStatus.VERIFIED_APPROVED,
                        ApprovalStatus.ASSUMED_APPROVED,
                        ApprovalStatus.RECEIVED,
                    ])
                )
            )
            .order_by(SD.created_at.asc())
        )
        reference_plan_record = ref_plan_result.scalars().first()

        if reference_plan_record is None:
            logger.info("No reference plan found for case %s – document %s is the reference.", doc.case_id, document_id)
            result.success = True
            result.steps_completed.append("no_reference_plan")
            return result

        result.steps_completed.append("find_reference")
    except Exception as exc:
        result.error = f"Reference plan lookup failed: {exc}"
        return result

    # ------------------------------------------------------------------
    # Step 6: Run DeviationEngine
    # ------------------------------------------------------------------
    try:
        from services.deviation_engine.engine import DeviationEngine
        from services.plan_parser.parser import StructuredPlanData

        reference_plan_data = StructuredPlanData.model_validate(reference_plan_record.plan_data)
        engine = DeviationEngine()
        deviation_results = engine.compare(reference_plan_data, plan_data)
        result.steps_completed.append("deviation_engine")
        logger.info("DeviationEngine found %d deviations for %s", len(deviation_results), document_id)
    except Exception as exc:
        result.error = f"Deviation engine failed: {exc}"
        logger.error("DeviationEngine failed for %s: %s", document_id, exc)
        return result

    # ------------------------------------------------------------------
    # Step 7: Persist Deviations
    # ------------------------------------------------------------------
    try:
        import uuid
        deviation_records = []
        for dev_result in deviation_results:
            # Map DeviationEngine category string to enum
            try:
                category = DeviationCategory(dev_result.category)
            except ValueError:
                # If engine returns old-style category, map it
                category = _map_legacy_category(dev_result.category)

            severity = _map_severity(dev_result.severity)

            deviation = Deviation(
                id=str(uuid.uuid4()),
                case_id=str(doc.case_id),
                category=category,
                severity=severity,
                description=dev_result.description,
                confidence=dev_result.confidence,
                evidence_ids=dev_result.evidence_references or [],
                rule_ids=[],
                status=DeviationStatus.OPEN,
            )
            db.add(deviation)
            deviation_records.append((deviation, dev_result))

        await db.flush()
        result.deviations_found = len(deviation_records)
        result.steps_completed.append("persist_deviations")
    except Exception as exc:
        result.error = f"Deviation persistence failed: {exc}"
        logger.error("Deviation persistence failed for %s: %s", document_id, exc)
        return result

    # ------------------------------------------------------------------
    # Step 8–9: Run RuleMatcher + Persist RuleMatches
    # ------------------------------------------------------------------
    try:
        from services.rule_engine.registry import RuleRegistry, RuleMatcher

        registry = RuleRegistry()
        await registry.load_from_db(db)
        matcher = RuleMatcher(registry)

        import uuid
        total_matches = 0
        for deviation, dev_result in deviation_records:
            matches = matcher.find_matching_rules(dev_result)
            for match in matches:
                rule_ids = list(deviation.rule_ids or [])
                if match.rule_code not in rule_ids:
                    rule_ids.append(match.rule_code)
                deviation.rule_ids = rule_ids

                rule_match = RuleMatch(
                    id=str(uuid.uuid4()),
                    deviation_id=str(deviation.id),
                    rule_id=match.rule_code,  # Use rule_code as reference (rule may not be in DB yet)
                    rationale=match.rationale,
                    confidence=match.confidence,
                    match_type=match.match_type,
                )
                db.add(rule_match)
                total_matches += 1

        await db.flush()
        result.rule_matches_found = total_matches
        result.steps_completed.append("rule_matching")
    except Exception as exc:
        logger.warning("Rule matching failed for %s: %s (non-fatal)", document_id, exc)
        result.steps_completed.append("rule_matching_failed")

    # ------------------------------------------------------------------
    # Step 10: Commit and return success
    # ------------------------------------------------------------------
    result.success = True
    result.steps_completed.append("complete")
    return result


def _map_legacy_category(category_str: str) -> "DeviationCategory":
    """Map old technical category names to new domain category names."""
    from app.models.property_case import DeviationCategory
    mapping = {
        "AREA_DEVIATION": DeviationCategory.ADDITION_DETECTED,
        "ROOM_COUNT": DeviationCategory.ADDITION_DETECTED,
        "ROOM_TYPE": DeviationCategory.ROOM_DEFINITION_CHANGE,
        "FLOOR_PLAN": DeviationCategory.ADDITION_DETECTED,
        "FACADE": DeviationCategory.USE_CHANGE_INDICATION,
        "HEIGHT": DeviationCategory.USE_CHANGE_INDICATION,
        "SETBACK": DeviationCategory.UNINSPECTED_AREA,
        "ACCESSIBILITY": DeviationCategory.UNINSPECTED_AREA,
        "FIRE_SAFETY": DeviationCategory.UNINSPECTED_AREA,
        "ENERGY": DeviationCategory.UNINSPECTED_AREA,
    }
    return mapping.get(category_str, DeviationCategory.UNINSPECTED_AREA)


def _map_severity(severity_str: str) -> "Severity":
    from app.models.property_case import Severity
    mapping = {
        "LOW": Severity.LOW,
        "MEDIUM": Severity.MEDIUM,
        "HIGH": Severity.HIGH,
        "CRITICAL": Severity.CRITICAL,
    }
    return mapping.get(str(severity_str).upper(), Severity.MEDIUM)
