"""Thin, version-tolerant wrapper around the Tree-sitter C grammar.

This is the single point of contact with Tree-sitter. The binding's
constructor signatures have shifted across 0.21/0.22, so initialization is
defensive: callers just get a working :class:`CParser`.
"""

from __future__ import annotations

from functools import lru_cache

import tree_sitter_c as tsc
from tree_sitter import Language, Node, Parser, Tree


@lru_cache(maxsize=1)
def _load_language() -> Language:
    """Load the C grammar, tolerating constructor differences across versions."""
    ptr = tsc.language()
    try:
        return Language(ptr)  # tree-sitter >= 0.21 single-arg form
    except TypeError:  # pragma: no cover - older binding fallback
        return Language(ptr, "c")  # type: ignore[call-arg]


class CParser:
    """Parses C source into a Tree-sitter concrete syntax tree."""

    def __init__(self) -> None:
        self._language = _load_language()
        # Constructor/assignment forms differ across tree-sitter 0.21–0.24;
        # try them in order of preference for the modern bindings.
        try:
            self._parser = Parser(self._language)
        except TypeError:  # pragma: no cover - older binding
            self._parser = Parser()
            try:
                self._parser.language = self._language
            except (AttributeError, TypeError):
                self._parser.set_language(self._language)  # type: ignore[attr-defined]

    def parse(self, source: str) -> Tree:
        """Parse ``source`` and return the Tree-sitter tree."""
        return self._parser.parse(source.encode("utf-8"))

    @staticmethod
    def node_text(node: Node, source_bytes: bytes) -> str:
        """Return the exact source text spanned by ``node``."""
        return source_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
