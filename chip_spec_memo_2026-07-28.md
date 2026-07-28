# Memory-bandwidth and FP4 specs for 2026–27 accelerators — research memo 2026-07-28

Written by a team of Konstantin's Claudes (four Sonnet research agents, Fable review; primary
sources spot-checked). Feeds TF_SPECS in sync_labs.py. Dense figures throughout; NVIDIA sparse
marketing numbers halved where noted.

| Chip | BW (TB/s) | Dense FP4 (TFLOP/s) | Status | Key source |
|---|---|---|---|---|
| TPU 8i ("Zebrafish") | 8.601 | 10,100 | Announced | [Google Cloud blog spec table](https://cloud.google.com/blog/products/compute/tpu-8t-and-tpu-8i-technical-deep-dive) |
| TPU 8t ("Sunfish") | 6.528 | 12,600 | Announced | same |
| TPU v9 ("Triggerfish") | ~13 (10–17 band) | ~30,000 | PROJECTION (~40% conf) | [Ming-Chi Kuo leak](https://www.thetechoutlook.com/news/innovation/google-tpu-v9-triggerfish-with-mediatek-tipped-hbm4e-memory-3x-sram-capacity-production-from-late-2027/); HBM4E scaling from 8i/8t |
| Trainium3 | 4.9 | 2,517 (MXFP4 at FP8 rate, not accelerated) | Announced | [AWS Trn3 GA](https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-ec2-trn3-ultraservers/); SemiAnalysis pin-speed cross-check |
| Trainium4 | 19.6 | 15,102 | Announced multipliers (4× BW, 6× FP4 vs Trn3), absolutes derived | [TheNextPlatform](https://www.nextplatform.com/2025/12/03/with-trainium4-aws-will-crank-up-everything-but-the-clocks/) |
| Inferentia v1 | 0.05 (DDR4) | — | Announced (retrospective) | [AWS Inferentia2 blog](https://aws.amazon.com/blogs/machine-learning/aws-inferentia2-builds-on-aws-inferentia1-by-delivering-4x-higher-throughput-and-10x-lower-latency/) |
| Rubin Ultra (per package; TrendForce counts packages) | 32 (4.6 PB/s ÷ 144) | 100,000 | Announced-derived | SemiAnalysis GTC 2025 (local); [Tom's Hardware GTC 2026 demo](https://www.tomshardware.com/pc-components/gpus/nvidia-demonstrates-rubin-ultra-tray-worlds-1st-ai-gpu-with-1tb-of-hbm4e) |
| MI455X (updates MI400/MI450 row) | 23.3 | 40,260 | Announced (supersedes 19.6/20,000) | [StorageReview, Jul 2026](https://www.storagereview.com/news/amd-mi455x-and-helios-432gb-hbm4-72-gpu-racks-and-a-real-answer-to-vera-rubin) |
| MI500 | ~35 (30–40) | ~77,000 (65–90k) | PROJECTION (~25–30% conf) | AMD CES 2026 arch-only disclosure; scaled from MI455X + HBM4E |
| Maia 200 | 7.0 | 10,000 ("over 10 PF") | Announced | [Microsoft blog](https://blogs.microsoft.com/blog/2026/01/26/maia-200-the-ai-accelerator-built-for-inference/) |
| Maia 300 | ~19.8 | — | PROJECTION (6× HBM4 stacks × Samsung ISSCC 3.3) | SemiAnalysis (2nm, late 2027, no specs) |
| MTIA 300 | 6.1 | 2,400 (projected 2× FP8) | Credible-reporting (two independent Meta-ratio derivations agree within 1%) | [Meta AI blog](https://ai.meta.com/blog/meta-mtia-scale-ai-chips-for-billions/) |
| MTIA 400 | 9.2 | 12,000 | Announced | same |
| MTIA 450 | 18.4 | 21,000 | Announced | same |
| MTIA 500 | 27.6 | 30,000 | Announced | same |
| Cambricon MLU blend | ~3.5 (3.0–4.0) | — | PROJECTION (60% MLU590 ~2.0 secondary-reported / 40% Siyuan 690 stack-count projection) | [TechBuzzChina](https://techbuzzchina.substack.com/p/cambricon-chinas-nvidiaor-nvidia); [TrendForce](https://www.trendforce.com/news/2025/12/15/insights-cambricon-remains-chinas-top-ai-chip-startup-rumored-2026-triple-output-faces-smic-limits/); rejected the widely-copied unsourced 192GB/2.4TB/s figure |

Notes: TPU gen-8 adds native FP4 (architectural change, announced). Google's table gives no dense/sparse
label, but TrendForce's pre-announcement FP8 ratios are almost exactly half the announced FP4 figures,
supporting the dense reading. Meta's MTIA percentage chain is three-way self-consistent. All projections
are flagged in the figure tooltips and carry `est: true` in TF_SPECS.
