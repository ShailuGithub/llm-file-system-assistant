# LLM-Powered File System Assistant

A small Python project where an LLM uses **tool calling** to read, list, search and write
resume files. Ask in plain English; the model decides which tool to call.

## Structure

| File | Purpose |
|---|---|
| `fs_tools.py` | Part A: `read_file`, `list_files`, `write_file`, `search_in_file` + JSON tool schemas |
| `llm_file_assistant.py` | Part B: agent loop that connects the tools to a Gemini LLM |
| `make_sample_data.py` | Generates 8 fictional resumes (PDF / DOCX / TXT) in `resumes/` |
| `test_fs_tools.py` | Unit tests for the tools |

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # then put your GEMINI_API_KEY in .env (free key: aistudio.google.com)
python make_sample_data.py      # optional: regenerate sample resumes
pytest                          # run the tests
```

## Usage

```bash
python llm_file_assistant.py                                   # interactive chat
python llm_file_assistant.py "Read all resumes in the resumes folder"
python llm_file_assistant.py "Find resumes mentioning Python experience"
python llm_file_assistant.py "Create a summary file for resume_john_doe.pdf"
```

Tool calls are printed as `[tool] name(args)` so you can watch the model work.
Summaries are saved to `summaries/`.

## Tools

- `read_file(filepath)` -> `{success, content, truncated, metadata}`; supports PDF, TXT, MD, DOCX.
- `list_files(directory, extension=None)` -> list of `{name, path, size_bytes, modified}`.
- `write_file(filepath, content)` -> `{success, path, bytes_written}`; creates folders; only .txt/.md/.json/.csv.
- `search_in_file(filepath, keyword)` -> case-insensitive matches with line number and surrounding text.

## Design notes

- **Never raises:** tools return `{"success": false, "error": ...}` so the LLM can read the failure and recover.
- **Sandboxed:** every path is resolved inside the project folder; `../` escapes are rejected.
- **Safe writes:** only text-like extensions can be written.
- **Bounded loop:** at most 12 tool-call rounds per question; content is truncated at 20k characters.
- Model is configurable with `LLM_MODEL` (default `gemini-flash-lite-latest`, via Gemini's OpenAI-compatible endpoint).

All resumes in `resumes/` are fictional.

## Demo

`python demo.py` runs the three example queries end to end. `record_demo.ps1` opens the demo in its own
window and records it to `demo/demo.mp4` (uses the bundled ffmpeg from `imageio-ffmpeg`).
