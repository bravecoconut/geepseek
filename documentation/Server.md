# Backend Execution and Inference Subsystem

The `app/server/` execution space manages the core inferential request lifecycle. It operates as the primary API ingress gateway, managing ephemeral state caching, parameterizing LLM proxy interactions, and orchestrating localized deterministic agents.

## Namespace: `app/server/`

### `server.py`
The primary WSGI/ASGI-compatible listener bound to loopback interface 5000.
- Implements strict CORS pre-flight assertions to isolate cross-origin resource sharing.
- **Gateway Endpoints**:
  - `/api/sessions`: Yields the serialized collection of active memory matrices.
  - `/api/load_conversation_on_session_id`: Rehydrates the prompt context window from the specified persistence shard.
  - `/chat` (POST): The primary computational node. Parses the inbound schema, instantiates the `search_agent` if the tool-use flag is high, injects the aggregated state into the transformer, and handles backpressure via token-by-token Server-Sent Events (SSE).
- Asynchronously schedules the session title generation heuristic upon new context initialization.

### `main_manager.py`
The Context State Machine mapping memory to disk.
- **`GenMan` Abstraction**: The base state manager. Enforces system instruction constraints (defining the execution parameters for `think` and `search` subroutines) and controls the tuple commit sequence to the embedded SQL engine.
- **`Man` Abstraction**: Inherits from `GenMan`, overriding initialization logic to perform bulk context rehydration directly from the SQLite cursors, rebuilding the conversational graph in-memory.

### `search_agent.py`
An autonomous deterministic actor bound to a localized retrieval-augmented generation (RAG) loop.
- Interfaces via an OpenAI-compatible function-calling JSON schema.
- Employs heuristic intent analysis to bypass static generation and branch into DOM execution strategies.
- Leverages functional definitions mapped in `tools.json` and executed within `search/search.py`.
- Aggregates external payloads, strips non-essential DOM nodes, and injects a heavily structured fact-block into the parent generation thread.

### Ancillary Modules
- `assets.py`: Extraneous state handlers for feedback arrays.
- `json/`: Schema registry, prominently housing the `tools.json` function mapping configurations.
- `search/`: The core DOM traversal and web request subroutines (`lookup_fact`, `web_search`).
- `utills/`: Shared execution logic and standardized telemetry (logging) output handlers.
