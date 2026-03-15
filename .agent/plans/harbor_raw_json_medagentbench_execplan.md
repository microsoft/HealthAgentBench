# Rebase MedAgentBench on Harbor-Only Raw-JSON Tasks

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

`PLANS.md` is checked into this repository at `/PLANS.md`; this document must be maintained in accordance with that file.

## Purpose / Big Picture

After this change, a contributor can generate and run the Harbor MedAgentBench benchmark task directly from the original raw benchmark JSON in `scripts/medagentbench/assets/test_data_v2.json`. The generated task no longer depends on legacy YAML manifests, no longer exposes answer-bearing data to the agent workspace, and no longer uses the old run-output schema. A human can see the change working by regenerating `tasks/medagentbench/`, inspecting the public task files versus the hidden verifier fixtures, and then running the Harbor smoke path or a real Harbor trial.

## Progress

- [x] (2026-03-13 01:05Z) Extracted shared MedAgentBench normalization logic into `scripts/medagentbench/normalization.py` so raw JSON ingestion, group inference, context merging, and instruction building no longer depend on YAML manifests.
- [x] (2026-03-13 01:10Z) Updated `scripts/medagentbench/import_tasks.py` to consume the shared normalization module so the legacy YAML import path remains runnable during transition, even though it is no longer canonical.
- [x] (2026-03-13 01:24Z) Rewrote `scripts/medagentbench/generate_harbor_tasks.py` to read `scripts/medagentbench/assets/test_data_v2.json` directly and generate the Harbor task from raw benchmark rows rather than from `tasks/*.yaml`.
- [x] (2026-03-13 01:31Z) Reduced the public benchmark task file to a plain JSON list of public task rows containing only `task_id` and `instruction`.
- [x] (2026-03-13 01:36Z) Changed the public submission contract so each submission row contains only safe task text plus `final_answer` and `payload`.
- [x] (2026-03-13 01:48Z) Added a Harbor-only evaluator at `scripts/medagentbench/harbor_evaluator.py` and updated the generated verifier bundle to use it instead of the legacy evaluator.
- [x] (2026-03-13 01:57Z) Moved answer-bearing data into verifier-side fixtures under `tasks/medagentbench/tests/`, including `task_answer_key.json` and write-payload templates.
- [x] (2026-03-13 02:08Z) Regenerated `tasks/medagentbench/` from raw JSON and validated the new generator shape locally.
- [x] (2026-03-13 02:21Z) Added and updated tests for raw-JSON Harbor generation and Harbor-only evaluation semantics.
- [x] (2026-03-13 02:37Z) Updated README and related markdown docs so Harbor plus raw JSON is documented as the canonical MedAgentBench path, while the older OAI and YAML-based path is marked as transitional and frozen.
- [x] (2026-03-13 03:10Z) Removed benchmark-identifying shortcuts and answer-bearing fields from public task files, including `benchmark_name`, `source_benchmark`, `expected_answer`, `sol`, and `eval_MRN`.
- [x] (2026-03-13 03:24Z) Reworked the generated instruction to use generic wording, row-by-row workflow guidance, and no benchmark-name background for the agent.
- [x] (2026-03-13 03:38Z) Split the generated FHIR helper interface into per-primitive scripts under `environment/workspace/scripts/primitives/`, each with `--help`, and aligned the debug helpers with the new layout.
- [x] (2026-03-13 03:51Z) Simplified the public `benchmark_tasks.json` shape to a plain list and removed top-level metadata such as `submission_path` and `reference_time`.
- [x] (2026-03-13 04:07Z) Replaced the public submission template with a pre-created `/workspace/submission.json`, removed `context` from public submission rows, and made submission-row instructions identical to the public benchmark task instructions.
- [x] (2026-03-13 04:14Z) Folded hidden expected write payloads into `tests/task_answer_key.json`, renamed hidden `sol` to `expected_answer`, and applied the same answer normalization used by the legacy importer.
- [x] (2026-03-13 04:24Z) Added debug-only submission snapshot helpers so a generated `/workspace/submission.json` can be copied to `.tmp/<project>/artifacts/submission.json` and restored later without rerunning the agent.
- [x] (2026-03-13 04:31Z) Extended the generated verifier/debug path to emit `error_analysis.json` containing failure-only rows with `expected_payload` and `final_payload`.
- [x] (2026-03-13 05:02Z) Refined the generated primitive interface so `scripts/primitives/` contains only runnable entrypoints, shared logic lives under `scripts/lib/`, and primitive discovery relies on `--help` without generated schema artifacts.
- [x] (2026-03-13 06:10Z) Enabled internet access for full Harbor runs so the installed Codex agent can bootstrap successfully, configured Harbor to collect `/workspace/submission.json` as a trial artifact, and made the generated verifier default its `error_analysis.json` output into the Harbor artifacts mount.

## Surprises & Discoveries

- Observation: the previous Harbor generator still depended on `tasks/*.yaml`, which directly conflicted with the desired long-term Harbor-first direction.
  Evidence: `scripts/medagentbench/generate_harbor_tasks.py` originally accepted a task-manifest root and normalized from YAML rather than from `scripts/medagentbench/assets/test_data_v2.json`.

- Observation: the existing instruction-building logic in `scripts/medagentbench/import_tasks.py` already encoded the task-family-specific answer-format hints needed for Harbor, so extracting and reusing that logic was lower risk than rewriting prompt normalization from scratch.
  Evidence: after extraction into `scripts/medagentbench/normalization.py`, both the legacy importer and the Harbor generator could produce consistent instructions from the same raw benchmark row.

- Observation: `eval_MRN` had to move to the hidden answer key as well, because in some task families, especially `task1`, it directly reveals the gold answer.
  Evidence: public `submission_template.json` originally exposed `eval_MRN`, and for `task1` that value matched the expected MRN answer exactly.

- Observation: writing the task-local verifier stdout to `/logs/verifier/test-stdout.txt` from inside the container shell was brittle; host-side capture was more reliable.
  Evidence: the debug verifier repeatedly failed on shell redirection while the verifier itself could still write `reward.txt` and `meta_results.json` once the output directory existed.

- Observation: the generated verifier originally dumped raw merged rows into `error_analysis.json`, which preserved the single `payload` field and stale row shapes instead of emitting a failure-oriented analysis artifact.
  Evidence: `.tmp/medagentbench-debug/verifier/error_analysis.json` initially contained raw merged rows with `context` and a single `payload`, so it did not match the newer failure-analysis schema.

- Observation: splitting the primitive helper into one file per primitive made the generated task easier to navigate, but also exposed stale debug references that still pointed at removed helper names.
  Evidence: `debug/medagentbench/check-workspace.sh` and `run-manually.sh` still referenced `fhir_tools.py` until the helper split forced them to be updated.

- Observation: generated schema files and a separate `--schema` flag were an awkward fit for agent usability; the agent benefited more from seeing the payload shape directly in `--help`.
  Evidence: manual debug runs produced repeated payload mismatches, and the review of `.tmp/medagentbench-debug/verifier/error_analysis.json` showed the missing information was specifically the POST payload shape, not a lack of access to another file.

- Observation: Harbor's installed Codex agent bootstrap requires outbound network access because it downloads NVM and installs the Codex CLI at runtime.
  Evidence: the failed Harbor job under `results/2026-03-13__21-43-58/` shows agent setup failing on DNS resolution for `deb.debian.org` and `raw.githubusercontent.com` while running Harbor's `install-codex.sh.j2`.

## Decision Log

- Decision: Harbor MedAgentBench uses `scripts/medagentbench/assets/test_data_v2.json` as its source of truth instead of `tasks/*.yaml`.
  Rationale: Harbor is the canonical task system for this workflow, so it should derive directly from the original benchmark data rather than from a transitional YAML representation.
  Date/Author: 2026-03-13 / Codex

- Decision: Public `benchmark_tasks.json` is a plain list of safe task rows rather than a wrapper object.
  Rationale: the file is agent-visible task input only, so wrapper metadata such as `submission_path` and `reference_time` is redundant and unnecessary.
  Date/Author: 2026-03-13 / Codex

- Decision: The public task browse file exposes only `task_id` and `instruction`.
  Rationale: `category`, `difficulty`, expected answers, and patient identifiers are not needed by the agent and either leak gold information or add benchmark-specific clutter.
  Date/Author: 2026-03-13 / Codex

- Decision: Harbor submissions contain only `task_id`, merged `instruction`, `final_answer`, and `payload`.
  Rationale: public `context` was redundant once it had been merged into `instruction`, and the submission rows should match the public benchmark rows as closely as possible.
  Date/Author: 2026-03-13 / Codex

- Decision: Harbor uses a new evaluator file instead of extending `scripts/medagentbench/evaluator.py`.
  Rationale: the legacy evaluator is tied to the old run/output contract and is scheduled for eventual removal; Harbor owns a clean evaluator for its own schema.
  Date/Author: 2026-03-13 / Codex

- Decision: hidden expected write payloads live inside `task_answer_key.json` under `payload`; there is no separate `action_payload_templates.json`.
  Rationale: one hidden verifier fixture is simpler than splitting expected answers and expected payloads across two files.
  Date/Author: 2026-03-13 / Codex

- Decision: debug verifier runs emit a shaped `error_analysis.json` containing only unsuccessful examples and separate `expected_payload` / `final_payload` fields.
  Rationale: raw merged rows are not useful for iterative debugging; the debug artifact should directly surface the mismatches a human cares about.
  Date/Author: 2026-03-13 / Codex

- Decision: Primitive GET and POST helpers live inside the generated Harbor task under `environment/workspace/scripts/primitives/`.
  Rationale: the user wants the Harbor task environment to be self-contained and easy for the agent to navigate file-by-file.
  Date/Author: 2026-03-13 / Codex

- Decision: Primitive discovery uses `--help` only; there is no `--schema` flag and no generated `scripts/schemas/` directory.
  Rationale: GET schemas are already captured by flags, and POST payload requirements are more usable when the original schema is inlined directly into `--help`.
  Date/Author: 2026-03-13 / Codex

- Decision: The generated MedAgentBench Harbor task leaves `allow_internet = true`.
  Rationale: full `harbor run` uses Harbor's installed Codex agent bootstrap path, which currently installs NVM and Codex over the network; enabling internet avoids setup failure without requiring a separate prebuilt agent image path.
  Date/Author: 2026-03-13 / Codex

- Decision: Harbor jobs for MedAgentBench explicitly download `/workspace/submission.json` as a trial artifact, and the generated verifier defaults `error_analysis.json` into `/logs/artifacts/`.
  Rationale: this makes the submission and failure analysis available in each trial directory without requiring a separate debug-only copy step.
  Date/Author: 2026-03-13 / Codex

## Outcomes & Retrospective

The Harbor MedAgentBench path is now structurally aligned with the intended end state. The task is generated from raw benchmark JSON, uses a Harbor-local public/private file split, keeps answer-bearing data verifier-side only, and exposes a simple row-by-row workflow to the agent. Full Harbor runs now also persist both `/workspace/submission.json` and a default verifier `error_analysis.json` into the trial artifacts directory, while the debug path still supports saving/restoring `submission.json` snapshots for fast local iteration. The remaining work is cleanup rather than architecture: once task conversion is finished for all desired benchmarks, the frozen legacy OAI path can be removed.

The main lesson is that the Harbor task became clearer once the agent-visible interface was aggressively minimized. A plain list of task rows, a pre-created submission file with merged instructions, and one file per primitive script are easier for both the agent and the developer to reason about than the earlier benchmark-heavy shape. The primitive interface also became more usable once schema discovery was folded back into `--help` instead of being split across extra files and flags.

## Context and Orientation

The relevant files now split into four groups.

The first group is the Harbor generation path. `scripts/medagentbench/generate_harbor_tasks.py` creates the single Harbor benchmark task at `tasks/medagentbench/`. It reads raw benchmark rows from `scripts/medagentbench/assets/test_data_v2.json`, emits a public task list at `benchmark_tasks.json`, emits a pre-created public `/workspace/submission.json`, writes workspace helper scripts, and copies verifier-side fixtures and a Harbor-only evaluator into `tasks/medagentbench/tests/`.

The second group is the shared normalization layer. `scripts/medagentbench/normalization.py` contains the reusable logic for raw-task loading, task-group inference, context merging, instruction construction, and hidden answer-key row construction. `scripts/medagentbench/import_tasks.py` still exists and uses the same normalization helpers to produce YAML manifests under `tasks/`, but that path is transitional.

The third group is the public task workspace. The agent-visible files are `tasks/medagentbench/benchmark_tasks.json`, `tasks/medagentbench/instruction.md`, and the workspace files under `tasks/medagentbench/environment/workspace/`, including the pre-created `submission.json` and the helper scripts under `scripts/`. The primitive FHIR helpers live under `scripts/primitives/`, shared runtime code lives under `scripts/lib/`, and each primitive supports `--help`.

The fourth group is evaluation. `scripts/medagentbench/harbor_evaluator.py` evaluates the Harbor submission contract after the generated verifier joins the public submission rows with the hidden answer key under `tasks/medagentbench/tests/task_answer_key.json`. The generated verifier writes `meta_results.json`, `reward.txt`, and a shaped `error_analysis.json`, with the latter defaulting into Harbor's artifacts mount so full runs capture it automatically. The debug perfect-submission helper also reads hidden expected payloads from that same answer key.

A “benchmark task” in this repository means one Harbor task directory that represents a benchmark run rather than one task instance. A “submission row” means one JSON object in `/workspace/submission.json` containing safe task text plus `final_answer` and `payload`. A “simulated POST helper” means a command that validates and echoes a would-be FHIR write payload without actually sending it to the FHIR server.

## Plan of Work

Start by keeping the normalization logic in one place. Put all raw-JSON-to-instruction logic in `scripts/medagentbench/normalization.py`, then make both the Harbor generator and the legacy YAML importer consume that module. This prevents drift while the old path still exists.

Next, make the Harbor generator raw-JSON-first and public/private by design. In `scripts/medagentbench/generate_harbor_tasks.py`, read `scripts/medagentbench/assets/test_data_v2.json`, derive the default selected task IDs as `task1_1` through `task10_1`, and generate a public `benchmark_tasks.json` as a plain list of safe task rows with only `task_id` and `instruction`. Generate a pre-created `/workspace/submission.json` as a JSON list of safe editable rows containing `task_id`, `instruction`, `final_answer`, and `payload`. Generate a hidden verifier fixture under `tasks/medagentbench/tests/` as `task_answer_key.json`, containing `expected_answer`, `eval_MRN`, and expected write `payload` keyed by task, along with verifier-only `category` and `difficulty`.

Then keep the generated task environment self-contained. Generate the public helper scripts under `tasks/medagentbench/environment/workspace/scripts/`, with common logic in `scripts/lib/fhir_common.py` and one file per primitive command under `scripts/primitives/`. The GET helpers should query the FHIR sidecar and express required inputs directly as required flags. The POST helpers should accept payload files, validate the top-level `resourceType`, print a success-like JSON blob that includes the payload without mutating the database, and inline the original payload schema into `--help`. The task environment should keep the `fhir-ready` sidecar gate so `main` only starts after the pinned FHIR image answers `/fhir/metadata`.

After that, isolate Harbor evaluation from legacy evaluation. Implement `scripts/medagentbench/harbor_evaluator.py` so it reads merged rows, evaluates query tasks from `final_answer`, evaluates write tasks from `payload`, and returns a summary with pass counts plus failure reasons. Copy that file into the generated Harbor verifier bundle and update `tasks/medagentbench/tests/verify_meta_task.py` generation so the Harbor verifier uses the Harbor-only evaluator plus the hidden answer key.

Finally, keep agent-facing language generic. The generated instruction should describe the environment, tell the agent to work row-by-row through `/workspace/submission.json`, and point it at `/workspace/scripts/primitives/` without mentioning benchmark internals that are not useful for solving the task.

## Concrete Steps

All commands below are run from the repository root.

1. Generate the Harbor task from raw benchmark JSON.

       uv run python scripts/medagentbench/generate_harbor_tasks.py \
         --input-json scripts/medagentbench/assets/test_data_v2.json \
         --output-root tasks/medagentbench

   Expected outcome: the command prints JSON indicating `task_name` is `medagentbench` and `selected_task_ids` are `task1_1` through `task10_1`.

2. Inspect the public benchmark task file.

       python - <<'PY'
       import json
       from pathlib import Path
       data = json.loads(Path('tasks/medagentbench/benchmark_tasks.json').read_text())
       print(type(data).__name__)
       print(data[0].keys())
       print(data[0])
       PY

   Expected outcome: the file is a JSON list, and each row contains exactly `task_id` and `instruction`.

3. Inspect the public submission template.

       python - <<'PY'
       import json
       from pathlib import Path
       rows = json.loads(Path('tasks/medagentbench/environment/workspace/submission.json').read_text())
       print(rows[0]['task_id'], rows[0]['final_answer'], rows[0]['payload'])
       print(rows[0].keys())
       PY

   Expected outcome: each row contains `task_id`, `instruction`, `final_answer`, and `payload`, with no `sol`, `eval_MRN`, `category`, or `difficulty`.

4. Inspect the hidden answer key.

       python - <<'PY'
       import json
       from pathlib import Path
       rows = json.loads(Path('tasks/medagentbench/tests/task_answer_key.json').read_text())
       print(rows[0].keys())
       print(rows[0])
       PY

   Expected outcome: each row contains `task_id`, `category`, `difficulty`, `expected_answer`, `eval_MRN`, and `payload`.

5. Inspect the primitive helper layout.

       find tasks/medagentbench/environment/workspace/scripts -maxdepth 2 -type f | sort

   Expected outcome: the workspace already contains `submission.json`, the primitive helper files live under `scripts/primitives/` with one file per primitive, and shared runtime code lives under `scripts/lib/fhir_common.py`.

6. Run the Harbor generation tests.

       uv run pytest tests/test_harbor_task_generation.py tests/test_harbor_medagentbench_evaluator.py -q

   Expected outcome: both test files pass.

7. Run the full test suite.

       uv run pytest -q

   Expected outcome: the repository test suite passes with the current Harbor raw-JSON flow in place.

8. Exercise the Harbor smoke path.

       bash debug/medagentbench/smoke-meta-task.sh

   Expected outcome: the generated Harbor verifier writes a perfect reward of `1.000000` when given the synthetic perfect submission.

9. Inspect full-run trial artifacts.

       find results/<job>/<trial>/artifacts -maxdepth 2 -type f | sort

   Expected outcome: the trial artifacts include `submission.json` and `error_analysis.json`.

## Validation and Acceptance

The change is accepted when a contributor can regenerate the benchmark task from `scripts/medagentbench/assets/test_data_v2.json`, inspect the plain-list public task file, inspect the safe submission template, inspect the hidden verifier fixtures, and run the Harbor smoke path successfully.

Behaviorally, `tasks/medagentbench/benchmark_tasks.json` must be a plain JSON list of safe public rows and must not contain `submission_path`, `reference_time`, `category`, `difficulty`, `expected_answer`, or `eval_MRN`. The generated `/workspace/submission.json` must be a JSON list of safe editable rows with `task_id`, merged `instruction`, `final_answer`, and `payload`. The generated helper interface must live under `scripts/primitives/`, with one file per primitive and `--help` support for each primitive script; there must be no generated `scripts/schemas/` artifact. The generated task config must keep `allow_internet = true`, and the Harbor job config must collect `/workspace/submission.json` as an artifact.

For evaluation, `scripts/medagentbench/harbor_evaluator.py` must remain the scoring implementation used inside the generated Harbor verifier. A perfect synthetic submission must score `1.0`, and the repository tests covering Harbor task generation and Harbor evaluation must pass.

## Idempotence and Recovery

The Harbor generator is safe to rerun. If the generated task directory is stale, rerun `scripts/medagentbench/generate_harbor_tasks.py`; it recreates the Harbor task deterministically. If generation fails halfway, delete only `tasks/medagentbench/` and rerun the command. Do not hand-edit generated Harbor task files.

The legacy YAML import path remains runnable but is no longer canonical. If a contributor needs the old manifests during transition, they may still rerun `scripts/medagentbench/import_tasks.py`, but Harbor validation must never depend on those manifests.

## Artifacts and Notes

Expected generator transcript shape:

    $ uv run python scripts/medagentbench/generate_harbor_tasks.py --input-json scripts/medagentbench/assets/test_data_v2.json --output-root tasks/medagentbench
    {
      "task_name": "medagentbench",
      "output_root": "tasks/medagentbench",
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

Expected public submission-row shape:

    {
      "task_id": "task3_1",
      "instruction": "...",
      "final_answer": "",
      "payload": null
    }

Expected hidden answer-key row shape:

    {
      "task_id": "task3_1",
      "category": "clinical_data_recording",
      "difficulty": "medium",
      "expected_answer": "",
      "eval_MRN": "S2380121",
      "payload": { ... }
    }

Plan revision note: this plan supersedes the earlier YAML-first Harbor task conversion direction because the repository is now standardizing on Harbor plus raw MedAgentBench JSON as the canonical path, with a strict public/private split inside the generated Harbor task.

## Interfaces and Dependencies

`scripts/medagentbench/normalization.py` must export functions that both the Harbor generator and the legacy importer can call. At minimum, it must provide raw-task loading, task-group inference, default selected-task-ID derivation, instruction construction, public Harbor-row construction, and hidden answer-key row construction.

`scripts/medagentbench/generate_harbor_tasks.py` must accept `--input-json` and write a single Harbor task at `tasks/medagentbench/`.

`scripts/medagentbench/harbor_evaluator.py` must expose `load_submission(path: Path) -> list[dict[str, Any]]`, `merge_submission_with_answer_key(...)`, and `evaluate_submission_rows(rows: list[dict[str, Any]]) -> dict[str, Any]` so the generated verifier can import and run it directly.

The generated Harbor workspace helper directories `environment/workspace/scripts/primitives/` and `environment/workspace/scripts/lib/` must remain self-contained and callable with standard Python inside the Harbor task container.
