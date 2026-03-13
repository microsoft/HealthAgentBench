# Rebase MedAgentBench on Harbor-Only Raw-JSON Tasks

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

`PLANS.md` is checked into this repository at `/PLANS.md`; this document must be maintained in accordance with that file.

## Purpose / Big Picture

After this change, a contributor can generate and run the MedAgentBench Harbor meta-task directly from the original raw benchmark JSON in `data/medagentbench/test_data_v2.json`. The Harbor task no longer depends on the legacy YAML task manifests under `tasks/`, and the Harbor verifier no longer depends on the legacy run-output schema. Instead, Harbor owns its own compact task normalization, its own submission format, and its own evaluator. A human can see the change working by regenerating `harbor_tasks/medagentbench/`, inspecting `benchmark_tasks.json` and `submission_template.json`, and then running the Harbor smoke path or a real Harbor trial.

## Progress

- [x] (2026-03-13 01:05Z) Extracted shared MedAgentBench normalization logic into `scripts/medagentbench/normalization.py` so raw JSON ingestion, group inference, category mapping, difficulty mapping, context merging, and instruction building no longer depend on YAML manifests.
- [x] (2026-03-13 01:10Z) Updated `scripts/medagentbench/import_tasks.py` to consume the shared normalization module so the legacy YAML import path remains runnable during transition, even though it is no longer canonical.
- [x] (2026-03-13 01:24Z) Rewrote `scripts/medagentbench/generate_harbor_tasks.py` to read `data/medagentbench/test_data_v2.json` directly and generate the Harbor task from raw benchmark rows rather than from `tasks/*.yaml`.
- [x] (2026-03-13 01:31Z) Changed the Harbor benchmark task payload to the new compact seven-field normalized shape: `task_id`, `category`, `difficulty`, `instruction`, `expected_answer`, `source_benchmark`, and `eval_mrn`.
- [x] (2026-03-13 01:36Z) Changed the Harbor submission contract so each submission row preserves the original raw task row and appends `final_answer` plus `payload`, where `payload` is `null`, one object, or a list of objects depending on the task.
- [x] (2026-03-13 01:48Z) Added a Harbor-only evaluator at `scripts/medagentbench/harbor_evaluator.py` and updated the generated verifier bundle to use it instead of the legacy evaluator.
- [x] (2026-03-13 01:57Z) Reworked the generated Harbor workspace helpers so MedAgentBench primitive FHIR operations live inside the Harbor task as `scripts/fhir_primitives.py`; simulated POST helpers now capture payloads without mutating the database.
- [x] (2026-03-13 02:08Z) Regenerated `harbor_tasks/medagentbench/` from raw JSON and validated the new generator shape locally.
- [x] (2026-03-13 02:21Z) Added new tests for raw-JSON Harbor generation and Harbor-only evaluation semantics.
- [x] (2026-03-13 02:37Z) Updated README and related markdown docs so Harbor plus raw JSON is documented as the canonical MedAgentBench path, while the older OAI and YAML-based path is marked as transitional and frozen.

## Surprises & Discoveries

- Observation: the previous Harbor generator still depended on `tasks/*.yaml`, which directly conflicted with the desired long-term Harbor-first direction.
  Evidence: `scripts/medagentbench/generate_harbor_tasks.py` originally accepted `--input-root tasks` and normalized from manifest YAML rather than from `data/medagentbench/test_data_v2.json`.

- Observation: the existing `_build_instruction` logic in `scripts/medagentbench/import_tasks.py` already encoded the instruction-format details needed for Harbor, so extracting and reusing it was lower risk than rewriting prompt normalization from scratch.
  Evidence: after extraction into `scripts/medagentbench/normalization.py`, both the legacy importer and the Harbor generator could produce consistent task instructions from the same raw benchmark row.

- Observation: the Harbor submission contract did not need the old `tool_trace` structure at all. The write-task evaluator can operate directly on `payload`, which makes the Harbor task contract smaller and easier for the agent to understand.
  Evidence: the new Harbor evaluator only needs `final_answer`, `payload`, and the original raw row fields such as `id`, `sol`, and `eval_MRN`.

- Observation: the MedAgentBench primitive POST behavior is better represented as a simulated write inside the Harbor task than as a policy instruction telling the agent not to mutate the database.
  Evidence: the generated `fhir_primitives.py` POST helpers now return a stable accepted payload with a message telling the agent to copy it into `submission.json`, which removes ambiguity from the task instruction.

## Decision Log

- Decision: Harbor MedAgentBench now uses `data/medagentbench/test_data_v2.json` as its source of truth instead of `tasks/*.yaml`.
  Rationale: the user wants Harbor to be the canonical task system, so Harbor should derive directly from the original benchmark data rather than from a transitional YAML representation.
  Date/Author: 2026-03-13 / Codex

- Decision: the Harbor benchmark task rows are reduced to seven fields.
  Rationale: the Harbor agent should infer how to solve the task from the instruction itself; extra legacy manifest metadata is not part of the Harbor task contract.
  Date/Author: 2026-03-13 / Codex

- Decision: Harbor submissions preserve the original raw task row and append `final_answer` plus `payload`.
  Rationale: this keeps the submission self-describing for evaluation while avoiding a second schema that would force the agent and verifier to translate between task identities.
  Date/Author: 2026-03-13 / Codex

- Decision: Harbor uses a new evaluator file instead of extending `scripts/medagentbench/evaluator.py`.
  Rationale: the legacy evaluator is tied to the old run/output contract and is scheduled for eventual removal; Harbor should own a clean evaluator for its own schema.
  Date/Author: 2026-03-13 / Codex

- Decision: primitive GET and POST helpers for MedAgentBench live inside the generated Harbor task, not under `src/medcli/tools/`.
  Rationale: the user wants Harbor task environments to be self-contained and no longer wants the MedAgentBench Harbor flow coupled to the legacy agent/tool stack.
  Date/Author: 2026-03-13 / Codex

## Outcomes & Retrospective

The Harbor MedAgentBench path is now structurally aligned with the desired end state. The Harbor task is generated from raw benchmark JSON, uses a Harbor-local task schema and evaluator, and no longer depends on YAML manifests as a canonical input. The remaining work is cleanup, not core architecture: once task conversion is finished for all benchmarks of interest, the frozen legacy OAI path can be removed.

The main lesson is that Harbor became simpler once it stopped trying to preserve the legacy run schema. The new task/output boundary is smaller and easier to reason about: normalized task metadata for browsing, raw rows for submission, and direct payload evaluation for write tasks.

## Context and Orientation

The relevant files now split into three groups.

The first group is the Harbor generation path. `scripts/medagentbench/generate_harbor_tasks.py` creates the single Harbor meta-task at `harbor_tasks/medagentbench/`. It reads raw benchmark rows from `data/medagentbench/test_data_v2.json`, normalizes the selected slice into `benchmark_tasks.json`, emits a submission template, writes Harbor workspace helper scripts, and copies a Harbor-only evaluator into the generated verifier bundle.

The second group is the shared normalization layer. `scripts/medagentbench/normalization.py` contains the reusable logic for raw-task loading, group inference, category mapping, difficulty mapping, context merging, and instruction construction. `scripts/medagentbench/import_tasks.py` still exists and uses the same normalization helpers to produce YAML manifests under `tasks/`, but that path is transitional.

The third group is evaluation. `scripts/medagentbench/harbor_evaluator.py` evaluates the Harbor submission contract. The legacy `scripts/medagentbench/evaluator.py` remains in the repository for the old run path, but the generated Harbor verifier now depends on `harbor_evaluator.py` instead.

A “meta-task” in this repository means one Harbor task directory that represents a benchmark slice rather than one task instance. A “submission row” means one JSON object in `/workspace/submission.json` that contains the original raw MedAgentBench row plus Harbor result fields. A “simulated POST helper” means a command that validates and echoes a would-be FHIR write payload without actually sending it to the FHIR server.

## Plan of Work

Start by keeping the normalization logic in one place. Put all raw-JSON-to-instruction logic in `scripts/medagentbench/normalization.py`, then make both the Harbor generator and the legacy YAML importer consume that module. This prevents drift while the old path still exists.

Next, make the Harbor generator raw-JSON-first. In `scripts/medagentbench/generate_harbor_tasks.py`, read `data/medagentbench/test_data_v2.json`, derive the default selected task IDs as `task1_1` through `task10_1`, and generate `benchmark_tasks.json` with only the seven required normalized fields. Generate `submission_template.json` as a JSON list of the selected raw rows with two appended result fields: `final_answer` and `payload`.

Then move MedAgentBench primitive behavior into the Harbor task environment. Generate `harbor_tasks/medagentbench/environment/workspace/scripts/fhir_primitives.py` with primitive GET helpers and simulated POST helpers. The GET helpers should query the FHIR sidecar. The POST helpers should accept payload files, validate the top-level `resourceType`, and print a success-like JSON blob that includes the payload without mutating the database.

After that, isolate Harbor evaluation from legacy evaluation. Implement `scripts/medagentbench/harbor_evaluator.py` so it reads submission rows, evaluates query tasks from `final_answer`, evaluates write tasks from `payload`, and returns a summary with pass counts plus failure reasons. Copy that file into the generated Harbor verifier bundle and update `harbor_tasks/medagentbench/tests/verify_meta_task.py` generation so the Harbor verifier uses the Harbor-only evaluator.

Finally, update documentation. The repository README, `AGENTS.md`, `CLAUDE.md`, and `scripts/medagentbench/README.md` must describe Harbor plus raw JSON as the canonical MedAgentBench workflow. They must explicitly say that the older OAI path and YAML import path still exist temporarily but are frozen and will be removed after conversion is complete.

## Concrete Steps

All commands below are run from the repository root.

1. Generate the Harbor task from raw benchmark JSON.

       uv run python scripts/medagentbench/generate_harbor_tasks.py \
         --input-json data/medagentbench/test_data_v2.json \
         --output-root harbor_tasks/medagentbench

   Expected outcome: the command prints JSON indicating `task_name` is `medagentbench` and `selected_task_ids` are `task1_1` through `task10_1`.

2. Inspect the normalized Harbor task browse file.

       python - <<'PY'
       import json
       from pathlib import Path
       data = json.loads(Path('harbor_tasks/medagentbench/benchmark_tasks.json').read_text())
       print(data['tasks'][0].keys())
       print(data['tasks'][0])
       PY

   Expected outcome: each task contains exactly `task_id`, `category`, `difficulty`, `instruction`, `expected_answer`, `source_benchmark`, and `eval_mrn`.

3. Inspect the submission template.

       python - <<'PY'
       import json
       from pathlib import Path
       rows = json.loads(Path('harbor_tasks/medagentbench/submission_template.json').read_text())
       print(rows[0]['id'], rows[0]['final_answer'], rows[0]['payload'])
       print(sorted(set(rows[0].keys()) - {'final_answer', 'payload'}))
       PY

   Expected outcome: each row preserves the raw benchmark row fields and adds empty `final_answer` plus `payload = None`.

4. Run the Harbor-only evaluator tests.

       uv run pytest tests/test_harbor_task_generation.py tests/test_harbor_medagentbench_evaluator.py -q

   Expected outcome: both test files pass.

5. Run the full test suite.

       uv run pytest -q

   Expected outcome: the repository test suite passes with the new Harbor raw-JSON flow in place.

6. Exercise the Harbor smoke path.

       bash debug/harbor/medagentbench/smoke-meta-task.sh

   Expected outcome: the generated Harbor verifier writes a perfect reward of `1.000000` when given the synthetic perfect submission.

## Validation and Acceptance

The change is accepted when a contributor can regenerate the MedAgentBench Harbor task from `data/medagentbench/test_data_v2.json`, inspect a compact normalized browse file, inspect a raw-row-preserving submission template, and run the Harbor smoke path successfully.

Behaviorally, `harbor_tasks/medagentbench/benchmark_tasks.json` must no longer be derived from `tasks/*.yaml`. The Harbor generator command must name `--input-json`, not `--input-root`. The generated `submission_template.json` must be a JSON list of raw selected task rows with `final_answer` and `payload`. The generated workspace helper script must be `scripts/fhir_primitives.py`, and its simulated POST helpers must not write to the FHIR server.

For evaluation, `scripts/medagentbench/harbor_evaluator.py` must be the scoring implementation used inside the generated Harbor verifier. A perfect synthetic submission must score `1.0`, and the repository tests covering Harbor task generation and Harbor evaluation must pass.

## Idempotence and Recovery

The Harbor generator is safe to rerun. If the generated task directory is stale, rerun `scripts/medagentbench/generate_harbor_tasks.py`; it recreates the Harbor task deterministically. If generation fails halfway, delete only `harbor_tasks/medagentbench/` and rerun the command. Do not edit generated Harbor task files by hand.

The legacy YAML import path remains runnable but is no longer canonical. If a contributor needs the old manifests during transition, they may still rerun `scripts/medagentbench/import_tasks.py`, but Harbor validation must never depend on those manifests.

## Artifacts and Notes

Expected generator transcript shape:

    $ uv run python scripts/medagentbench/generate_harbor_tasks.py --input-json data/medagentbench/test_data_v2.json --output-root harbor_tasks/medagentbench
    {
      "task_name": "medagentbench",
      "output_root": "harbor_tasks/medagentbench",
      "selected_task_ids": [
        "task1_1",
        "task2_1",
        "task3_1",
        "task4_1",
        "task5_1",
        "task6_1",
        "task7_1",
        "task8_1",
        "task9_1",
        "task10_1"
      ]
    }

Expected submission-row shape:

    {
      "id": "task3_1",
      "question": "...",
      "context": "...",
      "eval_MRN": "S1234567",
      "sol": "...",
      "final_answer": "",
      "payload": null
    }

Plan revision note: this plan supersedes the earlier YAML-first Harbor task conversion direction because the repository is now standardizing on Harbor plus raw MedAgentBench JSON as the canonical path.

## Interfaces and Dependencies

`scripts/medagentbench/normalization.py` must export functions that both the Harbor generator and the legacy importer can call. At minimum, it must provide raw-task loading, task-group inference, default selected-task-ID derivation, instruction construction, and normalized Harbor-row construction.

`scripts/medagentbench/generate_harbor_tasks.py` must accept `--input-json` and write a single Harbor task at `harbor_tasks/medagentbench/`.

`scripts/medagentbench/harbor_evaluator.py` must expose `load_submission(path: Path) -> list[dict[str, Any]]` and `evaluate_submission_rows(rows: list[dict[str, Any]]) -> dict[str, Any]` so the generated verifier can import and run it directly.

The generated Harbor workspace script `environment/workspace/scripts/fhir_primitives.py` must remain self-contained and callable with standard Python plus `requests` inside the Harbor task container.
