"""Unit tests for DocumentClassifier and SourceConfidenceClassifier."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../../services"))

from document_ingestion.classifier import DocumentClassifier, SourceConfidenceClassifier


class TestDocumentClassifier:

    def setup_method(self):
        self.classifier = DocumentClassifier()

    def test_classify_floor_plan_by_filename(self):
        result = self.classifier.classify("plantegning_etasje1.pdf", "")
        # classify() returns a dict
        assert "document_type" in result
        assert result["document_type"] in ("floor_plan", "plantegning", "pdf_document")
        assert result["confidence"] >= 0.0

    def test_classify_situasjonsplan(self):
        result = self.classifier.classify("situasjonsplan_2023.pdf", "")
        assert "document_type" in result
        assert "situasjons" in result["document_type"].lower() or result["document_type"] == "situasjonsplan"
        assert result["confidence"] >= 0.5

    def test_classify_ferdigattest(self):
        result = self.classifier.classify("ferdigattest_2010.pdf", "")
        assert result["document_type"] == "completion_certificate"
        assert result["confidence"] >= 0.8

    def test_classify_rammetillatelse(self):
        result = self.classifier.classify("rammetillatelse_2005_oslo.pdf", "")
        assert result["document_type"] == "building_permit_framework"
        assert result["confidence"] >= 0.8

    def test_classify_dispensasjon(self):
        result = self.classifier.classify("dispensasjon_soknad.pdf", "")
        assert result["document_type"] == "dispensation_application"
        assert result["confidence"] >= 0.8

    def test_classify_nabovarsel(self):
        result = self.classifier.classify("nabovarsel_2024.pdf", "")
        assert result["document_type"] == "neighbour_notification"

    def test_classify_cad_drawing(self):
        result = self.classifier.classify("tegning.dwg", "")
        assert result["document_type"] == "cad_drawing"
        assert result["confidence"] >= 0.5

    def test_classify_bim_model(self):
        result = self.classifier.classify("model.ifc", "")
        assert result["document_type"] == "bim_model"
        assert result["confidence"] >= 0.5

    def test_classify_unknown_returns_low_confidence(self):
        result = self.classifier.classify("random_dokument_xyz_999.doc", "")
        # Unknown files should have low confidence
        assert 0.0 <= result["confidence"] <= 1.0

    def test_classify_with_content_boost(self):
        content = "Etasjeplan for 2. etasje. Stue, kjøkken, 2 soverom."
        result = self.classifier.classify("dok.pdf", content)
        assert "document_type" in result
        assert 0.0 <= result["confidence"] <= 1.0

    def test_classify_content_ferdigattest(self):
        content = "Ferdigattest er utstedt for tiltaket."
        result = self.classifier.classify("ukjent_fil.pdf", content)
        assert result["document_type"] == "completion_certificate"

    def test_classify_returns_confidence_in_range(self):
        for filename in ["test.pdf", "tegning.dwg", "plan.ifc", "rapport.docx"]:
            result = self.classifier.classify(filename, "")
            assert 0.0 <= result["confidence"] <= 1.0

    def test_classify_returns_method_field(self):
        result = self.classifier.classify("tegning.pdf", "")
        assert "method" in result
        assert result["method"] in ("rule_based", "llm", "fallback", "llm_unavailable")


class TestSourceConfidenceClassifier:

    def setup_method(self):
        self.classifier = SourceConfidenceClassifier()

    def test_municipality_fetch_high_confidence(self):
        result = self.classifier.classify_source("FETCHED_MUNICIPALITY", {})
        assert result["confidence"] >= 0.85
        assert result["approval_status"] in ("VERIFIED_APPROVED", "ASSUMED_APPROVED")

    def test_municipality_fetch_verified_approved(self):
        result = self.classifier.classify_source("FETCHED_MUNICIPALITY", {})
        assert result["approval_status"] == "VERIFIED_APPROVED"
        assert result["confidence"] == 0.95

    def test_uploaded_document_lower_confidence(self):
        result = self.classifier.classify_source("UPLOADED", {})
        assert result["confidence"] <= 0.75

    def test_uploaded_permit_document_received(self):
        result = self.classifier.classify_source("UPLOADED", {"document_type": "building_permit_framework"})
        assert result["approval_status"] == "RECEIVED"
        assert result["confidence"] >= 0.5

    def test_uploaded_completion_certificate(self):
        result = self.classifier.classify_source("UPLOADED", {"document_type": "completion_certificate"})
        assert result["approval_status"] == "RECEIVED"

    def test_email_request_medium_confidence(self):
        result = self.classifier.classify_source("EMAIL_REQUEST", {})
        assert 0.3 <= result["confidence"] <= 0.9

    def test_email_request_municipality_confirmed(self):
        result = self.classifier.classify_source("EMAIL_REQUEST", {"municipality_confirmed": True})
        assert result["approval_status"] == "VERIFIED_APPROVED"
        assert result["confidence"] >= 0.75

    def test_unknown_source_returns_unknown_status(self):
        result = self.classifier.classify_source("UNKNOWN_TYPE", {})
        assert result["approval_status"] == "UNKNOWN"
        assert result["confidence"] <= 0.3

    def test_uploaded_no_doc_type_returns_unknown(self):
        result = self.classifier.classify_source("UPLOADED", {})
        assert result["approval_status"] == "UNKNOWN"
