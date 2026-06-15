# Persistence and State Serialization Topologies

GeepSeek relies on an embedded SQL-based state engine to enforce transactional consistency across its conversational memory matrix. The schema architecture is designed for rapid local I/O operations, residing within the `app/data/` volume.

## Volume: `app/data/`

### `database.db`
The primary entity-relationship namespace for granular conversational state vectors.
- Implements dynamic DDL executions, instantiating isolated B-tree table structures bound to unique session UUIDs (e.g., `S20260517030614927216`).
- Tuple structure per shard:
  - `id`: Auto-incrementing primary sequence index.
  - `role`: Actor designation (e.g., "user", "assistant", "system").
  - `content`: The raw text payload.
  - `thought`: Ephemeral neural-symbolic reasoning chains (utilized during `think` execution branching).
  - `source`: Serialized JSON arrays containing hypermedia references accessed during tool invocation.

### `session_info.db`
The metadata ledger tracking macro-level session lifecycle events.
- **Table: `info`**
  - `session_id`: Foreign key equivalent mapping to the dynamically generated DDL structures in `database.db`.
  - `session_name`: LLM-generated heuristic summary of the context namespace.
  - `date_created`: Initialization timestamp schema.
  - `date_last_commit`: Mutation timestamp reflecting the most recent tuple insertion.

### `chat_comment.db`
A secondary auxiliary datastore allocated for out-of-band telemetry and feedback aggregation nodes.

---

## Volume: `sql/`
This directory encapsulates the foundational query definitions.
- `chat_comment.sql`
- `session_info.sql`

These artifacts serve as the initial declarative schemas utilized during the application bootstrap sequence to ensure the presence of the necessary database shards before write operations commence.
