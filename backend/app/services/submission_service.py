"""Submission service: ingest source and persist normalized artifacts."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.function import FunctionUnit
from app.db.models.submission import Submission
from app.repositories.submission_repository import SubmissionRepository
from app.services.parsing_service import ParsingService


class SourceValidationError(ValueError):
    """Raised when uploaded source cannot be used for analysis.

    The message is user-facing and safe to surface in an API response.
    """


class SubmissionService:
    """Creates submissions, parsing and fingerprinting them on ingest."""

    def __init__(self, session: Session, parsing_service: ParsingService | None = None) -> None:
        self._session = session
        self._repo = SubmissionRepository(session)
        self._parser = parsing_service or ParsingService()

    def create(
        self, *, workspace: str, name: str, filename: str, source_code: str
    ) -> Submission:
        """Persist a submission and all of its analyzed functions.

        The submission is private to ``workspace`` (the creating browser tab).

        Raises:
            SourceValidationError: if the source is empty or contains no
                parseable C function definitions (nothing to compare).
        """
        if not source_code or not source_code.strip():
            raise SourceValidationError("The submission is empty.")

        try:
            analyzed = self._parser.analyze(source_code)
        except Exception as exc:  # noqa: BLE001 - normalize parser failures
            raise SourceValidationError(
                "The file could not be parsed as C source code."
            ) from exc

        if not analyzed:
            raise SourceValidationError(
                "No C function definitions were found. Upload a .c file that defines "
                "at least one function."
            )

        submission = Submission(
            workspace=workspace,
            name=name,
            filename=filename,
            language="c",
            source_code=source_code,
            ast_node_count=sum(fn.ast_node_count for fn in analyzed),
        )
        submission.functions = [
            FunctionUnit(
                name=fn.name,
                order_index=fn.order_index,
                ast_node_count=fn.ast_node_count,
                normalized_ast=fn.ast.to_dict(),
                fingerprints=fn.fingerprints,
                callees=fn.callees,
            )
            for fn in analyzed
        ]
        return self._repo.add(submission)

    def get(self, submission_id: int, *, workspace: str | None = None) -> Submission | None:
        return self._repo.get_with_functions(submission_id, workspace=workspace)

    def list(self, *, workspace: str, limit: int = 100, offset: int = 0) -> list[Submission]:
        return self._repo.list_with_counts(workspace=workspace, limit=limit, offset=offset)

    def delete(self, submission: Submission) -> None:
        self._repo.delete(submission)
