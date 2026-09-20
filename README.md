# Holy Grail

[Open the site](https://konstantinpilz.github.io/holy-grail/). Every page and its data are encrypted before publication, including the standalone compute-over-time page and embedded views. The browser shows an unlock prompt, then decrypts the bundle with the existing password. The gate keeps `noindex, nofollow` and remembers the password in localStorage using the existing section-lock key.

## Files and publication

1. `site/` holds all plaintext HTML, JavaScript, data, and local app assets. It is ignored by Git and is never published. The existing inner section encryption remains intact inside this directory.
2. `build_site.py` and `gate_template.html` build the encrypted site. AES-256-GCM protects one bundle, with a key derived using PBKDF2-HMAC-SHA256 and 310,000 iterations. An unchanged authenticated source bundle produces no new ciphertext.
3. `docs/` contains the encrypted bundle, unlock gates, `.nojekyll`, and public logos. GitHub Pages serves `main:/docs`. Each HTML route gets its own gate; `labs.html` preserves its redirect after unlock.
4. The password lives only on the VM at `~/.config/us-ai-compute-labs.pw`. Builds read that file directly; do not put the password in commands, commits, logs, or documentation. Browser localStorage retains the password on that browser until cleared.
5. Research inputs and local QA artifacts stay outside the published tree and are ignored by Git. The encrypted bundle is also a recoverable copy of the site sources for an authorized checkout.

To rebuild after changing private sources:

```bash
cd /home/ubuntu/projects/holy-grail
python3 build_site.py
python3 build_site.py --check-public
```

The build supports `--list-outputs` to list the generated files that may be staged, and `--check-source` to verify that local plaintext matches the current authenticated bundle. Stage only the listed build files and any deliberately reviewed generic tooling changes; never force-add `site/`, research inputs, or screenshots. Build and publish changes while holding the same `~/.local/state/holy-grail/publish.lock` used by the scheduled publishers.

A fresh checkout can recover private sources on the authorized VM:

```bash
python3 build_site.py --restore
```

Restore requires the password file. It refuses to overwrite differing local files unless `--force` is explicitly supplied. Keep a private backup before reconciling local source edits with a different remote encrypted bundle.

## Hourly publishers

Both jobs use `/home/ubuntu/projects/holy-grail` as the canonical checkout and share `scripts/publish_site.py` for the publication lock, clean-checkout check, fast-forward pull, encrypted build, output audit, restricted staging, commit, and push. The commit includes the requested co-author trailer. A failed push is retried on the next successful run even when inputs are unchanged.

1. At minute 47, `scripts/sync_regional_site.sh` runs `scripts/sync_regional_compute.py`. The reader validates its source, writes `site/regional_data.js`, and updates the asset hash and source date in `site/index.html` before encryption. The wrapper retains its separate lock to suppress overlapping regional cron instances.
2. At minute 25, `/home/ubuntu/research/us-owners-gb300e/sync_labs.py` validates the internal models, writes the existing inner encrypted blob to `site/labs_data.js`, updates its asset hash in `site/index.html`, then calls the shared publisher. Its model inputs stay in the external research directory. Its successful-payload hash is local state at `~/.local/state/holy-grail/labs_payload.sha`; its existing log location and cron entry remain unchanged.

If a pull changes the encrypted bundle, the shared helper restores its authenticated sources only when local plaintext matched the old bundle. If local unpublished edits conflict, it stops without overwriting them. The two scheduled jobs cannot overwrite each other's source changes or race their Git commits.

Local validation:

```bash
python3 scripts/test_sync_regional_compute.py
python3 scripts/test_regional_map.py
python3 scripts/test_publish_site.py
```

Pre-change plaintext remains in the public Git history. This change does not rewrite history or remove already downloaded copies; Konstantin decides whether to purge that history separately.
