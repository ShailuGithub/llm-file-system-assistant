"""LLM file assistant: lets an LLM call the tools in fs_tools.py (function calling).

Uses Google Gemini through its OpenAI-compatible endpoint.

Usage:
    python llm_file_assistant.py                                   # interactive chat
    python llm_file_assistant.py "Find resumes mentioning Python"  # one-shot
"""
from __future__ import annotations

import json
import os
import sys
import time

from dotenv import load_dotenv

import fs_tools

load_dotenv()

MODEL = os.environ.get("LLM_MODEL", "gemini-flash-lite-latest")
BASE_URL = os.environ.get("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
MAX_TURNS = 12  # safety cap on tool-call rounds per question
SYSTEM_PROMPT = (
    "You are a file assistant for a recruiter. Resumes live in the 'resumes' folder. "
    "Use the provided tools to read, list, search and write files; never guess file "
    "contents. For questions about many resumes, list the folder first, then read or "
    "search each relevant file. Save summaries as .md files in the 'summaries' folder. "
    "Be concise and say which files you used."
)

# Convert the tool schemas to the OpenAI function-calling format.
TOOLS = [
    {"type": "function",
     "function": {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}}
    for t in fs_tools.TOOL_SCHEMAS
]


def run_tool(name: str, args: dict) -> str:
    """Execute a tool by name and return its JSON result as a string."""
    func = fs_tools.TOOL_FUNCTIONS.get(name)
    if func is None:
        return json.dumps({"success": False, "error": f"Unknown tool: {name}"})
    try:
        return json.dumps(func(**args), default=str)
    except TypeError as exc:  # bad arguments from the model
        return json.dumps({"success": False, "error": f"Bad arguments: {exc}"})


def _chat(client, messages, retries: int = 5):
    """Call the LLM, retrying on transient overload/rate-limit errors."""
    from openai import APIConnectionError, APIStatusError  # APITimeoutError subclasses APIConnectionError

    for attempt in range(retries):
        try:
            return client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        except (APIStatusError, APIConnectionError) as exc:
            status = getattr(exc, "status_code", None)
            transient = status in (429, 500, 503) or isinstance(exc, APIConnectionError)
            if not transient or attempt == retries - 1:
                raise
            print(f"  (LLM busy, retrying {attempt + 1}/{retries - 1}...)")
            time.sleep(2 ** attempt * 2)


def ask(client, question: str, history: list | None = None, verbose: bool = True) -> str:
    """Send a question, execute any requested tools, loop until a final answer."""
    messages = history if history is not None else [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": question})

    for _ in range(MAX_TURNS):
        response = _chat(client, messages)
        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            return msg.content or ""

        for call in msg.tool_calls:
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            if verbose:
                print(f"  [tool] {call.function.name}({json.dumps(args)})")
            output = run_tool(call.function.name, args)
            if verbose:
                print(f"         -> {output[:110]}{'...' if len(output) > 110 else ''}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": output})

    return "Stopped: too many tool-call rounds."


def main() -> None:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY")
    if not api_key:
        sys.exit("Set GEMINI_API_KEY in .env (see .env.example).")
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=BASE_URL, timeout=60, max_retries=0)
    if len(sys.argv) > 1:
        print(ask(client, " ".join(sys.argv[1:])))
        return

    print("File assistant ready. Type a request, or 'exit'.")
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    while True:
        try:
            q = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in {"exit", "quit", ""}:
            break
        print("\n" + ask(client, q, history))


if __name__ == "__main__":
    main()
