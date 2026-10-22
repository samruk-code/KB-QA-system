# 1. Record architecture decisions

Date: 2026-10-22
Status: Accepted

## Context
This project involves many trade-offs: vector store, chunking, retrieval strategy, whether to use agents. Without a written record the reasoning gets lost and the same debates repeat.

## Decision
Each non-trivial decision is recorded as a short ADR in `docs/adr/NNNN-title.md`, following `template.md`. An accepted ADR is not edited; a change of direction is a new ADR that supersedes the old one.

## Consequences
- A little writing overhead per decision.
- Future readers, and AI assistants, get the context and the rejected alternatives.
