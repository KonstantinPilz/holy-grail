import fs from "node:fs";
import vm from "node:vm";

const pagePath = new URL("../../../docs/compute-over-time.html", import.meta.url);

if (!fs.existsSync(pagePath)) {
  throw new Error("compute-over-time.html has not been built yet");
}

const html = fs.readFileSync(pagePath, "utf8");
const requiredText = [
  '<meta name="robots" content="noindex, nofollow">',
  "1. Epoch-style 100% stacked area",
  "2. China-focus annotated",
  "3. Share lines",
  "4. Absolute stacked area",
  "TrendForce production aggregates, Epoch deployment data; our estimates",
  "through Q3 2026",
  "2021 and earlier",
  "export controls bind while the U.S. buildout compounds",
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

if (data.pulled !== "2026-08-20") throw new Error("Unexpected pull date");
if (data.years.join(",") !== "2023,2024,2025,2026") throw new Error("Unexpected year series");
if (data.shares.China.join(",") !== "12.679118927540745,8.605722942967235,6.872666069664385,5.613309372100744") {
  throw new Error("China p50 series does not match the live appendix pull");
}
if (data.intervals2026.China.p10 !== 4.302684020047999 || data.intervals2026.China.p90 !== 8.230865845634422) {
  throw new Error("China 2026 p10/p90 do not match the live appendix pull");
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
