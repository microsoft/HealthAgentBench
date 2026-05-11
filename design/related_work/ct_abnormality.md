# CT-RATE — Chest CT Multi-Abnormality Dataset

## Source

- Dataset: <https://huggingface.co/datasets/ibrahimhamamci/CT-RATE>
- Paper: Hamamci, I.E. et al. "A foundation model for radiology built on multimodal CT-RATE: A large-scale dataset of 25,692 non-contrast 3D chest CT scans paired with radiology reports." (2024)
- License: OpenRAIL (gated on Hugging Face — host must accept access terms)

## Dataset shape

CT-RATE pairs ~25 K non-contrast 3D chest CT volumes with the radiologist's free-text report. Volumes are stored as NIfTI (`.nii.gz`); axial slices are 512×512 voxels at ~0.7 × 0.7 mm in-plane and ~1.5 mm slice thickness; intensities are in Hounsfield Units (HU) ranging roughly −1024 (air) to +3000 (cortical bone, contrast).

The dataset ships:

- `dataset/{train_fixed, valid_fixed}/<patient>/<study>/<volume>.nii.gz` — the volumes, organized hierarchically. The `_fixed` directories are the corrected versions per the dataset's `data_correction_note.md`.
- `dataset/radiology_text_reports/{train_reports.csv, validation_reports.csv}` — paired physician reports with columns `VolumeName, ClinicalInformation_EN, Technique_EN, Findings_EN, Impressions_EN`.
- `dataset/multi_abnormality_labels/{train_predicted_labels.csv, valid_predicted_labels.csv}` — 18 binary multi-label classification columns, **predicted** (silver) labels not human-judged. Categories: Medical material, Arterial wall calcification, Cardiomegaly, Pericardial effusion, Coronary artery wall calcification, Hiatal hernia, Lymphadenopathy, Emphysema, Atelectasis, Lung nodule, Lung opacity, Pulmonary fibrotic sequela, Pleural effusion, Mosaic attenuation pattern, Peribronchial thickening, Consolidation, Bronchiectasis, Interlobular septal thickening.
- `dataset/anatomy_segmentation_labels/`, `dataset/ts_seg/` — derived 3-D anatomy segmentations (not used by MedCLI's integration).
- `dataset/vqa/` — derived VQA pairs (not used by MedCLI's integration).

Validation split: 3,038 volumes from 2,517 patients; representative distribution of the 18 abnormalities (positives range from 226 to 1,361 per category).

## Why a benchmark on this

Chest CT is the highest-volume cross-sectional radiology study. A general-purpose agent that can read a chest CT for the eighteen common findings the CT-RATE labelers track would be a clinically useful tool. CT-RATE is the largest publicly accessible chest-CT dataset with paired reports — substantially larger than the prior ChestCT-NER / RadGraph-CT cohorts — and the validation split is small enough that a deterministic 10-volume MedCLI subset can be shipped on top of it. The task is also the only 3-D imaging benchmark in MedCLI's current suite, complementing the 2-D `mimic_report_gen` (chest X-ray) and the structured-data tasks.

## Why MedCLI's integration is non-trivial

CT-RATE's predicted labels are silver (not physician-judged) and disagree with the report text in several places we sampled. MedCLI's integration therefore re-derives gold labels from the radiology report under a strict exact-wording rule: only labels whose value (positive or negative) is unambiguously grounded in the report text are retained per volume. This produces a smaller but verifiable label set per volume (4–12 labels) and makes pass-rate reporting deterministic. The 10-volume manifest is pinned in `scripts/ct_abnormality/assets/manifest.yaml`.

## What MedCLI does NOT cover

- Training-split scoring, anatomy segmentation, and VQA tasks — out of scope.
- Pulmonary fibrotic sequela (one of the 18 categories) — dropped from the evaluated set because no volume in our manifest retained it under the strict-wording rule. See `.agent/plans/ct_abnormality.md` for the decision.
