"""Policy engine for determining actions based on DLP findings."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from dlp.detector import Finding

logger = logging.getLogger(__name__)

# Valid actions
ACTIONS = {"ALLOW", "BLOCK", "ANONYMIZE", "LOG_ONLY", "ALERT"}
DEFAULT_ACTION = "LOG_ONLY"


@dataclass
class Policy:
    """A single policy rule."""

    name: str
    description: str
    priority: int
    categories: list[str]
    action: str
    enabled: bool = True

    def matches(self, findings: list[Finding]) -> bool:
        """Check if any finding matches this policy's categories."""
        if not self.categories:
            return True
        finding_categories = {f.category for f in findings}
        return bool(finding_categories & set(self.categories))


class PolicyEngine:
    """Evaluates findings against policies to determine an action."""

    def __init__(
        self,
        policies_path: Optional[str] = None,
        api_url: Optional[str] = None,
    ) -> None:
        self._policies: list[Policy] = []
        self._api_url = api_url

        if policies_path is None:
            policies_path = str(
                Path(__file__).parent / "default_policies.yaml"
            )

        self._load_from_yaml(policies_path)

        if self._api_url:
            self._fetch_from_api()

    def _load_from_yaml(self, path: str) -> None:
        """Load policies from a YAML file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            for p in data.get("policies", []):
                policy = Policy(
                    name=p["name"],
                    description=p.get("description", ""),
                    priority=p.get("priority", 0),
                    categories=p.get("categories", []),
                    action=p.get("action", DEFAULT_ACTION),
                    enabled=p.get("enabled", True),
                )
                if policy.action in ACTIONS:
                    self._policies.append(policy)
                else:
                    logger.warning(
                        "Skipping policy '%s' with invalid action '%s'",
                        policy.name,
                        policy.action,
                    )
        except FileNotFoundError:
            logger.warning("Policies file not found: %s", path)
        except (yaml.YAMLError, KeyError) as exc:
            logger.error("Error loading policies from %s: %s", path, exc)

    def _fetch_from_api(self) -> None:
        """Fetch additional policies from API backend."""
        try:
            import requests

            resp = requests.get(
                f"{self._api_url}/api/v1/policies", timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                for p in data.get("policies", []):
                    policy = Policy(
                        name=p["name"],
                        description=p.get("description", ""),
                        priority=p.get("priority", 0),
                        categories=p.get("categories", []),
                        action=p.get("action", DEFAULT_ACTION),
                        enabled=p.get("enabled", True),
                    )
                    if policy.action in ACTIONS:
                        self._policies.append(policy)
        except Exception as exc:
            logger.warning("Could not fetch policies from API: %s", exc)

    @property
    def policies(self) -> list[Policy]:
        """Return all loaded policies sorted by priority (highest first)."""
        return sorted(self._policies, key=lambda p: p.priority, reverse=True)

    def get_action(
        self,
        host: str,
        findings: list[Finding],
        user: Optional[str] = None,
    ) -> str:
        """Determine the action to take based on findings and policies.

        Evaluates policies in priority order (highest first). The first
        matching enabled policy determines the action.

        Args:
            host: The target host being accessed.
            findings: List of DLP findings detected in the request.
            user: Optional user identifier for user-specific policies.

        Returns:
            The action string (ALLOW, BLOCK, ANONYMIZE, LOG_ONLY, ALERT).
        """
        if not findings:
            return "ALLOW"

        for policy in self.policies:
            if not policy.enabled:
                continue
            if policy.matches(findings):
                logger.info(
                    "Policy '%s' matched for host=%s user=%s -> %s",
                    policy.name,
                    host,
                    user,
                    policy.action,
                )
                return policy.action

        return DEFAULT_ACTION
