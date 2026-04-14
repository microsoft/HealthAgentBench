# MIMIC-IV MEDS Extraction ETL (MIMIC_IV_MEDS v0.0.7)

- Upstream repository: https://github.com/Medical-Event-Data-Standard/MIMIC_IV_MEDS
- Pinned tag: `0.0.7`
- Pinned commit: `9699e0865b050325459b11f3c4e226a9dbe5b496`
- Source read date: April 6, 2026

## Summary

`MIMIC_IV_MEDS` is an ETL pipeline that converts MIMIC-IV data into the MEDS format. The upstream repo exposes a CLI entrypoint, `MEDS_extract-MIMIC_IV`, which downloads the needed MIMIC-IV files, performs pre-MEDS wrangling, and then constructs a final MEDS cohort through `MEDS_transforms`.

The repo README explicitly supports a fully open path through the public MIMIC-IV demo dataset via `do_demo=True`. That makes it a good candidate for a benchmark task because the task can be evaluated without requiring PhysioNet credentials or restricted data access.

## Why It Is Relevant to MedCLI

This repo is directly relevant to the `Cross-schema ETL & harmonization` task family already listed in `design/tasks.md`. It turns a clinically grounded ETL workflow into a concrete, agent-executable objective:

- inspect a real upstream data-transformation repo
- understand its environment and runtime expectations
- set up dependencies
- run the pipeline correctly
- validate the produced MEDS artifacts

This is materially different from row-based question answering or chart-retrieval tasks. It tests whether an agent can operate as a practical data-engineering assistant on a real healthcare ETL codebase.

## Important Design Implications

This benchmark should be treated as an adapted integration rather than a mechanical import.

Reasons:

1. The upstream repo is not itself a Harbor task.
2. The benchmark needs a stable, agent-facing environment with a pinned repo checkout.
3. The benchmark should use the fully open demo dataset, but should avoid live runtime downloads during the agent run for stability.
4. The benchmark needs a task-specific verifier that checks a generated directory tree rather than a JSON submission.
5. The benchmark should intentionally require in-container setup with `uv`, because environment setup is part of the skill being evaluated.

## Upstream Runtime Notes

At tag `0.0.7`, the repo declares Python `>=3.11` and depends on `meds-transforms~=0.2.1`, `polars~=1.27.0`, `hydra-core`, `requests`, and `beautifulsoup4`.

In local reproduction on April 6, 2026, the upstream pipeline failed during `MEDS_transforms` shard extraction because of lock-file cleanup behavior in `MEDS_transforms` / `filelock`. This means the benchmark integration should record and own a compatibility strategy rather than assuming the pristine upstream path is runnable in all environments.

## Implications for This Repository

1. This benchmark should become the first concrete example of a Harbor task for the `Cross-schema ETL & harmonization` family.
2. The task should expose the pinned repo checkout to the agent rather than hiding the code behind a wrapper CLI.
3. The benchmark should evaluate both environment setup with `uv` and the correctness of the generated MEDS output.
4. The benchmark integration should update `design/benchmark_addition_workflow.md` with lessons about adapted ETL-style benchmarks, staged inputs, and verifier design for directory outputs.
