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
  "1d. Centered ribbons",
  "1e. Circle grid",
  "Final candidate: 1e (consolidated)",
  "1f. Narrow bars with connectors (consolidated)",
  "Bar height uses one common scale for consolidated regional share",
  "Every bar is labeled; faint lines connect adjacent bar tops and bottoms.",
  "Shares below 2.5% use a two-unit minimum display height for visibility.",
  "Circle area is proportional to consolidated regional share",
  "Other combines East Asia ex-China (1.8%), India (1.5%), Australia &amp; NZ (0.7%), the prior Other category (0.7%), and Latin America (0.6%).",
  "Unrounded 2026E shares sum to 5.2%; the displayed component shares sum to approximately 5.3% because of rounding.",
  "Rest = SE Asia, India, East Asia ex-China, Middle East, Latin America, Australia &amp; NZ, and Other.",
  "Rows are centered independently and no longer visually sum to 100%.",
  "Circle area is proportional to regional share",
  "Circle area uses one common scale; the USA therefore dominates the visual, and no region-specific rescaling is applied.",
  "China's 2026 compute by origin",
  "The smuggled share is the most uncertain component; 80% interval roughly 35–68% of China's stock.",
  "Chips deployed by EOY 2026; production through Q3, smuggling full-year.",
  "🇺🇸",
  "🇨🇳",
  "🇪🇺",
  "🇲🇾🇸🇬",
  "🇮🇳",
  "🇯🇵🇰🇷🇹🇼",
  "🇦🇺🇳🇿",
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
  'id="chart-1d"',
  'id="chart-1e"',
  'id="chart-final-1e"',
  'id="chart-final-1f"',
  'id="chart-origin"',
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

const originMatch = html.match(/const CHINA_ORIGIN = (\{[\s\S]*?\n\s*\});\n\s*const DATA/);
if (!originMatch) throw new Error("Could not locate embedded China-origin aggregate literal");
const origin = vm.runInNewContext(`(${originMatch[1]})`);
const componentTotal = origin.components.reduce((sum, component) => sum + component.value, 0);
if (Math.abs(componentTotal - origin.total) > 1e-6) throw new Error("China-origin components do not reconcile");
if (origin.total !== 1199574.007520285) throw new Error("Unexpected China-origin total");
if (origin.smuggling2026Flow80.p10 !== 167576.416 || origin.smuggling2026Flow80.p90 !== 742886.404) {
  throw new Error("Unexpected 2026 smuggling-flow interval");
}
if (origin.smugglingStock80.p10 !== 297795.416 || origin.smugglingStock80.p90 !== 1315608.404) {
  throw new Error("Unexpected cumulative smuggling interval");
}
if (origin.share80.p10 !== 34.93589687830025 || origin.share80.p90 !== 67.7747522990999) {
  throw new Error("Unexpected indicative smuggled-share interval");
}

const barFamilyIndex = html.indexOf("1. Stacked bars (variant 1 family — pick one)");
const finalCandidateIndex = html.indexOf("Final candidate: 1e (consolidated)");
const finalConnectorIndex = html.indexOf("1f. Narrow bars with connectors (consolidated)");
const variant1cIndex = html.indexOf("1c. Labeled columns");
const variant1dIndex = html.indexOf("1d. Centered ribbons");
const variant1eIndex = html.indexOf("1e. Circle grid");
const originIndex = html.indexOf("China's 2026 compute by origin");
const originalVariantIndex = html.indexOf("1. Epoch-style 100% stacked area");
if ([finalCandidateIndex, finalConnectorIndex, barFamilyIndex, variant1cIndex, variant1dIndex, variant1eIndex, originIndex, originalVariantIndex].some(index => index < 0)
    || !(finalCandidateIndex < finalConnectorIndex && finalConnectorIndex < barFamilyIndex && barFamilyIndex < variant1cIndex && variant1cIndex < variant1dIndex && variant1dIndex < variant1eIndex && variant1eIndex < originIndex && originIndex < originalVariantIndex)) {
  throw new Error("The bar variants, China-origin figure, and original variants are out of order");
}
if (!html.includes("const BAR_LAYOUT = { width: 130, gap: 26 }")) {
  throw new Error("Expected a 20% inter-column gap in the shared bar layout");
}
if (!html.includes('opacity: .25')) {
  throw new Error("Expected quarter-opacity connector bands in variant 1b");
}
if (!html.includes("heightForShare = value => value / 100 * 44")) {
  throw new Error("Centered-ribbon height must use one linear share scale");
}
if (!html.includes("radiusForShare = value => Math.sqrt(value / 100) * 32.5")) {
  throw new Error("Circle radius must be the square root of share so area is proportional");
}
if ((html.match(/class="bar-prototype"/g) || []).length !== 5) {
  throw new Error("Expected five variants in the bar family");
}
if (!html.includes('const FINAL_OTHER_REGIONS = ["East Asia ex-China", "India", "Australia & NZ", "Other", "Latin America"]')) {
  throw new Error("Final Other grouping is missing or inconsistent");
}
if (!html.includes("const finalCenters = [150, 240, 330, 420]")) {
  throw new Error("Expected compact year spacing in the final candidate");
}
if (!html.includes("const finalRowGap = 45")) {
  throw new Error("Expected compact row spacing in the final candidate");
}
if (!html.includes('const FINAL_REGION_ORDER = ["USA", "Europe", "China", "SE Asia", "Middle East", "Other"]')) {
  throw new Error("The final circle grid order changed unexpectedly");
}
if (!html.includes('const FINAL_1F_REGION_ORDER = ["USA", "China", "Europe", "SE Asia", "Middle East", "Other"]')) {
  throw new Error("Variant 1f must place China above Europe");
}
if (!html.includes("const centers = [145, 195, 245, 295]")) {
  throw new Error("Variant 1f year columns must use the tightened spacing");
}
if (!html.includes("const narrowBarWidth = 14")) {
  throw new Error("Variant 1f bars must use the requested slim geometry");
}
if (!html.includes("const rowGap = 48")) {
  throw new Error("Variant 1f rows must leave enough vertical room for the taller scale");
}
if (!html.includes("const connectorOpacity = .24")) {
  throw new Error("Variant 1f connector lines must remain faint");
}
if (!html.includes("heightForShare = value => value / 100 * 80")) {
  throw new Error("Variant 1f bar height must use one common linear share scale");
}
if (!html.includes("const minVisibleHeight = 2")) {
  throw new Error("Variant 1f must keep the smallest regional bars clearly visible");
}
const variant1fFunction = html.slice(html.indexOf("function drawNarrowBarConnectors()"), html.indexOf("function drawCenteredRibbons()"));
if (!variant1fFunction.includes('svg.setAttribute("viewBox", "0 0 330 334")') || !variant1fFunction.includes("const rowStart = 74")) {
  throw new Error("Variant 1f must preserve clear space below the year headers");
}
if (variant1fFunction.includes('el("polygon"')) {
  throw new Error("Variant 1f must use connector lines rather than filled bands");
}
if (variant1fFunction.includes('class: "grid-line"')) {
  throw new Error("Variant 1f must not draw a center or row-axis line");
}
if (!variant1fFunction.includes("const top = centerY - height / 2") || !variant1fFunction.includes("const bottom = centerY + height / 2")) {
  throw new Error("Variant 1f bars must be vertically centered on each row axis");
}
if (!html.includes('`${value.toFixed(1)}%`, "cell-value", "middle"')) {
  throw new Error("Final variants must render one-decimal share labels");
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
