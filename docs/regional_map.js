import world from "https://esm.sh/@d3-maps/atlas@1.0.0/world/countries/countries-110m";
import { geoNaturalEarth1, geoPath } from "https://cdn.jsdelivr.net/npm/d3-geo@3/+esm";
import { feature } from "https://cdn.jsdelivr.net/npm/topojson-client@3.1.0/+esm";

const data = window.REGIONAL_COMPUTE;
const chart = document.getElementById("regional-chart");
const select = document.getElementById("regional-mode-select");
const note = document.getElementById("regional-mode-note");
const status = document.getElementById("regional-status");
const tooltip = document.getElementById("tooltip");
const countries = feature(world, world.objects.features).features;
const countryRegion = new Map();
for (const [region, ids] of Object.entries(data.regionCountries)) {
  for (const id of ids) countryRegion.set(id, region);
}
const regionLookup = new Map();
for (const region of data.regions) {
  regionLookup.set(region.key, region);
}
const NS = "http://www.w3.org/2000/svg";

const modes = {
  fp8: {
    label: "FP8 FLOP/s",
    note: "Linear scale. One GB300e equals 5,000 dense-FP8 TFLOP/s.",
  },
  fp4: {
    label: "FP4 FLOP/s",
    note: "Linear scale. One GB300e equals 15,000 dense-FP4 TFLOP/s.",
  },
  bw: {
    label: "Memory Bandwidth",
    note: "Linear scale. One GB300e equals 8 TB/s of memory bandwidth.",
  },
};

function showOtherTooltip(event) {
  if (!tooltip) return;
  tooltip.innerHTML = `
    <h3>Other</h3>
  `;
  tooltip.style.display = "block";
  const x = Math.min(window.innerWidth - tooltip.offsetWidth - 12, event.clientX + 12);
  const y = Math.min(window.innerHeight - tooltip.offsetHeight - 12, event.clientY + 12);
  tooltip.style.left = `${Math.max(12, x)}px`;
  tooltip.style.top = `${Math.max(12, y)}px`;
}

function wireRegionTooltip(target, region, mode) {
  target.addEventListener("pointerenter", (event) => showTooltip(event, region, mode));
  target.addEventListener("pointermove", trackTooltip);
  target.addEventListener("pointerleave", hideTooltip);
  target.addEventListener("pointerdown", (event) => {
    if (event.pointerType === "touch") showTooltip(event, region, mode);
  });
}

function wireOtherTooltip(target) {
  target.addEventListener("pointerenter", showOtherTooltip);
  target.addEventListener("pointermove", trackTooltip);
  target.addEventListener("pointerleave", hideTooltip);
  target.addEventListener("pointerdown", (event) => {
    if (event.pointerType === "touch") showOtherTooltip(event);
  });
}

const offsets = {
  wide: {
    "China": [10, -16],
    "United States": [14, 2],
    "Europe": [-10, -3],
    "Southeast Asia": [10, 39],
    "India": [-16, 34],
    "Japan, Korea & Taiwan": [11, 2],
    "Middle East": [-13, -12],
    "Latin America": [-12, 11],
    "Australia": [-11, 8],
  },
  narrow: {
    "China": [9, -18],
    "United States": [11, 2],
    "Europe": [-7, -4],
    "Southeast Asia": [8, 39],
    "India": [-10, 31],
    "Japan, Korea & Taiwan": [9, 23],
    "Middle East": [-12, -17],
    "Latin America": [-8, 10],
    "Australia": [9, 7],
  },
};

function svgEl(tag, attrs = {}) {
  const el = document.createElementNS(NS, tag);
  for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
  return el;
}

function formatCompact(value) {
  if (value >= 1e6) return (value / 1e6).toFixed(2).replace(/\.00$/, "") + "M";
  return Math.round(value / 1e3) + "K";
}

function formatExact(value) {
  if (value == null) return "N/A";
  return Math.round(value).toLocaleString("en-US");
}

function formatCI(region, mode) {
  const lowKey = `${mode}P10`;
  const highKey = `${mode}P90`;
  const low = region[lowKey];
  const high = region[highKey];
  if (low == null || high == null) return "";
  return `\n80% CI: ${formatExact(low)} - ${formatExact(high)} GB300e`;
}

function showTooltip(event, region, mode) {
  if (!tooltip) return;
  const compact = formatExact(region[mode]);
  const ci = formatCI(region, mode);
  tooltip.innerHTML = `
    <h3>${region.name}</h3>
    <p class="tt-ci">Value: ${compact} GB300e (${modes[mode].label})</p>
    ${ci ? `<p class=\"tt-ci\">${ci.trim()}</p>` : ""}
  `;
  tooltip.style.display = "block";
  const x = Math.min(window.innerWidth - tooltip.offsetWidth - 12, event.clientX + 12);
  const y = Math.min(window.innerHeight - tooltip.offsetHeight - 12, event.clientY + 12);
  tooltip.style.left = `${Math.max(12, x)}px`;
  tooltip.style.top = `${Math.max(12, y)}px`;
}

function hideTooltip() {
  if (tooltip) tooltip.style.display = "none";
}

function trackTooltip(event) {
  if (!tooltip) return;
  tooltip.style.left = `${Math.min(window.innerWidth - tooltip.offsetWidth - 12, event.clientX + 12)}px`;
  tooltip.style.top = `${Math.min(window.innerHeight - tooltip.offsetHeight - 12, event.clientY + 12)}px`;
}

function draw() {
  const mode = select.value;
  hideTooltip();
  const width = Math.max(280, Math.round(chart.clientWidth || 628));
  const narrow = width < 520;
  const height = narrow ? Math.round(width * 0.82) : Math.min(390, Math.round(width * 0.59));
  const side = narrow ? 6 : 12;
  const top = narrow ? 52 : 34;
  const bottom = narrow ? 14 : 16;

  chart.innerHTML = "";
  const svg = svgEl("svg", {
    viewBox: `0 0 ${width} ${height}`,
    width: "100%",
    height,
    role: "img",
    "aria-label": `Regional AI compute at the end of 2026 in GB300-equivalents, ${modes[mode].label}. Bar heights use a linear scale.`,
  });
  chart.appendChild(svg);

  const projection = geoNaturalEarth1().fitExtent(
    [[side, top], [width - side, height - bottom]],
    { type: "Sphere" },
  );
  const path = geoPath(projection);

  svg.appendChild(svgEl("path", { class: "regional-sphere", d: path({ type: "Sphere" }) }));
  const map = svgEl("g");
  for (const country of countries) {
    const region = countryRegion.get(country.properties.id);
    const countryPath = svgEl("path", {
      class: region ? "regional-country included" : "regional-country",
      d: path(country),
      ...(region ? { style: `--regional-color:var(--region-${region})` } : {}),
    });
    if (region) {
      wireRegionTooltip(countryPath, regionLookup.get(region), mode);
    } else {
      wireOtherTooltip(countryPath);
    }
    map.appendChild(countryPath);
  }
  svg.appendChild(map);

  const maximum = Math.max(...data.regions.map(region => region[mode]));
  const maxHeight = narrow ? 68 : 112;
  const barWidth = narrow ? 7 : 10;
  const layout = narrow ? offsets.narrow : offsets.wide;

  for (const region of data.regions) {
    const group = svgEl("g", {
      class: "regional-mark",
      "aria-label": `${region.name}: ${formatExact(region[mode])} GB300-equivalents`,
      tabindex: "0",
    });
    const [x, y] = projection(region.coordinates);
    const barHeight = region[mode] / maximum * maxHeight;
    const barTop = y - barHeight;
    const [dx, dy] = layout[region.name];
    const labelX = x + dx;
    const labelY = Math.max(12, barTop + dy);
    const anchor = dx < 0 ? "end" : "start";
    const displayName = narrow
      ? region.short
      : region.name;

    const bar = svgEl("rect", {
      class: "regional-bar",
      style: `--regional-color:var(--region-${region.key})`,
      x: x - barWidth / 2,
      y: barTop,
      width: barWidth,
      height: Math.max(1, barHeight),
      rx: Math.min(1.5, barHeight / 2),
    });
    const title = svgEl("title");
    title.textContent = `${region.name}: ${formatExact(region[mode])} GB300e (${modes[mode].label})${formatCI(region, mode)}`;
    bar.appendChild(title);
    wireRegionTooltip(bar, region, mode);
    wireRegionTooltip(group, region, mode);
    group.appendChild(bar);

    group.appendChild(svgEl("path", {
      class: "regional-leader",
      style: `--regional-color:var(--region-${region.key})`,
      d: `M${x},${barTop - 1} L${labelX + (dx < 0 ? 3 : -3)},${labelY - 4}`,
    }));

    const label = svgEl("text", {
      class: "regional-label",
      x: labelX,
      y: labelY,
      "text-anchor": anchor,
      "aria-hidden": "true",
    });
    const name = svgEl("tspan", { class: "regional-name", x: labelX });
    name.textContent = displayName;
    label.appendChild(name);
    const value = svgEl("tspan", { class: "regional-value", x: labelX, dy: "1.05em" });
    value.textContent = formatCompact(region[mode]);
    label.appendChild(value);
    group.appendChild(label);
    svg.appendChild(group);
  }

  note.textContent = modes[mode].note;
  status.hidden = true;
}

select.addEventListener("change", draw);
window.addEventListener("resize", draw);
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", draw);
draw();
