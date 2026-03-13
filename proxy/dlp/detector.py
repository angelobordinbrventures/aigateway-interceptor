"""DLP Detection engine for identifying sensitive data in text."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Finding:
    """Represents a detected piece of sensitive data."""

    category: str
    value: str
    start: int
    end: int
    severity: str
    pattern_name: Optional[str] = None


@dataclass
class PatternDefinition:
    """A regex pattern definition loaded from configuration."""

    name: str
    category: str
    regex: str
    severity: str
    description: str = ""
    compiled: re.Pattern = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.compiled = re.compile(self.regex)


def _luhn_check(number: str) -> bool:
    """Validate a number string using the Luhn algorithm."""
    digits = [int(d) for d in number if d.isdigit()]
    if len(digits) < 13:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


class DLPDetector:
    """Detects sensitive data in text using regex patterns and validation."""

    def __init__(
        self,
        patterns_dir: Optional[str] = None,
        extra_patterns: Optional[list[dict]] = None,
    ) -> None:
        self._patterns: list[PatternDefinition] = []

        if patterns_dir is None:
            patterns_dir = str(Path(__file__).parent / "patterns")

        self._load_patterns_from_dir(patterns_dir)

        if extra_patterns:
            for p in extra_patterns:
                self._patterns.append(
                    PatternDefinition(
                        name=p["name"],
                        category=p["category"],
                        regex=p["regex"],
                        severity=p.get("severity", "MEDIUM"),
                        description=p.get("description", ""),
                    )
                )

    def _load_patterns_from_dir(self, patterns_dir: str) -> None:
        """Load all pattern JSON files from a directory."""
        path = Path(patterns_dir)
        if not path.exists():
            return

        for json_file in sorted(path.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for p in data.get("patterns", []):
                    self._patterns.append(
                        PatternDefinition(
                            name=p["name"],
                            category=p["category"],
                            regex=p["regex"],
                            severity=p.get("severity", "MEDIUM"),
                            description=p.get("description", ""),
                        )
                    )
            except (json.JSONDecodeError, KeyError):
                continue

    @property
    def patterns(self) -> list[PatternDefinition]:
        """Return loaded patterns."""
        return list(self._patterns)

    def detect(self, text: str) -> list[Finding]:
        """Scan text for sensitive data and return all findings.

        Args:
            text: The input text to scan.

        Returns:
            A list of Finding objects for each detected piece of sensitive data.
        """
        if not text:
            return []

        findings: list[Finding] = []

        for pattern in self._patterns:
            for match in pattern.compiled.finditer(text):
                matched_value = match.group(0)

                # Additional validation for credit cards: run Luhn check
                if pattern.category == "CREDIT_CARD":
                    digits_only = re.sub(r"[\s-]", "", matched_value)
                    if not _luhn_check(digits_only):
                        continue

                findings.append(
                    Finding(
                        category=pattern.category,
                        value=matched_value,
                        start=match.start(),
                        end=match.end(),
                        severity=pattern.severity,
                        pattern_name=pattern.name,
                    )
                )

        # Sort by position in text
        findings.sort(key=lambda f: f.start)
        return findings
