#!/usr/bin/env python3
"""Build a self-contained, embeddable version of the owners figure.

Public data only: Epoch AI's chip-owners estimates (CC-BY 4.0) converted to
GB300e. No internal research is included, so the output can be shared freely.

Writes docs/embed/ai-chip-owners.html — a single file with no external requests,
usable either as an iframe target or pasted inline into a page.
"""
import json, re, os

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = json.loads(re.match(r"const DATA = (.*);\n",
                           open(os.path.join(ROOT, "docs", "data.js")).read(), re.S).group(1))

payload = {
    "pulled": DATA["meta"]["pulled"],
    "eoy": DATA["meta"]["eoy"],
    "gb300": DATA["meta"]["gb300"],
    "n_mc": DATA["meta"]["n_mc"],
    "owners": [{"owner": o["owner"], "has_ci": o["has_ci"],
                "modes": o["modes"],
                "chips": {c: {"units": v["units"], **{m: v[m] for m in
                              ("train_fp8", "train_fp4", "inference")}}
                          for c, v in o["chips"].items()}}
               for o in DATA["owners"]],
}

BODY = r'''<div class="hg-fig" id="hg-fig" data-title="US AI chip owners, end of 2025">
  <div class="hg-head">
    <div>
      <h3 class="hg-h">US AI chip owners, end of 2025</h3>
      <p class="hg-sub">Cumulative AI-chip installed base in <strong>GB300-equivalents (GB300e)</strong> — color intensity shows the probability distribution</p>
    </div>
    <select class="hg-select" id="hg-mode" aria-label="Conversion metric">
      <option value="train_fp8" selected>FP8 FLOP/s</option>
      <option value="train_fp4">FP4 FLOP/s</option>
      <option value="inference">Memory bandwidth</option>
    </select>
  </div>
  <p class="hg-note" id="hg-note"></p>
  <div id="hg-chart"></div>
  <div class="hg-tip" id="hg-tip" aria-hidden="true"></div>
  <p class="hg-fine">Source: <a href="https://epoch.ai/data/ai-chip-owners">Epoch AI, Data on AI Chip Owners</a>
    (CC&nbsp;BY&nbsp;4.0, pulled __PULLED__), converted to GB300-equivalents. xAI: point estimate only.
    Hover or tap a bar for the chip-level breakdown.</p>
</div>'''

CSS = r'''.hg-fig {
  --hg-bar: #1d81a2; --hg-text: #333; --hg-text2: #666; --hg-text3: #888;
  --hg-grid: #e6e6e6; --hg-bg: #fff; --hg-border: #ddd;
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: var(--hg-text); background: var(--hg-bg);
  max-width: 680px; margin: 0 auto; padding: 4px 2px 2px; box-sizing: border-box;
}
@media (prefers-color-scheme: dark) {
  .hg-fig { --hg-bar: #2e94bd; --hg-text: #e0e0e0; --hg-text2: #aaa; --hg-text3: #888;
            --hg-grid: #3a3a3a; --hg-bg: #1f1f1f; --hg-border: #444; }
}
.hg-fig[data-theme="light"] { --hg-bar: #1d81a2; --hg-text: #333; --hg-text2: #666;
  --hg-text3: #888; --hg-grid: #e6e6e6; --hg-bg: #fff; --hg-border: #ddd; }
.hg-fig[data-theme="dark"] { --hg-bar: #2e94bd; --hg-text: #e0e0e0; --hg-text2: #aaa;
  --hg-text3: #888; --hg-grid: #3a3a3a; --hg-bg: #1f1f1f; --hg-border: #444; }
.hg-fig * { box-sizing: border-box; }
.hg-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; }
.hg-h { font-size: 19px; font-weight: 700; margin: 0 0 4px; line-height: 1.25; }
.hg-sub { font-size: 13px; color: var(--hg-text2); margin: 0; line-height: 1.45; max-width: 460px; }
.hg-select { font: inherit; font-size: 13px; padding: 4px 8px; border: 1px solid var(--hg-border);
  border-radius: 6px; background: var(--hg-bg); color: var(--hg-text); }
.hg-note { color: var(--hg-text2); font-size: 12.5px; margin: 10px 0 2px; line-height: 1.45; min-height: 1.3em; }
.hg-fine { color: var(--hg-text3); font-size: 11.5px; line-height: 1.5; margin: 8px 0 0; }
.hg-fine a { color: inherit; }
.hg-fig svg { display: block; width: 100%; height: auto; overflow: visible; }
.hg-grid-line { stroke: var(--hg-grid); stroke-width: 1; }
.hg-zero-line { stroke: var(--hg-text3); stroke-width: 1; }
.hg-axis { fill: var(--hg-text3); font-size: 10.5px; }
.hg-unit { fill: var(--hg-text2); font-size: 11.5px; font-weight: 700; }
.hg-name { fill: var(--hg-text); font-size: 12.5px; }
.hg-val { fill: var(--hg-text); font-size: 11.5px; font-weight: 700; }
.hg-tip { position: fixed; display: none; z-index: 2147483000; pointer-events: none;
  background: var(--hg-bg); color: var(--hg-text); border: 1px solid var(--hg-border);
  border-radius: 6px; padding: 8px 10px; font-size: 12px; line-height: 1.45;
  box-shadow: 0 4px 14px rgba(0,0,0,.13); max-width: 300px; }
.hg-tip h4 { margin: 0 0 2px; font-size: 12.5px; }
.hg-tip .hg-ci { color: var(--hg-text2); margin: 0 0 6px; font-size: 11.5px; }
.hg-tip table { border-collapse: collapse; width: 100%; }
.hg-tip td { padding: 1px 0; }
.hg-tip td:nth-child(2), .hg-tip td:nth-child(3) { text-align: right; padding-left: 10px; white-space: nowrap; }
.hg-tip .hg-tot td { border-top: 1px solid var(--hg-border); font-weight: 700; padding-top: 3px; }'''

JS = r'''(function () {
  var DATA = __DATA__;
  var root = document.getElementById("hg-fig");
  var chartEl = document.getElementById("hg-chart");
  var tipEl = document.getElementById("hg-tip");
  var sel = document.getElementById("hg-mode");
  var mode = "train_fp8";
  var NS = "http://www.w3.org/2000/svg";

  var NOTES = {
    train_fp8: "Conversion: chip's dense FP8 FLOP/s ÷ GB300's " + DATA.gb300.fp8_pflops +
      " PFLOP/s. Chips without FP8 use FP16/BF16; Google TPUs without FP8 use INT8.",
    train_fp4: "Conversion: chip's dense FP4 FLOP/s ÷ GB300's " + DATA.gb300.fp4_pflops +
      " PFLOP/s, falling back to the FP8 basis where FP4 is unsupported.",
    inference: "Conversion: chip's memory bandwidth ÷ GB300's " + DATA.gb300.bw_tbs +
      " TB/s — decode throughput is memory-bandwidth-bound."
  };

  function el(tag, attrs) {
    var n = document.createElementNS(NS, tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }
  function fmtM(v) {
    var m = v / 1e6;
    return m >= 10 ? m.toFixed(1) + "m" : m >= 1 ? m.toFixed(2) + "m" : Math.round(v / 1e3) + "k";
  }
  function fmtUnits(v) { return v >= 1e6 ? (v / 1e6).toFixed(2) + "m" : Math.round(v / 1e3) + "k"; }
  function fmtTick(v) { return v >= 1e6 ? parseFloat((v / 1e6).toFixed(2)) + "m" : Math.round(v / 1e3) + "k"; }
  function niceStep(max) {
    var target = max / 5, pow = Math.pow(10, Math.floor(Math.log10(target))), ms = [1, 2, 2.5, 5, 10];
    for (var i = 0; i < ms.length; i++) if (target <= ms[i] * pow) return ms[i] * pow;
    return 10 * pow;
  }
  function wrapLabel(text, maxChars) {
    if (text.length <= maxChars || text.indexOf(" ") < 0) return [text];
    var best = null;
    for (var i = 0; i < text.length; i++) {
      if (text[i] !== " ") continue;
      var a = text.slice(0, i), b = text.slice(i + 1), score = Math.max(a.length, b.length);
      if (best === null || score < best.score) best = { score: score, lines: [a, b] };
    }
    return best.lines;
  }

  function render() {
    var owners = DATA.owners.slice().sort(function (a, b) {
      return b.modes[mode].median - a.modes[mode].median;
    });
    var W = Math.max(320, Math.min(chartEl.clientWidth || 660, 680));
    var ROWH = 40, BARH = 18, LEFT = 96, RIGHT = 12, TOP = 24, BOT = 6;
    var H = TOP + owners.length * ROWH + BOT, plotW = W - LEFT - RIGHT;
    var maxX = Math.max.apply(null, owners.map(function (o) {
      var m = o.modes[mode];
      return m.dist ? m.dist.x1 : m.median * 1.1;
    })) * 1.02;
    var x = function (v) { return LEFT + (v / maxX) * plotW; };

    chartEl.innerHTML = "";
    var svg = el("svg", { viewBox: "0 0 " + W + " " + H, role: "img",
      "aria-label": "US AI chip owners in GB300 equivalents" });
    chartEl.appendChild(svg);

    var step = niceStep(maxX);
    for (var v = 0; v <= maxX; v += step) {
      svg.appendChild(el("line", { class: v === 0 ? "hg-zero-line" : "hg-grid-line",
        x1: x(v), x2: x(v), y1: TOP - 4, y2: H - BOT }));
      var last = v + step > maxX;
      var t = el("text", { class: last ? "hg-unit" : "hg-axis",
        x: last ? Math.min(x(v) + 30, W) : x(v), y: TOP - 9,
        "text-anchor": v === 0 ? "start" : last ? "end" : "middle" });
      t.textContent = (v === 0 ? "0" : fmtTick(v)) + (last ? " GB300e" : "");
      svg.appendChild(t);
    }

    var color = getComputedStyle(root).getPropertyValue("--hg-bar").trim();
    owners.forEach(function (o, i) {
      var yMid = TOP + i * ROWH + ROWH / 2, m = o.modes[mode];
      var g = el("g", {});
      if (m.dist) {
        var xL = x(m.dist.x0), xR = x(m.dist.x1);
        var gid = "hg-g-" + o.owner.replace(/[^a-z]/gi, "") + "-" + mode;
        var grad = el("linearGradient", { id: gid, gradientUnits: "userSpaceOnUse",
          x1: xL, x2: xR, y1: 0, y2: 0 });
        for (var k = 0; k <= 80; k += 2) {
          grad.appendChild(el("stop", { offset: (k / 80).toFixed(3), "stop-color": color,
            "stop-opacity": Math.pow(m.dist.d[k], 0.6).toFixed(3) }));
        }
        svg.appendChild(grad);
        g.appendChild(el("rect", { x: xL, width: Math.max(2, xR - xL),
          y: yMid - BARH / 2, height: BARH, fill: "url(#" + gid + ")" }));
      } else {
        g.appendChild(el("line", { x1: x(m.median), x2: x(m.median),
          y1: yMid - BARH / 2, y2: yMid + BARH / 2, stroke: color, "stroke-width": 3 }));
      }
      var name = el("text", { class: "hg-name", x: LEFT - 8, "text-anchor": "end" });
      var lines = wrapLabel(o.owner, 15);
      if (lines.length === 1) {
        name.setAttribute("y", yMid + 4);
        name.textContent = lines[0];
      } else {
        name.setAttribute("y", yMid - 2);
        lines.forEach(function (ln, j) {
          var ts = el("tspan", { x: LEFT - 8 });
          if (j) ts.setAttribute("dy", "13");
          ts.textContent = ln;
          name.appendChild(ts);
        });
      }
      g.appendChild(name);
      var val = el("text", { class: "hg-val", x: Math.max(x(m.median), LEFT + 14),
        y: yMid + BARH / 2 + 11, "text-anchor": "middle" });
      val.textContent = fmtM(m.median);
      g.appendChild(val);
      var hit = el("rect", { x: 0, y: yMid - ROWH / 2, width: W, height: ROWH, fill: "transparent" });
      hit.addEventListener("mousemove", function (e) { showTip(o, e); });
      hit.addEventListener("mouseleave", hideTip);
      hit.addEventListener("click", function (e) { showTip(o, e); });
      g.appendChild(hit);
      svg.appendChild(g);
    });

    document.getElementById("hg-note").textContent = NOTES[mode];
    postHeight();
  }

  function showTip(o, ev) {
    var m = o.modes[mode];
    var chips = Object.keys(o.chips).map(function (c) {
      return { chip: c, units: o.chips[c].units, v: o.chips[c][mode] };
    }).sort(function (a, b) { return b.v - a.v; });
    var html = "<h4>" + o.owner + " — " + fmtM(m.median) + " GB300e</h4>";
    html += "<p class='hg-ci'>" + (o.has_ci ? "80% CI: " + fmtM(m.lo) + "–" + fmtM(m.hi)
      : "Point estimate — Epoch publishes no interval") + "</p><table>";
    chips.forEach(function (c) {
      html += "<tr><td>" + c.chip + "</td><td>" + fmtUnits(c.units) + " chips</td><td>" +
        fmtM(c.v) + " · " + Math.round(c.v / m.median * 100) + "%</td></tr>";
    });
    html += "<tr class='hg-tot'><td>Total</td><td></td><td>" + fmtM(m.median) + "</td></tr></table>";
    tipEl.innerHTML = html;
    tipEl.style.display = "block";
    var tw = tipEl.offsetWidth, th = tipEl.offsetHeight;
    var tx = ev.clientX + 12, ty = ev.clientY + 10;
    if (tx + tw > window.innerWidth - 8) tx = ev.clientX - tw - 12;
    if (ty + th > window.innerHeight - 8) ty = ev.clientY - th - 10;
    tipEl.style.left = tx + "px";
    tipEl.style.top = ty + "px";
  }
  function hideTip() { tipEl.style.display = "none"; }
  document.addEventListener("click", function (e) {
    if (!e.target.closest || !e.target.closest("#hg-chart")) hideTip();
  });

  // Lets a host page size an iframe to the figure: listen for
  // {type:"hg-figure-height", height:<px>} on window.message.
  function postHeight() {
    if (window.parent === window) return;
    try {
      window.parent.postMessage({ type: "hg-figure-height",
        height: document.documentElement.scrollHeight }, "*");
    } catch (err) { /* cross-origin parent without a listener */ }
  }

  sel.addEventListener("change", function (e) { mode = e.target.value; hideTip(); render(); });
  if (window.ResizeObserver) new ResizeObserver(render).observe(chartEl);
  else window.addEventListener("resize", render);
  render();
})();'''

body = BODY.replace("__PULLED__", DATA["meta"]["pulled"])
js = JS.replace("__DATA__", json.dumps(payload, separators=(",", ":")))
snippet = f"<style>\n{CSS}\n</style>\n\n{body}\n\n<script>\n{js}\n</script>\n"

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>US AI chip owners, end of 2025 — embeddable figure</title>
<style>html,body{{margin:0;padding:0;background:transparent}}</style>
</head>
<body>
{snippet}</body>
</html>
"""

out_dir = os.path.join(ROOT, "docs", "embed")
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, "ai-chip-owners.html"), "w") as f:
    f.write(page)
with open(os.path.join(out_dir, "ai-chip-owners.snippet.html"), "w") as f:
    f.write(snippet)
print("wrote docs/embed/ai-chip-owners.html", os.path.getsize(os.path.join(out_dir, "ai-chip-owners.html")), "bytes")
print("wrote docs/embed/ai-chip-owners.snippet.html")
