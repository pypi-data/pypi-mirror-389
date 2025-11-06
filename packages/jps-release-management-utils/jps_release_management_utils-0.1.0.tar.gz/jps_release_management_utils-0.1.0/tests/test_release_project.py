#!/usr/bin/env python3
import subprocess

import pytest


@pytest.fixture
def repo_with_version(tmp_path):
    """Create a temp repo with .version file for release testing."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Jaideep Sundaram"], cwd=repo_dir)
    subprocess.run(["git", "config", "user.email", "jai.python3@gmail.com"], cwd=repo_dir)

    (repo_dir / ".version").write_text("1.0.0\n")
    (repo_dir / "README.md").write_text("# Dummy\n")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_dir, check=True)
    subprocess.run(["git", "tag", "v1.0.0"], cwd=repo_dir, check=True)

    return repo_dir


def test_release_dry_run(repo_with_version):
    """Run release_project.py in dry-run mode and confirm output."""
    # The repo fixture likely did this:
    # - git init
    # - create .version and README.md
    # - add and commit
    # We'll just add a fake remote so git push won't fail.
    subprocess.run(
        ["git", "remote", "add", "origin", repo_with_version.as_uri()],
        cwd=repo_with_version,
        check=True,
    )

    result = subprocess.run(
        [
            "python3",
            "-m",
            "jps_release_management_utils.scripts.release_project",
            "--minor",
            "--dry-run",
        ],
        cwd=repo_with_version,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "DRY RUN" in result.stdout or "would bump" in result.stdout.lower()


def test_release_blocks_dirty_repo(repo_with_version):
    """Simulate uncommitted change and verify release aborts."""
    dirty_file = repo_with_version / "temp.txt"
    dirty_file.write_text("Uncommitted content\n")

    result = subprocess.run(
        ["python3", "-m", "jps_release_management_utils.scripts.release_project", "--minor"],
        cwd=repo_with_version,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "Working directory not clean" in result.stdout or result.stderr
