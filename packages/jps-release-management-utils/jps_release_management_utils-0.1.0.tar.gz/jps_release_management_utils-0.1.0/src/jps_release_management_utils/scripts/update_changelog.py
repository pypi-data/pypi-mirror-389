#!/usr/bin/env python3
"""
update_changelog.py

Generates or previews a CHANGELOG.md section for the current version
using git commit history. Captures only the first line (subject)
from each commit message.

Usage:
    python scripts/update_changelog.py <version> [--preview]
"""

import subprocess
import sys
from datetime import date
from pathlib import Path


# -------------------------------------------------------------
# Utility functions
# -------------------------------------------------------------
def run_git_command(args):
    """Execute a git command and return stdout as text."""
    result = subprocess.run(
        ["git", "--no-pager", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def get_repo_url():
    """Return the repository HTTPS URL from git config."""
    try:
        url = run_git_command(["config", "--get", "remote.origin.url"])
        if not url:
            return "(unknown repository)"
        # Convert SSH form (git@github.com:user/repo.git) → HTTPS
        if url.startswith("git@"):
            url = url.replace(":", "/").replace("git@", "https://")
        if url.endswith(".git"):
            url = url[:-4]
        return url
    except Exception:
        return "(unknown repository)"


def get_latest_tag():
    """Return the latest version tag matching v* (or None)."""
    try:
        tag = run_git_command(["describe", "--tags", "--abbrev=0", "--match", "v*"])
        return tag or None
    except subprocess.CalledProcessError:
        return None


def get_commits(prev_tag=None):
    """Retrieve commits, capturing only the first line (subject)."""
    fmt = "%h%x1f%ad%x1f%an%x1f%s%x1e"
    args = [
        "log",
        f"{prev_tag}..HEAD" if prev_tag else "HEAD",
        f"--pretty=format:{fmt}",
        "--date=short",
        "--no-color",
    ]
    output = run_git_command(args)
    entries = []
    for raw in output.strip().split("\x1e"):
        if not raw.strip():
            continue
        parts = raw.split("\x1f")
        if len(parts) < 4:
            continue
        short_hash, commit_date, author, subject = parts[:4]
        entries.append(
            {
                "hash": short_hash.strip(),
                "date": commit_date.strip(),
                "author": author.strip(),
                "subject": subject.strip(),
            }
        )
    # ✅ Display newest commits first for more intuitive changelog order
    return entries  # reversed output removed; newest first


# -------------------------------------------------------------
# Formatting functions
# -------------------------------------------------------------
def format_changelog_entries(entries, repo_url, color=False):
    """Format commit entries into Markdown or colorized terminal output."""
    lines = []
    for e in entries:
        commit_link = f"[({e['hash']})]({repo_url}/commit/{e['hash']})"
        if color:
            # Add ANSI colors for terminal preview only
            YELLOW = "\033[1;33m"
            GREEN = "\033[1;32m"
            CYAN = "\033[1;36m"
            RESET = "\033[0m"
            lines.append(
                f"- {YELLOW}[{e['date']}] {RESET}"
                f"{GREEN}{e['author']}{RESET} "
                f"{CYAN}{commit_link}{RESET}: {e['subject']}"
            )
        else:
            # Plain Markdown (no ANSI escapes)
            lines.append(f"- [{e['date']}] {e['author']} {commit_link}: {e['subject']}")
    return "\n".join(lines) + "\n"


def build_changelog_section(version, repo_url, preview=False):
    """Generate the full changelog text for a given version."""
    today = date.today().strftime("%Y-%m-%d")
    prev_tag = get_latest_tag()

    if preview:
        print("🧾 Previewing changelog entries since last tag...")
    else:
        print("🧾 Updating CHANGELOG.md...")

    header = f"## [{version}] - {today}\n- Released via automated Makefile workflow.\n\n"
    entries = get_commits(prev_tag)
    body = format_changelog_entries(entries, repo_url, color=preview)
    return header + body


def prepend_to_file(path: Path, text: str):
    """Prepend text to a file, preserving a top-level # Changelog heading."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("# Changelog\n\n" + text)
        return

    existing = path.read_text().splitlines()
    if existing and existing[0].startswith("# Changelog"):
        # Insert after the top-level header
        updated = [existing[0], ""] + text.strip().splitlines() + [""] + existing[1:]
        path.write_text("\n".join(updated))
    else:
        # Fallback if no header present
        path.write_text("# Changelog\n\n" + text + "\n" + "\n".join(existing))


# -------------------------------------------------------------
# Main
# -------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("❌ Missing version argument.")
        print("Usage: update_changelog.py <version> [--preview]")
        sys.exit(1)

    version = sys.argv[1]
    preview = "--preview" in sys.argv
    repo_url = get_repo_url()

    changelog_section = build_changelog_section(version, repo_url, preview=preview)

    if preview:
        print(changelog_section)
        print("✅ Above entries would be added to the next changelog section.")
    else:
        # ✅ Ensure docs/ directory exists before writing CHANGELOG.md
        docs_dir = Path("docs")
        docs_dir.mkdir(exist_ok=True)

        changelog_path = docs_dir / "CHANGELOG.md"
        prepend_to_file(changelog_path, changelog_section)
        print(f"✅ CHANGELOG updated at {changelog_path}")


if __name__ == "__main__":
    main()
