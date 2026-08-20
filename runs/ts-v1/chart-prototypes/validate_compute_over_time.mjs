import fs from "node:fs";
import vm from "node:vm";

const pagePath = new URL("../../../docs/compute-over-time.html", import.meta.url);

if (!fs.existsSync(pagePath)) {
  throw new Error("compute-over-time.html has not been built yet");
}

const html = fs.readFileSync(pagePath, "utf8");
const requiredText = [
  '<meta name="robots" content="noindex, nofollow">',
  "1. Stacked bars (variant 1 family — pick one)",
  "1a. Plain 100% stacked columns",
  "1b. Stacked columns with connectors",
  "1c. Labeled columns",
  "Rest = SE Asia, India, East Asia ex-China, Middle East, Latin America, Australia &amp; NZ, and Other.",
  "1. Epoch-style 100% stacked area",
  "2. China-focus annotated",
  "3. Share lines",
  "4. Absolute stacked area",
  "TrendForce production aggregates, Epoch deployment data; our estimates",
  "Each year-end includes direct and legal deployment flows through Q3; smuggling counts full calendar years.",
  "2021 and earlier",
  "China: 13.8% → 6.1%",
  "export controls bind while the U.S. buildout compounds",
  'id="chart-1a"',
  'id="chart-1b"',
  'id="chart-1c"',
  'id="chart-1"',
  'id="chart-2"',
  'id="chart-3"',
  'id="chart-4"',
];

for (const text of requiredText) {
  if (!html.includes(text)) throw new Error(`Missing required text: ${text}`);
}

const forbidden = [
  /docs\.google\.com/i,
  /spreadsheets/i,
  /Table S[13]/i,
  /Def-[0-9]/i,
  /\b(?:NVIDIA|AMD|Huawei|Cambricon|Google TPU|Trainium)\b/i,
];
for (const pattern of forbidden) {
  if (pattern.test(html)) throw new Error(`Forbidden public-page content: ${pattern}`);
}

const match = html.match(/const DATA = (\{[\s\S]*?\n\s*\});\n\s*const REGION_ORDER/);
if (!match) throw new Error("Could not locate embedded DATA literal");
const data = vm.runInNewContext(`(${match[1]})`);

const barFamilyIndex = html.indexOf("1. Stacked bars (variant 1 family — pick one)");
const originalVariantIndex = html.indexOf("1. Epoch-style 100% stacked area");
if (barFamilyIndex < 0 || originalVariantIndex < 0 || barFamilyIndex >= originalVariantIndex) {
  throw new Error("The stacked-bar family must appear before the original variants");
}
if (!html.includes("const BAR_LAYOUT = { width: 130, gap: 26 }")) {
  throw new Error("Expected a 20% inter-column gap in the shared bar layout");
}
if (!html.includes('opacity: .25')) {
  throw new Error("Expected quarter-opacity connector bands in variant 1b");
}
if (Object.hasOwn(data.shares, "Rest")) {
  throw new Error("Rest must be a visual grouping, not an embedded data series");
}
if (Object.keys(data.shares).length !== 10) {
  throw new Error("Expected all ten underlying regional share series");
}

if (data.pulled !== "2026-08-20") throw new Error("Unexpected pull date");
if (data.years.join(",") !== "2023,2024,2025,2026") throw new Error("Unexpected year series");
if (data.shares.China.join(",") !== "13.798683161420586,9.29293670542866,7.775300663131625,6.052330939014623") {
  throw new Error("China p50 series does not match the live appendix pull");
}
if (data.intervals2026.China.p10 !== 4.514527377413835 || data.intervals2026.China.p90 !== 9.1393861199388) {
  throw new Error("China 2026 p10/p90 do not match the live appendix pull");
}
if (data.shares.USA[3] !== 74.00261980094427) throw new Error("USA 2026 p50 does not match the live appendix pull");
if (data.worldTotals.join(",") !== "738138.4128240641,2576111.379378585,8031363.021967141,20309710.30081132") {
  throw new Error("World totals do not match the live appendix pull");
}

for (let i = 0; i < data.years.length; i += 1) {
  const shareTotal = Object.values(data.shares).reduce((sum, series) => sum + series[i], 0);
  if (Math.abs(shareTotal - 100) > 1e-9) throw new Error(`Shares do not sum to 100 in ${data.years[i]}`);
  const absoluteTotal = Object.values(data.absolute).reduce((sum, series) => sum + series[i], 0);
  if (Math.round(absoluteTotal) !== Math.round(data.worldTotals[i])) {
    throw new Error(`Absolute values do not reconcile in ${data.years[i]}`);
  }
}

console.log("compute-over-time validation passed");
