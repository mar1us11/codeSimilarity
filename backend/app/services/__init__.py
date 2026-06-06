"""Service layer: business logic and pipeline orchestration.

Services coordinate the parsing, algorithm and repository layers. They contain
no HTTP concerns (that is :mod:`app.api`) and no raw SQL (that is
:mod:`app.repositories`).
"""

from app.services.comparison_service import ComparisonService, SubmissionNotFoundError
from app.services.parsing_service import ParsingService
from app.services.pipeline import FunctionArtifacts, PipelineResult, SimilarityPipeline
from app.services.submission_service import SubmissionService

__all__ = [
    "ParsingService",
    "SubmissionService",
    "ComparisonService",
    "SubmissionNotFoundError",
    "SimilarityPipeline",
    "PipelineResult",
    "FunctionArtifacts",
]
