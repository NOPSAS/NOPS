"""
ByggSjekk – ARQ background job definitions.

Worker startup:
  $ arq app.services.jobs.WorkerSettings
"""

from __future__ import annotations

import logging
from typing import Any

import arq.connections

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Job functions
# ---------------------------------------------------------------------------


async def process_document_job(ctx: dict, document_id: str) -> dict:
    """ARQ background job alias for process_document."""
    return await process_document(ctx, document_id)


async def process_document(ctx: dict, document_id: str) -> dict:
    """ARQ background job: run full document processing pipeline."""
    from sqlalchemy import select
    from app.db.base import AsyncSessionLocal
    from app.models.property_case import SourceDocument, ProcessingStatus
    from app.services.storage import get_storage_adapter
    from app.services.pipeline import run_document_pipeline

    logger.info("Starting pipeline for document %s", document_id)

    async with AsyncSessionLocal() as db:
        # Mark as processing
        result = await db.execute(select(SourceDocument).where(SourceDocument.id == document_id))
        doc = result.scalar_one_or_none()
        if doc is None:
            logger.error("Document %s not found", document_id)
            return {"success": False, "error": "Document not found"}

        doc.processing_status = ProcessingStatus.PROCESSING
        await db.commit()
        await db.refresh(doc)

        # Run pipeline in its own transaction
        async with AsyncSessionLocal() as pipeline_db:
            storage = get_storage_adapter()
            pipeline_result = await run_document_pipeline(pipeline_db, storage, document_id)

            if pipeline_result.success:
                await pipeline_db.commit()
            else:
                await pipeline_db.rollback()

        # Update final status
        async with AsyncSessionLocal() as status_db:
            result2 = await status_db.execute(select(SourceDocument).where(SourceDocument.id == document_id))
            doc2 = result2.scalar_one_or_none()
            if doc2:
                if pipeline_result.success:
                    doc2.processing_status = ProcessingStatus.COMPLETED
                else:
                    doc2.processing_status = ProcessingStatus.FAILED
                    doc2.processing_error = pipeline_result.error
                await status_db.commit()

    logger.info("Pipeline completed for %s: success=%s, deviations=%d",
                document_id, pipeline_result.success, pipeline_result.deviations_found)
    return {
        "success": pipeline_result.success,
        "document_id": document_id,
        "document_type": pipeline_result.document_type,
        "deviations_found": pipeline_result.deviations_found,
        "steps": pipeline_result.steps_completed,
        "error": pipeline_result.error,
    }


async def generate_report_job(ctx: dict, case_id: str) -> dict:
    """
    ARQ background job: generer vurderingsrapport for en sak.

    Henter alle avvik og regeltreff for saken, kjører NorwegianReportGenerator
    og lagrer rapporten i databasen.
    """
    import sys
    import os

    _here = os.path.dirname(os.path.abspath(__file__))
    _project_root = os.path.join(_here, "../../../../..")
    _services_local = os.path.join(_project_root, "services")
    for _path in [_services_local, "/app/services"]:
        if _path not in sys.path and os.path.isdir(_path):
            sys.path.insert(0, _path)

    from sqlalchemy import select
    from app.db.base import AsyncSessionLocal
    from app.models.property_case import PropertyCase, Deviation, RuleMatch, AssessmentReport, ReportType

    logger.info("Starter rapportgenerering for sak %s", case_id)

    async with AsyncSessionLocal() as db:
        # Hent sak
        case_result = await db.execute(select(PropertyCase).where(PropertyCase.id == case_id))
        case = case_result.scalar_one_or_none()
        if case is None:
            logger.error("Sak %s ikke funnet", case_id)
            return {"success": False, "error": f"Sak {case_id} ikke funnet"}

        # Hent avvik
        devs_result = await db.execute(
            select(Deviation).where(Deviation.case_id == case_id)
        )
        deviations = devs_result.scalars().all()

        # Hent regeltreff
        deviation_ids = [str(d.id) for d in deviations]
        rule_matches = []
        if deviation_ids:
            rm_result = await db.execute(
                select(RuleMatch).where(RuleMatch.deviation_id.in_(deviation_ids))
            )
            rule_matches = rm_result.scalars().all()

        # Bygg dict-representasjoner
        case_dict = {
            "id": str(case.id),
            "title": case.title,
            "status": case.status.value,
            "created_at": case.created_at.isoformat() if case.created_at else None,
        }
        devs_dicts = [
            {
                "id": str(d.id),
                "category": d.category.value if hasattr(d.category, "value") else str(d.category),
                "severity": d.severity.value if hasattr(d.severity, "value") else str(d.severity),
                "description": d.description,
                "confidence_score": d.confidence,
                "status": d.status.value if hasattr(d.status, "value") else str(d.status),
                "architect_note": d.architect_note,
            }
            for d in deviations
        ]
        rules_dicts = [
            {
                "deviation_id": str(rm.deviation_id),
                "rule_id": str(rm.rule_id),
                "match_confidence": rm.confidence,
                "match_reason": rm.rationale,
            }
            for rm in rule_matches
        ]

        try:
            from reporting.generator import NorwegianReportGenerator
        except ImportError:
            from services.reporting.generator import NorwegianReportGenerator

        generator = NorwegianReportGenerator()

        # Generer begge rapporter
        internal = await generator.generate_internal_report(case_dict, devs_dicts, rules_dicts)
        customer = await generator.generate_customer_report(case_dict, devs_dicts)

        # Sjekk eksisterende rapportversjon
        existing_result = await db.execute(
            select(AssessmentReport)
            .where(AssessmentReport.case_id == case_id)
            .order_by(AssessmentReport.version.desc())
            .limit(1)
        )
        existing = existing_result.scalar_one_or_none()
        next_version = (existing.version + 1) if existing else 1

        import uuid
        report = AssessmentReport(
            id=str(uuid.uuid4()),
            case_id=case_id,
            report_type=ReportType.INTERNAL,
            content={
                "internal": internal.content,
                "customer": customer.content,
                "internal_markdown": internal.markdown,
                "customer_markdown": customer.markdown,
            },
            version=next_version,
        )
        db.add(report)
        await db.commit()

        logger.info("Rapport generert for sak %s (v%d)", case_id, next_version)
        return {
            "success": True,
            "case_id": case_id,
            "report_id": str(report.id),
            "version": next_version,
            "deviations_count": len(deviations),
        }


async def fetch_municipality_data_job(
    ctx: dict,
    case_id: str,
    knr: str,
    gnr: str,
    bnr: str,
    adapter_type: str = "arealplaner",
) -> dict:
    """
    ARQ background job: hent kommunedata for en eiendom.

    Bruker ArealplanerAdapter eller DokAnalyseAdapter basert på adapter_type.
    Lagrer resultatet som MunicipalityRequest i databasen.
    """
    import sys, os

    _here = os.path.dirname(os.path.abspath(__file__))
    _project_root = os.path.join(_here, "../../../../..")
    _services_local = os.path.join(_project_root, "services")
    for _path in [_services_local, "/app/services"]:
        if _path not in sys.path and os.path.isdir(_path):
            sys.path.insert(0, _path)

    from sqlalchemy import select
    from app.db.base import AsyncSessionLocal
    from app.models.property_case import MunicipalityRequest, RequestStatus, RequestMethod

    logger.info(
        "Henter kommunedata for sak %s (knr=%s gnr=%s bnr=%s adapter=%s)",
        case_id, knr, gnr, bnr, adapter_type,
    )

    try:
        from municipality_connectors.adapter import get_municipality_adapter
    except ImportError:
        from services.municipality_connectors.adapter import get_municipality_adapter

    adapter = get_municipality_adapter(adapter_type, use_mock=False)

    result_data: dict = {}

    try:
        if hasattr(adapter, "fetch_planrapport"):
            planrapport = await adapter.fetch_planrapport(knr, gnr, bnr)
            result_data["planrapport"] = planrapport.to_dict()

        if hasattr(adapter, "fetch_dok_analyse"):
            dok = await adapter.fetch_dok_analyse(knr, gnr, bnr)
            result_data["dok_analyse"] = dok.to_dict()

        if hasattr(adapter, "fetch_arealplaner"):
            planer = await adapter.fetch_arealplaner(knr, gnr, bnr)
            result_data["arealplaner"] = [p.to_dict() for p in planer]

        success = True
        status = RequestStatus.RECEIVED

    except Exception as exc:
        logger.error("Kommunedata-henting feilet for sak %s: %s", case_id, exc, exc_info=True)
        result_data["error"] = str(exc)
        success = False
        status = RequestStatus.FAILED

    async with AsyncSessionLocal() as db:
        import uuid
        from datetime import datetime, timezone

        req = MunicipalityRequest(
            id=str(uuid.uuid4()),
            case_id=case_id,
            municipality=f"knr {knr}",
            request_type="DOK_ANALYSE_OG_AREALPLANER",
            request_method=RequestMethod.API,
            status=status,
            request_payload={"knr": knr, "gnr": gnr, "bnr": bnr, "adapter": adapter_type},
            response_payload=result_data,
            sent_at=datetime.now(timezone.utc),
            received_at=datetime.now(timezone.utc) if success else None,
        )
        db.add(req)
        await db.commit()

        logger.info(
            "Kommunedata-jobb fullført for sak %s: success=%s", case_id, success
        )
        return {
            "success": success,
            "case_id": case_id,
            "request_id": str(req.id),
            "adapter": adapter_type,
            "data_keys": list(result_data.keys()),
        }


# ---------------------------------------------------------------------------
# ARQ WorkerSettings
# ---------------------------------------------------------------------------


class WorkerSettings:
    """Configuration class consumed by the ``arq`` worker process."""

    functions = [process_document, process_document_job, generate_report_job, fetch_municipality_data_job]

    redis_settings = arq.connections.RedisSettings.from_dsn(settings.REDIS_URL)

    # Maximum seconds a job may run before being cancelled
    job_timeout = 300

    # How many jobs to run concurrently
    max_jobs = 4

    # Retry failed jobs up to 3 times
    keep_result = 3600  # keep result for 1 hour

    on_startup = None
    on_shutdown = None
