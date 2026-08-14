#!/usr/bin/env python3
"""Sync the public regional-compute map from the Google Sheet Summary tab."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path


SHEET_ID = "1fKutDSCU4Hce-YAKra6zQX2-Y0uANfwc8_Atn7jguuc"
SHEET_GID = 1904826130
SOURCE_URL = (
    "https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/edit?gid={SHEET_GID}#gid={SHEET_GID}"
)
REPO = Path(__file__).resolve().parents[1]
DATA_PATH = REPO / "docs" / "regional_data.js"
INDEX_PATH = REPO / "docs" / "index.html"
CREDENTIALS_PATH = Path(
    os.environ.get(
        "GOOGLE_WORKSPACE_CREDENTIALS",
        "/home/ubuntu/.google_workspace_mcp/credentials/konstantinsclaude@gmail.com.json",
    )
)

REGION_META = {
    "China": {"key": "china", "short": "CN", "coordinates": [104, 35]},
    "USA": {"key": "us", "name": "United States", "short": "US", "coordinates": [-101, 38]},
    "Europe": {"key": "europe", "short": "EU", "coordinates": [13, 51]},
    "SE Asia": {"key": "sea", "name": "Southeast Asia", "short": "SEA", "coordinates": [106, 7]},
    "India": {"key": "india", "short": "IN", "coordinates": [78, 22]},
    "East Asia ex-China": {"key": "east-asia", "short": "EA", "coordinates": [139, 37]},
    "Middle East": {"key": "middle-east", "short": "ME", "coordinates": [46, 27]},
    "Latin America": {"key": "latam", "short": "LATAM", "coordinates": [-60, -16]},
    "Australia & NZ": {"key": "anz", "name": "Australia & New Zealand", "short": "ANZ", "coordinates": [146, -34]},
}

REGION_COUNTRIES = {
    "us": ["USA"],
    "china": ["CHN"],
    "india": ["IND"],
    "east-asia": ["JPN", "KOR", "TWN"],
    "anz": ["AUS", "NZL"],
    "sea": ["BRN", "KHM", "IDN", "LAO", "MYS", "MMR", "PHL", "SGP", "THA", "TLS", "VNM"],
    "europe": ["ALB", "AND", "AUT", "BEL", "BGR", "BIH", "CHE", "CYP", "CZE", "DEU", "DNK", "ESP", "EST", "FIN", "FRA", "GBR", "GRC", "HRV", "HUN", "IRL", "ISL", "ITA", "LTU", "LUX", "LVA", "MDA", "MKD", "MLT", "MNE", "NLD", "NOR", "POL", "PRT", "ROU", "SRB", "SVK", "SVN", "SWE", "UKR"],
    "middle-east": ["ARE", "BHR", "IRN", "IRQ", "ISR", "JOR", "KWT", "LBN", "OMN", "QAT", "SAU", "TUR", "YEM"],
    "latam": ["ARG", "BHS", "BLZ", "BOL", "BRA", "CHL", "COL", "CRI", "CUB", "DOM", "ECU", "GTM", "GUY", "HND", "HTI", "JAM", "MEX", "NIC", "PAN", "PER", "PRY", "SLV", "SUR", "TTO", "URY", "VEN"],
}


def request_json(url: str, *, data: bytes | None = None, headers: dict[str, str] | None = None) -> dict:
    request = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def access_token() -> str:
    with CREDENTIALS_PATH.open() as handle:
        credentials = json.load(handle)
    payload = urllib.parse.urlencode(
        {
            "client_id": credentials["client_id"],
            "client_secret": credentials["client_secret"],
            "refresh_token": credentials["refresh_token"],
            "grant_type": "refresh_token",
        }
    ).encode()
    return request_json(
        credentials["token_uri"],
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )["access_token"]


def sheet_values(token: str) -> list[list[object]]:
    headers = {"Authorization": f"Bearer {token}"}
    metadata_url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}"
        "?fields=sheets(properties(sheetId,title))"
    )
    metadata = request_json(metadata_url, headers=headers)
    title = next(
        sheet["properties"]["title"]
        for sheet in metadata["sheets"]
        if sheet["properties"]["sheetId"] == SHEET_GID
    )
    quoted = "'" + title.replace("'", "''") + "'!A:Z"
    encoded_range = urllib.parse.quote(quoted, safe="")
    values_url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{encoded_range}"
        "?majorDimension=ROWS&valueRenderOption=UNFORMATTED_VALUE"
    )
    return request_json(values_url, headers=headers).get("values", [])


def parse_values(rows: list[list[object]]) -> tuple[str, list[dict[str, object]]]:
    def norm(value: object) -> str:
        return re.sub(r"\s+", " ", str(value).replace("\xa0", " ").strip()).strip().lower()

    def token_set(value: object) -> set[str]:
        return set(re.findall(r"[a-z0-9]+", norm(value)))

    def pick_column(predicate, prefer_p50: bool = True) -> int:
        matches = [
            (index, toks)
            for index, toks in header_tokens.items()
            if predicate(toks)
        ]
        if not matches:
            return -1
        if prefer_p50:
            p50 = [index for index, toks in matches if "p50" in toks]
            if p50:
                return p50[0]
        return matches[0][0]

    updated = next(
        (
            match.group(1)
            for row in rows
            for cell in row[:1]
            if (match := re.fullmatch(r"Last updated (\d{4}-\d{2}-\d{2})", str(cell)))
        ),
        None,
    )
    if not updated:
        raise ValueError("Summary tab has no 'Last updated YYYY-MM-DD' line")

    header_index = next(
        index
        for index, row in enumerate(rows)
        if row and isinstance(row[0], str) and norm(row[0]) == "region"
    )
    header_tokens = {
        index: token_set(name)
        for index, name in enumerate(rows[header_index])
    }

    fp8_col = pick_column(
        lambda token: "fp8" in token and "gb300e" in token and "share" not in token,
        prefer_p50=True,
    )
    fp4_col = pick_column(
        lambda token: "fp4" in token and "gb300e" in token and "share" not in token,
        prefer_p50=False,
    )
    bw_col = pick_column(
        lambda token: "bw" in token and "gb300e" in token and "share" not in token,
        prefer_p50=False,
    )

    missing_columns = []
    if fp8_col < 0:
        missing_columns.append("FP8 GB300e")
    if fp4_col < 0:
        missing_columns.append("FP4 GB300e")
    if bw_col < 0:
        missing_columns.append("BW GB300e")
    if missing_columns:
        raise ValueError(f"Missing expected columns: {missing_columns}")

    region_aliases = {
        norm("USA"): "usa",
        norm("United States"): "usa",
        norm("SE Asia"): "sea",
        norm("Southeast Asia"): "sea",
        norm("East Asia ex-China"): "east-asia",
        norm("Australia & NZ"): "anz",
        norm("Australia and NZ"): "anz",
    }
    region_aliases.update({norm(key): key for key in REGION_META})

    by_name = {}
    for row in rows[header_index + 1:]:
        if not row or not isinstance(row[0], str):
            continue
        region_key = region_aliases.get(norm(row[0]))
        if region_key:
            by_name[region_key] = row

    missing = set(REGION_META) - set(by_name)
    if missing:
        raise ValueError(f"Missing expected regions: {sorted(missing)}")

    required_index = max(fp8_col, fp4_col, bw_col)
    regions = []
    for sheet_name, meta in REGION_META.items():
        row = by_name[sheet_name]
        if len(row) <= required_index:
            raise ValueError(f"Incomplete row for {sheet_name}")
        values = [row[fp8_col], row[fp4_col], row[bw_col]]
        if not all(
            isinstance(value, (int, float)) and math.isfinite(value) and value > 0 for value in values
        ):
            raise ValueError(f"Invalid compute values for {sheet_name}: {values}")
        regions.append(
            {
                "key": meta["key"],
                "name": meta.get("name", sheet_name),
                "short": meta["short"],
                "coordinates": meta["coordinates"],
                "fp8": round(values[0]),
                "fp4": round(values[1]),
                "bw": round(values[2]),
            }
        )
    return updated, regions


def atomic_write(path: Path, content: str) -> bool:
    if path.read_text() == content:
        return False
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.replace(path)
    return True


def main() -> None:
    updated, regions = parse_values(sheet_values(access_token()))
    payload = {
        "updated": updated,
        "sourceUrl": SOURCE_URL,
        "regions": regions,
        "regionCountries": REGION_COUNTRIES,
    }
    serialized = json.dumps(payload, indent=2, ensure_ascii=False)
    data_content = f'"use strict";\n\nwindow.REGIONAL_COMPUTE = Object.freeze({serialized});\n'
    cache_tag = hashlib.sha256(data_content.encode()).hexdigest()[:10]
    data_changed = atomic_write(DATA_PATH, data_content)

    index = INDEX_PATH.read_text()
    new_index, count = re.subn(
        r'regional_data\.js\?v=[^"<]+',
        f"regional_data.js?v={cache_tag}",
        index,
    )
    if count != 1:
        raise ValueError(f"Expected one regional_data.js tag, found {count}")
    index_changed = atomic_write(INDEX_PATH, new_index)
    state = "updated" if data_changed or index_changed else "unchanged"
    print(f"regional compute {state}: sheet {updated}, cache {cache_tag}")


if __name__ == "__main__":
    main()
