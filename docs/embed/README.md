# Embeddable figure: US AI chip owners (GB300e)

Self-contained interactive figure. **Public data only** — Epoch AI's
[Data on AI Chip Owners](https://epoch.ai/data/ai-chip-owners) (CC BY 4.0),
converted to GB300-equivalents. No external requests, no dependencies, no build step.

## Option A — iframe (recommended for testing)

```html
<iframe src="https://konstantinpilz.github.io/holy-grail/embed/ai-chip-owners.html"
        title="US AI chip owners, end of 2025"
        width="100%" height="470" style="border:0" scrolling="no" loading="lazy"></iframe>
```

The figure posts its height to the parent whenever it renders or resizes, so the
iframe can size itself:

```html
<script>
window.addEventListener("message", function (e) {
  if (e.data && e.data.type === "hg-figure-height") {
    document.querySelector("iframe[title='US AI chip owners, end of 2025']").height = e.data.height;
  }
});
</script>
```

Working example: `host-test.html` in this directory.

## Option B — inline

Paste the contents of `ai-chip-owners.snippet.html` (style + markup + script) directly
into a page. All CSS is scoped under `.hg-fig`, all element ids are `hg-`-prefixed, and
the JavaScript runs in an IIFE with no globals.

## Notes for integrators

- **Theming**: follows `prefers-color-scheme` by default. To force a mode, set
  `data-theme="light"` or `data-theme="dark"` on the `.hg-fig` element.
- **Responsive**: re-renders on container resize (ResizeObserver); usable down to ~320px.
- **Interaction**: the dropdown switches the conversion metric (FP8 / FP4 / memory
  bandwidth); hovering or tapping a bar opens a chip-level tooltip.
- **The bars are distributions, not error bars.** Color intensity is the probability
  density from a 20,000-draw Monte Carlo over Epoch's published unit percentiles; the
  printed number is the median. xAI renders as a tick because Epoch publishes a point
  estimate only.
- **Attribution is required** by CC BY 4.0 and is built into the figure's footer —
  please keep it.

Regenerate after new Epoch data: `./make_embed.py` (reads `docs/data.js`).
