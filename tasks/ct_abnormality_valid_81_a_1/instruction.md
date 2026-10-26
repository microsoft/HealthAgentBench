# Chest CT Multi-Abnormality Classification

You are working inside an environment that contains a single non-contrast
chest-CT volume and a list of clinical findings to evaluate. **For each
listed finding, decide whether the finding is present or absent in the
scan, and write your prediction.**

## Inputs

- `/workspace/data/scan.nii.gz` — the chest CT volume.
- `/workspace/data/labels.txt` — the clinical labels you must evaluate,
  one per line. Only these labels will be scored. The list is short
  (typically 4 to 12 labels) and is volume-specific.

## Output

Write a plain text file at `/workspace/submission/predictions.txt`
containing one `<label>: yes` or `<label>: no` line per requested label.
Use the exact label name from `labels.txt` (case-insensitive). Order
does not matter; the verifier matches by label name.

Format example:

    Cardiomegaly: no
    Pleural effusion: yes
    Lung nodule: no
    # comments and blank lines are ignored

## Rules

- How to actually look at a 3-D volume is up to you to figure out.
- The reward is **binary** — you must get **every** requested label
  correct to score `1.0`. A single mistake yields `0.0`. Diagnostic
  per-label and per-disease F1 are reported alongside but do not affect the per-task reward.

## Resources

You have 1 hour to complete the task. There is no internet access beyond the model
API. The container is configured for 2 CPUs, 8 GiB of memory, 8 GiB of disk, and no
GPU. System tools may report host resources, not these limits.
