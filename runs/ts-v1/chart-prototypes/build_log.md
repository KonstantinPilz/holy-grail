# Compute-over-time chart prototypes — build log

- **Status:** Refreshed, published, and live-verified.
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
- Refresh commit: `949796f` (`Refresh regional compute prototype data`).
- Pushed to `main`; GitHub Pages serves the repository's `docs/` directory.
- The live page returned HTTP 200 and rendered four refreshed chart SVGs in headless Chromium with no browser errors on 2026-08-20.
- Live URL: https://konstantinpilz.github.io/holy-grail/compute-over-time.html

## Stacked-bar family (2026-08-20)

- Added three discrete treatments above the original four prototypes while preserving the embedded aggregate data and the original reference charts.
- Variant 1a uses four 130-pixel columns separated by 26 pixels, a gap equal to 20% of bar width, with direct 2026E labels for the United States, China, and Europe.
- Variant 1b uses the same columns and labels, with quarter-opacity regional bands spanning only the gaps between adjacent years.
- Variant 1c groups the seven smaller regions into a visual Rest segment and labels every displayed segment of at least 3%. The JavaScript data literal remains unpooled with all ten regions; the Rest membership is stated below the chart.
- Updated automated checks cover page order, the three bar chart containers, the shared gap ratio, connector opacity, Rest disclosure, and preservation of all ten source series.
- Headless Chromium rendered all seven charts without console or page errors, found no horizontal overflow at 390 pixels, and captured `variant-1a.png`, `variant-1b.png`, and `variant-1c.png` for QA.
- Published in commit `6ae962d` (`Add stacked bar chart prototypes`) and pushed to `main`.
- GitHub Pages updated on the fourth polling attempt. A fresh headless-Chromium render of the live URL produced three bar-family SVGs and four original-variant SVGs while preserving the noindex directive.

## Flags and China-origin figure (2026-08-20)

- Added native emoji flags beside region names in legends and direct labels. The mappings are United States 🇺🇸, China 🇨🇳, Europe 🇪🇺, SE Asia 🇲🇾🇸🇬, India 🇮🇳, East Asia ex-China 🇯🇵🇰🇷🇹🇼, and Australia & NZ 🇦🇺🇳🇿. Middle East, Latin America, Other, and Rest remain unflagged rather than implying a single country.
- Added a horizontal 100% composition figure immediately after the bar family. The embedded aggregate component values are domestic production 431,327.825 GB300e, legal Western imports 152,213.556, and smuggled Western chips 616,032.626, reconciling to 1,199,574.008 GB300e before display rounding.
- The internal hand-off table gives the cumulative smuggling component an indicative p10/p50/p90 of 297,795 / 616,033 / 1,315,608 GB300e and total China stock of 852,405 / 1,199,574 / 1,941,148. Same-tail indicative division gives 297,795 ÷ 852,405 = 34.94% and 1,315,608 ÷ 1,941,148 = 67.77%, displayed as roughly 35–68%.
- The chart also reports the separate 2026 smuggling-flow 80% interval of 167,576–742,886 GB300e. A whisker spans the indicative stock-share interval, and a dashed line ties its 51.4% median to the smuggled segment boundary.
- Browser QA rendered eight SVG charts with no console or page errors and no horizontal overflow at 390 pixels. Native color flags rendered correctly in both SVG labels and HTML legends. Saved `china-origin.png` and `flagged-variant-1a.png` for QA.
- Published in commit `137542e` (`Add flags and China compute origin chart`) and pushed to `main`.
- GitHub Pages updated on the fourth polling attempt. Live browser QA returned HTTP 200, rendered eight SVGs and fourteen flagged legend entries with zero console or page errors, and preserved the noindex directive.

## Centered-ribbon and circle-grid variants (2026-08-20)

- Added variants 1d and 1e after 1c, leaving the embedded data literal and every existing chart unchanged.
- Both new charts order rows by 2026E share: USA, Europe, China, SE Asia, Middle East, East Asia ex-China, India, Australia & NZ, Other, and Latin America.
- Variant 1d gives every region a separate 53-pixel row. Each annual block is centered on that row and uses one linear height scale (44 pixels per 100 share points); faint 18%-opacity connectors bridge only adjacent annual blocks. A right-hand value column reports the 2026E share.
- Variant 1e uses a single radius formula, `sqrt(share / 100) × 32.5`, so circle area is proportional to share across every region and year. It labels cells at or above 1% and states that the USA dominates because no regional rescaling is applied.
- Browser QA rendered all ten SVG charts without console or page errors, found no horizontal overflow at 390 pixels, and captured `variant-1d.png` and `variant-1e.png`. Visual inspection found no clipped labels, overlaps, or misleading rescaling.
- Published in commit `2cd9bca` (`Add centered ribbon and circle grid variants`) and pushed to `main`.
- GitHub Pages updated on the fifth polling attempt. Live browser QA returned HTTP 200, rendered ten SVGs including five bar-family variants with zero console or page errors, and preserved the noindex directive.
