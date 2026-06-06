"""Submission endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, UploadFile, status

from app.api.deps import SubmissionServiceDep, WorkspaceDep
from app.schemas.submission import (
    FunctionRead,
    SubmissionCreate,
    SubmissionRead,
    SubmissionSummary,
)
from app.services.submission_service import SourceValidationError

router = APIRouter()

#: Source file extensions we accept for upload.
_ALLOWED_EXTENSIONS = (".c", ".h")
#: Reject oversized uploads early (2 MiB is generous for a C assignment).
_MAX_UPLOAD_BYTES = 2 * 1024 * 1024


def _to_read(submission: object) -> SubmissionRead:
    functions = [FunctionRead.from_model(fn) for fn in submission.functions]  # type: ignore[attr-defined]
    return SubmissionRead(
        id=submission.id,  # type: ignore[attr-defined]
        name=submission.name,  # type: ignore[attr-defined]
        filename=submission.filename,  # type: ignore[attr-defined]
        language=submission.language,  # type: ignore[attr-defined]
        ast_node_count=submission.ast_node_count,  # type: ignore[attr-defined]
        created_at=submission.created_at,  # type: ignore[attr-defined]
        functions=functions,
    )


def _to_summary(submission: object) -> SubmissionSummary:
    return SubmissionSummary(
        id=submission.id,  # type: ignore[attr-defined]
        name=submission.name,  # type: ignore[attr-defined]
        filename=submission.filename,  # type: ignore[attr-defined]
        language=submission.language,  # type: ignore[attr-defined]
        ast_node_count=submission.ast_node_count,  # type: ignore[attr-defined]
        function_count=len(submission.functions),  # type: ignore[attr-defined]
        created_at=submission.created_at,  # type: ignore[attr-defined]
    )


@router.post(
    "",
    response_model=SubmissionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a submission from a JSON body",
)
def create_submission(
    payload: SubmissionCreate, service: SubmissionServiceDep, workspace: WorkspaceDep
) -> SubmissionRead:
    try:
        submission = service.create(
            workspace=workspace,
            name=payload.name,
            filename=payload.filename,
            source_code=payload.source_code,
        )
    except SourceValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return _to_read(submission)


@router.post(
    "/upload",
    response_model=SubmissionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a submission from an uploaded .c file",
)
async def upload_submission(
    service: SubmissionServiceDep,
    workspace: WorkspaceDep,
    file: UploadFile,
    name: str | None = None,
) -> SubmissionRead:
    filename = file.filename or "submission.c"
    if not filename.lower().endswith(_ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only C source files (.c, .h) are supported.",
        )

    raw = await file.read()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is empty."
        )
    if len(raw) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File is too large (2 MiB maximum).",
        )

    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is not valid UTF-8 text.",
        ) from exc

    try:
        submission = service.create(
            workspace=workspace,
            name=name or filename,
            filename=filename,
            source_code=source,
        )
    except SourceValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return _to_read(submission)


@router.get("", response_model=list[SubmissionSummary], summary="List submissions")
def list_submissions(
    service: SubmissionServiceDep,
    workspace: WorkspaceDep,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[SubmissionSummary]:
    return [
        _to_summary(s)
        for s in service.list(workspace=workspace, limit=limit, offset=offset)
    ]


@router.get("/{submission_id}", response_model=SubmissionRead, summary="Get a submission")
def get_submission(
    submission_id: int, service: SubmissionServiceDep, workspace: WorkspaceDep
) -> SubmissionRead:
    submission = service.get(submission_id, workspace=workspace)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    return _to_read(submission)


@router.delete(
    "/{submission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a submission",
)
def delete_submission(
    submission_id: int, service: SubmissionServiceDep, workspace: WorkspaceDep
) -> None:
    submission = service.get(submission_id, workspace=workspace)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    service.delete(submission)
