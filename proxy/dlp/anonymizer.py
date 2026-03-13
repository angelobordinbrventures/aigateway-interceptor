"""Anonymization engine for replacing sensitive data with redaction tokens."""

from __future__ import annotations

import base64
import json
import uuid
from dataclasses import dataclass, field
from typing import Optional

from .detector import Finding


@dataclass
class AnonymizationMapping:
    """Stores the mapping between redacted tokens and original values."""

    session_id: str
    mappings: dict[str, str] = field(default_factory=dict)
    # token -> original value

    def add(self, token: str, original: str) -> None:
        """Add a mapping entry."""
        self.mappings[token] = original

    def get_original(self, token: str) -> Optional[str]:
        """Retrieve the original value for a given token."""
        return self.mappings.get(token)

    def export_encrypted(self) -> str:
        """Export mappings as base64-encoded JSON (MVP encryption)."""
        payload = json.dumps(
            {"session_id": self.session_id, "mappings": self.mappings}
        )
        return base64.b64encode(payload.encode("utf-8")).decode("utf-8")

    @classmethod
    def import_encrypted(cls, encoded: str) -> "AnonymizationMapping":
        """Import mappings from base64-encoded JSON."""
        payload = base64.b64decode(encoded.encode("utf-8")).decode("utf-8")
        data = json.loads(payload)
        mapping = cls(session_id=data["session_id"])
        mapping.mappings = data["mappings"]
        return mapping


class Anonymizer:
    """Replaces detected sensitive data with redaction tokens.

    Maintains a reversible mapping per session so that original values
    can be restored for audit purposes.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, AnonymizationMapping] = {}

    def anonymize(
        self,
        text: str,
        findings: list[Finding],
        session_id: Optional[str] = None,
    ) -> tuple[str, str]:
        """Replace all findings in text with redaction tokens.

        Args:
            text: The original text.
            findings: List of Finding objects to redact.
            session_id: Optional session identifier. Auto-generated if not provided.

        Returns:
            A tuple of (anonymized_text, session_id).
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        if session_id not in self._sessions:
            self._sessions[session_id] = AnonymizationMapping(
                session_id=session_id
            )

        mapping = self._sessions[session_id]

        # Track counters per category for numbering
        category_counters: dict[str, int] = {}

        # Sort findings by start position in reverse so replacements
        # don't shift indices of earlier findings.
        sorted_findings = sorted(findings, key=lambda f: f.start, reverse=True)

        # First pass: assign numbers in forward order
        forward_findings = sorted(findings, key=lambda f: f.start)
        token_assignments: dict[int, str] = {}  # finding id -> token

        for finding in forward_findings:
            cat = finding.category
            counter = category_counters.get(cat, 0) + 1
            category_counters[cat] = counter
            token = f"[{cat}_REDACTED_{counter}]"
            token_assignments[id(finding)] = token
            mapping.add(token, finding.value)

        # Second pass: replace in reverse order
        result = text
        for finding in sorted_findings:
            token = token_assignments[id(finding)]
            result = result[:finding.start] + token + result[finding.end:]

        return result, session_id

    def restore(self, anonymized_text: str, session_id: str) -> str:
        """Restore original values from the anonymized text.

        Args:
            anonymized_text: Text containing redaction tokens.
            session_id: The session ID used during anonymization.

        Returns:
            Text with original values restored.
        """
        mapping = self._sessions.get(session_id)
        if mapping is None:
            return anonymized_text

        result = anonymized_text
        for token, original in mapping.mappings.items():
            result = result.replace(token, original)

        return result

    def get_mapping(self, session_id: str) -> Optional[AnonymizationMapping]:
        """Return the mapping for a given session."""
        return self._sessions.get(session_id)

    def export_mapping(self, session_id: str) -> Optional[str]:
        """Export the mapping for a session as an encrypted string."""
        mapping = self._sessions.get(session_id)
        if mapping is None:
            return None
        return mapping.export_encrypted()

    def import_mapping(self, encoded: str) -> str:
        """Import a mapping from an encrypted string and return its session_id."""
        mapping = AnonymizationMapping.import_encrypted(encoded)
        self._sessions[mapping.session_id] = mapping
        return mapping.session_id
