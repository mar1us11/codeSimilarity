"""Shared conversion from persisted function units to pipeline artifacts.

Both :class:`~app.services.comparison_service.ComparisonService` and
:class:`~app.services.analysis_service.AnalysisService` need to rebuild the
in-memory :class:`~app.services.pipeline.FunctionArtifacts` consumed by the
similarity pipeline from a stored :class:`~app.db.models.function.FunctionUnit`.
Keeping it here avoids duplicating the (de)serialization logic.
"""

from __future__ import annotations

from app.db.models.function import FunctionUnit
from app.parsing.ast_nodes import ASTNode
from app.services.pipeline import FunctionArtifacts


def artifacts_from_function(function: FunctionUnit) -> FunctionArtifacts:
    """Rebuild in-memory pipeline artifacts from a persisted function unit."""
    return FunctionArtifacts(
        name=function.name,
        ast=ASTNode.from_dict(function.normalized_ast),
        fingerprints=set(function.fingerprints),
        callees=list(function.callees),
        ref=function.id,
    )
