# Architectural Topography

GeepSeek enforces a bipartite decoupled architecture contained within the primary `app/` execution namespace. The infrastructure strictly isolates the synchronous view-rendering logic from the high-latency inferential backend, supported by embedded relational state engines.

## Top-Level Namespace Segregation
- `app/client/`: The lightweight WSGI presentation layer. It consumes DOM templates and handles the asynchronous propagation of user events to the downstream API gateway.
- `app/server/`: The core inference engine and API ingress controller. Responsible for managing the retrieval-augmented generation (RAG) pipeline, coordinating autonomous agent tool closures, and handling non-blocking streaming data protocols.
- `app/data/`: The localized persistence shards (`database.db`, `session_info.db`, `chat_comment.db`) utilizing B-tree structures to maintain transactional conversational memory.
- `sql/`: DDL schemas and raw query definitions dictating table instantiation rules.
- `logs/`: High-fidelity telemetry outputs for the execution sub-processes.
- `venv/`: The isolated virtual environment mapping dependency boundaries.

## Request Lifecycle and Data Flow
1. The DOM fires state events routed to the `app/client/` WSGI daemon.
2. The view-controller dispatches authenticated HTTP/1.1 requests to the `app/server/` endpoints.
3. Upon parsing the payload, the backend determines execution branch logic. If external data heuristics are flagged, the `search_agent.py` closure initiates a parallel DOM scraping subroutine to aggregate deterministic context.
4. The aggregated payload is serialized and injected into the transformer context window. The proxy forwards the generation request, and the engine multiplexes the returning byte-stream as Server-Sent Events (SSE).
5. Post-generation, the memory manager commits the resulting state vectors into the localized SQLite shards via standard ACID operations.
