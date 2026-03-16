"""Initial schema – all tables and enums for ByggSjekk.

Revision ID: 001
Revises:
Create Date: 2026-03-14 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 0. Extensions
    # ------------------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ------------------------------------------------------------------
    # 1. Enum types
    # ------------------------------------------------------------------
    case_status = sa.Enum(
        "DRAFT", "ACTIVE", "UNDER_REVIEW", "COMPLETED", "ARCHIVED",
        name="case_status",
    )
    customer_type = sa.Enum(
        "PRIVATE", "PROFESSIONAL", "MUNICIPALITY",
        name="customer_type",
    )
    source_type = sa.Enum(
        "UPLOADED", "FETCHED_MUNICIPALITY", "EMAIL_REQUEST",
        name="source_type",
    )
    approval_status = sa.Enum(
        "RECEIVED", "ASSUMED_APPROVED", "VERIFIED_APPROVED", "UNKNOWN",
        name="approval_status",
    )
    processing_status = sa.Enum(
        "PENDING", "PROCESSING", "COMPLETED", "FAILED",
        name="processing_status",
    )
    deviation_category = sa.Enum(
        "AREA_DEVIATION", "ROOM_COUNT", "ROOM_TYPE", "FLOOR_PLAN",
        "FACADE", "HEIGHT", "SETBACK", "ACCESSIBILITY", "FIRE_SAFETY", "ENERGY",
        name="deviation_category",
    )
    severity = sa.Enum(
        "LOW", "MEDIUM", "HIGH", "CRITICAL",
        name="severity",
    )
    deviation_status = sa.Enum(
        "OPEN", "REVIEWED", "DISMISSED", "CONFIRMED",
        name="deviation_status",
    )
    report_type = sa.Enum(
        "INTERNAL", "CUSTOMER",
        name="report_type",
    )
    review_status = sa.Enum(
        "PENDING", "IN_PROGRESS", "COMPLETED",
        name="review_status",
    )
    request_method = sa.Enum(
        "API", "EMAIL",
        name="request_method",
    )
    request_status = sa.Enum(
        "PENDING", "SENT", "RECEIVED", "FAILED",
        name="request_status",
    )

    for enum in [
        case_status, customer_type, source_type, approval_status,
        processing_status, deviation_category, severity, deviation_status,
        report_type, review_status, request_method, request_status,
    ]:
        enum.create(op.get_bind(), checkfirst=True)

    # ------------------------------------------------------------------
    # 2. users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(1024), nullable=False),
        sa.Column("full_name", sa.String(512), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_architect", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ------------------------------------------------------------------
    # 3. properties
    # ------------------------------------------------------------------
    op.create_table(
        "properties",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("street_address", sa.String(512), nullable=False),
        sa.Column("postal_code", sa.String(10), nullable=False),
        sa.Column("municipality", sa.String(256), nullable=False),
        sa.Column("gnr", sa.Integer(), nullable=True),
        sa.Column("bnr", sa.Integer(), nullable=True),
        sa.Column("plan_references", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_properties_id", "properties", ["id"])
    op.create_index("ix_properties_municipality", "properties", ["municipality"])

    # ------------------------------------------------------------------
    # 4. property_cases
    # ------------------------------------------------------------------
    op.create_table(
        "property_cases",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "ACTIVE", "UNDER_REVIEW", "COMPLETED", "ARCHIVED", name="case_status"),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column(
            "customer_type",
            sa.Enum("PRIVATE", "PROFESSIONAL", "MUNICIPALITY", name="customer_type"),
            nullable=False,
            server_default="PRIVATE",
        ),
        sa.Column("intake_source", sa.String(256), nullable=True),
        sa.Column(
            "property_id",
            sa.UUID(),
            sa.ForeignKey("properties.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "assigned_architect_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_property_cases_id", "property_cases", ["id"])
    op.create_index("ix_property_cases_status", "property_cases", ["status"])
    op.create_index("ix_property_cases_property_id", "property_cases", ["property_id"])
    op.create_index("ix_property_cases_assigned_architect_id", "property_cases", ["assigned_architect_id"])
    op.create_index("ix_property_cases_created_by_id", "property_cases", ["created_by_id"])

    # ------------------------------------------------------------------
    # 5. source_documents
    # ------------------------------------------------------------------
    op.create_table(
        "source_documents",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "case_id",
            sa.UUID(),
            sa.ForeignKey("property_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("original_filename", sa.String(512), nullable=False),
        sa.Column("storage_key", sa.String(1024), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=False),
        sa.Column(
            "source_type",
            sa.Enum("UPLOADED", "FETCHED_MUNICIPALITY", "EMAIL_REQUEST", name="source_type"),
            nullable=False,
            server_default="UPLOADED",
        ),
        sa.Column(
            "approval_status",
            sa.Enum("RECEIVED", "ASSUMED_APPROVED", "VERIFIED_APPROVED", "UNKNOWN", name="approval_status"),
            nullable=False,
            server_default="UNKNOWN",
        ),
        sa.Column("approval_status_confidence", sa.Float(), nullable=True),
        sa.Column("document_type", sa.String(128), nullable=True),
        sa.Column("document_type_confidence", sa.Float(), nullable=True),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column(
            "processing_status",
            sa.Enum("PENDING", "PROCESSING", "COMPLETED", "FAILED", name="processing_status"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_source_documents_id", "source_documents", ["id"])
    op.create_index("ix_source_documents_case_id", "source_documents", ["case_id"])
    op.create_index("ix_source_documents_processing_status", "source_documents", ["processing_status"])

    # ------------------------------------------------------------------
    # 6. document_evidence
    # ------------------------------------------------------------------
    op.create_table(
        "document_evidence",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "document_id",
            sa.UUID(),
            sa.ForeignKey("source_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("bounding_box", sa.JSON(), nullable=True),
        sa.Column("text_excerpt", sa.Text(), nullable=True),
        sa.Column("observation", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_document_evidence_id", "document_evidence", ["id"])
    op.create_index("ix_document_evidence_document_id", "document_evidence", ["document_id"])

    # ------------------------------------------------------------------
    # 7. structured_plans
    # ------------------------------------------------------------------
    op.create_table(
        "structured_plans",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "document_id",
            sa.UUID(),
            sa.ForeignKey("source_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "case_id",
            sa.UUID(),
            sa.ForeignKey("property_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("floor_number", sa.Integer(), nullable=True),
        sa.Column("plan_data", sa.JSON(), nullable=False),
        sa.Column("total_area", sa.Float(), nullable=True),
        sa.Column("room_count", sa.Integer(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_structured_plans_id", "structured_plans", ["id"])
    op.create_index("ix_structured_plans_document_id", "structured_plans", ["document_id"])
    op.create_index("ix_structured_plans_case_id", "structured_plans", ["case_id"])

    # ------------------------------------------------------------------
    # 8. spaces
    # ------------------------------------------------------------------
    op.create_table(
        "spaces",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "plan_id",
            sa.UUID(),
            sa.ForeignKey("structured_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("space_type", sa.String(128), nullable=False),
        sa.Column("floor_number", sa.Integer(), nullable=True),
        sa.Column("area", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("attributes", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_spaces_id", "spaces", ["id"])
    op.create_index("ix_spaces_plan_id", "spaces", ["plan_id"])

    # ------------------------------------------------------------------
    # 9. rules
    # ------------------------------------------------------------------
    op.create_table(
        "rules",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("rule_code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("legal_reference", sa.String(512), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("applies_to_categories", sa.JSON(), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_rules_id", "rules", ["id"])
    op.create_index("ix_rules_rule_code", "rules", ["rule_code"], unique=True)

    # ------------------------------------------------------------------
    # 10. deviations
    # ------------------------------------------------------------------
    op.create_table(
        "deviations",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "case_id",
            sa.UUID(),
            sa.ForeignKey("property_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.Enum(
                "AREA_DEVIATION", "ROOM_COUNT", "ROOM_TYPE", "FLOOR_PLAN",
                "FACADE", "HEIGHT", "SETBACK", "ACCESSIBILITY", "FIRE_SAFETY", "ENERGY",
                name="deviation_category",
            ),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="severity"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("evidence_ids", sa.JSON(), nullable=True),
        sa.Column("rule_ids", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("OPEN", "REVIEWED", "DISMISSED", "CONFIRMED", name="deviation_status"),
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column("architect_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_deviations_id", "deviations", ["id"])
    op.create_index("ix_deviations_case_id", "deviations", ["case_id"])
    op.create_index("ix_deviations_category", "deviations", ["category"])
    op.create_index("ix_deviations_severity", "deviations", ["severity"])
    op.create_index("ix_deviations_status", "deviations", ["status"])

    # ------------------------------------------------------------------
    # 11. rule_matches
    # ------------------------------------------------------------------
    op.create_table(
        "rule_matches",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "deviation_id",
            sa.UUID(),
            sa.ForeignKey("deviations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "rule_id",
            sa.UUID(),
            sa.ForeignKey("rules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("match_type", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_rule_matches_id", "rule_matches", ["id"])
    op.create_index("ix_rule_matches_deviation_id", "rule_matches", ["deviation_id"])
    op.create_index("ix_rule_matches_rule_id", "rule_matches", ["rule_id"])

    # ------------------------------------------------------------------
    # 12. assessment_reports
    # ------------------------------------------------------------------
    op.create_table(
        "assessment_reports",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "case_id",
            sa.UUID(),
            sa.ForeignKey("property_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "report_type",
            sa.Enum("INTERNAL", "CUSTOMER", name="report_type"),
            nullable=False,
            server_default="INTERNAL",
        ),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column(
            "approved_by_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_assessment_reports_id", "assessment_reports", ["id"])
    op.create_index("ix_assessment_reports_case_id", "assessment_reports", ["case_id"])

    # ------------------------------------------------------------------
    # 13. architect_reviews
    # ------------------------------------------------------------------
    op.create_table(
        "architect_reviews",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "case_id",
            sa.UUID(),
            sa.ForeignKey("property_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("PENDING", "IN_PROGRESS", "COMPLETED", name="review_status"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("overrides", sa.JSON(), nullable=True),
        sa.Column("audit_log", sa.JSON(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_architect_reviews_id", "architect_reviews", ["id"])
    op.create_index("ix_architect_reviews_case_id", "architect_reviews", ["case_id"])
    op.create_index("ix_architect_reviews_reviewer_id", "architect_reviews", ["reviewer_id"])
    op.create_index("ix_architect_reviews_status", "architect_reviews", ["status"])

    # ------------------------------------------------------------------
    # 14. dispensation_cases
    # ------------------------------------------------------------------
    op.create_table(
        "dispensation_cases",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "case_id",
            sa.UUID(),
            sa.ForeignKey("property_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "deviation_id",
            sa.UUID(),
            sa.ForeignKey("deviations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(64), nullable=False, server_default="PENDING"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_dispensation_cases_id", "dispensation_cases", ["id"])
    op.create_index("ix_dispensation_cases_case_id", "dispensation_cases", ["case_id"])
    op.create_index("ix_dispensation_cases_deviation_id", "dispensation_cases", ["deviation_id"])

    # ------------------------------------------------------------------
    # 15. dispensation_statistics
    # ------------------------------------------------------------------
    op.create_table(
        "dispensation_statistics",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("municipality", sa.String(256), nullable=False),
        sa.Column("rule_code", sa.String(64), nullable=False),
        sa.Column("total_applications", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("approved_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("municipality", "rule_code", "year", name="uq_dispensation_stats"),
    )
    op.create_index("ix_dispensation_statistics_id", "dispensation_statistics", ["id"])
    op.create_index("ix_dispensation_statistics_municipality", "dispensation_statistics", ["municipality"])
    op.create_index("ix_dispensation_statistics_rule_code", "dispensation_statistics", ["rule_code"])
    op.create_index("ix_dispensation_statistics_year", "dispensation_statistics", ["year"])

    # ------------------------------------------------------------------
    # 16. municipality_requests
    # ------------------------------------------------------------------
    op.create_table(
        "municipality_requests",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "case_id",
            sa.UUID(),
            sa.ForeignKey("property_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("municipality", sa.String(256), nullable=False),
        sa.Column("request_type", sa.String(128), nullable=False),
        sa.Column(
            "request_method",
            sa.Enum("API", "EMAIL", name="request_method"),
            nullable=False,
            server_default="EMAIL",
        ),
        sa.Column(
            "status",
            sa.Enum("PENDING", "SENT", "RECEIVED", "FAILED", name="request_status"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("request_payload", sa.JSON(), nullable=True),
        sa.Column("response_payload", sa.JSON(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_municipality_requests_id", "municipality_requests", ["id"])
    op.create_index("ix_municipality_requests_case_id", "municipality_requests", ["case_id"])
    op.create_index("ix_municipality_requests_municipality", "municipality_requests", ["municipality"])
    op.create_index("ix_municipality_requests_status", "municipality_requests", ["status"])


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table("municipality_requests")
    op.drop_table("dispensation_statistics")
    op.drop_table("dispensation_cases")
    op.drop_table("architect_reviews")
    op.drop_table("assessment_reports")
    op.drop_table("rule_matches")
    op.drop_table("deviations")
    op.drop_table("rules")
    op.drop_table("spaces")
    op.drop_table("structured_plans")
    op.drop_table("document_evidence")
    op.drop_table("source_documents")
    op.drop_table("property_cases")
    op.drop_table("properties")
    op.drop_table("users")

    # Drop enum types
    for enum_name in [
        "request_status", "request_method", "review_status", "report_type",
        "deviation_status", "severity", "deviation_category", "processing_status",
        "approval_status", "source_type", "customer_type", "case_status",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")

    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
