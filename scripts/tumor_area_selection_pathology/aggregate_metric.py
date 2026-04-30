# /// script
# requires-python = ">=3.10"
# ///
"""Aggregate benchmark metrics across tumor_area_selection_pathology trials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_rewards(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


def _f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0


def main(input_path: Path, output_path: Path) -> None:
    rewards = _load_rewards(input_path)
    tcga_tp = sum(int(r.get("tcga_tp", 0)) for r in rewards)
    tcga_fp = sum(int(r.get("tcga_fp", 0)) for r in rewards)
    tcga_fn = sum(int(r.get("tcga_fn", 0)) for r in rewards)
    tcga_tn = sum(int(r.get("tcga_tn", 0)) for r in rewards)

    cam_tp = sum(int(r.get("cam_tp", 0)) for r in rewards)
    cam_fp = sum(int(r.get("cam_fp", 0)) for r in rewards)
    cam_fn = sum(int(r.get("cam_fn", 0)) for r in rewards)
    cam_coverage_sum = sum(float(r.get("cam_tumor_coverage", 0.0)) for r in rewards)
    cam_coverage_count = sum(1 for r in rewards if "cam_tumor_coverage" in r)

    tcga_precision = _safe_div(tcga_tp, tcga_tp + tcga_fp)
    tcga_recall = _safe_div(tcga_tp, tcga_tp + tcga_fn)
    cam_precision = _safe_div(cam_tp, cam_tp + cam_fp)
    cam_recall = _safe_div(cam_tp, cam_tp + cam_fn)

    result = {
        "num_trials": len(rewards),
        "tcga_slide_precision": round(tcga_precision, 4),
        "tcga_slide_recall": round(tcga_recall, 4),
        "tcga_slide_f1": round(_f1(tcga_precision, tcga_recall), 4),
        "tcga_slide_accuracy": round(
            _safe_div(tcga_tp + tcga_tn, tcga_tp + tcga_fp + tcga_fn + tcga_tn), 4
        ),
        "camelyon_tile_precision": round(cam_precision, 4),
        "camelyon_tile_recall": round(cam_recall, 4),
        "camelyon_tile_f1": round(_f1(cam_precision, cam_recall), 4),
        "camelyon_tumor_coverage": round(
            _safe_div(cam_coverage_sum, cam_coverage_count), 4
        ),
    }
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", dest="input_path", type=Path, required=True)
    parser.add_argument("-o", "--output", dest="output_path", type=Path, required=True)
    args = parser.parse_args()
    main(args.input_path, args.output_path)
