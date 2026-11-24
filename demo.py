"""Scripted demo: runs the three example queries from the assignment."""
import os
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


def main():
    client = OpenAI(api_key=os.environ["GEMINI_API_KEY"], base_url=app.BASE_URL, timeout=60, max_retries=0)
    print("=== LLM File Assistant demo (tool calling) ===\n")
    time.sleep(3)
    for q in QUERIES:
        print(f"you> {q}\n")
        time.sleep(2)
        print(app.ask(client, q))
        print("\n" + "-" * 70 + "\n")
        time.sleep(4)
    print("Files written by the assistant:")
    for f in app.fs_tools.list_files("summaries"):
        print(" ", f["path"], f"({f['size_bytes']} bytes)")
    time.sleep(5)


if __name__ == "__main__":
    main()
