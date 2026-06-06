"""Repository layer: the only place that issues persistence queries.

Repositories wrap a SQLAlchemy :class:`~sqlalchemy.orm.Session` and expose
intention-revealing methods. Services depend on these abstractions rather than
on the ORM directly (repository pattern).
"""

from app.repositories.comparison_repository import ComparisonRepository
from app.repositories.submission_repository import SubmissionRepository

__all__ = ["SubmissionRepository", "ComparisonRepository"]
