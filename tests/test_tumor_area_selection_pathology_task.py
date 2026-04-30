from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import tifffile


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = REPO_ROOT / "scripts" / "tumor_area_selection_pathology"
sys.path.insert(0, str(SCRIPT_DIR))

import aggregate_metric  # noqa: E402
import harbor_evaluator  # noqa: E402


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_rgb_tiff(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tifffile.imwrite(path, array.astype(np.uint8))


def _make_tcga_row(task_id: str = "tcga_slide_0001") -> dict:
    return {
        "task_name": task_id,
        "task_id": task_id,
        "subset": "tcga",
        "source_file_id": "fake-tcga-file",
        "source_label_name": "Primary Tumor",
        "contains_tumor": True,
        "download_url": "https://example.invalid/fake.svs",
        "tile_size": 256,
        "analysis_downsample": 16,
    }


def _make_camelyon_row(image_path: Path, mask_path: Path, task_id: str = "camelyon_slide_0001") -> dict:
    return {
        "task_name": task_id,
        "task_id": task_id,
        "subset": "camelyon16",
        "source_slide_name": "tumor_test_001",
        "contains_tumor": True,
        "image_url": image_path.as_posix(),
        "mask_url": mask_path.as_posix(),
        "annotation_url": "file:///tmp/unused.xml",
        "tile_size": 4,
        "analysis_downsample": 1,
        "tumor_threshold": 0.2,
    }


def test_generate_harbor_tasks_materializes_expected_layout(tmp_path: Path) -> None:
    tcga_manifest = tmp_path / "tcga_manifest.json"
    cam_manifest = tmp_path / "cam_manifest.json"
    output_root = tmp_path / "tasks" / "tumor_area_selection_pathology"

    image = np.zeros((8, 8, 3), dtype=np.uint8)
    image[:4, :4, :] = 220
    mask = np.ones((8, 8), dtype=np.uint8)
    mask[:4, :4] = 2
    image_path = tmp_path / "camelyon_slide.tif"
    mask_path = tmp_path / "camelyon_mask.tif"
    _write_rgb_tiff(image_path, image)
    tifffile.imwrite(mask_path, mask)

    _write_json(tcga_manifest, [_make_tcga_row()])
    _write_json(cam_manifest, [_make_camelyon_row(image_path, mask_path)])

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "generate_harbor_tasks.py"),
            "--output-root",
            str(output_root),
            "--tcga-manifest",
            str(tcga_manifest),
            "--camelyon-manifest",
            str(cam_manifest),
        ],
        check=True,
    )

    tcga_task = output_root / "tcga_slide_0001"
    cam_task = output_root / "camelyon_slide_0001"
    for task_dir in (tcga_task, cam_task):
        assert (task_dir / "instruction.md").exists()
        assert (task_dir / "task.toml").exists()
        assert (task_dir / "environment" / "Dockerfile").exists()
        assert (task_dir / "environment" / "docker-compose.yaml").exists()
        assert (task_dir / "environment" / "entrypoint.sh").exists()
        assert (task_dir / "environment" / "workspace" / "benchmark_tasks.json").exists()
        assert (task_dir / "environment" / "workspace" / "submission.json").exists()
        assert (task_dir / "environment" / "workspace" / "scripts" / "primitives" / "get_tile.py").exists()
        assert (task_dir / "tests" / "verify_meta_task.py").exists()
        assert (task_dir / "tests" / "task_answer_key.json").exists()

    docker_compose = (tcga_task / "environment" / "docker-compose.yaml").read_text(encoding="utf-8")
    assert "MEDCLI_TUMOR_PATH_TCGA_CACHE" in docker_compose
    assert "MEDCLI_TUMOR_PATH_CAMELYON_CACHE" in docker_compose
    assert "MEDCLI_TUMOR_PATH_GIGAPATH_CACHE" in docker_compose

    tcga_submission = json.loads(
        (tcga_task / "environment" / "workspace" / "submission.json").read_text(encoding="utf-8")
    )
    assert tcga_submission == [
        {
            "task_id": "tcga_slide_0001",
            "instruction": tcga_submission[0]["instruction"],
            "contains_tumor": False,
            "predicted_tumor_tiles": [],
        }
    ]

    cam_answer_key = json.loads(
        (cam_task / "tests" / "task_answer_key.json").read_text(encoding="utf-8")
    )
    assert cam_answer_key[0]["expected_tumor_tiles"] == [{"x": 0, "y": 0}]


def test_harbor_evaluator_scores_tcga_and_camelyon() -> None:
    tcga_summary = harbor_evaluator.evaluate_submission_rows(
        [
            {
                "task_id": "tcga_slide_0001",
                "contains_tumor": True,
                "predicted_tumor_tiles": [],
            }
        ],
        [
            {
                "task_id": "tcga_slide_0001",
                "subset": "tcga",
                "expected_contains_tumor": True,
                "expected_tumor_tiles": [],
            }
        ],
    )
    assert tcga_summary["results"][0]["reward"] == 1.0
    assert tcga_summary["results"][0]["tp"] == 1

    cam_summary = harbor_evaluator.evaluate_submission_rows(
        [
            {
                "task_id": "camelyon_slide_0001",
                "contains_tumor": True,
                "predicted_tumor_tiles": [{"x": 0, "y": 0}, {"x": 1, "y": 0}],
            }
        ],
        [
            {
                "task_id": "camelyon_slide_0001",
                "subset": "camelyon16",
                "expected_contains_tumor": True,
                "expected_tumor_tiles": [{"x": 0, "y": 0}],
            }
        ],
    )
    row = cam_summary["results"][0]
    assert row["tp"] == 1
    assert row["fp"] == 1
    assert row["fn"] == 0
    assert row["tile_precision"] == 0.5
    assert row["tile_recall"] == 1.0


def test_verify_meta_task_uses_precomputed_camelyon_tiles(tmp_path: Path) -> None:
    slide_dir = tmp_path / "slide_current"
    slide_dir.mkdir(parents=True)
    image = np.zeros((8, 8, 3), dtype=np.uint8)
    image[:4, :4, :] = 200
    _write_rgb_tiff(slide_dir / "slide.tif", image)

    submission = [
        {
            "task_id": "camelyon_slide_0001",
            "instruction": "predict tumor tiles",
            "contains_tumor": True,
            "predicted_tumor_tiles": [{"x": 0, "y": 0}, {"x": 1, "y": 0}],
        }
    ]
    answer_key = [
        {
            "task_id": "camelyon_slide_0001",
            "subset": "camelyon16",
            "expected_contains_tumor": True,
            "expected_tumor_tiles": [{"x": 0, "y": 0}],
            "tile_size": 4,
            "analysis_downsample": 1,
            "tumor_threshold": 0.2,
            "source_slide_name": "tumor_test_001",
            "mask_path": str((slide_dir / "mask.tif").resolve()),
        }
    ]

    submission_path = tmp_path / "submission.json"
    answer_key_path = tmp_path / "task_answer_key.json"
    reward_file = tmp_path / "logs" / "reward.txt"
    reward_json = tmp_path / "logs" / "reward.json"
    results_json = tmp_path / "logs" / "meta_results.json"
    error_file = tmp_path / "logs" / "error_analysis.json"
    _write_json(submission_path, submission)
    _write_json(answer_key_path, answer_key)
    tifffile.imwrite(slide_dir / "mask.tif", np.array([[2] * 4 + [1] * 4] * 4 + [[1] * 8] * 4, dtype=np.uint8))

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "verify_meta_task.py"),
            "--submission",
            str(submission_path),
            "--answer-key",
            str(answer_key_path),
            "--reward-file",
            str(reward_file),
            "--reward-json",
            str(reward_json),
            "--results-json",
            str(results_json),
            "--error-analysis-file",
            str(error_file),
            "--slide-path",
            str(slide_dir),
        ],
        check=True,
    )

    reward_payload = json.loads(reward_json.read_text(encoding="utf-8"))
    assert reward_payload["cam_tp"] == 1
    assert reward_payload["cam_fp"] == 1
    assert reward_payload["cam_fn"] == 0
    assert reward_payload["cam_tumor_coverage"] == 1.0
    assert not reward_file.exists()

    results_payload = json.loads(results_json.read_text(encoding="utf-8"))
    row = results_payload["summary"]["results"][0]
    assert row["tumor_coverage"] == 1.0


def test_aggregate_metric_reports_subset_scores(tmp_path: Path) -> None:
    rewards_path = tmp_path / "rewards.jsonl"
    rewards_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "reward": 1.0,
                        "tcga_tp": 1,
                        "tcga_fp": 0,
                        "tcga_fn": 0,
                        "tcga_tn": 0,
                        "cam_tp": 0,
                        "cam_fp": 0,
                        "cam_fn": 0,
                    }
                ),
                json.dumps(
                    {
                        "reward": 0.5,
                        "tcga_tp": 0,
                        "tcga_fp": 0,
                        "tcga_fn": 0,
                        "tcga_tn": 0,
                        "cam_tp": 1,
                        "cam_fp": 1,
                        "cam_fn": 0,
                        "cam_tumor_coverage": 0.75,
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "metric.json"
    aggregate_metric.main(rewards_path, output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["tcga_slide_f1"] == 1.0
    assert payload["camelyon_tile_precision"] == 0.5
    assert payload["camelyon_tile_recall"] == 1.0
    assert payload["camelyon_tumor_coverage"] == 0.75


def test_gigapath_topk_falls_back_without_hf_token(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    slide_dir = tmp_path / "slide_current"
    workspace.mkdir(parents=True)
    slide_dir.mkdir(parents=True)

    image = np.zeros((8, 8, 3), dtype=np.uint8)
    image[:4, :4, 0] = 180
    image[:4, :4, 2] = 180
    image[:4, :4, 1] = 80
    _write_rgb_tiff(slide_dir / "slide.tif", image)
    _write_json(
        workspace / "benchmark_tasks.json",
        [
            {
                "task_id": "camelyon_slide_0001",
                "subset": "camelyon16",
                "instruction": "predict tumor tiles",
                "analysis_tile_size": 4,
                "analysis_downsample": 1,
                "tumor_threshold": 0.2,
            }
        ],
    )
    _write_json(
        slide_dir / "manifest.json",
        {
            "task_id": "camelyon_slide_0001",
            "subset": "camelyon16",
            "tile_size": 4,
            "analysis_downsample": 1,
            "slide_path": "/data/slide/current/slide.tif",
        },
    )

    spec = importlib.util.spec_from_file_location(
        "pathology_common_test",
        SCRIPT_DIR / "runtime" / "lib" / "pathology_common.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    monkeypatch.setattr(module, "WORKSPACE", workspace)
    monkeypatch.setattr(module, "SLIDE_DIR", slide_dir)
    monkeypatch.setattr(module, "TOOL_OUTPUT_DIR", workspace / "tool_outputs")
    monkeypatch.delenv("HF_TOKEN", raising=False)

    for fn_name in (
        "_open_benchmark_payload",
        "current_task",
        "runtime_manifest",
        "_materialized_slide_file",
        "slide_dimensions",
        "slide_extension",
        "analysis_config",
        "grid_shape",
        "read_thumbnail",
        "_cached_tissue_mask",
    ):
        getattr(module, fn_name).cache_clear()

    payload = module.topk_attention_tiles(k=2, max_tiles=16)
    assert payload["backend"] == "heuristic_fallback"
    assert len(payload["tiles"]) <= 2


def test_runtime_self_heals_missing_slide_dir_from_task_manifest(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    slide_dir = tmp_path / "slide_current"
    cache_dir = tmp_path / "cache" / "camelyon16" / "slides"
    workspace.mkdir(parents=True)
    slide_dir.mkdir(parents=True)
    cache_dir.mkdir(parents=True)

    image = np.zeros((8, 8, 3), dtype=np.uint8)
    image[:4, :4, :] = 180
    cached_slide = cache_dir / "tumor_test_001.tif"
    _write_rgb_tiff(cached_slide, image)

    _write_json(
        workspace / "benchmark_tasks.json",
        [
            {
                "task_id": "camelyon_slide_0001",
                "subset": "camelyon16",
                "instruction": "predict tumor tiles",
                "analysis_tile_size": 4,
                "analysis_downsample": 1,
                "tumor_threshold": 0.2,
            }
        ],
    )
    task_manifest_path = tmp_path / "task_manifest.json"
    _write_json(
        task_manifest_path,
        {
            "task_id": "camelyon_slide_0001",
            "subset": "camelyon16",
            "tile_size": 4,
            "analysis_downsample": 1,
            "download_url": "https://example.invalid/tumor_test_001.tif",
            "slide_extension": ".tif",
            "source_slide_name": "tumor_test_001",
        },
    )

    spec = importlib.util.spec_from_file_location(
        "pathology_common_self_heal_test",
        SCRIPT_DIR / "runtime" / "lib" / "pathology_common.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    monkeypatch.setattr(module, "WORKSPACE", workspace)
    monkeypatch.setattr(module, "SLIDE_DIR", slide_dir)
    monkeypatch.setattr(module, "TOOL_OUTPUT_DIR", workspace / "tool_outputs")
    monkeypatch.setattr(module, "TASK_MANIFEST_PATH", task_manifest_path)
    monkeypatch.setattr(module, "CAMELYON_CACHE_DIR", cache_dir)

    for fn_name in (
        "_open_benchmark_payload",
        "current_task",
        "task_manifest",
        "runtime_manifest",
        "_materialized_slide_file",
        "slide_dimensions",
        "slide_extension",
        "analysis_config",
        "grid_shape",
        "read_thumbnail",
        "_cached_tissue_mask",
    ):
        getattr(module, fn_name).cache_clear()

    manifest = module.runtime_manifest()
    slide_file = module._materialized_slide_file()

    assert manifest["task_id"] == "camelyon_slide_0001"
    assert slide_file.name == "slide.tif"
    assert slide_file.is_symlink()
    assert slide_file.resolve() == cached_slide.resolve()
    assert (slide_dir / "manifest.json").exists()


def test_generated_camelyon_tasks_all_have_positive_gold_tiles() -> None:
    answer_keys = sorted(
        (REPO_ROOT / "tasks" / "tumor_area_selection_pathology").glob(
            "camelyon_slide_*/tests/task_answer_key.json"
        )
    )
    assert len(answer_keys) == 10
    counts = []
    for path in answer_keys:
        payload = json.loads(path.read_text(encoding="utf-8"))
        counts.append((path.parent.parent.parent.name, len(payload[0]["expected_tumor_tiles"])))
    assert all(count > 0 for _task_id, count in counts), counts
