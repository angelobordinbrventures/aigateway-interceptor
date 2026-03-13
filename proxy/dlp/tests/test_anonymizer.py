"""Tests for the anonymization engine."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from proxy.dlp.anonymizer import Anonymizer, AnonymizationMapping
from proxy.dlp.detector import DLPDetector, Finding


@pytest.fixture
def anonymizer() -> Anonymizer:
    return Anonymizer()


@pytest.fixture
def detector() -> DLPDetector:
    return DLPDetector()


class TestAnonymizeCPF:
    def test_anonymize_cpf(self, anonymizer: Anonymizer) -> None:
        text = "Meu CPF é 123.456.789-09"
        findings = [
            Finding(
                category="CPF",
                value="123.456.789-09",
                start=10,
                end=24,
                severity="HIGH",
            )
        ]
        result, session_id = anonymizer.anonymize(text, findings)
        assert "[CPF_REDACTED_1]" in result
        assert "123.456.789-09" not in result
        assert session_id is not None


class TestAnonymizeMultiple:
    def test_anonymize_multiple(self, anonymizer: Anonymizer) -> None:
        text = "CPF: 111.222.333-44, Email: joao@teste.com"
        findings = [
            Finding(
                category="CPF",
                value="111.222.333-44",
                start=5,
                end=19,
                severity="HIGH",
            ),
            Finding(
                category="EMAIL",
                value="joao@teste.com",
                start=28,
                end=42,
                severity="MEDIUM",
            ),
        ]
        result, session_id = anonymizer.anonymize(text, findings)
        assert "[CPF_REDACTED_1]" in result
        assert "[EMAIL_REDACTED_1]" in result
        assert "111.222.333-44" not in result
        assert "joao@teste.com" not in result


class TestPreservesContext:
    def test_anonymize_preserves_context(self, anonymizer: Anonymizer) -> None:
        text = "O cliente com CPF 111.222.333-44 solicitou reembolso."
        findings = [
            Finding(
                category="CPF",
                value="111.222.333-44",
                start=18,
                end=32,
                severity="HIGH",
            )
        ]
        result, _ = anonymizer.anonymize(text, findings)
        assert result.startswith("O cliente com CPF ")
        assert result.endswith(" solicitou reembolso.")
        assert "[CPF_REDACTED_1]" in result


class TestRestoreMapping:
    def test_restore_mapping(self, anonymizer: Anonymizer) -> None:
        text = "Meu CPF é 123.456.789-09"
        findings = [
            Finding(
                category="CPF",
                value="123.456.789-09",
                start=10,
                end=24,
                severity="HIGH",
            )
        ]
        anonymized, session_id = anonymizer.anonymize(text, findings)
        restored = anonymizer.restore(anonymized, session_id)
        assert restored == text

    def test_restore_multiple(self, anonymizer: Anonymizer) -> None:
        text = "CPF: 111.222.333-44, Email: joao@teste.com"
        findings = [
            Finding(
                category="CPF",
                value="111.222.333-44",
                start=5,
                end=19,
                severity="HIGH",
            ),
            Finding(
                category="EMAIL",
                value="joao@teste.com",
                start=28,
                end=42,
                severity="MEDIUM",
            ),
        ]
        anonymized, session_id = anonymizer.anonymize(text, findings)
        restored = anonymizer.restore(anonymized, session_id)
        assert restored == text


class TestCategoryNumbering:
    def test_different_categories_numbered_separately(
        self, anonymizer: Anonymizer
    ) -> None:
        text = "CPF1: 111.111.111-11, CPF2: 222.222.222-22, Email: a@b.com"
        findings = [
            Finding(
                category="CPF",
                value="111.111.111-11",
                start=6,
                end=20,
                severity="HIGH",
            ),
            Finding(
                category="CPF",
                value="222.222.222-22",
                start=28,
                end=42,
                severity="HIGH",
            ),
            Finding(
                category="EMAIL",
                value="a@b.com",
                start=51,
                end=58,
                severity="MEDIUM",
            ),
        ]
        result, _ = anonymizer.anonymize(text, findings)
        assert "[CPF_REDACTED_1]" in result
        assert "[CPF_REDACTED_2]" in result
        assert "[EMAIL_REDACTED_1]" in result


class TestMappingExportImport:
    def test_export_import_mapping(self, anonymizer: Anonymizer) -> None:
        text = "CPF: 111.222.333-44"
        findings = [
            Finding(
                category="CPF",
                value="111.222.333-44",
                start=5,
                end=19,
                severity="HIGH",
            )
        ]
        _, session_id = anonymizer.anonymize(text, findings)
        exported = anonymizer.export_mapping(session_id)
        assert exported is not None

        # Create a new anonymizer and import
        new_anonymizer = Anonymizer()
        imported_session = new_anonymizer.import_mapping(exported)
        assert imported_session == session_id

        mapping = new_anonymizer.get_mapping(imported_session)
        assert mapping is not None
        assert "[CPF_REDACTED_1]" in mapping.mappings
