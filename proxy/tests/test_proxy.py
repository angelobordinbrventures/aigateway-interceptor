"""Tests for the proxy addon's target detection."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from proxy.main import is_ai_target, AI_API_TARGETS


class TestIsAITarget:
    def test_is_ai_target_openai(self) -> None:
        assert is_ai_target("api.openai.com") is True

    def test_is_ai_target_anthropic(self) -> None:
        assert is_ai_target("api.anthropic.com") is True

    def test_is_ai_target_groq(self) -> None:
        assert is_ai_target("api.groq.com") is True

    def test_is_ai_target_deepseek(self) -> None:
        assert is_ai_target("api.deepseek.com") is True

    def test_is_ai_target_mistral(self) -> None:
        assert is_ai_target("api.mistral.ai") is True

    def test_is_ai_target_xai(self) -> None:
        assert is_ai_target("api.x.ai") is True

    def test_is_ai_target_cohere(self) -> None:
        assert is_ai_target("api.cohere.ai") is True

    def test_is_ai_target_openrouter(self) -> None:
        assert is_ai_target("openrouter.ai") is True

    def test_is_ai_target_google(self) -> None:
        assert is_ai_target("generativelanguage.googleapis.com") is True

    def test_is_not_ai_target_google(self) -> None:
        assert is_ai_target("www.google.com") is False

    def test_is_not_ai_target_random(self) -> None:
        assert is_ai_target("example.com") is False

    def test_is_not_ai_target_empty(self) -> None:
        assert is_ai_target("") is False

    def test_is_not_ai_target_subdomain(self) -> None:
        assert is_ai_target("sub.api.openai.com") is False

    def test_all_targets_registered(self) -> None:
        assert len(AI_API_TARGETS) == 9
