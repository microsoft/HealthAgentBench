"""Shared CheXbert labeler used by verify_meta_task.py (per-trial labeling).

f1chexbert loads a BERT classifier that assigns each radiology report a 14-dim
label vector over CheXpert pathologies (13 observations + "No Finding"). We
call it once per (prediction, reference) pair inside the verifier so that the
aggregator only needs to stack vectors and run sklearn — no BERT in the
aggregator, no filesystem walks, no Harbor temp-dir surprises.

The weights are downloaded from HuggingFace on first use. To keep task
containers warm, the Dockerfile pre-populates the cache at build time.
"""

from __future__ import annotations

import os
from pathlib import Path

CHEXBERT_LABELS: tuple[str, ...] = (
    "Enlarged Cardiomediastinum",
    "Cardiomegaly",
    "Lung Opacity",
    "Lung Lesion",
    "Edema",
    "Consolidation",
    "Pneumonia",
    "Atelectasis",
    "Pneumothorax",
    "Pleural Effusion",
    "Pleural Other",
    "Fracture",
    "Support Devices",
    "No Finding",
)

CHEXBERT_LABELS_5: tuple[str, ...] = (
    "Atelectasis",
    "Cardiomegaly",
    "Consolidation",
    "Edema",
    "Pleural Effusion",
)


def _slug(label: str) -> str:
    """Turn 'Enlarged Cardiomediastinum' into 'enlarged_cardiomediastinum'."""
    return label.replace(" ", "_").lower()


def label_field_name(role: str, label: str) -> str:
    """Produce the reward.json scalar field name for one CheXbert label.

    `role` is "ref" or "pred". E.g.
        label_field_name("ref", "Pleural Effusion") -> "chx_ref_pleural_effusion"
    """
    assert role in {"ref", "pred"}
    return f"chx_{role}_{_slug(label)}"


def ensure_weights() -> Path:
    """Ensure CheXbert's `chexbert.pth` exists where f1chexbert expects it.

    f1chexbert calls `hf_hub_download(..., force_filename='chexbert.pth')` but
    modern huggingface_hub ignores `force_filename`, so the blob lands in the
    standard cache layout and the library's fixed target path is missing. We
    materialize the file at `~/.cache/chexbert/chexbert.pth` (via symlink when
    possible) so f1chexbert can load it.
    """
    from appdirs import user_cache_dir

    cache_dir = Path(user_cache_dir("chexbert"))
    target = cache_dir / "chexbert.pth"
    if target.exists():
        return target

    cache_dir.mkdir(parents=True, exist_ok=True)
    from huggingface_hub import hf_hub_download

    source = Path(
        hf_hub_download(
            repo_id="StanfordAIMI/RRG_scorers",
            filename="chexbert.pth",
            cache_dir=str(cache_dir),
        )
    )
    try:
        os.symlink(source, target)
    except OSError:
        import shutil

        shutil.copy2(source, target)
    return target


_LABELER = None


def get_labeler(device: str | None = None):
    """Return a cached `f1chexbert.F1CheXbert` instance."""
    global _LABELER
    if _LABELER is not None:
        return _LABELER
    ensure_weights()
    if device is None:
        try:
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            device = "cpu"
    from f1chexbert import F1CheXbert

    _LABELER = F1CheXbert(device=device)
    return _LABELER


def label_text(text: str, labeler=None) -> list[int]:
    """Return a 14-dim (0/1) CheXpert label vector for a single report."""
    labeler = labeler or get_labeler()
    raw = labeler.get_label((text or "").strip())
    # f1chexbert returns numpy ints; cast to plain Python int for JSON emission
    return [int(v) for v in raw]


def label_to_fields(role: str, vec: list[int]) -> dict[str, int]:
    """Flatten a 14-dim label vector into named scalar fields keyed by label."""
    return {label_field_name(role, name): int(val) for name, val in zip(CHEXBERT_LABELS, vec)}
