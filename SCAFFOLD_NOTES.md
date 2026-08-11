# EOY-2026 forecast scaffold

The locked labs section now ends with an **EOY-2026 forecast** subsection. It
shows the five requested US developers in teal and the five requested Chinese
developers in red as horizontal density-fade rows. The main panel uses one
shared linear axis so the US–Chinese gap remains visible. A smaller **Chinese
developers (zoom)** panel repeats the five Chinese rows on its own linear axis.
Each row uses an 81-point two-piece-lognormal density, opacity gamma 0.6,
p10/p90 ticks, and a median label.

## Files

- `forecast2026_input.json` is the handoff input. It contains the real forecast
  percentiles and has `"test": false`.
- `build_forecast2026.py` validates the ten labs, fits their distributions, and
  encrypts the payload independently of `sync_labs.py`.
- `docs/forecast2026_data.js` is generated ciphertext. It uses the labs password
  and the same AES-256-GCM / PBKDF2-SHA256 (300,000 iterations) envelope as
  `docs/labs_data.js`.
- `docs/index.html` contains a small, delimited container, loader, and renderer.
  The forecast decrypts from the same password submission as the existing labs
  data.

## Rebuilding

1. Keep values positive and ordered `p10 < median < p90`. Keep the ten names and
   `us`/`cn` country tags exactly as scaffolded.
2. Use top-level `"test": false` for real data. Setting it to `true` restores
   the **TEST DATA** subtitle label and chart watermark on the next build.
3. Run:

   ```bash
   python3 build_forecast2026.py
   ```

The builder reads the same local password file as the labs sync:
`~/.config/us-ai-compute-labs.pw`. It writes only
`docs/forecast2026_data.js`; it does not import, invoke, or modify
`sync_labs.py`, and it performs no git operations.

The hourly labs sync explicitly stages only `docs/labs_data.js`, so these new
files are outside its data-change commit path.
