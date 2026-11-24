"""File system tools for the LLM file assistant.

Every tool returns plain dicts/lists (JSON-serialisable) and never raises:
errors are reported as ``{"success": False, "error": "..."}`` so an LLM can
read the failure and react to it.

All paths are resolved inside ``BASE_DIR`` (the project folder by default,
override with the ``FS_BASE_DIR`` environment variable). Anything that
escapes it (``../``, absolute paths elsewhere) is rejected.
"""
from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(os.environ.get("FS_BASE_DIR", Path(__file__).parent)).resolve()
SUPPORTED_READ = {".txt", ".md", ".pdf", ".docx"}
MAX_CONTENT_CHARS = 20000  # keep tool results small enough for an LLM context


class PathError(ValueError):
    """Raised when a path is outside the sandbox."""


def _safe_path(p: str) -> Path:
    """Resolve ``p`` relative to BASE_DIR and refuse to leave it."""
    path = (BASE_DIR / p).resolve()
    if path != BASE_DIR and BASE_DIR not in path.parents:
        raise PathError(f"Path '{p}' is outside the allowed directory")
    return path


def _meta(path: Path) -> dict:
    st = path.stat()
    return {
        "name": path.name,
        "path": str(path.relative_to(BASE_DIR)).replace("\\", "/"),
        "size_bytes": st.st_size,
        "modified": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
    }


def _extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".txt", ".md"):
        return path.read_text(encoding="utf-8", errors="replace")
    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    if ext == ".docx":
        from docx import Document

        doc = Document(str(path))
        parts = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                parts.append(" | ".join(c.text for c in row.cells))
        return "\n".join(parts)
    raise ValueError(f"Unsupported file type '{ext}'. Supported: {sorted(SUPPORTED_READ)}")


def read_file(filepath: str) -> dict:
    """Read a PDF, TXT, MD or DOCX file and return its text plus metadata."""
    try:
        path = _safe_path(filepath)
        if not path.is_file():
            return {"success": False, "error": f"File not found: {filepath}"}
        text = _extract_text(path)
        truncated = len(text) > MAX_CONTENT_CHARS
        return {
            "success": True,
            "content": text[:MAX_CONTENT_CHARS],
            "truncated": truncated,
            "metadata": {**_meta(path), "type": path.suffix.lower().lstrip("."),
                         "char_count": len(text), "word_count": len(text.split())},
        }
    except Exception as exc:  # noqa: BLE001 - tools must never raise
        return {"success": False, "error": f"{type(exc).__name__}: {exc}"}


def list_files(directory: str = ".", extension: str | None = None) -> list | dict:
    """List files in a directory, optionally filtered by extension (e.g. '.pdf').

    Returns a list of {name, path, size_bytes, modified}, or an error dict.
    """
    try:
        path = _safe_path(directory)
        if not path.is_dir():
            return {"success": False, "error": f"Directory not found: {directory}"}
        ext = None
        if extension:
            ext = extension.lower() if extension.startswith(".") else f".{extension.lower()}"
        files = [
            _meta(f)
            for f in sorted(path.iterdir())
            if f.is_file() and (ext is None or f.suffix.lower() == ext)
        ]
        return files
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": f"{type(exc).__name__}: {exc}"}


def write_file(filepath: str, content: str) -> dict:
    """Write text to a file, creating parent directories if needed."""
    try:
        path = _safe_path(filepath)
        if path.suffix.lower() not in {".txt", ".md", ".json", ".csv"}:
            return {"success": False,
                    "error": "Only .txt, .md, .json and .csv files can be written"}
        existed = path.exists()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"success": True, "path": str(path.relative_to(BASE_DIR)).replace("\\", "/"),
                "bytes_written": len(content.encode("utf-8")), "overwritten": existed}
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": f"{type(exc).__name__}: {exc}"}


def search_in_file(filepath: str, keyword: str, context_chars: int = 60) -> dict:
    """Case-insensitive keyword search; each match includes surrounding text."""
    try:
        if not keyword:
            return {"success": False, "error": "keyword must not be empty"}
        path = _safe_path(filepath)
        if not path.is_file():
            return {"success": False, "error": f"File not found: {filepath}"}
        text = _extract_text(path)
        matches = []
        for m in re.finditer(re.escape(keyword), text, flags=re.IGNORECASE):
            start, end = max(0, m.start() - context_chars), min(len(text), m.end() + context_chars)
            line_no = text.count("\n", 0, m.start()) + 1
            matches.append({
                "line": line_no,
                "match": m.group(0),
                "context": text[start:end].replace("\n", " ").strip(),
            })
        return {"success": True, "file": str(path.relative_to(BASE_DIR)).replace("\\", "/"),
                "keyword": keyword, "match_count": len(matches), "matches": matches[:20]}
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": f"{type(exc).__name__}: {exc}"}


# JSON schemas handed to the LLM (converted to OpenAI function format).
TOOL_SCHEMAS = [
    {
        "name": "read_file",
        "description": "Read a resume/document (PDF, TXT, MD, DOCX) and return its text and metadata.",
        "input_schema": {"type": "object", "properties": {
            "filepath": {"type": "string", "description": "Path relative to the project, e.g. resumes/john_doe.pdf"}},
            "required": ["filepath"]},
    },
    {
        "name": "list_files",
        "description": "List files in a directory with name, size and modified date. Optionally filter by extension.",
        "input_schema": {"type": "object", "properties": {
            "directory": {"type": "string", "description": "Directory path, e.g. resumes"},
            "extension": {"type": "string", "description": "Optional extension filter, e.g. .pdf"}},
            "required": ["directory"]},
    },
    {
        "name": "write_file",
        "description": "Write text content to a .txt/.md/.json/.csv file, creating folders if needed.",
        "input_schema": {"type": "object", "properties": {
            "filepath": {"type": "string"}, "content": {"type": "string"}},
            "required": ["filepath", "content"]},
    },
    {
        "name": "search_in_file",
        "description": "Case-insensitive keyword search in a file. Returns matches with surrounding context.",
        "input_schema": {"type": "object", "properties": {
            "filepath": {"type": "string"}, "keyword": {"type": "string"}},
            "required": ["filepath", "keyword"]},
    },
]

TOOL_FUNCTIONS = {
    "read_file": read_file,
    "list_files": list_files,
    "write_file": write_file,
    "search_in_file": search_in_file,
}
