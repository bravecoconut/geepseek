# Deterministic Tool Execution & LLM Binding Subsystem

This architectural document defines the integration methodology for coupling the parameterized DOM traversal functions (`app/search.py`) with the OpenAI JSON Schema compliance layer, enabling autonomous function execution.

---

## 1. Tool Closure Topologies

The scraping execution engine exposes 5 distinct operational closures through the `build_search_tools()` factory pattern:

1. **`lookup_fact`**: Optimized for temporal heuristic resolution. Executes a two-phase operation: aggregating initial duckduckgo snippets, followed by asynchronous multi-node DOM extraction of the top references.
2. **`web_search`**: Standardized breadth-first web extraction. Supports secondary NLP keyword filtering on the resultant text buffers.
3. **`search_sites`**: Targeted DOM scraping of explicit FQDN arrays, bypassing the intermediary search indexer.
4. **`list_page_sections`**: Executes a structural analysis of the DOM tree, returning an array of `<hx>` level heading nodes. Crucial for partitioning heavy text blobs to bypass maximum context window token limits.
5. **`fetch_sections`**: The synchronous counterpart to `list_page_sections`. Consumes the selected heading indices and extracts the specific nested text siblings.

---

## 2. JSON Schema Definitions

The function parameter constraints must be rigorously defined to ensure correct serialization by the inferential model. Below are the required JSON representations for the `tools` parameter block.

```python
OPENAI_SEARCH_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_fact",
            "description": (
                "Primary heuristic resolver for temporal entities (news, temporal metrics, live status). "
                "Aggregates search snippets and subsequently initiates parallel scraping of the topmost indices."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Explicit search payload. Must incorporate temporal anchors (dates) if contextually relevant."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Iteration bounds for the secondary scraping pass. Ceiling: 5. Default: 4.",
                        "default": 4
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Non-specific search index traversal and subsequent DOM scraping. Use lookup_fact for time-sensitive parameters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The lexical string to be resolved by the search indexer."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Scraping depth limit for resulting hyperlinks. Ceiling: 5. Default: 3.",
                        "default": 3
                    },
                    "key_words": {
                        "type": "string",
                        "description": "Comma-delimited lexical anchors utilized to filter extracted DOM node text arrays."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_sites",
            "description": "Direct node traversal over provided Fully Qualified Domain Names (FQDNs).",
            "parameters": {
                "type": "object",
                "properties": {
                    "sites": {
                        "type": "string",
                        "description": "Comma-delimited FQDNs strings."
                    },
                    "key_words": {
                        "type": "string",
                        "description": "Optional lexical anchors for strict filtering."
                    }
                },
                "required": ["sites"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_page_sections",
            "description": (
                "DOM tree analyzer. Returns document heading arrays for targeted extraction via fetch_sections."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search index payload (mutually exclusive with sites array)."
                    },
                    "sites": {
                        "type": "string",
                        "description": "Comma-delimited FQDN targets."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Target extraction limit for search indexing. Ceiling: 5. Default: 2.",
                        "default": 2
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_sections",
            "description": "Stateful execution routine. Extracts text nested beneath headings identified by list_page_sections.",
            "parameters": {
                "type": "object",
                "properties": {
                    "choosen_headings": {
                        "type": "string",
                        "description": "Comma-delimited string of heading identifiers strictly matching the prior analyzer output."
                    }
                },
                "required": ["choosen_headings"]
            }
        }
    }
]
```

---

## 3. Integration Pipeline Implementation

The following execution script demonstrates the control flow required to map the inference output back into local operational closures.

```python
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Ensure module namespace visibility
from app.search import build_search_tools

load_dotenv()

# 1. Instantiate REST client instance
client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")  # Redirection URL for proxy clusters
)

# 2. Allocate the local tool closures
# Returns the operational array: [lookup_fact, web_search, search_sites, list_page_sections, fetch_sections]
local_tools = build_search_tools()
tool_mapping = {func.__name__: func for func in local_tools}

def run_execution_loop(user_payload: str):
    # System Prompt: Defines behavioral constraints and execution paths
    system_instruction = (
        "You operate with active DOM traversal capacities.\n"
        "Execution Constraints:\n"
        "1. Prioritize lookup_fact for temporal data resolution (live stats, chronological events). Bypass static memory caching.\n"
        "2. lookup_fact executes multi-phase extraction (snippets -> DOM text).\n"
        "3. web_search handles standard queries; search_sites resolves explicit FQDNs; list_page_sections/fetch_sections mitigates token overflow on large DOMs.\n"
        "4. Strict adherence to source attribution and hypermedia referencing is mandatory."
    )

    message_stack = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_payload}
    ]

    print(f"Ingested Payload: '{user_payload}'\n")

    # Phase 1: Transmission to Inference Engine
    response = client.chat.completions.create(
        model="gpt-4o",  # Base proxy model
        messages=message_stack,
        tools=OPENAI_SEARCH_TOOLS,
        tool_choice="auto",
    )

    response_node = response.choices[0].message
    message_stack.append(response_node)

    # Phase 2: Function Call Resolution
    if response_node.tool_calls:
        print("--- Execution Branching: Tool Invocation Detected ---")
        for tool_call in response_node.tool_calls:
            target_function = tool_call.function.name
            target_arguments = json.loads(tool_call.function.arguments)

            print(f"Targeting Node: {target_function}")
            print(f"Parameters: {json.dumps(target_arguments, indent=2)}")

            # Resolve function pointer within local namespace
            mapped_function = tool_mapping.get(target_function)
            if mapped_function:
                try:
                    # Execute synchronous DOM traversal
                    execution_result = mapped_function(**target_arguments)
                except Exception as e:
                    execution_result = {"error": str(e)}
            else:
                execution_result = {"error": f"Function node '{target_function}' unresolvable."}

            # Telemetry verification block
            print(f"Extraction Cycle Complete. Emitted Keys: {list(execution_result.keys())}")
            if "instant_snippets" in execution_result and execution_result["instant_snippets"]:
                print(f"Primary Snippet Header: {execution_result['instant_snippets'][0].get('title')}")

            # Inject resultant payload into message matrix
            message_stack.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": target_function,
                "content": json.dumps(execution_result),
            })

        # Phase 3: Final Synthesis Generation
        print("\n--- Awaiting Synthesis Subroutine ---")
        synthesis_response = client.chat.completions.create(
            model="gpt-4o",
            messages=message_stack,
        )
        return synthesis_response.choices[0].message.content
    else:
        # Standard Generation Branch
        return response_node.content

if __name__ == "__main__":
    # Execution Test Case
    result_stream = run_execution_loop("Who secured the Super Bowl victory in 2026 and what was the concluding point differential?")
    print("\nInference Output Stream:")
    print(result_stream)
```

---

## 4. Operational Considerations & System Constraints

### Stateful Traversal Caching
The factory method `build_search_tools()` instantiates an isolated closure memory space (`ctx = {"search": None}`) to persist the operational state of the underlying `Search` class. This mechanism is critical for maintaining consistency between asynchronous calls to `list_page_sections` and `fetch_sections`.
To circumvent state pollution, ensure `build_search_tools()` is initialized **strictly per conversational UUID**. Global initialization will cause race conditions and cross-contamination of heading arrays between concurrent threads.

### Error Mitigation Tactics
* **Asynchronous Socket Timeouts**: The `trafilatura` extraction layer enforces a strict `DOWNLOAD_TIMEOUT` threshold of 5000ms, effectively terminating blocking requests from underperforming remote nodes.
* **Network Saturation Handling**: Upstream DDG query indexing operations are wrapped in an exponential backoff retry loop (maximum 2 passes) to mitigate intermittent rate-limiting phenomena.
* **FQDN Normalization Scripts**: Target URL schemas (e.g. `example.com`) missing TLS definitions are heuristically coerced via string prefixing to strictly enforce `https://` compliance pre-flight.
