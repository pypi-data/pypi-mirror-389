#!/usr/bin/env python3
"""
release_project.py

Automates semantic version bumping, changelog update, tagging, and pushing to GitHub.
Supports dry-run mode and now allows simple flags like --minor, --patch, and --major.

Usage:
    python3 scripts/release_project.py --minor [--dry-run]
    python3 scripts/release_project.py --part minor [--dry-run]
"""

import argparse
import subprocess
import sys
import tomllib
from datetime import date
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> str:
    """Run a shell command and return its stdout text."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        sys.exit(result.returncode)
    return result.stdout.strip()


def is_dirty_repo() -> bool:
    """Check if the git working directory has uncommitted changes."""
    result = run(["git", "status", "--porcelain"], check=False)
    return bool(result)


def get_current_version() -> str:
    if Path(".version").exists():
        return Path(".version").read_text().strip()
    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        with pyproject.open("rb") as f:
            data = tomllib.load(f)
        version = data.get("project", {}).get("version")
        if version:
            return version
    print("❌ Unable to find current version in .version or pyproject.toml")
    sys.exit(1)


def bump_version(version: str, part: str) -> str:
    """Return the next semantic version string."""
    major, minor, patch = [int(x) for x in version.split(".")]
    if part == "major":
        major += 1
        minor = patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        print(f"❌ Unknown part: {part}")
        sys.exit(1)
    return f"{major}.{minor}.{patch}"


def tag_exists(tag: str) -> bool:
    """Check if a git tag already exists."""
    result = subprocess.run(["git", "rev-parse", tag], capture_output=True)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Automate software release management.")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--part", choices=["patch", "minor", "major"], help="Version part to bump")
    group.add_argument("--patch", action="store_true", help="Bump patch version (x.y.Z)")
    group.add_argument("--minor", action="store_true", help="Bump minor version (x.Y.0)")
    group.add_argument("--major", action="store_true", help="Bump major version (X.0.0)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate release without changes")
    args = parser.parse_args()

    # Derive part argument if shorthand flag used
    part = args.part or (
        "patch" if args.patch else "minor" if args.minor else "major" if args.major else None
    )
    if not part:
        print("❌ You must specify one of --part, --patch, --minor, or --major.")
        parser.print_help()
        sys.exit(2)

    if is_dirty_repo():
        print("❌ Working directory not clean. Commit or stash changes before releasing.")
        sys.exit(1)

    current_version = get_current_version()
    new_version = bump_version(current_version, part)
    today = date.today().isoformat()

    print(f"🔢 Bumping version: {current_version} → {new_version}")
    if args.dry_run:
        print("🧪 [DRY RUN] Skipping commit, tag, push, and changelog update.")
        sys.exit(0)

    if tag_exists(f"v{new_version}"):
        print(f"⚠️  Tag v{new_version} already exists — aborting release.")
        sys.exit(1)

    # Update .version
    Path(".version").write_text(new_version + "\n")

    # Commit, tag, and push
    run(["git", "add", ".version"])
    run(["git", "commit", "-m", f"Release v{new_version}"])
    run(
        [
            "git",
            "tag",
            "-a",
            f"v{new_version}",
            "-m",
            f"Release v{new_version}\n\nReleased on {today}",
        ]
    )
    run(["git", "push", "origin", "main"])
    run(["git", "push", "origin", f"v{new_version}"])

    print("✅ Release complete.")
    print(f"📦 Version: v{new_version}")
    print(f"📅 Date: {today}")
    print("🚀 Tag pushed to GitHub.")


if __name__ == "__main__":
    main()
