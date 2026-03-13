"""Comprehensive tests for the DLP detector."""

import sys
from pathlib import Path

import pytest

# Ensure the proxy package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from proxy.dlp.detector import DLPDetector, Finding, _luhn_check


@pytest.fixture
def detector() -> DLPDetector:
    """Create a DLPDetector instance with default patterns."""
    return DLPDetector()


class TestDetectCPF:
    def test_detect_cpf(self, detector: DLPDetector) -> None:
        text = "Meu CPF é 123.456.789-09"
        findings = detector.detect(text)
        assert len(findings) == 1
        assert findings[0].category == "CPF"
        assert findings[0].value == "123.456.789-09"
        assert findings[0].severity == "HIGH"

    def test_detect_cpf_in_sentence(self, detector: DLPDetector) -> None:
        text = "O contribuinte com CPF 987.654.321-00 solicitou reembolso."
        findings = detector.detect(text)
        cpf_findings = [f for f in findings if f.category == "CPF"]
        assert len(cpf_findings) == 1
        assert cpf_findings[0].value == "987.654.321-00"


class TestDetectCNPJ:
    def test_detect_cnpj(self, detector: DLPDetector) -> None:
        text = "A empresa com CNPJ 12.345.678/0001-95 está cadastrada."
        findings = detector.detect(text)
        cnpj_findings = [f for f in findings if f.category == "CNPJ"]
        assert len(cnpj_findings) == 1
        assert cnpj_findings[0].value == "12.345.678/0001-95"
        assert cnpj_findings[0].severity == "HIGH"


class TestDetectEmail:
    def test_detect_email(self, detector: DLPDetector) -> None:
        text = "Entre em contato pelo email usuario@exemplo.com.br para mais informações."
        findings = detector.detect(text)
        email_findings = [f for f in findings if f.category == "EMAIL"]
        assert len(email_findings) == 1
        assert email_findings[0].value == "usuario@exemplo.com.br"
        assert email_findings[0].severity == "MEDIUM"


class TestDetectCreditCard:
    def test_detect_credit_card_visa(self, detector: DLPDetector) -> None:
        # 4111111111111111 passes Luhn check
        text = "Meu cartão é 4111111111111111"
        findings = detector.detect(text)
        cc_findings = [f for f in findings if f.category == "CREDIT_CARD"]
        assert len(cc_findings) == 1
        assert cc_findings[0].value == "4111111111111111"
        assert cc_findings[0].severity == "CRITICAL"

    def test_reject_invalid_luhn(self, detector: DLPDetector) -> None:
        # 4111111111111112 does NOT pass Luhn
        text = "Número 4111111111111112 não é válido"
        findings = detector.detect(text)
        cc_findings = [f for f in findings if f.category == "CREDIT_CARD"]
        assert len(cc_findings) == 0

    def test_luhn_check_valid(self) -> None:
        assert _luhn_check("4111111111111111") is True

    def test_luhn_check_invalid(self) -> None:
        assert _luhn_check("4111111111111112") is False


class TestDetectAPIKeys:
    def test_detect_api_key_openai(self, detector: DLPDetector) -> None:
        text = "Use a chave sk-proj-abc123def456ghi789jkl0mn"
        findings = detector.detect(text)
        key_findings = [f for f in findings if f.category == "API_KEY"]
        assert len(key_findings) == 1
        assert key_findings[0].value.startswith("sk-proj-")
        assert key_findings[0].severity == "CRITICAL"

    def test_detect_api_key_aws(self, detector: DLPDetector) -> None:
        text = "AWS key: AKIAIOSFODNN7EXAMPLE"
        findings = detector.detect(text)
        key_findings = [f for f in findings if f.category == "API_KEY"]
        assert len(key_findings) == 1
        assert key_findings[0].value == "AKIAIOSFODNN7EXAMPLE"

    def test_detect_api_key_github(self, detector: DLPDetector) -> None:
        text = "Token: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"
        findings = detector.detect(text)
        key_findings = [f for f in findings if f.category == "API_KEY"]
        assert len(key_findings) == 1
        assert key_findings[0].value.startswith("ghp_")


class TestDetectPhoneBR:
    def test_detect_phone_br(self, detector: DLPDetector) -> None:
        text = "Ligue para (11) 98765-4321 para suporte."
        findings = detector.detect(text)
        phone_findings = [f for f in findings if f.category == "PHONE_BR"]
        assert len(phone_findings) == 1
        assert "98765" in phone_findings[0].value


class TestDetectJWT:
    def test_detect_jwt_token(self, detector: DLPDetector) -> None:
        token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0."
            "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )
        text = f"Authorization: Bearer {token}"
        findings = detector.detect(text)
        jwt_findings = [f for f in findings if f.category == "JWT"]
        assert len(jwt_findings) == 1
        assert jwt_findings[0].severity == "HIGH"


class TestNoFalsePositives:
    def test_no_false_positive_clean_text(self, detector: DLPDetector) -> None:
        text = "Qual é a capital do Brasil?"
        findings = detector.detect(text)
        assert len(findings) == 0

    def test_no_false_positive_normal_numbers(self, detector: DLPDetector) -> None:
        text = "A população do Brasil é de 213 milhões de pessoas."
        findings = detector.detect(text)
        assert len(findings) == 0

    def test_empty_text(self, detector: DLPDetector) -> None:
        assert detector.detect("") == []
        assert detector.detect(None) == []


class TestMultipleFindings:
    def test_multiple_findings_in_text(self, detector: DLPDetector) -> None:
        text = (
            "O cliente com CPF 123.456.789-09 e email joao@teste.com "
            "enviou a senha password: minhasenha123"
        )
        findings = detector.detect(text)
        categories = {f.category for f in findings}
        assert "CPF" in categories
        assert "EMAIL" in categories
        assert "PASSWORD" in categories
        assert len(findings) >= 3
