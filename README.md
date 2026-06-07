# CodeGuard

Structural plagiarism detection for C assignments.

CodeGuard compares C source files by **structure**, not text. It parses each
submission with Tree-sitter, normalizes away identifiers/comments/formatting,
and runs a pipeline of structural-similarity algorithms whose results are fused
into a single, order-independent similarity score.

## Architecture

```
React + TypeScript  ->  FastAPI  ->  Analysis Engine  ->  PostgreSQL
   (frontend)           (api)        (services +           (SQLAlchemy
                                       algorithms +          + Alembic)
                                       parsing)
```

### Layers (backend)

| Layer        | Package                | Responsibility                                  |
|--------------|------------------------|-------------------------------------------------|
| API routes   | `app.api`              | HTTP surface, request/response validation       |
| Schemas      | `app.schemas`          | Pydantic I/O contracts                          |
| Services     | `app.services`         | Business logic, pipeline orchestration          |
| Algorithms   | `app.algorithms`       | Pure, self-contained algorithm modules          |
| Parsing      | `app.parsing`          | Tree-sitter parsing + structural normalization  |
| Repositories | `app.repositories`     | Persistence access (repository pattern)         |
| DB / Models  | `app.db`               | SQLAlchemy models, session, base                |

### Algorithm pipeline

1. **AST Parsing** — Tree-sitter C -> normalized `ASTNode` tree per function.
2. **Normalization** — identifiers, literals, comments, formatting erased.
3. **Winnowing** — token stream -> document fingerprints.
4. **Jaccard Similarity** — set similarity over fingerprints.
5. **Tree Edit Distance** — Zhang–Shasha on normalized function ASTs.
6. **Hopcroft–Karp** — maximum bipartite matching aligns functions across two
   submissions, so function *order* never affects the score.
7. **Function Call Graph** — directed call graph per submission.
8. **DFS/BFS Connected Components** — structural decomposition of call graphs.

See `backend/README.md` for module-level contracts and `docs/PIPELINE.md` for
the end-to-end data flow.

### Cohort analysis & AI reference solutions

Beyond manual pairwise comparison, `POST /api/analysis` runs an **all-pairs**
analysis across every submission:

- every submission is compared against every other submission
  (**student similarity**);
- high-similarity pairs are linked into a suspicion graph and **DFS connected
  components** surface *suspicious clusters* of likely collaboration;
- optionally, the engine generates *N* **AI reference solutions** from a problem
  description (OpenAI) and compares each submission against them, reported
  separately as **AI reference similarity**.

AI references are ephemeral — parsed in-memory through the same pipeline and then
discarded. The system never labels code as "AI generated"; it only reports
similarity to a known-correct reference.

Enable AI references by setting `OPENAI_API_KEY` in the backend environment
(`backend/.env`). Without it, the rest of the system works unchanged and the UI
toggle stays disabled.

## Quick start

```bash
# Backend
cd backend
python -m venv .venv && . .venv/Scripts/activate   # Windows
pip install -e ".[dev]"
docker compose up -d db                            # from repo root
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Tests

```bash
cd backend && pytest
cd frontend && npm run test
```
