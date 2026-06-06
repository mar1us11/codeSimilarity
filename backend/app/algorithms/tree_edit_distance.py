"""Tree Edit Distance via the Zhang–Shasha algorithm.

Contract:
    TreeEditDistance.distance(a, b) -> int
        the minimum number of node insert/delete/relabel operations to turn the
        ordered, labeled tree ``a`` into ``b``. Costs: insert = delete = 1,
        relabel = 0 if node *signatures* match else 1.

    TreeEditDistance.similarity(a, b) -> SimilarityResult
        ``score = 1 - distance / (size(a) + size(b))`` ∈ [0, 1].

Operating on the *normalized* AST (identifiers/literals erased) makes the
distance a measure of pure structural difference. Zhang–Shasha runs in
O(n·m·min(depth,leaves)^2) which is comfortably fast for function-sized trees.

Reference: K. Zhang and D. Shasha, "Simple Fast Algorithms for the Editing
Distance Between Trees and Related Problems", SIAM J. Comput., 1989.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.algorithms.base import SimilarityResult
from app.parsing.ast_nodes import ASTNode


@dataclass(slots=True)
class _Annotated:
    """Postorder annotation of a tree (1-based indices, slot 0 unused)."""

    signatures: list[str]   # signatures[i] = signature of i-th postorder node
    leftmost: list[int]     # leftmost[i] = postorder index of i's leftmost leaf
    keyroots: list[int]     # sorted keyroot postorder indices

    @property
    def size(self) -> int:
        return len(self.signatures) - 1


def _annotate(root: ASTNode) -> _Annotated:
    """Compute postorder signatures, leftmost-leaf map and keyroots."""
    signatures: list[str] = [""]   # 1-based
    leftmost: list[int] = [0]

    def visit(node: ASTNode) -> int:
        child_lms: list[int] = []
        first_lm: int | None = None
        for i, child in enumerate(node.children):
            child_index = visit(child)
            if i == 0:
                first_lm = leftmost[child_index]
            child_lms.append(child_index)
        signatures.append(node.signature)
        index = len(signatures) - 1
        leftmost.append(index if first_lm is None else first_lm)
        return index

    visit(root)

    # keyroots = for each distinct leftmost value, the largest postorder index.
    by_leftmost: dict[int, int] = {}
    for i in range(1, len(signatures)):
        by_leftmost[leftmost[i]] = i  # ascending i keeps the max
    keyroots = sorted(by_leftmost.values())
    return _Annotated(signatures=signatures, leftmost=leftmost, keyroots=keyroots)


def _tree_edit_distance(a: _Annotated, b: _Annotated) -> int:
    """Core Zhang–Shasha dynamic program."""
    n, m = a.size, b.size
    if n == 0 and m == 0:
        return 0
    if n == 0:
        return m
    if m == 0:
        return n

    la, lb = a.leftmost, b.leftmost
    # treedist[i][j] over the full node ranges (1-based).
    treedist = [[0] * (m + 1) for _ in range(n + 1)]

    for ki in a.keyroots:
        for kj in b.keyroots:
            li, lj = la[ki], lb[kj]
            rows = ki - li + 2
            cols = kj - lj + 2
            # forestdist offset so that fd[di - li + 1][dj - lj + 1] is valid;
            # index 0 represents the empty forest.
            fd = [[0] * cols for _ in range(rows)]
            for di in range(li, ki + 1):
                fd[di - li + 1][0] = fd[di - li][0] + 1  # delete
            for dj in range(lj, kj + 1):
                fd[0][dj - lj + 1] = fd[0][dj - lj] + 1  # insert

            for di in range(li, ki + 1):
                for dj in range(lj, kj + 1):
                    fi, fj = di - li + 1, dj - lj + 1
                    delete = fd[fi - 1][fj] + 1
                    insert = fd[fi][fj - 1] + 1
                    if la[di] == li and lb[dj] == lj:
                        relabel = fd[fi - 1][fj - 1] + (
                            0 if a.signatures[di] == b.signatures[dj] else 1
                        )
                        fd[fi][fj] = min(delete, insert, relabel)
                        treedist[di][dj] = fd[fi][fj]
                    else:
                        prev = fd[la[di] - li][lb[dj] - lj] + treedist[di][dj]
                        fd[fi][fj] = min(delete, insert, prev)

    return treedist[n][m]


class TreeEditDistance:
    """Zhang–Shasha tree edit distance and derived similarity."""

    name = "tree_edit_distance"

    def distance(self, a: ASTNode, b: ASTNode) -> int:
        """Edit distance between two normalized AST roots."""
        return _tree_edit_distance(_annotate(a), _annotate(b))

    def similarity(self, a: ASTNode, b: ASTNode, /) -> SimilarityResult:
        ann_a = _annotate(a)
        ann_b = _annotate(b)
        dist = _tree_edit_distance(ann_a, ann_b)
        denom = ann_a.size + ann_b.size
        score = 1.0 if denom == 0 else 1.0 - dist / denom
        return SimilarityResult(
            score=max(0.0, min(1.0, score)),
            detail={
                "distance": float(dist),
                "size_a": float(ann_a.size),
                "size_b": float(ann_b.size),
            },
        )
