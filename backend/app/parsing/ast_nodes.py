"""Normalized AST data structures.

These types are the contract between the parsing layer and every algorithm.
They are deliberately free of Tree-sitter types so algorithms never depend on
the parser, and they are trivially (de)serializable for persistence.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ASTNode:
    """A node in the normalized abstract syntax tree.

    Attributes:
        label: Structural kind of the node (e.g. ``"if_statement"``). Never an
            identifier or literal value, so renaming variables/functions cannot
            change it.
        value: Optional normalized leaf payload. Only carries semantics that are
            *not* identifiers — operator tokens (``"+"``) or literal class
            placeholders (``"NUM"``, ``"STR"``). ``None`` for internal nodes.
        children: Ordered child nodes.
    """

    label: str
    value: str | None = None
    children: list[ASTNode] = field(default_factory=list)

    # structural helpers
    @property
    def signature(self) -> str:
        """Comparison key used by Tree Edit Distance."""
        return self.label if self.value is None else f"{self.label}:{self.value}"

    def size(self) -> int:
        """Total number of nodes in the subtree rooted here."""
        return 1 + sum(child.size() for child in self.children)

    def iter_preorder(self) -> Iterator[ASTNode]:
        """Yield nodes in preorder (root, then children left-to-right)."""
        yield self
        for child in self.children:
            yield from child.iter_preorder()

    def iter_postorder(self) -> Iterator[ASTNode]:
        """Yield nodes in postorder (children left-to-right, then root)."""
        for child in self.children:
            yield from child.iter_postorder()
        yield self

    def token_stream(self) -> list[str]:
        """Preorder sequence of node signatures, used as the winnowing input.

        Because labels are structural and values are limited to operators and
        literal classes, this stream is invariant under identifier renaming,
        comment removal and reformatting.
        """
        return [node.signature for node in self.iter_preorder()]

    # serialization
    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        out: dict[str, Any] = {"label": self.label}
        if self.value is not None:
            out["value"] = self.value
        if self.children:
            out["children"] = [child.to_dict() for child in self.children]
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ASTNode:
        """Reconstruct an :class:`ASTNode` from :meth:`to_dict` output."""
        return cls(
            label=data["label"],
            value=data.get("value"),
            children=[cls.from_dict(child) for child in data.get("children", [])],
        )


@dataclass(slots=True)
class NormalizedFunction:
    """A single function after structural normalization."""

    #: Original source name. Used only for display and intra-submission call
    #: resolution — never fed into cross-submission similarity.
    name: str
    #: Position of the function in the source file (informational only).
    order_index: int
    #: Root of the normalized AST for this function.
    ast: ASTNode
    #: Original names of functions invoked in the body (call-graph edges).
    callees: list[str] = field(default_factory=list)

    def ast_node_count(self) -> int:
        return self.ast.size()
