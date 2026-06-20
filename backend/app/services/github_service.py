import os
import shutil
import tempfile
from pathlib import Path
import git
from app.core.config import settings


def parse_github_url(url: str) -> tuple[str, str]:
    """Returns (owner, repo_name) from a GitHub URL."""
    url = url.rstrip("/").replace(".git", "")
    parts = url.split("/")
    if len(parts) < 2:
        raise ValueError("Invalid GitHub URL")
    return parts[-2], parts[-1]


def clone_repository(github_url: str, repo_id: str) -> str:
    """Clones repo to /tmp/repos/{repo_id}. Returns clone path."""
    clone_dir = f"/tmp/repos/{repo_id}"
    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir)
    os.makedirs(clone_dir, exist_ok=True)

    clone_url = github_url
    if settings.GITHUB_TOKEN:
        # Inject token for private repos / higher rate limits
        clone_url = github_url.replace("https://", f"https://{settings.GITHUB_TOKEN}@")

    git.Repo.clone_from(clone_url, clone_dir, depth=1)
    return clone_dir


def cleanup_clone(repo_id: str):
    clone_dir = f"/tmp/repos/{repo_id}"
    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir)


def walk_files(clone_dir: str) -> list[Path]:
    from app.services.chunking_service import should_skip
    root = Path(clone_dir)
    files = []
    for path in root.rglob("*"):
        if path.is_file():
            relative = path.relative_to(root)
            if not should_skip(str(relative)):
                try:
                    if path.stat().st_size > 500_000:  # skip files > 500KB
                        continue
                    files.append(path)
                except OSError:
                    continue
    return files
