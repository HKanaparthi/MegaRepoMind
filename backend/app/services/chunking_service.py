import re
from dataclasses import dataclass
from app.core.config import settings

CODE_EXTENSIONS = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".jsx": "javascript", ".tsx": "typescript", ".java": "java",
    ".go": "go", ".rs": "rust", ".cpp": "cpp", ".c": "c",
    ".cs": "csharp", ".rb": "ruby", ".php": "php", ".swift": "swift",
    ".kt": "kotlin", ".scala": "scala", ".sh": "bash", ".sql": "sql",
    ".html": "html", ".css": "css", ".json": "json", ".yaml": "yaml",
    ".yml": "yaml", ".md": "markdown", ".toml": "toml", ".xml": "xml",
}

SKIP_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff",
                   ".woff2", ".ttf", ".eot", ".mp4", ".mp3", ".pdf", ".zip",
                   ".tar", ".gz", ".lock", ".pyc"}

SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", "env",
             "dist", "build", ".next", "coverage", ".pytest_cache"}


@dataclass
class TextChunk:
    content: str
    start_line: int
    end_line: int


def get_language(file_path: str) -> str:
    from pathlib import Path
    ext = Path(file_path).suffix.lower()
    return CODE_EXTENSIONS.get(ext, "text")


def should_skip(file_path: str) -> bool:
    from pathlib import Path
    path = Path(file_path)
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return True
    return any(part in SKIP_DIRS for part in path.parts)


def chunk_code(content: str, language: str) -> list[TextChunk]:
    lines = content.splitlines()
    if not lines:
        return []

    # For Python: split at top-level def/class
    if language == "python":
        return _split_at_definitions(lines, r"^(def |class |async def )")

    # For JS/TS: split at function/class/export declarations
    if language in ("javascript", "typescript"):
        return _split_at_definitions(lines, r"^(export |function |class |const \w+ = (?:async )?(?:\(|function))")

    # Everything else: line-based with overlap
    return _line_chunks(lines)


def _split_at_definitions(lines: list[str], pattern: str) -> list[TextChunk]:
    splits = [0]
    for i, line in enumerate(lines):
        if i > 0 and re.match(pattern, line):
            splits.append(i)
    splits.append(len(lines))

    chunks = []
    max_lines = settings.MAX_CHUNK_SIZE // 4  # rough chars-to-lines ratio

    for start, end in zip(splits, splits[1:]):
        block_lines = lines[start:end]
        if len(block_lines) <= max_lines:
            text = "\n".join(block_lines).strip()
            if text:
                chunks.append(TextChunk(text, start + 1, end))
        else:
            # Block too large — split into sub-chunks
            sub = _line_chunks(block_lines, base_line=start)
            chunks.extend(sub)
    return chunks


def _line_chunks(lines: list[str], base_line: int = 0) -> list[TextChunk]:
    max_lines = settings.MAX_CHUNK_SIZE // 4
    overlap = settings.CHUNK_OVERLAP // 4
    chunks = []
    i = 0
    while i < len(lines):
        end = min(i + max_lines, len(lines))
        text = "\n".join(lines[i:end]).strip()
        if text:
            chunks.append(TextChunk(text, base_line + i + 1, base_line + end))
        i = end - overlap if end < len(lines) else end
    return chunks
