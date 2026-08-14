#!/usr/bin/env python3
"""Regional map regression checks for the Holy Grail site.

These tests are intentionally static and local: they inspect scripts/styles/data
to verify tooltip interactivity wiring, renamed region labels, cache-busting,
and syntax validity.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
INDEX_HTML = DOCS / "index.html"
REGIONAL_MAP_JS = DOCS / "regional_map.js"
REGIONAL_DATA_JS = DOCS / "regional_data.js"


def line_number(text: str, needle: str) -> int | None:
    idx = text.find(needle)
    if idx < 0:
        return None
    return text.count("\n", 0, idx) + 1


def compact_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def extract_block(source: str, start_token: str) -> str:
    start_idx = source.find(start_token)
    if start_idx < 0:
        return ""
    start = source.find("{", start_idx)
    if start < 0:
        return ""

    depth = 0
    end = start
    for i in range(start, len(source)):
        ch = source[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    return source[start + 1 : end]


def extract_function_block(source: str, function_name: str) -> str:
    token = f"function {function_name}"
    start_idx = source.find(token)
    if start_idx < 0:
        return ""
    start = source.find("{", start_idx)
    if start < 0:
        return ""

    depth = 0
    for i in range(start, len(source)):
        ch = source[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[start + 1 : i]
    return ""


def record(results: list[tuple[str, bool, str | None]], name: str, passed: bool, note: str | None = None) -> None:
    results.append((name, passed, note))


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_regions() -> tuple[dict, str]:
    text = load_text(REGIONAL_DATA_JS)
    m = re.search(r"window\.REGIONAL_COMPUTE\s*=\s*Object\.freeze\((\{[\s\S]*\})\);", text)
    if not m:
        raise ValueError("Unable to locate window.REGIONAL_COMPUTE object in regional_data.js")
    payload = m.group(1)
    return json.loads(payload), text


def run_node_syntax_check(results: list[tuple[str, bool, str | None]]) -> None:
    proc = subprocess.run(
        ["bash", "-lc", f"cat '{REGIONAL_MAP_JS}' | node --check --input-type=module"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    passed = proc.returncode == 0
    record(
        results,
        "node --check parse for docs/regional_map.js",
        passed,
        None if passed else f"node exited {proc.returncode}: {proc.stdout.strip()}",
    )


def main() -> int:
    results: list[tuple[str, bool, str | None]] = []
    passed_count = 0
    failed_count = 0
    failures: list[tuple[str, int | None, str]] = []

    index_text = load_text(INDEX_HTML)
    map_text = load_text(REGIONAL_MAP_JS)
    compact_map = compact_whitespace(map_text)

    # 1) regional_map.js interactivity function + listener wiring
    for fn in ("showTooltip", "trackTooltip", "hideTooltip"):
        if f"function {fn}(" in map_text:
            passed = True
            note = None
        else:
            ln = line_number(map_text, f"function {fn}(")
            passed = False
            note = f"function {fn} definition missing"
            failures.append((f"regional_map.js defines {fn}", ln, note))
        record(results, f"regional_map.js defines {fn}", passed, note)

    wire_block = extract_block(map_text, "function wireRegionTooltip")
    helper_ok = all(
        evt in wire_block
        for evt in [
            "target.addEventListener(\"pointerenter\"",
            "target.addEventListener(\"pointermove\"",
            "target.addEventListener(\"pointerleave\"",
            "target.addEventListener(\"pointerdown\"",
            "event.pointerType === \"touch\"",
        ]
    )
    if helper_ok:
        passed = True
        touch_note = None
    else:
        touch_line = line_number(map_text, "function wireRegionTooltip")
        passed = False
        touch_note = "wireRegionTooltip missing required pointer bindings or touch fallback"
        failures.append(("wireRegionTooltip has expected listeners", touch_line, touch_note))
    record(results, "wireRegionTooltip has expected listeners + touch fallback", passed, touch_note)

    for target in ("group", "bar"):
        call_pattern = f"wireRegionTooltip({target}, region, mode)"
        if call_pattern in compact_map:
            passed = True
            note = None
        else:
            ln = line_number(compact_map, "wireRegionTooltip(")
            passed = False
            note = f"missing call: {call_pattern}"
            failures.append((f"wireRegionTooltip call for {target}", ln, note))
        record(results, f"wireRegionTooltip called for {target}", passed, note)

    # 2) draw() calls hideTooltip at start
    draw_block = extract_block(map_text, "function draw() ")
    if not draw_block:
        ln = line_number(map_text, "function draw()")
        passed = False
        note = "draw() function body not found"
        failures.append(("draw() hideTooltip at start", ln, note))
        record(results, "draw() calls hideTooltip before drawing geometry", passed, note)
    else:
        compact_draw = compact_whitespace(draw_block)
        hide_pattern = "const mode = select.value;"
        has_hide = "hideTooltip();" in compact_draw
        has_start = hide_pattern in compact_draw and compact_draw.index("hideTooltip();") > compact_draw.index(hide_pattern)
        passed = has_hide and has_start
        if passed:
            note = None
        else:
            ln = line_number(draw_block, "hideTooltip();")
            note = "draw() should call hideTooltip() near function start (after mode declaration)"
            failures.append(("draw() calls hideTooltip at start", ln, note))
        record(results, "draw() calls hideTooltip at start", passed, note)

    # 3) regional interaction zone cursor + tabindex
    bar_style_present = re.search(r"\.regional-bar\s*{[^}]*cursor:\s*pointer", index_text, re.S) is not None
    mark_style_present = re.search(r"\.regional-mark\s*{[^}]*cursor:\s*pointer", index_text, re.S) is not None
    tabindex_present = "tabindex: \"0\"" in compact_map
    if not bar_style_present:
        ln = line_number(index_text, ".regional-bar")
        failures.append(("regional-bar cursor pointer", ln, "CSS rule missing: .regional-bar { cursor: pointer; }"))
    if not mark_style_present:
        ln = line_number(index_text, ".regional-mark")
        failures.append(("regional-mark cursor pointer", ln, "CSS rule missing: .regional-mark { cursor: pointer; }"))
    if not tabindex_present:
        ln = line_number(map_text, "tabindex:")
        failures.append(("regional-bar tabindex", ln, "JS region bars missing tabindex for touch/keyboard-accessible interaction"))
    mark_pointer_ok = ".regional-mark { pointer-events: none;" not in index_text
    if not mark_pointer_ok:
        ln = line_number(index_text, ".regional-mark {")
        failures.append(("regional-mark keeps pointer events enabled", ln, "Wrapper element cannot disable pointer events on region bars"))
    record(results, "CSS sets regional bar pointer cursor", bar_style_present, None if bar_style_present else "missing")
    record(results, "CSS sets regional mark pointer cursor", mark_style_present, None if mark_style_present else "missing")
    record(results, "regional region elements include tabindex", tabindex_present, None if tabindex_present else "missing")
    record(results, "regional-mark wrapper does not disable pointer events", mark_pointer_ok, None if mark_pointer_ok else "found pointer-events: none")

    # 4) regional_data.js mapping + region/country keys + style references
    data, _ = load_regions()
    regions = data.get("regions", [])
    region_countries = data.get("regionCountries", {})

    region_names = [r.get("name") for r in regions]
    regions_ok = "Japan, Korea & Taiwan" in region_names and "Australia" in region_names
    if not regions_ok:
        failures.append(
            ("renamed region labels in region list", None, "Expected 'Japan, Korea & Taiwan' and 'Australia' in regional_data.js"),
        )
    record(results, "renamed region labels exist in regions list", regions_ok, None)

    region_keys = {r.get("key") for r in regions if "key" in r}
    countries_ok = all(k in region_countries for k in ("east-asia", "anz"))
    if not countries_ok:
        failures.append(
            ("regionCountries includes east-asia and anz", None, "Expected keys east-asia and anz in regionCountries"),
        )
    east_asia_countries = set(region_countries.get("east-asia", []))
    anz_countries = set(region_countries.get("anz", []))
    country_sets_ok = {"JPN", "KOR", "TWN"}.issubset(east_asia_countries) and {"AUS", "NZL"}.issubset(anz_countries)
    if not country_sets_ok:
        failures.append(
            ("regionCountries for east-asia and anz mapped correctly", None, "Expected east-asia includes JPN/KOR/TWN and anz includes AUS/NZL"),
        )
    record(results, "regionCountries includes east-asia/anz", countries_ok, None)
    record(results, "east-asia and anz country lists are complete", country_sets_ok, None)

    region_color_vars = {f"region-{r['key']}" for r in regions if "key" in r}
    css_has_vars = all(f"--{v}:" in index_text for v in region_color_vars)
    if not css_has_vars:
        missing = sorted([v for v in region_color_vars if f"--{v}:" not in index_text])
        ln = line_number(index_text, ":root")
        failures.append(("CSS declares every region color variable", ln, f"Missing CSS vars: {missing}"))
    map_color_refs_ok = "--regional-color:var(--region-" in map_text
    if not map_color_refs_ok:
        ln = line_number(map_text, "--regional-color:var(--region-")
        failures.append(("JS uses region colors per key", ln, "Bar style not setting --regional-color with region-key token"))
    record(results, "index.css declares region-<key> color vars", css_has_vars, None)
    record(results, "regional bars use --region-<key> colors", map_color_refs_ok, None)

    coordinate_ok = all(isinstance(r.get("coordinates"), list) and len(r["coordinates"]) == 2 for r in regions)
    if not coordinate_ok:
        failures.append(("regions include coordinates", None, "One or more regions missing [lon, lat] coordinates"))
    record(results, "every region has coordinates [lon, lat]", coordinate_ok, None)

    # 5) cache-bust tag in index.html
    cache_ok = 'regional_map.js?v=5"' in index_text
    cache_line = line_number(index_text, 'regional_map.js?v=5"')
    cache_note = None if cache_ok else "regional_map.js cache-buster missing or not expected v=5"
    if not cache_ok:
        failures.append(("index cache-bust is regional_map.js?v=5", cache_line, cache_note))
    record(results, "index.html regional_map.js includes ?v=5", cache_ok, cache_note)

    # 6) negative/failing-mode regression test: tooltip null guard
    show_block = extract_function_block(map_text, "showTooltip")
    hide_block = extract_function_block(map_text, "hideTooltip")
    move_block = extract_function_block(map_text, "trackTooltip")
    tooltip_guard_show = (
        'if (!tooltip) return;' in show_block
        and 'tooltip.style.display = "block"' in show_block
    )
    tooltip_guard_hide = (
        "tooltip.style.display = \"none\"" in hide_block
        and ("if (tooltip)" in hide_block or "if (!tooltip) return;" in hide_block)
    )
    tooltip_guard_move = (
        'if (!tooltip) return;' in move_block
        and "tooltip.style.left" in move_block
    )
    negative_ok = bool(tooltip_guard_show and tooltip_guard_hide and tooltip_guard_move)
    if not negative_ok:
        failures.append(
            ("negative tooltip robustness test", None, "One of showTooltip/hideTooltip/trackTooltip lacks `if (!tooltip) return;`"),
        )
    record(
        results,
        "negative test: tooltip-guard logic exists for missing tooltip element",
        negative_ok,
        None if negative_ok else "Regression-prone code path for missing tooltip not guarded",
    )

    # 6) node syntax check (also required as one test)
    run_node_syntax_check(results)

    for name, passed, note in results:
        if passed:
            passed_count += 1
        else:
            failed_count += 1
            print(f"FAIL: {name}")
            if note:
                print(f"  reason: {note}")
    for _, passed, _ in results:
        if not passed:
            # line output after primary summary, to keep output deterministic
            break

    if failures:
        for name, ln, detail in failures:
            print(f"FAIL: {name} | line {ln if ln is not None else 'n/a'}")
            print(f"       detail: {detail}")

    print(f"SUMMARY: pass={passed_count}, fail={failed_count}")
    return 1 if failed_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
