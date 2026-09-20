#!/usr/bin/env python3
"""Encrypt the private site/ tree for GitHub Pages; never publish its sources.

The AES-GCM / PBKDF2 mechanism follows ../x-drafter/build.py. Passwords are
read from a local file, never command-line arguments or generated artifacts.
"""
from __future__ import annotations

import argparse
import base64
import fcntl
import hashlib
import json
import mimetypes
import os
from pathlib import Path, PurePosixPath
import sys
import tempfile

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

HERE = Path(__file__).resolve().parent
ITERATIONS = 310_000
FORMAT = "holy-grail-site-v1"
BUNDLE = "site.enc.json"
GATE_MARKER = "<!-- holy-grail encrypted gate v1 -->"
PASSWORD_FILE = Path.home() / ".config/us-ai-compute-labs.pw"


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def unb64(data: str) -> bytes:
    return base64.b64decode(data, validate=True)


def password_from(path: Path) -> str:
    password = path.expanduser().read_text(encoding="utf-8").strip()
    if not password:
        raise ValueError("Password file is empty; refusing to build")
    return password


def key_for(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS, 32)


def encode_payload(files: dict) -> bytes:
    return json.dumps({"format": FORMAT, "files": files}, ensure_ascii=False,
                      sort_keys=True, separators=(",", ":")).encode("utf-8")


def collect(src: Path) -> bytes:
    if not src.is_dir() or not (src / "index.html").is_file():
        raise ValueError("Private source directory/index.html is missing; refusing to overwrite the published bundle")
    files = {}
    for path in sorted(src.rglob("*")):
        if path.is_symlink():
            raise ValueError("Symlinks are not permitted in the private source tree")
        if not path.is_file():
            continue
        relative = path.relative_to(src).as_posix()
        if any(p.startswith(".") for p in PurePosixPath(relative).parts):
            raise ValueError("Hidden files are not permitted in the private source tree")
        mime = mimetypes.guess_type(relative)[0] or "application/octet-stream"
        if relative.endswith(".js"):
            mime = "text/javascript"
        files[relative] = {"type": mime, "data": b64(path.read_bytes())}
    if "compute-over-time.html" not in files:
        raise ValueError("Private compute-over-time.html is missing; refusing an incomplete build")
    return encode_payload(files)


def encrypt(plaintext: bytes, password: str) -> bytes:
    salt, iv = os.urandom(16), os.urandom(12)
    ciphertext = AESGCM(key_for(password, salt)).encrypt(iv, plaintext, None)
    envelope = {"format": FORMAT, "iterations": ITERATIONS, "salt": b64(salt),
                "iv": b64(iv), "ciphertext": b64(ciphertext)}
    return (json.dumps(envelope, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def decrypt(encrypted: bytes, password: str) -> bytes:
    envelope = json.loads(encrypted)
    if envelope.get("format") != FORMAT or envelope.get("iterations") != ITERATIONS:
        raise ValueError("Unsupported encrypted bundle format")
    salt, iv = unb64(envelope["salt"]), unb64(envelope["iv"])
    if len(salt) != 16 or len(iv) != 12:
        raise ValueError("Invalid encryption parameters")
    return AESGCM(key_for(password, salt)).decrypt(iv, unb64(envelope["ciphertext"]), None)


def payload_files(plaintext: bytes) -> dict:
    payload = json.loads(plaintext)
    if payload.get("format") != FORMAT or not isinstance(payload.get("files"), dict):
        raise ValueError("Invalid decrypted bundle")
    files = payload["files"]
    if "index.html" not in files or "compute-over-time.html" not in files:
        raise ValueError("Encrypted bundle is missing required pages")
    for name, item in files.items():
        path = PurePosixPath(name)
        if path.is_absolute() or any(p in ("", ".", "..") or p.startswith(".") for p in path.parts):
            raise ValueError("Invalid path in encrypted bundle")
        if path.as_posix() != name or "\\" in name:
            raise ValueError("Invalid path in encrypted bundle")
        unb64(item["data"])
    return files


def atomic_write(path: Path, data: bytes, mode: int = 0o644) -> bool:
    if path.is_file() and path.read_bytes() == data:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".sitegate-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp, mode)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return True


def output_names(files: dict) -> list[str]:
    return sorted([BUNDLE, ".nojekyll"] + [name for name in files if name.endswith(".html")])


def gate_pages(files: dict, encrypted: bytes) -> dict[str, bytes]:
    template = (HERE / "gate_template.html").read_text(encoding="utf-8")
    digest = hashlib.sha256(encrypted).hexdigest()[:16]
    pages = {}
    for name in files:
        if not name.endswith(".html"):
            continue
        depth = len(PurePosixPath(name).parts) - 1
        root = "../" * depth or "./"
        page = template
        for token, value in (("{{ENTRY_JSON}}", json.dumps(name)),
                             ("{{ROOT_JSON}}", json.dumps(root)),
                             ("{{BUNDLE_JSON}}", json.dumps(root + BUNDLE + "?v=" + digest))):
            if token not in page:
                raise ValueError("Gate template is missing a required placeholder")
            page = page.replace(token, value)
        if "{{" in page or GATE_MARKER not in page:
            raise ValueError("Invalid gate template")
        pages[name] = page.encode("utf-8")
    return pages


def audit(out: Path, files: dict, pages: dict | None = None) -> None:
    allowed = set(output_names(files))
    for path in out.rglob("*"):
        if path.is_symlink():
            raise ValueError("Symlinks are not permitted in the published directory")
        if not path.is_file():
            continue
        name = path.relative_to(out).as_posix()
        if name.startswith("logos/") and name in files and path.suffix.lower() in {".svg", ".png", ".webp", ".jpg", ".jpeg", ".ico"}:
            if path.read_bytes() != unb64(files[name]["data"]):
                raise ValueError("Published logo differs from its bundled source")
            continue
        if name not in allowed:
            raise ValueError(f"Unexpected published file: {name}; move it to site/ before building")
        if pages is not None and name in pages and path.read_bytes() != pages[name]:
            raise ValueError(f"Published HTML is not the generated gate: {name}")
    if pages is not None:
        for name in allowed:
            if not (out / name).is_file():
                raise ValueError(f"Missing published output: {name}")


def restore(src: Path, files: dict, force: bool) -> int:
    # Check every destination before writing any source bytes.
    for name, item in files.items():
        path = src / name
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
            raise ValueError("Refusing to restore through a symlink")
        if path.exists() and (not path.is_file() or (not force and path.read_bytes() != unb64(item["data"]))):
            raise ValueError("Private source differs from bundle; refusing to overwrite (use --force only after preserving edits)")
    changed = sum(atomic_write(src / name, unb64(item["data"]), 0o600) for name, item in files.items())
    print(f"Restored {len(files)} private source files ({changed} changed)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="src", type=Path, default=HERE / "site")
    parser.add_argument("--out", type=Path, default=HERE / "docs")
    parser.add_argument("--password-file", type=Path, default=PASSWORD_FILE)
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("--restore", action="store_true", help="Restore private source bytes from the authenticated bundle")
    operation.add_argument("--check-source", action="store_true", help="Fail if private sources differ from the authenticated bundle")
    operation.add_argument("--check-public", action="store_true", help="Authenticate and audit every published output")
    operation.add_argument("--list-outputs", action="store_true", help="Print generated output paths, relative to the repository")
    parser.add_argument("--force", action="store_true", help="Allow --restore to overwrite differing existing sources")
    args = parser.parse_args()
    if args.force and not args.restore:
        parser.error("--force requires --restore")
    src, out = args.src.resolve(), args.out.resolve()
    if src == out or src in out.parents or out in src.parents:
        raise ValueError("Private source and public output must be separate directories")
    lock_dir = Path.home() / ".local/state/holy-grail"
    lock_dir.mkdir(parents=True, exist_ok=True)
    with (lock_dir / "build.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        password = password_from(args.password_file)
        bundle_path = out / BUNDLE
        previous = bundle_path.read_bytes() if bundle_path.is_file() else None
        if args.restore or args.check_source or args.check_public or args.list_outputs:
            if previous is None:
                raise ValueError("Published encrypted bundle is missing")
            plain = decrypt(previous, password)
            files = payload_files(plain)
            if args.restore:
                return restore(src, files, args.force)
            if args.check_source:
                if collect(src) != plain:
                    raise ValueError("Private sources differ from the authenticated published bundle")
                print("Private sources match the authenticated published bundle")
            elif args.list_outputs:
                for name in output_names(files):
                    path = out / name
                    print(path.relative_to(HERE) if path.is_relative_to(HERE) else path)
            else:
                audit(out, files, gate_pages(files, previous))
                print("Public output audit passed: only gates, ciphertext, and approved logos")
            return 0
        plain = collect(src)
        files = payload_files(plain)
        audit(out, files)
        # Authenticate old data; corruption/wrong password stops the publisher.
        # A partial source tree must never silently discard published content.
        previous_plain = decrypt(previous, password) if previous is not None else None
        if previous_plain is not None and set(payload_files(previous_plain)) - set(files):
            raise ValueError("Private source files are missing from the existing bundle; restore them before building")
        # Random salt/nonce are reused ONLY by preserving an identical envelope.
        encrypted = previous if previous_plain == plain else encrypt(plain, password)
        pages = gate_pages(files, encrypted)
        changed = atomic_write(bundle_path, encrypted)
        for name, data in pages.items():
            changed = atomic_write(out / name, data) or changed
        changed = atomic_write(out / ".nojekyll", b"") or changed
        audit(out, files, pages)
        print(f"Encrypted site {'updated' if changed else 'unchanged'}: {len(files)} files, {len(pages)} gates; AES-256-GCM / PBKDF2-SHA256 {ITERATIONS:,}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        # Do not emit decrypted payloads or password values on any failure.
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
