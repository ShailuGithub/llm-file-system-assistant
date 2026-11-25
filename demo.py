"""Scripted demo: runs the three example queries from the assignment."""
import os
import subprocess
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI

import llm_file_assistant as app

load_dotenv()
QUERIES = [
    "Read all resumes in the resumes folder and give a one-line summary of each",
    "Find resumes mentioning Python experience",
    "Create a summary file for resume_john_doe.pdf",
]


def intro():
    print("=== Project overview ===\n")
    print("Project files:")
    for name in ("fs_tools.py  (Part A: the 4 file tools)", "llm_file_assistant.py  (Part B: LLM + tool calling)",
                 "requirements.txt", "README.md", "test_fs_tools.py", "resumes/  (sample data)"):
        print("  -", name)
    time.sleep(5)
    print("\nTools exposed to the LLM (function calling):")
    for t in app.fs_tools.TOOL_SCHEMAS:
        print(f"  * {t['name']:<16} {t['description'][:80]}")
    time.sleep(7)
    print("\nSample resumes:")
    for f in app.fs_tools.list_files("resumes"):
        print(f"  {f['name']:<28} {f['size_bytes']:>7} bytes")
    print(f"\nModel: {app.MODEL}\n")
    time.sleep(7)
    print("Unit tests for the tools:")
    subprocess.run([sys.executable, "-m", "pytest", "-q", "test_fs_tools.py"])
    print()
    time.sleep(5)

def main():
    client = OpenAI(api_key=os.environ["GEMINI_API_KEY"], base_url=app.BASE_URL, timeout=60, max_retries=0)
    intro()
    print("=== LLM File Assistant demo (tool calling) ===\n")
    time.sleep(3)
    for q in QUERIES:
        print(f"you> {q}\n")
        time.sleep(4)
        print(app.ask(client, q))
        print("\n" + "-" * 70 + "\n")
        time.sleep(14)
    print("Files written by the assistant:")
    for f in app.fs_tools.list_files("summaries"):
        print(" ", f["path"], f"({f['size_bytes']} bytes)")
    time.sleep(4)
    for f in app.fs_tools.list_files("summaries"):
        if "john" in f["name"].lower():
            print(f"\n--- {f['path']} ---")
            print(app.fs_tools.read_file(f["path"]).get("content", ""))
    time.sleep(30)


if __name__ == "__main__":
    main()

