# Add the MIMIC-IV MEDS Extraction ETL benchmark

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document is governed by `PLANS.md` in the repository root and must be maintained in accordance with that file.

## Purpose / Big Picture

After this change, MedCLI can run a Harbor benchmark that evaluates whether an agent can inspect a real healthcare ETL repository, create its environment with `uv`, and produce a valid MEDS cohort from the open MIMIC-IV demo dataset. A user can observe the result by generating `tasks/mimic_iv_meds/`, running `uv run harbor run -c jobs/mimic_iv_meds.yaml`, and seeing Harbor score the run from the generated MEDS output directory instead of a JSON answer file.

## Progress

- [x] (2026-04-06 14:05Z) Added design intake artifacts for `MIMIC_IV_MEDS` and tracked the benchmark in `design/tasks.md`.
- [x] (2026-04-06 14:24Z) Wrote benchmark scaffolding under `scripts/mimic_iv_meds/`, including the Harbor task generator and reference-summary builder.
- [x] (2026-04-06 14:51Z) Reproduced the upstream demo pipeline, identified the `MEDS_transforms` lock-file cleanup bug, and confirmed a task-local compatibility patch makes the pinned upstream workflow succeed.
- [x] (2026-04-06 15:08Z) Built a verifier-side gold summary from a known-good reference run and generated `tasks/mimic_iv_meds/`.
- [ ] (2026-04-06 15:18Z) Add benchmark-specific tests for task generation and verifier behavior.
- [ ] (2026-04-06 15:18Z) Run benchmark-specific validation and update repo docs to reflect the integrated benchmark.

## Surprises & Discoveries

- Observation: The pinned upstream repo does not run cleanly in a fresh `uv` environment on its own.
  Evidence: Running `uv run MEDS_extract-MIMIC_IV ... do_demo=True` failed during `MEDS_transforms` sharding with `FileNotFoundError` on a `.lock` file under `mapreduce`.

- Observation: A minimal compatibility patch inside the created `.venv` is sufficient to make the pinned upstream workflow succeed.
  Evidence: Replacing the unconditional `lock_fp.unlink()` with `if lock_fp.exists(): lock_fp.unlink()` in `MEDS_transforms/mapreduce/utils.py` produced a complete demo run with `MEDS_cohort/metadata/dataset.json`, `codes.parquet`, `subject_splits.parquet`, and data shards.

- Observation: The upstream repo tag `0.0.7` does not ship a checked-in `uv.lock`.
  Evidence: A clean clone of tag `0.0.7` contained `pyproject.toml` but no `uv.lock`, which means the presence of `uv.lock` after the agent run is a valid verifier-side signal that `uv sync` was executed.

- Observation: Passing `pre_MEDS_dir` and `MEDS_cohort_dir` is not enough; the pinned Hydra config still requires `root_output_dir`.
  Evidence: A direct container run failed with `InterpolationToMissingValueError: Missing mandatory value: root_output_dir` while resolving `hydra.run.dir`.

## Decision Log

- Decision: Treat this benchmark as an adapted integration instead of a mechanical import.
  Rationale: The upstream repo is not a Harbor task, expects networked downloads by default, and needed a task-specific verifier plus a compatibility patch to become stable in this environment.
  Date/Author: 2026-04-06 / Codex

- Decision: Stage the public demo input during image build instead of requiring the agent to download it at run time.
  Rationale: The benchmark is supposed to test repository understanding, `uv` setup, and ETL execution. Tying scoring to live network fetches during the trial would add noise unrelated to that skill.
  Date/Author: 2026-04-06 / Codex

- Decision: Require the agent to create the runnable environment with `uv` during the trial.
  Rationale: The user explicitly wants environment setup to be part of the task, and the upstream repo is a realistic example of a codebase an agent should be able to make runnable.
  Date/Author: 2026-04-06 / Codex

- Decision: Score with structural checks plus a compact gold summary rather than exact artifact hashing.
  Rationale: Full file hashing is brittle for Parquet outputs and incidental metadata. The compact summary is stable enough to catch semantic regressions without overfitting to byte-level details.
  Date/Author: 2026-04-06 / Codex

- Decision: Ship a task-local helper script that patches the known `MEDS_transforms` lock-file bug after `uv sync`.
  Rationale: The benchmark should test following instructions and making the pinned upstream repo work in this task environment, not discovering an unrelated transitive-dependency bug from scratch.
  Date/Author: 2026-04-06 / Codex

- Decision: Require `root_output_dir=/workspace/output` in the canonical command even though the benchmark also passes explicit output directories.
  Rationale: The pinned upstream Hydra config resolves logging through `root_output_dir`, so omitting it causes the run to fail before ETL starts.
  Date/Author: 2026-04-06 / Codex

## Outcomes & Retrospective

The benchmark design is now concrete and runnable in principle: a pinned upstream checkout, staged demo input, `uv`-based setup, and a verifier built around MEDS directory outputs. The main remaining work is quality and proof: benchmark-specific tests and at least one validation run through the supported Harbor path.

## Context and Orientation

MedCLI stores benchmark-specific integration logic under `scripts/<benchmark>/`, generated Harbor tasks under `tasks/<benchmark>/`, and Harbor jobs under `jobs/`. This benchmark uses the upstream repository `Medical-Event-Data-Standard/MIMIC_IV_MEDS` at tag `0.0.7`, pinned to commit `9699e0865b050325459b11f3c4e226a9dbe5b496`.

The key files for this benchmark are:

- `scripts/mimic_iv_meds/generate_harbor_task.py`: generates the Harbor task files for this benchmark.
- `scripts/mimic_iv_meds/build_reference_summary.py`: derives a compact verifier-side gold summary from a known-good output tree.
- `scripts/mimic_iv_meds/assets/gold_demo_summary.json`: the committed gold summary used by the verifier.
- `tasks/mimic_iv_meds/`: the generated Harbor task artifact.
- `jobs/mimic_iv_meds.yaml`: the Harbor job config.
- `design/related_work/mimic_iv_meds_0.0.7.md`: the design intake note that explains why this benchmark exists.

In this plan, “staged demo input” means the public MIMIC-IV demo files are copied into the container during the Docker build so the agent does not need to fetch them during the trial. “Gold summary” means a compact JSON description of the expected MEDS output structure, metadata schemas, and row counts, not a copy of the full reference output tree.

## Plan of Work

First, keep the benchmark intake accurate. The related-work note and `design/tasks.md` must describe the benchmark as an adapted ETL integration that requires staged inputs, `uv` setup, and directory-output verification.

Second, build the benchmark-specific scripts. `scripts/mimic_iv_meds/generate_harbor_task.py` must generate the task instruction, Dockerfile, staged-input helper, compatibility patch helper, verifier entrypoint, and verifier logic. `scripts/mimic_iv_meds/build_reference_summary.py` must compute the stable summary from a known-good output tree. `scripts/mimic_iv_meds/README.md` and `debug/mimic_iv_meds/README.md` must explain how to regenerate the task and run it.

Third, generate and commit `tasks/mimic_iv_meds/`. The task must expose the pinned upstream repo under `/workspace/MIMIC_IV_MEDS`, instruct the agent to run `uv sync`, apply the compatibility patch, and write the final MEDS cohort to `/workspace/output/MEDS_cohort`. The verifier must check both the setup artifacts and the output tree.

Fourth, add tests. One test should prove the generator creates the expected task layout. Another should exercise the generated verifier on synthetic output: a passing case with matching metadata and row counts, and a failing case where the `uv` setup artifacts are missing.

Finally, update repo-facing docs. Promote the benchmark from `Planned` to `Integrated` in `design/tasks.md`, add it to `tasks/README.md`, and refine `design/benchmark_addition_workflow.md` with the general lessons learned from this adapted ETL benchmark.

## Concrete Steps

From the repository root:

    uv run python scripts/mimic_iv_meds/build_reference_summary.py \
      --output-root /tmp/mimic_iv_meds_demo_run_patch \
      --summary-out scripts/mimic_iv_meds/assets/gold_demo_summary.json

Expected result: `scripts/mimic_iv_meds/assets/gold_demo_summary.json` is written and contains the required metadata files plus the expected shard paths and row counts.

    uv run python scripts/mimic_iv_meds/generate_harbor_task.py \
      --output-root tasks/mimic_iv_meds

Expected result: `tasks/mimic_iv_meds/` contains `instruction.md`, `task.toml`, `environment/Dockerfile`, and `tests/verify_output.py`.

    uv run pytest tests/test_mimic_iv_meds_task.py -q

Expected result: the benchmark-specific tests pass.

    uv run harbor run -c jobs/mimic_iv_meds.yaml

Expected result: Harbor builds the environment, the agent creates the repo-local `uv` environment, and the verifier writes a non-zero reward only when the MEDS output matches the gold summary.

## Validation and Acceptance

The change is accepted when all of these are true:

- `tasks/mimic_iv_meds/` exists and is reproducibly generated from `scripts/mimic_iv_meds/generate_harbor_task.py`.
- `tests/test_mimic_iv_meds_task.py` passes and proves both the success path and the missing-`uv`-setup failure path.
- `design/tasks.md` lists the benchmark under `Integrated`.
- `tasks/README.md` lists the benchmark.
- A Harbor run using `jobs/mimic_iv_meds.yaml` can, at minimum, start from the generated task artifact and exercise the supported run path.

## Idempotence and Recovery

The generator is safe to rerun because it recreates `tasks/mimic_iv_meds/` from scratch. The reference-summary builder is safe to rerun as long as the input reference tree is known-good. If the benchmark task needs to be regenerated after edits, rerun the builder first if the gold reference changed, then rerun the generator, then rerun the tests.

## Artifacts and Notes

Useful evidence from the design phase:

    gold_demo_summary.json:
      metadata.dataset.json.dataset_name = "MIMIC-IV"
      metadata.dataset.json.dataset_version = "3.1:0.0.7"
      data_files = ["data/held_out/0.parquet", "data/train/0.parquet", "data/tuning/0.parquet"]

    Upstream compatibility patch:
      lock.release()
      if lock_fp.exists():
          lock_fp.unlink()

## Interfaces and Dependencies

This benchmark depends on Harbor tasks generated under `tasks/`, the upstream `MIMIC_IV_MEDS` repo at tag `0.0.7`, and `uv` inside the task container. The generated verifier script must accept:

    --repo-dir PATH
    --output-root PATH
    --gold-summary PATH
    --reward-file PATH
    --error-analysis-file PATH

The verifier contract is pass/fail. It must check for a repo-local `.venv`, `uv.lock`, the `MEDS_extract-MIMIC_IV` entrypoint, required MEDS metadata files, the expected data shard set, and the reference row counts and metadata schemas from the gold summary.

Revision note (2026-04-06 / Codex): created this ExecPlan after the initial benchmark scaffolding so the adapted-benchmark decisions and validation requirements are preserved in one self-contained place.
