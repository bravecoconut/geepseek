# Presentation Layer and State Hydration

The client subsystem acts as a lightweight presentation execution engine, decoupled from the computationally intensive backend to ensure deterministic DOM rendering and isolated fault tolerance.

## Namespace: `app/client/`

### `serv.py` (or `client.py`)
The primary WSGI View-Controller daemon, mapping network requests to template render cycles. Bound to the 5001 interface.

**Routing Matrix:**
- `/`: Absolute root; triggers a 302 redirect to the default initialization state.
- `/chat/`: Intermediate alias resolver, redirecting to the instantiation node `/chat/new`.
- `/chat/new`: Invokes the Jinja2 AST compiler against `chat.html`, injecting a null-state `session_id` to signal context reset.
- `/chat/<session_id>`: Compiles the view template with a populated UUID token, instructing the frontend asynchronous logic to request state rehydration from the backend infrastructure.

### `templates/`
Houses the declarative HTML DOM schemas, awaiting server-side compilation and parameter injection prior to client transmission.

### `static/`
The asset delivery volume. Serves statically compiled CSS object models, rasterized imagery, and the core asynchronous JavaScript bundles responsible for managing the bidirectional SSE streaming protocols and maintaining client-side interactivity state.
