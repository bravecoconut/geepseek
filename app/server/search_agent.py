import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import pytz
from datetime import datetime
from search.search import build_search_tools

now = datetime.now(pytz.timezone("Asia/Kolkata"))
load_dotenv()

with open("app/server/json/tools.json", "r") as file:
    OPENAI_SEARCH_TOOLS = json.load(file)

base_url = os.getenv("BASE_URL")
api_key = os.getenv("API_KEY")
model = os.getenv("MODEL")


# 1. Initialize OpenAI client
client = OpenAI(
    api_key=api_key, base_url=f"{base_url}/v1"  # Optional, if using custom endpoint
)

# 2. Build the actual local function callables
# Note: build_search_tools returns: [lookup_fact, web_search, search_sites, list_page_sections, fetch_sections]
local_tools = build_search_tools()
tool_mapping = {func.__name__: func for func in local_tools}


def search_agent(user_contents: str):
    # Standard System Instructions instructing the model when/how to search
    system_instruction = (
        f"Current date: {now.strftime('%A, %B %d, %Y')}. "
        f"Current time: {now.strftime('%I:%M %p')} IST.\n\n"
        "You are a search agent. Your output will be consumed by another AI model, not a human.\n"
        "Your only job is to rewrite a user question "
        "Your job is to fetch, extract, and structure raw facts — NOT to write a readable answer.\n\n"
        "## Output format (strict)\n"
        "Return a structured fact block like this:\n"
        "  FACT: <exact fact, number, name, score, date>\n"
        "  SOURCE: <full URL>\n"
        "  FETCHED: <date/time>\n"
        "  CONFIDENCE: high | medium | low\n\n"
        "  FACT: ...\n"
        "  SOURCE: ...\n"
        "  ...\n\n"
        "## Rules (part-A)\n"
        "1. Never summarize or explain — only extract facts.\n"
        "2. Never paraphrase numbers, scores, names, or dates — copy them exactly as found.\n"
        "3. If two sources conflict, emit both facts and flag: CONFLICT: yes.\n"
        "4. If no result was found, emit: FACT: NOT FOUND. SOURCE: none.\n"
        "5. Do not add opinions, caveats, or filler text — the downstream model handles that.\n"
        "6. Every fact must have a source URL — no orphan facts.\n\n"
        "## Rules (part-B)\n"
        "1. Identify every distinct piece of information the user wants.\n"
        "2. For each piece, write one explicit search query — include the current year, "
        "   sport/league/topic name, and any named entities explicitly.\n"
        "3. Resolve vague words: 'latest' → use the actual current year; "
        "   'now' → 'as of {now.strftime('%B %Y')}'; 'last match' → 'most recent match result'.\n"
        "4. If the question has multiple sub-questions, list each as a separate query.\n"
        "5. Output ONLY a numbered list of search queries. No explanation, no preamble.\n\n"
        "## Rules (part-C)\n"
        "1. Always call lookup_fact first for anything time-sensitive.\n"
        "2. Run a second search if the first result is ambiguous or older than 7 days.\n"
        "3. Use list_page_sections + fetch_sections for tables (points tables, standings).\n"
    )

    messages = [
        {"role": "system", "content": system_instruction},
    ]

    messages += user_contents

    # print(messages)

    print(f"User Question: \n{messages[-1]['content']}\n")

    # Step 1: Send initial request to model with tool schemas
    response = client.chat.completions.create(
        model=model,  # or your desired model
        messages=messages,
        tools=OPENAI_SEARCH_TOOLS,
        tool_choice="auto",
    )

    response_message = response.choices[0].message
    messages.append(response_message.model_dump(exclude_none=True))

    # Step 2: Check if the model wants to call a tool
    if response_message.tool_calls:
        print("--- model decided to call a tool ---")
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            print(f"tool to call: {function_name}")
            print(f"arguments: {json.dumps(function_args, indent=2)}")

            # Find matching local python function
            local_func = tool_mapping.get(function_name)
            if local_func:
                try:
                    # Execute local search tool
                    tool_result = local_func(**function_args)
                except Exception as e:
                    tool_result = {"error": str(e)}
            else:
                tool_result = {"error": f"Function '{function_name}' not found."}

            # Print a snippet of the search tool output
            print(f"tool output fetched! keys: {list(tool_result.keys())}")
            if "instant_snippets" in tool_result and tool_result["instant_snippets"]:
                print(
                    f"top Snippet title: {tool_result['instant_snippets'][0].get('title')}"
                )

            # Append the tool response to messages

            content = {
                "tool": function_name,
                "args": function_args,
                "fetched_at": now.strftime("%Y-%m-%d %H:%M IST"),
                "result": tool_result,
            }

            results = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps(content),
            }

            # print(results)

            messages.append(results)

        # Step 3: Get final model response with search data injected
        print("\n--- sending results from model")

        return results
    else:
        return "their is nothing to search in this query, reply by your Own."


# if __name__ == "__main__":
#     # Example 1: Current Event / Factual Search
#     ans = search_agent("Who is currently leading the IPL 2026 points table right now, and what was the result of the last match?")
#     print("\nModel Response:")
#     print(ans)
