# AI Agent Architecture Overview

This document describes the AI-oriented agent abstractions that orchestrate ingestion, retrieval, and operational tasks against the OpenLegislation data model.

## Goals

- Provide composable, testable components that encapsulate ingestion, retrieval, and mutation capabilities.
- Offer a high-level façade that application layers can call to interact with AI workflows without understanding low-level services.
- Prepare the codebase for future Retrieval Augmented Generation (RAG) or autonomous planning features.

## Components

### `AIDataContext`

Acts as the bridge between agents and the persisted `Document` entities. It centralizes repository access patterns so agents can share helper logic safely.

### `AIIngestionAgent`

Wraps the existing `IngestionService` to make targeted RSS or API pulls on-demand. This allows orchestrators to enrich the document store before running AI tasks.

### `AIRetrievalAgent`

Provides semantic retrieval methods (recent documents, keyword search, URL lookup) that can be consumed by downstream RAG pipelines.

### `AIOperationsAgent`

Handles document level mutations and analytics (source counts, metadata updates, stale document identification) so that AI copilots can manage the corpus.

### `AIAgentOrchestrator`

Coordinates the specialized agents and exposes a single entry point that controllers, schedulers, or conversational interfaces can call.

## Future Extensions

- Plug in vector database lookups alongside the keyword search to support hybrid retrieval.
- Add summarization and enrichment workflows that store AI-generated insights back into the `metadata` column.
- Surface the orchestrator through REST endpoints or messaging interfaces for interactive AI assistants.
