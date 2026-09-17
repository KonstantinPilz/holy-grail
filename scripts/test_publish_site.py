#!/usr/bin/env python3
"""Exercise the publisher's Git boundaries with isolated local repositories."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import publish_site as publisher


class PublicationBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "checkout"
        self.remote = self.root / "origin.git"
        self.run_git("init", "--bare", "--initial-branch=main", str(self.remote))
        self.run_git("clone", str(self.remote), str(self.repo))
        self.run_git("-C", str(self.repo), "config", "user.name", "Test Publisher")
        self.run_git("-C", str(self.repo), "config", "user.email", "publisher@example.invalid")
        self.source = self.repo / "site"
        self.source.mkdir()
        (self.repo / "docs").mkdir()
        (self.repo / ".gitignore").write_text("site/\n")
        (self.repo / "docs/index.html").write_text("Unlock prompt")
        (self.repo / "docs/.nojekyll").write_text("")
        (self.source / "old.html").write_text("fixture-one")
        self.bundle = self.repo / "docs/site.enc.json"
        self.bundle.write_text(json.dumps({"old.html": "fixture-one"}))
        self.run_git("-C", str(self.repo), "add", "--", ".gitignore", "docs")
        self.run_git("-C", str(self.repo), "commit", "-m", "Initial test fixture")
        self.run_git("-C", str(self.repo), "push", "origin", "main")
        for key, value in {
            "REPO": self.repo, "SOURCE": self.source, "BUNDLE": self.bundle,
            "LOCK": self.root / "state/publish.lock",
        }.items():
            patch = mock.patch.object(publisher, key, value)
            patch.start()
            self.addCleanup(patch.stop)
        patch = mock.patch.object(publisher, "build", self.fixture_build)
        patch.start()
        self.addCleanup(patch.stop)

    def run_git(self, *args):
        return subprocess.run(
            ["git", *args], check=True, text=True, capture_output=True, timeout=15)

    def head(self, directory=None):
        return self.run_git("-C", str(directory or self.repo), "rev-parse", "HEAD").stdout.strip()

    def fixture_build(self, *args, check=True):
        """Stand in for independently tested encryption; exercise real Git I/O."""
        result = subprocess.CompletedProcess(args, 0, stdout="", stderr="")
        if "--check-source" in args:
            files = {str(path.relative_to(self.source)): path.read_text()
                     for path in self.source.rglob("*") if path.is_file()}
            result.returncode = 0 if files == json.loads(self.bundle.read_text()) else 1
        elif "--restore" in args:
            target = Path(args[args.index("--in") + 1]) if "--in" in args else self.source
            target.mkdir(parents=True, exist_ok=True)
            for name, content in json.loads(self.bundle.read_text()).items():
                (target / name).write_text(content)
        elif "--list-outputs" in args:
            result.stdout = "docs/site.enc.json\ndocs/index.html\ndocs/.nojekyll\n"
        return result

    def advance_remote(self):
        other = self.root / "other"
        self.run_git("clone", str(self.remote), str(other))
        (other / "docs/site.enc.json").write_text(json.dumps({"new.html": "fixture-two"}))
        self.run_git("-C", str(other), "add", "docs/site.enc.json")
        self.run_git("-C", str(other), "-c", "user.name=Test Publisher",
                     "-c", "user.email=publisher@example.invalid", "commit", "-m", "Remote fixture")
        self.run_git("-C", str(other), "push", "origin", "main")

    def test_staged_plaintext_prevents_session(self):
        self.run_git("-C", str(self.repo), "add", "--force", "site/old.html")
        before = self.head()
        with self.assertRaisesRegex(RuntimeError, "uncommitted changes"):
            with publisher.publication_session():
                self.fail("dirty checkout entered publication session")
        self.assertEqual(self.head(), before)

    def test_unexpected_staged_file_cannot_enter_commit(self):
        before = self.head()
        with publisher.publication_session():
            (self.repo / "unexpected.txt").write_text("private fixture")
            self.run_git("-C", str(self.repo), "add", "unexpected.txt")
            with self.assertRaisesRegex(RuntimeError, "outside the encrypted build"):
                publisher.publish("Must not commit")
        self.assertEqual(self.head(), before)

    def test_remote_bundle_restores_exact_source_set(self):
        self.advance_remote()
        with publisher.publication_session():
            self.assertFalse((self.source / "old.html").exists())
            self.assertEqual((self.source / "new.html").read_text(), "fixture-two")

    def test_remote_change_preserves_unpublished_sources(self):
        (self.source / "old.html").write_text("local edit")
        self.advance_remote()
        before = self.head()
        for _ in range(2):
            with self.assertRaisesRegex(RuntimeError, "unpublished edits"):
                with publisher.publication_session():
                    self.fail("conflict entered publication session")
        self.assertEqual(self.head(), before)
        self.assertEqual((self.source / "old.html").read_text(), "local edit")
        self.assertFalse((self.source / "new.html").exists())

    def test_no_change_retries_unpushed_commit_without_new_commit(self):
        (self.repo / "docs/index.html").write_text("Updated unlock prompt")
        self.run_git("-C", str(self.repo), "add", "docs/index.html")
        self.run_git("-C", str(self.repo), "commit", "-m", "Unpushed fixture")
        before = self.head()
        self.assertNotEqual(self.head(self.remote), before)
        with publisher.publication_session():
            self.assertFalse(publisher.publish("No change"))
        self.assertEqual(self.head(), before)
        self.assertEqual(self.head(self.remote), before)

    def test_changed_gate_commit_has_required_trailer(self):
        with publisher.publication_session():
            (self.repo / "docs/index.html").write_text("Updated unlock prompt")
            self.assertTrue(publisher.publish("Updated encrypted gate"))
        message = self.run_git("-C", str(self.repo), "log", "-1", "--format=%B").stdout
        self.assertIn(publisher.CO_AUTHOR, message)
        files = self.run_git("-C", str(self.repo), "show", "--format=", "--name-only").stdout.splitlines()
        self.assertEqual(files, ["docs/index.html"])


if __name__ == "__main__":
    unittest.main()
