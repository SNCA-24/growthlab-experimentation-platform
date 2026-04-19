from __future__ import annotations

from typing import Any

import json
from pathlib import Path
import streamlit as st


def _read_text(path) -> str:
    return path.read_text(encoding="utf-8") if path and path.exists() else ""


def _mime_for_path(path: Path) -> str:
    if path.suffix.lower() == ".json":
        return "application/json"
    if path.suffix.lower() == ".csv":
        return "text/csv"
    if path.suffix.lower() in {".md", ".txt"}:
        return "text/markdown"
    return "application/octet-stream"


def render_downloads_page(context: dict[str, Any]) -> None:
    st.subheader("Downloads")
    paths = context.get("paths", {})

    for label, key in [
        ("Decision JSON", "decision_json"),
        ("Decision Markdown", "decision_md"),
        ("Validation JSON", "validation_json"),
        ("Trust JSON", "trust_json"),
        ("Analysis JSON", "analysis_json"),
        ("Decision CSV", "decision_csv"),
        ("Guardrail CSV", "guardrail_csv"),
        ("Segment CSV", "segment_csv"),
    ]:
        path = paths.get(key)
        if path and path.exists():
            data = path.read_bytes()
            st.download_button(label=label, data=data, file_name=path.name, mime=_mime_for_path(path))

    if context.get("decision"):
        st.download_button(
            label="Compact decision payload",
            data=json.dumps(context["decision"], indent=2, sort_keys=True, default=str),
            file_name="decision_summary.json",
            mime="application/json",
        )
