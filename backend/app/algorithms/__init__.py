"""Algorithm layer.

Every algorithm lives in its own module, depends only on the normalized data
structures from :mod:`app.parsing`, and exposes a small, explicit input/output
contract (see :mod:`app.algorithms.base`). Nothing here touches the database,
HTTP, or configuration — they are pure, independently testable functions.
"""

from app.algorithms.base import SimilarityResult
from app.algorithms.call_graph import CallGraph, CallGraphSimilarity
from app.algorithms.graph_traversal import ConnectedComponents
from app.algorithms.hopcroft_karp import HopcroftKarp, Matching
from app.algorithms.jaccard import JaccardSimilarity
from app.algorithms.tree_edit_distance import TreeEditDistance
from app.algorithms.winnowing import Winnowing, WinnowingSimilarity

__all__ = [
    "SimilarityResult",
    "JaccardSimilarity",
    "Winnowing",
    "WinnowingSimilarity",
    "TreeEditDistance",
    "HopcroftKarp",
    "Matching",
    "CallGraph",
    "CallGraphSimilarity",
    "ConnectedComponents",
]
