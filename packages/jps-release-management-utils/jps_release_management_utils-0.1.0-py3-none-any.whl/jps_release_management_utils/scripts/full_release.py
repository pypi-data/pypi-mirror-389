#!/usr/bin/env python3
"""
Full release orchestrator for jps-release-management-utils.

This script replaces the old Makefile-based release logic.
It performs all release management steps in one invocation:
    1. Validates repo cleanliness
    2. Bumps version (patch/minor/major)
    3. Updates CHANGELOG.md
    4. Commits changes, creates annotated tag
    5. Pushes tag to origin
    6. Displays final release summary with CI workflow link
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


# -----------------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------------
def run(cmd, cwd=None, capture=False, quiet=False, check=True):
    """Run shell command with pretty output and error handling."""
    display = " ".join(cmd)
    if not quiet:
        print(f"👉 {display}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        capture_output=capture,
    )
    if check and result.returncode != 0:
        print(f"❌ Command failed: {display}")
        if result.stderr:
            print(result.stderr.strip())
        sys.exit(result.returncode)
    return result


def read_version_file(repo_root):
    """Return current version from .version file."""
    version_file = repo_root / ".version"
    if not version_file.exists():
        print("❌ .version file missing.")
        sys.exit(1)
    return version_file.read_text().strip()


def find_repo_root(start: Path = Path(__file__).resolve()) -> Path:
    """Walk upward until .git or pyproject.toml is found."""
    for parent in [start, *start.parents]:
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
    print("❌ Unable to locate repository root.")
    sys.exit(1)


# -----------------------------------------------------------------------------
# Main release orchestration
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Perform a full software release workflow.")
    parser.add_argument(
        "--part",
        required=True,
        choices=["patch", "minor", "major"],
        help="Version part to bump.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the release process without making permanent changes.",
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Perform all steps locally but skip git push operations.",
    )

    args = parser.parse_args()
    repo_root = find_repo_root()

    # ✅ Determine actual script directory (inside src/.../scripts)
    script_dir = Path(__file__).resolve().parent
    release_script = script_dir / "release_project.py"
    changelog_script = script_dir / "update_changelog.py"

    print("🚀 Starting full release orchestration...\n")

    # -------------------------------------------------------------------------
    # 1️⃣ Verify repo cleanliness (reuse logic from release_project.py)
    # -------------------------------------------------------------------------
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        print("❌ Working directory not clean. Commit or stash changes before releasing.")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # 2️⃣ Perform version bump (dry-run or real)
    # -------------------------------------------------------------------------
    cmd = ["python3", str(release_script), f"--{args.part}"]
    if args.dry_run:
        cmd.append("--dry-run")
    run(cmd, cwd=repo_root)

    if args.dry_run:
        print("\n🧪 Dry-run complete. Skipping changelog and commit steps.\n")
        sys.exit(0)

    # -------------------------------------------------------------------------
    # 3️⃣ Read bumped version
    # -------------------------------------------------------------------------
    new_version = read_version_file(repo_root)
    print(f"\n🔢 New version detected: {new_version}")

    # -------------------------------------------------------------------------
    # 4️⃣ Update changelog
    # -------------------------------------------------------------------------
    print("🗒️  Updating CHANGELOG.md...")
    run(["python3", str(changelog_script), new_version], cwd=repo_root)

    # -------------------------------------------------------------------------
    # 5️⃣ Commit + tag
    # -------------------------------------------------------------------------
    print("\n📦 Committing and tagging release...")
    run(["git", "add", ".version", "docs/CHANGELOG.md", "pyproject.toml"], cwd=repo_root)

    # Try initial commit, capture possible markdownlint modification
    result = subprocess.run(
        ["git", "commit", "-m", f"Release v{new_version}"],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0 and "files were modified" in (result.stdout + result.stderr):
        print("⚙️  Detected markdownlint auto-fix — re-staging files and retrying commit...")
        subprocess.run(["git", "add", "docs/CHANGELOG.md"], cwd=repo_root, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Release v{new_version}"],
            cwd=repo_root,
            check=True,
        )
    elif result.returncode != 0:
        print(f"❌ Command failed: git commit\n{result.stdout}\n{result.stderr}")
        sys.exit(result.returncode)

    # -------------------------------------------------------------------------
    # 6️⃣ Push (optional)
    # -------------------------------------------------------------------------
    if args.no_push:
        print("🚫 Skipping push (local-only release).")
    else:
        print("\n🚀 Pushing commits and tags to origin...")
        run(["git", "push", "origin", "main"], cwd=repo_root)
        run(["git", "push", "origin", f"v{new_version}"], cwd=repo_root)

    # -------------------------------------------------------------------------
    # 7️⃣ Final summary
    # -------------------------------------------------------------------------
    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        capture_output=True,
        text=True,
    )
    remote_url = result.stdout.strip()

    org = None
    repo_name = None

    if remote_url:
        match = re.search(r"github\\.com[:/](?P<org>[^/]+)/(?P<repo>[^/.]+)", remote_url)
        if match:
            org = match.group("org")
            repo_name = match.group("repo")

    if not org:
        org = "unknown-org"
    if not repo_name:
        repo_name = Path(repo_root).name

    print("\n✅ Release workflow complete!")
    print(f"   Version: v{new_version}")
    print(
        f"   CI workflow: https://github.com/{org}/{repo_name}/actions/workflows/publish-to-pypi.yml\n"  # noqa: E501
    )


if __name__ == "__main__":
    main()
