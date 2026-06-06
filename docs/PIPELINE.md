# Analysis Pipeline

End-to-end data flow from raw C source to a similarity score.

## 1. Ingest (once per submission)

```
source.c
   │  CParser (Tree-sitter C)
   ▼
concrete syntax tree
   │  StructuralNormalizer
   ▼
list[NormalizedFunction]      # per function:
   ├── ast: ASTNode           #   identifiers -> "identifier"
   │                          #   literals    -> NUM/STR/CHAR/BOOL/NULL
   │                          #   comments    -> removed
   │                          #   formatting  -> dropped (named nodes only)
   │                          #   operators   -> preserved
   ├── token_stream()         # preorder structural tokens
   └── callees                # resolved later to call-graph edges
   │  Winnowing
   ▼
fingerprints: set[int]        # persisted alongside the AST + callees
```

`SubmissionService.create` persists each function's normalized AST,
fingerprints and callees, so parsing happens exactly once.

## 2. Compare (per submission pair)

```
functions A           functions B
     │                     │
     └──────── similarity matrix ────────┘
        sim[i][j] = w_ted'·TED(i,j) + w_winnow'·Jaccard(fp_i, fp_j)
     │
     │  edges where sim ≥ match_threshold
     ▼
   Hopcroft–Karp maximum bipartite matching   → aligned (i, j) pairs
     │
     ├── aligned_ted    = Σ TED(i,j)    / max(|A|, |B|)
     ├── aligned_winnow = Σ Jaccard(i,j)/ max(|A|, |B|)
     │
     │  CallGraph.from_functions(A), (B)
     ▼
   CallGraphSimilarity            → degree signature (multiset Jaccard)
     (uses DFS/BFS components)      + edge density + component-count ratio
     │
     ▼
overall = w_ted·aligned_ted + w_winnow·aligned_winnow + w_callgraph·callgraph
```

Component scores (`ted_score`, `winnow_score`, `callgraph_score`) and the
per-function matches are stored on the `Comparison` for explainability and
surfaced in the UI.

## Why each algorithm is here

- **Tree Edit Distance** — fine-grained structural difference between two
  function ASTs; robust to statement-level edits.
- **Winnowing + Jaccard** — fast, locality-preserving fingerprint overlap;
  catches copied blocks even when surrounding structure differs.
- **Hopcroft–Karp** — optimal function alignment, making the score independent
  of function order and tolerant of added/removed helpers.
- **Call graph + DFS/BFS** — captures *program decomposition* (how routines
  call each other), a structural signal invisible to per-function metrics.

## Tunable parameters (`app.core.config.Settings`)

| Setting | Meaning | Default |
|---------|---------|---------|
| `winnow_k` | k-gram length | 5 |
| `winnow_window` | winnowing window `w` | 4 |
| `weight_ted` / `weight_winnow` / `weight_callgraph` | fusion weights | 0.50 / 0.35 / 0.15 |
| `match_threshold` | min per-function similarity for a match edge | 0.60 |
