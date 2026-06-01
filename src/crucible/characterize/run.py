"""Characterization runner (research-grounding §11) — the real-run driver.

Integration glue (coordinator-owned): calibration items → judge prompts → model
judgments (via the model adapters, sequential/deterministic serving) →
``JudgmentRecord``s → ``build_profile`` → ``JudgeProfile``; plus the known-groups
instrument check and the panel submodularity (ρ) analysis.

This module does the *judge-admission* run: each calibration item is a complete
grading task whose ``gold`` is the correct verdict (PASS/FAIL). A local model is
asked to grade; we compare its verdict to gold to profile it as a judge.

Usage:
    uv run python -m crucible.characterize.run --k 3 --out report.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from crucible.calibration.loader import load_items
from crucible.calibration.types import CalibrationCategory, CalibrationItem
from crucible.characterize import aggregate
from crucible.characterize.profile import build_profile
from crucible.characterize.types import JudgeProfile, JudgmentRecord, RoleSlot
from crucible.models.ollama_adapter import OllamaModel

_VERDICT_RE = re.compile(r"\b(PASS|FAIL)\b", re.IGNORECASE)

# Default local panel (cross-family) — already pulled on the Omen. (model_id, family, quant)
DEFAULT_PANEL: list[tuple[str, str, str | None]] = [
    ("qwen3.6:27b", "qwen", None),
    ("mistral-small:24b", "mistral", None),
    ("gemma4:31b", "gemma", None),
    ("aya-expanse:32b", "cohere", None),
    ("granite4.1:30b", "granite", None),
    ("devstral-small-2:24b", "mistral-devstral", None),
]


def parse_verdict(text: str) -> str | None:
    """Pull a PASS/FAIL verdict from raw model output (first occurrence)."""
    m = _VERDICT_RE.search(text or "")
    return m.group(1).upper() if m else None


async def run_model(
    model: OllamaModel, items: list[CalibrationItem], *, k: int = 3
) -> tuple[JudgeProfile, list[JudgmentRecord]]:
    """Run one model as a judge over the calibration items (k reruns for test-retest)."""
    records: list[JudgmentRecord] = []
    for item in items:
        for ri in range(k):
            rec = await model.judge_item(item.prompt, run_index=ri)
            gold_num = 1 if str(item.gold).upper() == "PASS" else 0
            parsed = parse_verdict(str(rec.predicted))
            if parsed == "PASS":
                pred_num = 1
            elif parsed == "FAIL":
                pred_num = 0
            else:
                pred_num = 1 - gold_num  # unparsed → always wrong, kept numeric for agreement
            rec.predicted = pred_num
            rec.gold = gold_num
            rec.correct = pred_num == gold_num
            rec.metadata["category"] = item.category.value
            rec.metadata["raw_verdict"] = parsed
            records.append(rec)
    profile = build_profile(model.model_id, RoleSlot.JUDGE, records, quant=model.quant)
    return profile, records


def _evict(model_id: str) -> None:
    """Free VRAM after a model's run (keep_alive=0 unloads it)."""
    try:
        import httpx

        httpx.post(
            "http://localhost:11434/api/generate",
            json={"model": model_id, "keep_alive": 0},
            timeout=30,
        )
    except Exception:
        pass


async def run_panel(
    panel: list[tuple[str, str, str | None]],
    items: list[CalibrationItem],
    *,
    k: int = 3,
) -> tuple[dict[str, JudgeProfile], dict[str, list[JudgmentRecord]]]:
    """Sequential load → judge → evict across the panel (VRAM-respecting, §11.2)."""
    os.environ.setdefault("OLLAMA_NUM_PARALLEL", "1")
    os.environ.setdefault("OLLAMA_MAX_LOADED_MODELS", "1")
    profiles: dict[str, JudgeProfile] = {}
    records: dict[str, list[JudgmentRecord]] = {}
    for model_id, family, quant in panel:
        model = OllamaModel(model_id=model_id, family=family, quant=quant)
        t0 = time.monotonic()
        try:
            profile, recs = await run_model(model, items, k=k)
        except Exception as exc:  # noqa: BLE001 — one bad model must not sink the panel
            print(f"[{model_id}] ERROR: {exc!r}")
            _evict(model_id)
            continue
        elapsed = time.monotonic() - t0
        profiles[model_id] = profile
        records[model_id] = recs
        print(
            f"[{model_id}] {profile.seat_decision.value}  "
            f"acc={profile.objective_accuracy}  consistency={profile.consistency}  ({elapsed:.0f}s)"
        )
        _evict(model_id)
    return profiles, records


def known_groups_report(
    items: list[CalibrationItem], records: dict[str, list[JudgmentRecord]]
) -> dict[str, Any]:
    """Instrument validation: on KNOWN_TRIVIAL items every model should be correct;
    a miss is an instrument/model-fault flag (§11.3)."""
    trivial_ids = {i.id for i in items if i.category == CalibrationCategory.KNOWN_TRIVIAL}
    flags: list[str] = []
    for model_id, recs in records.items():
        misses = {r.item_id for r in recs if r.item_id in trivial_ids and not r.correct}
        if misses:
            flags.append(f"{model_id} missed trivial items: {sorted(misses)}")
    return {"trivial_item_count": len(trivial_ids), "violations": flags, "passed": not flags}


def panel_correlation_report(
    records: dict[str, list[JudgmentRecord]],
) -> dict[str, Any]:
    """ρ<0.25 submodularity analysis over per-item error vectors (§11.4)."""
    # error vector per model: item_id -> (1 if wrong else 0), aggregated over reruns
    err: dict[str, dict[str, int]] = {}
    for model_id, recs in records.items():
        by_item: dict[str, list[bool]] = {}
        for r in recs:
            by_item.setdefault(r.item_id, []).append(bool(r.correct))
        err[model_id] = {iid: 0 if (sum(v) / len(v)) >= 0.5 else 1 for iid, v in by_item.items()}
    try:
        corr = aggregate.pairwise_error_correlation(err)
        ok = aggregate.passes_submodularity(corr)
        flat = {f"{a}|{b}": c for (a, b), c in corr.items()}
        return {"pairwise_error_correlation": flat, "submodular": ok}
    except Exception as exc:  # noqa: BLE001
        return {"error": repr(exc)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Crucible judge-admission characterization run.")
    ap.add_argument("--items", type=Path, default=None, help="items file/dir")
    ap.add_argument("--k", type=int, default=3, help="reruns per item (test-retest)")
    ap.add_argument("--models", nargs="*", default=None, help="model_id@family specs")
    ap.add_argument("--out", type=Path, default=Path("characterization-report.json"))
    args = ap.parse_args(argv)

    items = load_items(args.items) if args.items else _load_admission_items()
    panel = _parse_models(args.models) if args.models else DEFAULT_PANEL

    profiles, records = asyncio.run(run_panel(panel, items, k=args.k))

    report = {
        "n_items": len(items),
        "k": args.k,
        "profiles": {m: asdict(p) for m, p in profiles.items()},
        "known_groups": known_groups_report(items, records),
        "panel_correlation": panel_correlation_report(records),
    }
    args.out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\nseated: {[m for m, p in profiles.items() if p.seat_decision.value == 'seat']}")
    print(f"report -> {args.out}")
    return 0


def _parse_models(specs: list[str]) -> list[tuple[str, str, str | None]]:
    """Parse ``model_id@family`` specs. The model_id itself may contain a ':'
    (e.g. ``qwen3.6:27b``), so split on the LAST '@' only."""
    out: list[tuple[str, str, str | None]] = []
    for s in specs:
        if "@" in s:
            mid, fam = s.rsplit("@", 1)
            out.append((mid, fam, None))
        else:
            out.append((s, "unknown", None))
    return out


def _load_admission_items() -> list[CalibrationItem]:
    """Load the bundled judge-admission set (a single JSON file of complete grading tasks)."""
    path = Path(__file__).parent.parent / "calibration" / "admission_set.json"
    return load_items(path)


if __name__ == "__main__":
    raise SystemExit(main())
