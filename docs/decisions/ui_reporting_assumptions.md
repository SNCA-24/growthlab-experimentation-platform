# UI and Reporting Assumptions

- The Streamlit app reads local scenario artifacts directly from `reports/demo/` when present, and otherwise falls back to the shared `reports/decision/` and `reports/validation/full_pack/` outputs.
- `scripts/build_demo_artifacts.py` assembles a compact demo bundle for the main scenarios and writes JSON, markdown, and CSV summaries for the UI download flow.
- The UI is intentionally read-only and does not recompute analysis, trust, or decision logic.
- The download panel exposes the compact exported summaries, not the raw canonical parquet data, to keep the demo fast on a 16 GB laptop.

