#!/usr/bin/env python3
"""Build the standalone encrypted EOY-2026 developer forecast payload."""

import base64
import hashlib
import json
import math
import os
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


ROOT = os.path.dirname(os.path.abspath(__file__))
INPUT = os.path.join(ROOT, "forecast2026_input.json")
OUTPUT = os.path.join(ROOT, "docs", "forecast2026_data.js")
PW_FILE = os.path.expanduser("~/.config/us-ai-compute-labs.pw")
Z80 = 1.2815515655446004
EXPECTED = {
    "OpenAI": "us",
    "Anthropic": "us",
    "Google DeepMind": "us",
    "Meta MSL": "us",
    "SpaceXAI": "us",
    "Qwen": "cn",
    "DeepSeek": "cn",
    "Zhipu": "cn",
    "MiniMax": "cn",
    "Moonshot": "cn",
}


def two_piece_density(p10, median, p90):
    """Return an 81-point density grid for a two-piece lognormal fit."""
    sigma_lo = (math.log(median) - math.log(p10)) / Z80
    sigma_hi = (math.log(p90) - math.log(median)) / Z80
    x0 = median * math.exp(-3.1 * sigma_lo)
    x1 = median * math.exp(3.1 * sigma_hi)
    density = []
    for i in range(81):
        x = x0 + (x1 - x0) * i / 80
        sigma = sigma_hi if x > median else sigma_lo
        z = (math.log(x) - math.log(median)) / sigma
        density.append(math.exp(-0.5 * z * z) / (x * sigma))
    peak = max(density)
    return {
        "x0": round(x0, 1),
        "x1": round(x1, 1),
        "d": [round(value / peak, 3) for value in density],
    }


def load_payload():
    with open(INPUT, encoding="utf-8") as handle:
        source = json.load(handle)
    if not isinstance(source, dict) or not isinstance(source.get("labs"), list):
        raise ValueError('input must be an object with a "labs" array')
    if len(source["labs"]) != len(EXPECTED):
        raise ValueError(f"expected {len(EXPECTED)} labs, found {len(source['labs'])}")

    labs = []
    seen = set()
    for index, row in enumerate(source["labs"]):
        if not isinstance(row, dict):
            raise ValueError(f"labs[{index}] must be an object")
        name, country = row.get("name"), row.get("country")
        if name not in EXPECTED:
            raise ValueError(f"labs[{index}] has unexpected name {name!r}")
        if name in seen:
            raise ValueError(f"duplicate lab {name!r}")
        if country != EXPECTED[name]:
            raise ValueError(f"{name} must have country {EXPECTED[name]!r}")
        seen.add(name)
        try:
            p10, median, p90 = (float(row[key]) for key in ("p10", "median", "p90"))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{name} must have numeric p10, median, and p90") from exc
        if not (math.isfinite(p10) and math.isfinite(median) and math.isfinite(p90)):
            raise ValueError(f"{name} percentiles must be finite")
        if not (0 < p10 < median < p90):
            raise ValueError(f"{name} must satisfy 0 < p10 < median < p90")
        labs.append({
            "name": name,
            "country": country,
            "p10": p10,
            "median": median,
            "p90": p90,
            "dist": two_piece_density(p10, median, p90),
        })
    missing = set(EXPECTED) - seen
    if missing:
        raise ValueError(f"missing labs: {sorted(missing)}")

    test = source.get("test", False)
    if not isinstance(test, bool):
        raise ValueError('optional "test" field must be true or false')
    return {
        "model": "EOY-2026",
        "units": "GB300e",
        "test": test,
        "watermark": "TEST DATA" if test else None,
        "labs": labs,
    }


def encrypt_and_write(payload):
    payload_json = json.dumps(payload, ensure_ascii=False)
    with open(PW_FILE, encoding="utf-8") as handle:
        password = handle.read().strip()
    if not password:
        raise ValueError(f"password file is empty: {PW_FILE}")
    salt, iv = secrets.token_bytes(16), secrets.token_bytes(12)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 300000, dklen=32)
    ciphertext = AESGCM(key).encrypt(iv, payload_json.encode(), None)
    b64 = lambda value: base64.b64encode(value).decode()
    with open(OUTPUT, "w", encoding="utf-8") as handle:
        handle.write(
            f'const FORECAST2026_CT = {{"salt":"{b64(salt)}","iv":"{b64(iv)}",'
            f'"ct":"{b64(ciphertext)}"}};\n'
        )


if __name__ == "__main__":
    encrypt_and_write(load_payload())
    print(f"Wrote encrypted forecast to {OUTPUT}")
