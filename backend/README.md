# CodeGuard Backend

FastAPI service + analysis engine. Layered so each concern is independently
testable and the algorithms stay pure.

```
app/
├── core/          # config (pydantic-settings) + logging
├── db/            # SQLAlchemy base, session, ORM models
├── repositories/  # repository pattern over the ORM
├── parsing/       # Tree-sitter C parsing + structural normalization
│   ├── parser.py        # CParser: the only Tree-sitter touch point
│   ├── ast_nodes.py     # ASTNode / NormalizedFunction (parser-free contracts)
│   └── normalizer.py    # StructuralNormalizer: erase identifiers/literals/...
├── algorithms/    # one self-contained module per algorithm
│   ├── base.py            # SimilarityResult + SimilarityAlgorithm protocol
│   ├── jaccard.py         # set similarity
│   ├── winnowing.py       # fingerprinting (+ WinnowingSimilarity)
│   ├── tree_edit_distance.py  # Zhang–Shasha TED
│   ├── hopcroft_karp.py   # maximum bipartite matching
│   ├── call_graph.py      # call-graph build + structural similarity
│   └── graph_traversal.py # DFS/BFS connected components
├── services/      # business logic + pipeline orchestration
│   ├── parsing_service.py     # source -> persistable artifacts
│   ├── submission_service.py  # ingest + persist (+ source validation)
│   ├── comparison_service.py  # DB <-> pipeline bridge (caching)
│   ├── artifacts.py           # FunctionUnit -> pipeline artifacts (shared)
│   ├── ai_reference.py        # OpenAI reference-solution generation
│   ├── analysis_service.py    # all-pairs cohort analysis + clustering
│   └── pipeline.py            # SimilarityPipeline: fuses every algorithm
├── schemas/       # Pydantic request/response contracts
└── api/           # FastAPI routers + dependencies
```

## Cohort analysis (`POST /api/analysis`)

`AnalysisService` orchestrates the unchanged `SimilarityPipeline` over a whole
cohort instead of a single pair:

- **student-vs-student**: every submission compared against every other;
- **suspicious clusters**: high-similarity pairs form a graph; DFS connected
  components group transitively-linked submissions;
- **student-vs-AI-reference** (optional): when `OPENAI_API_KEY` is set and the
  request enables it (with a problem description), `AiReferenceService` generates
  *N* C solutions which are parsed in-memory and compared against each
  submission. References are never persisted and code is never classified as
  "AI generated" — only similarity to a reference is reported.

`GET /api/analysis/capabilities` reports whether AI references are configured so
the UI can enable/disable the toggle.

## Configuration

`OPENAI_API_KEY` / `OPENAI_MODEL` are read directly from the (unprefixed)
environment per the OpenAI SDK convention; everything else uses the
`CODEGUARD_` prefix. See `.env.example`. Never commit a real key.

## Algorithm I/O contracts

| Module | Input | Output |
|--------|-------|--------|
| `jaccard` | two sets of hashables | score `|A∩B|/|A∪B|` |
| `winnowing` | token sequence | set of k-gram fingerprints |
| `tree_edit_distance` | two `ASTNode` roots | Zhang–Shasha edit distance + similarity |
| `hopcroft_karp` | bipartite adjacency | maximum matching (`pairs`, `size`) |
| `call_graph` | normalized functions | directed `CallGraph`; shape similarity |
| `graph_traversal` | nodes + undirected edges | connected components (DFS and BFS) |

## How order-independence is achieved

Submissions are compared **function by function**. A per-function similarity
matrix (TED + winnowing/Jaccard) is thresholded into a bipartite graph, and
**Hopcroft–Karp** computes the maximum alignment. Because the alignment is a
matching — not a positional zip — reordering functions cannot change the score.
Identifier/comment/format normalization happens in the parsing layer, so
renaming cannot change it either.

## Local setup

```bash
python -m venv .venv && . .venv/Scripts/activate
pip install -e ".[dev]"

# point CODEGUARD_DATABASE_URL at your local Postgres (see .env.example)
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Tests

```bash
pytest            # algorithm + parsing + pipeline suites (no DB required)
mypy app          # strict type checking
ruff check app
```
