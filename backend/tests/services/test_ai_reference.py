"""Unit tests for the AI reference-solution service (no network calls)."""

from __future__ import annotations

import pytest

from app.services.ai_reference import AiReferenceError, AiReferenceService


class _FakeSettings:
    """Duck-typed stand-in for app.core.config.Settings."""

    def __init__(self, key: str | None) -> None:
        self.openai_api_key = key
        self.openai_model = "test-model"
        self.ai_reference_default_count = 5
        self.ai_reference_max_count = 3

    @property
    def openai_configured(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key.strip())


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, content: str) -> None:
        self._content = content
        self.calls = 0
        self.last_kwargs: dict[str, object] | None = None

    def create(self, **kwargs: object) -> _FakeResponse:
        self.calls += 1
        self.last_kwargs = kwargs
        return _FakeResponse(self._content)


class _FakeChat:
    def __init__(self, completions: _FakeCompletions) -> None:
        self.completions = completions


class _FakeClient:
    def __init__(self, content: str) -> None:
        self.chat = _FakeChat(_FakeCompletions(content))


def test_generate_requires_description() -> None:
    service = AiReferenceService(_FakeSettings("sk-test"))  # type: ignore[arg-type]
    with pytest.raises(AiReferenceError, match="description"):
        service.generate("   ", 3)


def test_generate_requires_configuration() -> None:
    service = AiReferenceService(_FakeSettings(None))  # type: ignore[arg-type]
    with pytest.raises(AiReferenceError, match="not configured"):
        service.generate("Sum two numbers", 3)


def test_generate_extracts_fenced_code_and_clamps_count(monkeypatch: pytest.MonkeyPatch) -> None:
    code = "int main(void) { return 0; }"
    client = _FakeClient(f"Here you go:\n```c\n{code}\n```\nDone.")
    service = AiReferenceService(_FakeSettings("sk-test"))  # type: ignore[arg-type]
    monkeypatch.setattr(service, "_client", lambda: client)

    # Requested 10 but max_count is 3 -> clamped to 3 calls/results.
    refs = service.generate("Print zero", 10)

    assert len(refs) == 3
    assert client.chat.completions.calls == 3
    assert client.chat.completions.last_kwargs is not None
    assert "temperature" not in client.chat.completions.last_kwargs
    assert all(r.source_code == code for r in refs)
    assert refs[0].label == "AI Reference 1"


def test_generate_without_fence_returns_raw(monkeypatch: pytest.MonkeyPatch) -> None:
    code = "void f(void) {}"
    service = AiReferenceService(_FakeSettings("sk-test"))  # type: ignore[arg-type]
    monkeypatch.setattr(service, "_client", lambda: _FakeClient(code))
    refs = service.generate("Empty function", 1)
    assert refs[0].source_code == code


def test_generate_propagates_provider_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Boom:
        def create(self, **_kwargs: object) -> object:
            raise RuntimeError("rate limited")

    class _BoomClient:
        def __init__(self) -> None:
            self.chat = type("C", (), {"completions": _Boom()})()

    service = AiReferenceService(_FakeSettings("sk-test"))  # type: ignore[arg-type]
    monkeypatch.setattr(service, "_client", lambda: _BoomClient())
    with pytest.raises(AiReferenceError, match="provider request failed"):
        service.generate("anything", 1)


def test_generate_uses_concise_provider_error_message(monkeypatch: pytest.MonkeyPatch) -> None:
    class _ProviderError(Exception):
        body = {"error": {"message": "Unsupported value: temperature is fixed."}}

    class _Boom:
        def create(self, **_kwargs: object) -> object:
            raise _ProviderError("raw provider payload")

    class _BoomClient:
        def __init__(self) -> None:
            self.chat = type("C", (), {"completions": _Boom()})()

    service = AiReferenceService(_FakeSettings("sk-test"))  # type: ignore[arg-type]
    monkeypatch.setattr(service, "_client", lambda: _BoomClient())
    with pytest.raises(AiReferenceError, match="Unsupported value: temperature is fixed"):
        service.generate("anything", 1)
