from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from decisioning.actions.render import render_decision_markdown
from validation.trust._models import to_jsonable


def build_decision_payload(result: Any) -> dict[str, Any]:
    payload = to_jsonable(result)
    if isinstance(payload, dict):
        payload.setdefault("final_action", getattr(result, "final_action", None))
        payload.setdefault("decided_stage", getattr(result, "decided_stage", None))
    return payload


def write_decision_report(result: Any, output_dir: str | Path) -> dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_decision_payload(result)
    (out_dir / "decision_summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    (out_dir / "decision_summary.md").write_text(render_decision_markdown(payload), encoding="utf-8")
    return payload

