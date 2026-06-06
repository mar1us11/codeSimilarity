"""ORM models for CodeGuard.

Importing this package registers every model on the shared declarative
``Base.metadata`` so that Alembic autogeneration and ``create_all`` see them.
"""

from app.db.models.comparison import Comparison, FunctionMatch
from app.db.models.function import FunctionUnit
from app.db.models.saved_lab import SavedLab
from app.db.models.submission import Submission

__all__ = ["Submission", "FunctionUnit", "Comparison", "FunctionMatch", "SavedLab"]
