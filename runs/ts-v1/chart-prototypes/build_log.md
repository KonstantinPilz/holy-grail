# Compute-over-time chart prototypes — build log

- **Status:** Data refresh built and validated locally; publication pending.
- **Target URL:** https://konstantinpilz.github.io/holy-grail/compute-over-time.html
- **Data pull:** Live appendix pulled 2026-08-20. Publication-safe aggregate regional shares, aggregate regional GB300e totals, and 2026 p10/p90 share endpoints only.
- **Source definitions:** Each year-end counts direct and legal deployment flows through Q3; smuggling counts full calendar years. The model excludes chips shipped in 2021 or earlier and does not retire chips.

## Data checkpoint

- China p50 share: 13.7987% (EOY 2023), 9.2929% (EOY 2024), 7.7753% (EOY 2025), 6.0523% (EOY 2026E).
- United States p50 share: 66.7823%, 72.3059%, 72.3810%, 74.0026%.
- World totals: 738,138; 2,576,111; 8,031,363; 20,309,710 GB300e.
- 2026E China 80% interval: 4.5145%–9.1394%.

## Design decisions

- Reused the site's Roboto typography, white/dark color variables, compact titles, teal for the United States, and red-orange for China. The page uses plain SVG and browser JavaScript, matching the existing site rather than adding a chart framework.
- Preserved all ten regions. Stacking order is USA, China, Europe, SE Asia, India, East Asia ex-China, Middle East, Latin America, Australia & NZ, Other.
- Used unrounded p50 values for geometry and one-decimal labels. Each p50 year sums to 100% without a second chart-side normalization.
- Isolated the USA in a small upper panel for the line variant because its 68–74% range would flatten the other nine series. All line-end labels are direct; there is no legend.
- Used the China 2026E p10/p90 share endpoints only in variant 2, as a compact 80% interval inside the callout.
- Plotted world totals as a dashed line at the top of the absolute stack and labeled all four totals: 0.7m, 2.6m, 8.0m, and 20.3m GB300e.
- Included the 2021-and-earlier scope caveat once at page level. Each chart repeats the unit, the through-Q3/full-year-smuggling convention, and required one-line source note.

## Validation

- `validate_compute_over_time.mjs` checks the noindex tag, required chart copy, absence of Google Sheet links/internal table labels/vendor detail, the full China series, China 2026 p10/p90, 100% share reconciliation, and absolute/world-total reconciliation.
- Browser QA rendered the page with no console or page errors. Four desktop screenshots and one mobile line-chart screenshot were captured.
- Visual inspection found no clipped titles, overlapping labels, missing series, or horizontal mobile overflow.

## Publication

- Initial page commit: `c5356d3` (`Add regional AI compute chart prototypes`).
- The 2026-08-20 model refresh is pending commit, push, and live verification.
- Live URL: https://konstantinpilz.github.io/holy-grail/compute-over-time.html
