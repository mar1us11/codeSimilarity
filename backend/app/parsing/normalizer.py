"""Structural normalization of C source.

Turns Tree-sitter trees into :class:`NormalizedFunction` objects. The
normalization erases everything a plagiarist trivially changes while keeping
everything that reflects program *structure*:

* identifiers (variables, functions, types, fields) -> generic ``identifier``;
* literals -> a class placeholder (``NUM``/``STR``/``CHAR``/``BOOL``/``NULL``);
* comments -> removed entirely;
* formatting / punctuation -> dropped (only *named* nodes are kept);
* operators -> preserved, since they carry real structural meaning.

Function order is irrelevant here: functions are emitted as an unordered-ish
list and aligned later by Hopcroft–Karp bipartite matching.
"""

from __future__ import annotations

from collections.abc import Iterator

from tree_sitter import Node

from app.parsing.ast_nodes import ASTNode, NormalizedFunction
from app.parsing.parser import CParser

# Identifier-like node types collapse to a single anonymous label.
_IDENTIFIER_TYPES = frozenset(
    {
        "identifier",
        "field_identifier",
        "type_identifier",
        "statement_identifier",
        "namespace_identifier",
    }
)

# Literal node types map to a normalized value placeholder.
_LITERAL_PLACEHOLDERS: dict[str, str] = {
    "number_literal": "NUM",
    "string_literal": "STR",
    "concatenated_string": "STR",
    "char_literal": "CHAR",
    "true": "BOOL",
    "false": "BOOL",
    "null": "NULL",
}

# Node types whose ``operator`` field should be preserved as the node value.
_OPERATOR_FIELD_TYPES = frozenset(
    {
        "binary_expression",
        "unary_expression",
        "assignment_expression",
        "update_expression",
    }
)

_SKIP_TYPES = frozenset({"comment"})


class StructuralNormalizer:
    """Converts C source into normalized per-function structures."""

    def __init__(self, parser: CParser | None = None) -> None:
        self._parser = parser or CParser()

    # -- public API ----------------------------------------------------------
    def normalize_source(self, source: str) -> list[NormalizedFunction]:
        """Parse and normalize every top-level function in ``source``."""
        source_bytes = source.encode("utf-8")
        tree = self._parser.parse(source)
        functions: list[NormalizedFunction] = []
        index = 0
        for node in self._iter_function_definitions(tree.root_node):
            ast = self._normalize_node(node, source_bytes)
            if ast is None:
                continue
            functions.append(
                NormalizedFunction(
                    name=self._function_name(node, source_bytes),
                    order_index=index,
                    ast=ast,
                    callees=self._extract_callees(node, source_bytes),
                )
            )
            index += 1
        return functions

    # -- traversal helpers ---------------------------------------------------
    def _iter_function_definitions(self, root: Node) -> Iterator[Node]:
        """Yield all ``function_definition`` nodes, including nested ones."""
        stack = [root]
        while stack:
            node = stack.pop()
            for child in node.named_children:
                if child.type == "function_definition":
                    yield child
                else:
                    stack.append(child)

    def _normalize_node(self, node: Node, source_bytes: bytes) -> ASTNode | None:
        """Recursively build the normalized AST for ``node``."""
        if node.type in _SKIP_TYPES:
            return None

        label, value = self._label_and_value(node, source_bytes)

        children: list[ASTNode] = []
        for child in node.named_children:
            normalized = self._normalize_node(child, source_bytes)
            if normalized is not None:
                children.append(normalized)

        return ASTNode(label=label, value=value, children=children)

    def _label_and_value(self, node: Node, source_bytes: bytes) -> tuple[str, str | None]:
        """Compute the normalized (label, value) pair for a node."""
        node_type = node.type

        if node_type in _IDENTIFIER_TYPES:
            return "identifier", None

        if node_type in _LITERAL_PLACEHOLDERS:
            return node_type, _LITERAL_PLACEHOLDERS[node_type]

        if node_type in _OPERATOR_FIELD_TYPES:
            operator = node.child_by_field_name("operator")
            if operator is not None:
                return node_type, operator.type
        return node_type, None

    # -- semantic extraction -------------------------------------------------
    def _function_name(self, definition: Node, source_bytes: bytes) -> str:
        """Best-effort extraction of the declared function name."""
        declarator = definition.child_by_field_name("declarator")
        identifier = self._first_identifier(declarator)
        if identifier is not None:
            return CParser.node_text(identifier, source_bytes)
        return "<anonymous>"

    def _first_identifier(self, node: Node | None) -> Node | None:
        """Find the first identifier in a declarator subtree (the callable name)."""
        if node is None:
            return None
        if node.type == "identifier":
            return node
        # Prefer the declarator field path (skips parameter identifiers).
        declarator = node.child_by_field_name("declarator")
        found = self._first_identifier(declarator)
        if found is not None:
            return found
        for child in node.named_children:
            found = self._first_identifier(child)
            if found is not None:
                return found
        return None

    def _extract_callees(self, definition: Node, source_bytes: bytes) -> list[str]:
        """Collect the names of functions called within ``definition``."""
        callees: list[str] = []
        stack = [definition]
        while stack:
            node = stack.pop()
            if node.type == "call_expression":
                func = node.child_by_field_name("function")
                if func is not None and func.type == "identifier":
                    callees.append(CParser.node_text(func, source_bytes))
            stack.extend(node.named_children)
        return callees
