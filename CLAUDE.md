# KB QA System

Enterprise policy knowledge-base question answering (RAG). Corpus: AI-generated company policies. Vector DB: Weaviate. See `ROADMAP.md` for phases and `docs/adr/` for decisions.

## Commands
- `make install`: sync deps and install pre-commit hooks
- `make check`: lint, mypy and unit tests (run before every commit)
- `make format`: auto-fix lint and formatting
- `uv run pytest -m integration`: integration tests (need Weaviate running)

## Conventions
- Python 3.14, `src/kbqa/` layout, full type hints (`mypy --strict` must pass)
- Weaviate, the LLM and the embedder sit behind interfaces; tests use fakes
- Config only through `kbqa.core.config.Settings` (env prefix `KBQA_`); never read `os.environ` elsewhere
- Logging via structlog; never log secrets or full document contents
- Unit tests in `tests/unit`; tests needing external services go in `tests/integration` with `@pytest.mark.integration`
- Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`); one task per PR, small diffs

## Rules for AI assistance
- Propose a plan and the files you will touch before any large change
- Write or update tests with each change, and make sure they can fail
- Do not add dependencies or frameworks (e.g. LangChain) without an ADR
- Do not hard-code model IDs or API keys; check current docs instead of guessing library APIs
- Record non-trivial decisions as an ADR in `docs/adr/`
