# KB QA System: Senior-Level Roadmap

A knowledge-base question answering system (RAG) built with production engineering habits and AI-assisted coding. Roughly 10-12 weeks at ~8-10 hrs/week. Each phase ends with exit criteria. Don't move on until you meet them.

## Guiding principles

1. **Eval-first.** You can't improve retrieval or answers you can't measure. The golden dataset comes before the pipeline.
2. **Thin vertical slice first.** Get a crude end-to-end version working in week 2, then deepen each layer.
3. **Decisions are written down.** Every non-trivial choice gets a short ADR (`docs/adr/`): context, options, decision, consequences.
4. **You own every line.** AI writes drafts; you review diffs, run tests, and can explain the code. If you can't, ask for an explanation or rewrite it.
5. **Boring infrastructure.** Typed, tested, linted, containerized, observable, with CI from day one.

## AI-assisted coding workflow (applies to every phase)

- **CLAUDE.md** at repo root: stack, commands (test/lint/run), conventions, architecture rules, "don't do" list. Update it as the project evolves.
- **Plan, then code.** For each task, have the AI propose a plan and the files it will touch. Edit the plan, then implement.
- **Tests first for logic.** Write (or have the AI write, then you review) failing tests, then implement. Never accept tests the AI wrote *after* the code without checking they can fail.
- **Small diffs, small commits.** One task = one branch/PR = one reviewable diff (<300 lines). Conventional commits.
- **Self-review before merge.** Read the full diff as if a stranger wrote it. Use `/code-review` as a second pass, not a replacement.
- **Verify, don't trust.** Library APIs and model IDs change; check docs. Run the code. Hallucinated imports and silently swallowed errors are the usual failures.
- **Keep a `docs/ai-log.md`.** Note where AI helped, where it was wrong, and what prompt or constraint fixed it. This becomes your strongest learning artifact.

---

## Phase 0: Project foundations (Week 1)

**Goal:** a repo where bad code can't easily get in.

- `git init`, GitHub remote, branch protection, PR template
- Python 3.12+, `uv` for deps, `pyproject.toml`
- `ruff` (lint+format), `mypy --strict` (or pyright), `pytest`, `pre-commit`
- Layout: `src/kbqa/{ingestion,retrieval,generation,api,evals,core}`, `tests/`, `docs/`
- Typed config via `pydantic-settings`; secrets only via env
- GitHub Actions CI: lint, type-check, test on every PR
- `CLAUDE.md`, `README.md` skeleton, `docs/adr/0001-record-decisions.md`

**Exit:** a trivial PR goes through CI green; pre-commit blocks a lint violation.

## Phase 1: Problem definition and eval dataset (Week 2)

**Goal:** know what "good" means before building.

- **Corpus: AI-generated enterprise policies** for a fictional company (HR, IT security, finance/expenses, legal/compliance, travel, remote work). Target 100-300 documents.
  - Make it realistic, not tidy. Generate varied formats (Markdown, HTML, PDF, DOCX), headings and tables, version numbers and effective dates, **superseded policies** (v1 vs v2), **contradictions between departments**, region-specific variants, cross-references ("see Policy IT-204"), and documents restricted by department/role.
  - Give each document metadata: `doc_id`, `department`, `version`, `effective_date`, `status` (active/superseded), `access_level`.
  - **Risk: circular evaluation.** If the same model writes the corpus and the questions, evals will be flattering. Generate questions with a different model or prompt style, include paraphrased and vague questions, and hand-verify every golden answer.
- Write a one-page spec: users (employees, HR, auditors), query types (factoid, multi-hop, "which version applies?", "not in KB"), non-goals, latency/cost targets.
- Build a **golden set of 50-100 Q&A pairs**: question, reference answer, supporting doc/chunk IDs, plus 10-15 unanswerable questions and a few access-control cases ("can an intern see the salary bands policy?"). Hand-verify. AI can draft candidates, but you validate.
- Define metrics: retrieval (recall@k, MRR, nDCG), generation (faithfulness, answer correctness, abstention accuracy), ops (p95 latency, cost/query).

**Exit:** `evals/golden.jsonl` committed; metrics defined in `docs/evaluation.md`.

## Phase 2: Ingestion pipeline (Weeks 3-4)

**Goal:** reliable, repeatable, incremental indexing.

- Loaders (Markdown/HTML/PDF), cleaning, metadata extraction (source, title, section, URL, updated_at, ACL tag)
- Chunking strategies behind one interface: fixed, recursive, structure-aware (headings). Compare them with your eval set.
- Embedding provider behind an interface (swap-able); batching, retries with backoff, rate-limit handling
- Vector store: **Weaviate** (decided). Write an ADR covering why (native hybrid search, filtering, multi-tenancy) and what you give up (extra service to run, separate store from any relational data).
  - Run via docker compose; use the v4 Python client
  - Design the collection schema deliberately: properties for the metadata above, which are filterable/searchable, and vectorizer choice (bring your own vectors vs. a Weaviate vectorizer module; prefer bring-your-own behind your embedder interface)
  - Decide on one collection vs. per-tenant/department; document the trade-off
  - Wrap Weaviate behind a `VectorStore` interface so tests use an in-memory fake
- **Idempotent and incremental:** content hashes, upserts, deletion of removed docs, re-embed only what changed
- CLI: `kbqa ingest <path>`; structured logging

**Exit:** re-running ingest is a no-op; changing one doc re-indexes only that doc; a superseded policy version is marked, not deleted; integration tests run against a real Weaviate via Testcontainers or docker compose.

## Phase 3: Retrieval (Weeks 5-6)

**Goal:** the highest-leverage quality work.

- Baseline dense retrieval; measure with the golden set
- **Hybrid search:** Weaviate's native hybrid query (BM25 + vector) and tune `alpha` and the fusion method (relativeScore vs rankedFusion) against your eval set. Policy text has exact terms (policy codes, acronyms), so BM25 should matter here.
- **Reranking:** cross-encoder or hosted reranker on top-N
- **Metadata-aware retrieval:** default to `status = active`, filter by department/region, and handle "which version applies on date X?"
- Query rewriting/expansion, optional HyDE; keep each as a toggleable, measured experiment
- Experiment log: each change shows the metric delta in `docs/experiments.md`. Drop anything that doesn't earn its complexity.

**Exit:** a table showing baseline vs. hybrid vs. rerank on recall@k/MRR, plus a documented decision on what ships.

## Phase 4: Generation and grounding (Week 7)

**Goal:** answers you can trust.

- Prompt templates under version control, separate from code
- **Citations** mapped to chunk IDs and source URLs; verify cited IDs exist in the retrieved context
- **Abstention:** "I don't know" when retrieval is weak (threshold + model instruction); measure on unanswerable questions
- Structured outputs (Pydantic schema) for answer, citations, confidence
- Streaming responses; context-window budgeting; conversation history handling
- LLM-as-judge for faithfulness, calibrated against your hand labels

**Exit:** end-to-end eval run reports faithfulness, correctness, and abstention accuracy.

## Phase 5: API and service layer (Week 8)

**Goal:** a real service, not a notebook.

- **FastAPI** async: `POST /ask` (streaming SSE), `GET /health`, `POST /feedback`, admin ingest endpoints
- Dependency injection for LLM/embedder/store so tests use fakes
- Provider-level timeouts, retries, circuit breaking, graceful fallback
- Auth (API keys or OAuth/JWT), rate limiting, request validation, consistent error model
- Response caching (semantic or exact-match); measure hit rate and savings
- Contract tests; OpenAPI docs

**Exit:** the API passes tests with all external providers faked; load test (k6/locust) shows p95 at the target.

## Phase 6: Evals in CI and observability (Week 9)

**Goal:** know when quality, cost, or latency regresses.

- `make eval` runs the golden set; **CI fails on metric regression** beyond a tolerance (use a small fast subset on PRs, full set nightly)
- Tracing end to end (OpenTelemetry, Langfuse, or Phoenix): retrieval spans, LLM calls, tokens, cost, latency
- Structured logs with request IDs; metrics dashboard (latency, error rate, tokens/query, abstention rate)
- User feedback (thumbs up/down) stored and fed back into the eval set

**Exit:** you can open one trace and see why a given answer was bad.

## Phase 7: Security and safety (Week 10)

**Goal:** treat the KB and the user as untrusted.

- **Prompt injection** via documents: delimit context, instruct to ignore embedded instructions, and test with poisoned docs
- **ACL-aware retrieval:** filter by user role/department in the Weaviate query itself (or via multi-tenancy) *before* the LLM sees the content. Enforce it server-side from the auth token, never from client input. Test that an intern never gets restricted HR/legal docs.
- PII detection/redaction at ingest and in logs
- Dependency scanning (`pip-audit`, Dependabot), secret scanning, threat model in `docs/security.md`
- Red-team test suite in `tests/security/`

**Exit:** injection and cross-tenant leakage tests pass in CI.

## Phase 8: Agentic extension (Week 11)

**Goal:** apply the agent skills you learned, only where evals show they help.

- Query decomposition for multi-hop questions
- Tool use: retrieval as a tool, plus optionally SQL/web/code tools; bounded loop, step limits, and cost caps
- Compare agentic vs. static pipeline on the eval set (accuracy gain vs. latency and cost increase)
- Optional: MCP server exposing the KB to other agents

**Exit:** an ADR with data on whether the agent ships by default, behind a flag, or not at all.

## Phase 9: Deploy and polish (Week 12)

**Goal:** something a hiring manager can run in five minutes.

- Multi-stage `Dockerfile`, `docker-compose` (app + Postgres + observability)
- CD to a cloud host (Fly.io, Render, Cloud Run, or ECS); infra config in the repo; health checks, migrations (Alembic)
- Simple UI (Streamlit or a minimal React/HTMX chat) with citations shown
- README: architecture diagram, quickstart, eval results table, cost/latency numbers, trade-offs and what you'd do next
- Short demo video or write-up on what you learned and where AI-assisted coding helped or failed

**Exit:** fresh clone to running system in <10 minutes, following the README only.

---

## Target architecture

```
Docs -> Loaders -> Cleaner -> Chunker -> Embedder -> Vector store (Weaviate)
                                                           |
User -> API (auth, rate limit, cache) -> Query rewrite -> Hybrid retrieve -> Rerank
                                                                              |
                          Answer + citations <- LLM (grounded prompt) <- Context builder
                                  |
                      Tracing / metrics / feedback -> Eval set
```

## Senior-level signals to demonstrate

| Area | Evidence |
|---|---|
| Measurement | Golden set, metric tables, regression gates in CI |
| Decisions | ADRs with trade-offs and rejected alternatives |
| Reliability | Retries, timeouts, idempotent ingest, graceful degradation |
| Testing | Unit + integration + eval + security tests; fakes at boundaries |
| Operability | Traces, structured logs, dashboards, cost tracking |
| Security | ACL-aware retrieval, injection tests, threat model |
| Communication | Clear README, architecture diagram, honest limitations |

## Suggested stack (change via ADR)

Python 3.12, uv, FastAPI, Pydantic, Weaviate (v4 client), pytest, ruff, mypy, Docker, GitHub Actions (add Postgres + Alembic only if you need relational data such as users or feedback), OpenTelemetry/Langfuse, Anthropic API for generation (check current model IDs in the docs), an embeddings provider of your choice. Prefer thin custom code over heavy frameworks (LangChain/LlamaIndex) so you understand each layer. You can compare against one later.

## Common pitfalls

- Tuning prompts before you have an eval set
- Adopting a framework before you understand what it hides
- Accepting large AI-generated diffs without reading them
- Judging quality by trying a few queries by hand
- Skipping the "not in KB" case
- Over-building: add reranking, agents, or caching only when the numbers justify it
