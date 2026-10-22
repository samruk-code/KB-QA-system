# KB QA System

Enterprise policy knowledge-base question answering using retrieval-augmented generation, with Weaviate as the vector store.

**Status:** Phase 0 (foundations). See [ROADMAP.md](ROADMAP.md).

## Development
```bash
make install   # sync dependencies and install pre-commit hooks
make check     # lint, type-check, unit tests
```
Copy `.env.example` to `.env` for local settings.

## Documentation
- [ROADMAP.md](ROADMAP.md): phases and exit criteria
- [docs/adr/](docs/adr/): architecture decision records
- [docs/ai-log.md](docs/ai-log.md): notes on AI-assisted coding
