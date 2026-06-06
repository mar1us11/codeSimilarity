"""Parsing layer: Tree-sitter C parsing and structural normalization.

This layer is the only place that knows about Tree-sitter. It turns raw C
source into a list of :class:`~app.parsing.ast_nodes.NormalizedFunction`
objects whose AST, token stream and call edges are stripped of identifiers,
literals, comments and formatting. Downstream algorithm modules operate purely
on these normalized structures.
"""

from app.parsing.ast_nodes import ASTNode, NormalizedFunction
from app.parsing.normalizer import StructuralNormalizer
from app.parsing.parser import CParser

__all__ = ["ASTNode", "NormalizedFunction", "StructuralNormalizer", "CParser"]
