#!/usr/bin/env python3
"""Shared, serialized publication of the encrypted site by the hourly jobs."""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import subprocess
import sys
import tempfile
import time
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "site"
BUNDLE = REPO / "docs" / "site.enc.json"
LOCK = Path.home() / ".local/state/holy-grail/publish.lock"
CO_AUTHOR = "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        check=check, text=True, capture_output=True, timeout=180,
    )


def build(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO / "build_site.py"), *args],
        check=check, text=True, capture_output=True, timeout=180,
    )


def bundle_hash() -> str | None:
    return hashlib.sha256(BUNDLE.read_bytes()).hexdigest() if BUNDLE.exists() else None


def restore_remote_sources() -> None:
    """Replace exactly the old authenticated source set after a remote update."""
    with tempfile.TemporaryDirectory(prefix="site-restore-", dir=LOCK.parent) as temporary:
        root = Path(temporary)
        restored = root / "site"
        build("--restore", "--in", str(restored))
        previous = root / "previous"
        # The caller proved local sources matched the old bundle. Restoring to a
        # fresh directory also removes files deliberately removed upstream.
        if SOURCE.exists():
            SOURCE.rename(previous)
        try:
            restored.rename(SOURCE)
        except BaseException:
            if previous.exists():
                previous.rename(SOURCE)
            raise


@contextlib.contextmanager
def publication_session():
    """Hold one lock across pull, source update, encrypted build, commit, push."""
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a") as lock:
        deadline = time.monotonic() + 900
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise RuntimeError("publication lock stayed busy for 15 minutes")
                time.sleep(1)
        try:
            if git("status", "--porcelain").stdout.strip():
                raise RuntimeError("publisher skipped: repository has uncommitted changes")
            if git("branch", "--show-current").stdout.strip() != "main":
                raise RuntimeError("publisher requires the main branch")
            before = bundle_hash()
            source_matches = build("--check-source", check=False).returncode == 0
            # Inspect the fetched commit before advancing HEAD. Otherwise a
            # source conflict would disappear on the next scheduled run even
            # though the private edits had not been reconciled.
            git("fetch", "--quiet", "origin", "main")
            if git("merge-base", "--is-ancestor", "HEAD", "origin/main", check=False).returncode == 0:
                incoming = git("show", "origin/main:docs/site.enc.json").stdout.encode()
                remote_changed = hashlib.sha256(incoming).hexdigest() != before
                if remote_changed and not source_matches and SOURCE.exists():
                    raise RuntimeError(
                        "remote encrypted bundle changed while site/ has unpublished "
                        "edits; reconcile private sources before publishing"
                    )
            git("merge", "--ff-only", "--quiet", "origin/main")
            if bundle_hash() != before:
                restore_remote_sources()
            if not SOURCE.is_dir():
                build("--restore")
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def publish(message: str) -> bool:
    """Build and audit, then stage only generated gates and the ciphertext."""
    built = build()
    if built.stdout.strip():
        print(built.stdout.strip(), flush=True)
    build("--check-public")
    outputs = build("--list-outputs").stdout.splitlines()
    if not outputs or "docs/site.enc.json" not in outputs:
        raise RuntimeError("encrypted build did not return its output allowlist")
    for name in outputs:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or path.parts[0] != "docs":
            raise RuntimeError("encrypted build returned an unsafe output path")
        if name != "docs/site.enc.json" and name != "docs/.nojekyll" and path.suffix != ".html":
            raise RuntimeError("publisher output is neither a gate nor the encrypted bundle")
    git("add", "--", *outputs)
    staged = git("diff", "--cached", "--name-only").stdout.splitlines()
    if set(staged) - set(outputs):
        raise RuntimeError("refusing to commit staged files outside the encrypted build")
    committed = bool(staged)
    if committed:
        git("-c", "user.email=konstantin@ctspolicy.org", "-c", "user.name=Konstantin Pilz",
            "commit", "--quiet", "-m", message, "-m", CO_AUTHOR)
    # Retry a previous failed push even if the current input has not changed.
    git("push", "--quiet", "origin", "main")
    print("published encrypted update" if committed else "encrypted site unchanged", flush=True)
    return committed


def main() -> None:
    if sys.argv[1:] != ["regional"]:
        raise SystemExit("usage: publish_site.py regional")
    with publication_session():
        subprocess.run(
            [sys.executable, str(REPO / "scripts/sync_regional_compute.py")],
            check=True, cwd=REPO, timeout=180,
        )
        publish("Auto-sync regional compute data")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.SubprocessError) as error:
        print(f"publisher failed: {error}", file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr.strip(), file=sys.stderr)
        raise SystemExit(1)
