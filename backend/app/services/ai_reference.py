"""AI reference-solution generation via the official OpenAI SDK.

When an instructor opts in, this service asks an LLM to synthesize several
*independent* correct C implementations of an assignment from its description.
Those solutions are then fed through the very same structural pipeline as
student submissions, so a student's code can be measured against "what a typical
correct solution looks like".

Design notes
------------
* The API key is read from the environment (never hard-coded) via
  :class:`~app.core.config.Settings`.
* The ``openai`` package is imported lazily so the rest of the app (and the test
  suite) runs without the dependency installed or a key configured.
* Generated solutions are **ephemeral**: this layer only returns source strings;
  nothing is persisted. We never claim a student's code *is* AI-generated — we
  only expose similarity to these references.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Fenced code block, optionally tagged ```c / ```cpp.
_FENCE_RE = re.compile(r"```(?:c|cpp|c\+\+)?\s*\n(.*?)```", re.IGNORECASE | re.DOTALL)

_SYSTEM_PROMPT = (
    "You are an expert C programmer producing reference solutions for an "
    "introductory programming course. Given an assignment description, write a "
    "single, complete, idiomatic, self-contained C program that solves it. "
    "Return ONLY the C source code inside one ```c code block, with no prose, "
    "no explanation and no markdown outside the code block."
)


class AiReferenceError(RuntimeError):
    """Raised when reference solutions cannot be generated.

    Carries a user-friendly message safe to surface in the API response.
    """


@dataclass(frozen=True, slots=True)
class GeneratedReference:
    """One synthesized reference solution."""

    label: str
    source_code: str


class AiReferenceService:
    """Generates C reference solutions for an assignment description."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def configured(self) -> bool:
        """Whether an API key is available to call the provider."""
        return self._settings.openai_configured

    def generate(self, description: str, count: int) -> list[GeneratedReference]:
        """Generate ``count`` independent C solutions for ``description``.

        Raises:
            AiReferenceError: if the description is empty, the provider is not
                configured, or the provider call fails.
        """
        description = (description or "").strip()
        if not description:
            raise AiReferenceError(
                "An assignment description is required to generate AI references."
            )
        if not self.configured:
            raise AiReferenceError(
                "AI reference generation is not configured. Set OPENAI_API_KEY in the "
                "backend environment to enable it."
            )

        bounded = self._bounded_count(count)
        client = self._client()

        references: list[GeneratedReference] = []
        for index in range(bounded):
            source = self._generate_one(client, description, index)
            if source:
                references.append(
                    GeneratedReference(label=f"AI Reference {index + 1}", source_code=source)
                )

        if not references:
            raise AiReferenceError(
                "The AI provider did not return any usable C source. Please retry or refine "
                "the assignment description."
            )
        logger.info("Generated %d/%d AI reference solution(s).", len(references), bounded)
        return references

    # internals
    def _bounded_count(self, count: int) -> int:
        if count < 1:
            return self._settings.ai_reference_default_count
        return min(count, self._settings.ai_reference_max_count)

    def _client(self) -> object:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - dependency missing
            raise AiReferenceError(
                "The 'openai' package is not installed on the server."
            ) from exc
        return OpenAI(api_key=self._settings.openai_api_key)

    def _generate_one(self, client: object, description: str, index: int) -> str:
        """Request a single solution; return extracted C source (may be empty)."""
        # A nudge toward stylistic diversity so the references aren't near-clones.
        variation = (
            "Vary naming, helper-function decomposition and control-flow style from a "
            f"typical solution (variant #{index + 1})."
        )
        try:
            response = client.chat.completions.create(  # type: ignore[attr-defined]
                model=self._settings.openai_model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": f"{description}\n\n{variation}"},
                ],
            )
        except Exception as exc:  # noqa: BLE001 - normalize any SDK/transport error
            detail = self._provider_error_message(exc)
            logger.warning("OpenAI request failed: %s", detail)
            raise AiReferenceError(f"AI provider request failed: {detail}") from exc

        content = self._first_message(response)
        return self._extract_code(content)

    @staticmethod
    def _provider_error_message(exc: Exception) -> str:
        """Return the concise provider message from an SDK exception."""
        body = getattr(exc, "body", None)
        if isinstance(body, dict):
            error = body.get("error")
            if isinstance(error, dict) and isinstance(error.get("message"), str):
                return error["message"]
            if isinstance(body.get("message"), str):
                return body["message"]

        message = getattr(exc, "message", None)
        if isinstance(message, str) and message:
            return message
        return str(exc)

    @staticmethod
    def _first_message(response: object) -> str:
        try:
            return response.choices[0].message.content or ""  # type: ignore[attr-defined]
        except (AttributeError, IndexError):  # pragma: no cover - defensive
            return ""

    @staticmethod
    def _extract_code(content: str) -> str:
        """Pull C source out of the model reply, tolerating extra prose/fences."""
        if not content:
            return ""
        match = _FENCE_RE.search(content)
        code = match.group(1) if match else content
        return code.strip()
