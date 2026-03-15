# Remove the Frozen Legacy OAI MedAgentBench Path

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

`PLANS.md` is checked into this repository at `/PLANS.md`; this document must be maintained in accordance with that file.

## Purpose / Big Picture

After this change, MedAgentBench in this repository is Harbor-only. A contributor can generate the Harbor task from `scripts/medagentbench/assets/test_data_v2.json`, run it through Harbor, debug it through `debug/`, and inspect trial artifacts under `results/` without any parallel OpenAI-style runner, YAML manifest importer, or legacy evaluator path remaining in the tree.

## Progress

- [x] (2026-03-14 00:10Z) Audited the remaining legacy MedAgentBench surface and confirmed the old path still included `src/medcli/agents/oai_agent/`, `run.py`, `demo.py`, `scripts/medagentbench/import_tasks.py`, `scripts/medagentbench/evaluate.py`, `scripts/medagentbench/evaluator.py`, MedAgentBench YAML manifests under `tasks/`, and tests/docs that exercised those pieces.
- [x] (2026-03-14 00:16Z) Removed the frozen legacy MedAgentBench runtime and manifest path, including the OpenAI-style agent package, legacy CLIs, YAML manifests, legacy evaluator/import scripts, and legacy-only tests.
- [x] (2026-03-14 00:22Z) Rewrote README, `AGENTS.md`, `CLAUDE.md`, and `scripts/medagentbench/README.md` so MedAgentBench is documented as Harbor-only and no longer advertises the removed path.
- [x] (2026-03-14 22:26Z) Removed the leftover legacy `src/medcli/backends/`, `src/medcli/tools/`, and `src/medcli/utils/` trees, along with the Azure OpenAI CLI entrypoint and their associated tests.
- [x] (2026-03-14 23:40Z) Renamed the generated Harbor task root from `harbor_tasks/` to `tasks/`, flattened `debug/harbor/` into `debug/`, and regenerated the MedAgentBench task and docs to match the new layout.
- [x] (2026-03-14 23:52Z) Moved raw benchmark assets into `scripts/medagentbench/assets/`, removed the standalone local FHIR runtime scripts, and simplified the benchmark docs around the Harbor-only path.
- [x] (2026-03-15 00:18Z) Ran the reduced test suite and repository-wide reference sweeps; no remaining live references to the removed path remain outside historical plan documents.

## Surprises & Discoveries

- Observation: the remaining legacy surface was broader than just `src/medcli/agents/oai_agent/`; it also included the YAML importer, legacy evaluator CLI, integration smoke tests, and repository docs that still taught the old workflow.
  Evidence: repo-wide search found active references to `run.py`, `demo.py`, `import_tasks.py`, `scripts/medagentbench/evaluate.py`, and MedAgentBench YAML manifests in tests and top-level docs.

- Observation: the `tasks/` tree had become MedAgentBench-only rather than a general task registry in practice.
  Evidence: `find tasks -maxdepth 4 -type f` showed only `tasks/README.md`, `tasks/__init__.py`, and MedAgentBench YAML manifests under task-type subdirectories.

- Observation: Harbor-specific MedAgentBench evaluation and generation code is already cleanly separated from the legacy output shape.
  Evidence: Harbor generation uses `scripts/medagentbench/generate_harbor_tasks.py` and Harbor scoring uses `scripts/medagentbench/harbor_evaluator.py`, while the deleted scripts were the only ones still operating on `tool_trace`-based legacy run outputs.

- Observation: the remaining `src/medcli/backends`, `src/medcli/tools`, and `src/medcli/utils` trees were only referenced by their own tests and the `medcli-azure-openai` console script.
  Evidence: repo-wide search after the first cleanup showed no Harbor-path imports into those modules; all remaining live references were in `tests/test_azure_openai_cli.py`, `tests/test_fhir_client.py`, `tests/test_fhir_tools.py`, `tests/integration/test_gpt52_function_calling_smoke.py`, and `pyproject.toml`.

- Observation: once the legacy YAML manifests were removed, the generated Harbor task and its surrounding docs benefited from generic path names and benchmark placeholders rather than MedAgentBench-specific top-level wording.
  Evidence: the repository now uses `tasks/<benchmark>/`, `scripts/<benchmark>/`, and `debug/<benchmark>/README.md` in the top-level docs, while keeping one concrete current-benchmark note for MedAgentBench.

- Observation: the standalone `scripts/medagentbench/docker-compose.yaml` and `fhir_up.sh` / `fhir_down.sh` path became redundant after Harbor debug became the only supported runtime environment for the FHIR sidecar.
  Evidence: after the Harbor debug workflow stabilized, those files were referenced only by each other and one README section.

## Decision Log

- Decision: remove the entire legacy MedAgentBench OAI path rather than leaving deprecation stubs.
  Rationale: Harbor task conversion is complete, and keeping an unused parallel runtime increases maintenance cost and doc ambiguity.
  Date/Author: 2026-03-14 / Codex

- Decision: remove the MedAgentBench YAML manifests and the `tasks/` directory entirely.
  Rationale: after the Harbor migration, the raw JSON benchmark source and generated Harbor task are the only supported MedAgentBench task representations in this repository.
  Date/Author: 2026-03-14 / Codex

- Decision: remove legacy MedAgentBench analysis/evaluation utilities that depend on `tool_trace` output rather than porting them to Harbor.
  Rationale: they only served the deleted runner/evaluator path, and Harbor now owns its own submission/evaluation contract.
  Date/Author: 2026-03-14 / Codex

- Decision: keep historical ExecPlan documents that describe the old path, but remove live repo-facing docs that advertise it.
  Rationale: plan documents are historical records; user-facing docs and instructions should only describe supported workflows.
  Date/Author: 2026-03-14 / Codex

- Decision: remove the leftover `src/medcli/backends`, `src/medcli/tools`, and `src/medcli/utils` trees instead of preserving them as generic shared infrastructure.
  Rationale: they were no longer used by Harbor MedAgentBench or any remaining supported workflow, and keeping them would preserve dead entrypoints and dead tests.
  Date/Author: 2026-03-14 / Codex

- Decision: rename the generated Harbor task root from `harbor_tasks/` to `tasks/` and flatten `debug/harbor/` into `debug/`.
  Rationale: the Harbor path is now the only supported execution path, so the extra Harbor-specific directory prefixes only added noise rather than clarity.
  Date/Author: 2026-03-14 / Codex

- Decision: move raw MedAgentBench assets into `scripts/medagentbench/assets/` and remove the standalone local FHIR runtime scripts.
  Rationale: benchmark-specific assets belong with the benchmark-specific generation code, and Harbor debug is now the only supported local runtime path.
  Date/Author: 2026-03-14 / Codex

## Outcomes & Retrospective

The repository now has one MedAgentBench execution story instead of two, and the leftover generic runtime support that only served the deleted path is gone as well. The old OpenAI-style runtime, YAML manifest layer, legacy evaluator tooling, Azure OpenAI backend wrapper, and shared tool/client modules tied to that path are removed. The remaining Harbor implementation is also cleaner than it was during the transition: generated tasks now live under `tasks/`, raw assets live under `scripts/medagentbench/assets/`, benchmark-specific debug docs live under `debug/medagentbench/`, and Harbor debug is the only supported local runtime path.

The main lesson is that migration cleanup should happen promptly once the new path is stable. Leaving the frozen path in place long enough to compare behavior was useful, but after the Harbor task became fully runnable end-to-end, the extra code primarily created ambiguity about what was still supported.

## Context and Orientation

Before this cleanup, MedAgentBench had two parallel representations in the repository: a Harbor meta-task generated from raw JSON, and a legacy OpenAI-style runner path driven by generated YAML manifests under `tasks/`. The final Harbor path is centered on `scripts/medagentbench/generate_harbor_tasks.py`, `scripts/medagentbench/assets/`, `tasks/medagentbench/`, `jobs/medagentbench_meta.yaml`, `debug/`, and `scripts/medagentbench/harbor_evaluator.py`. The deleted path was centered on `run.py`, `demo.py`, `src/medcli/agents/oai_agent/`, `scripts/medagentbench/import_tasks.py`, and `scripts/medagentbench/evaluator.py`.

In this document, “legacy OAI path” means the deleted OpenAI-style runtime, YAML manifest importer, and evaluator stack. “Harbor path” means the raw-JSON-to-Harbor generation path plus Harbor job/debug execution. “Historical plan docs” means the archived ExecPlans in `.agent/plans/` that may still describe prior states for reference.

## Plan of Work

First, remove the old runtime and manifest pipeline together. Delete the `src/medcli/agents/oai_agent/` package, the top-level CLIs `run.py` and `demo.py`, the MedAgentBench YAML importer and legacy evaluator scripts under `scripts/medagentbench/`, and the MedAgentBench YAML manifests under `tasks/`. Remove the tests that only exercise that path so the test suite no longer depends on deleted entrypoints.

Second, rewrite repo-facing documentation and instructions so they no longer describe the deleted workflow. Update `README.md`, `AGENTS.md`, `CLAUDE.md`, `scripts/medagentbench/README.md`, `tasks/README.md`, and the benchmark-specific debug docs so Harbor is the only supported path. Keep `AGENTS.md` and `CLAUDE.md` identical.

Third, record the cleanup as its own ExecPlan milestone rather than retrofitting the already-completed raw-JSON Harbor conversion plan. The conversion plan remains the record of how Harbor became canonical; this plan records the subsequent deletion of the obsolete path.

## Concrete Steps

All commands below are run from the repository root.

1. Verify the Harbor generator still works.

       uv run python scripts/medagentbench/generate_harbor_tasks.py \
         --input-json scripts/medagentbench/assets/test_data_v2.json \
         --output-root tasks/medagentbench

   Expected outcome: the command prints JSON indicating `task_name` is `medagentbench` and `selected_task_ids` are `task1_1` through `task10_1`.

2. Run the Harbor-focused tests.

       .venv/bin/python -m pytest tests/test_harbor_task_generation.py tests/test_harbor_medagentbench_evaluator.py -q

   Expected outcome: both Harbor-focused test files pass.

3. Run the full test suite after removal.

       .venv/bin/python -m pytest -q

   Expected outcome: the remaining repository tests pass without any reference to `run.py`, `demo.py`, `src/medcli/agents/oai_agent/`, or the deleted MedAgentBench YAML/evaluator stack.

4. Audit for remaining live references.

       rg -n -S "oai_agent|run.py|demo.py|import_tasks.py|scripts/medagentbench/evaluate.py|scripts/medagentbench/evaluator.py|tasks/.*sources/medagentbench" \
         README.md AGENTS.md CLAUDE.md scripts tests src debug jobs

   Expected outcome: no matches outside intentionally historical plan documents.

## Validation and Acceptance

The cleanup is accepted when MedAgentBench can only be run through the Harbor path, the deleted legacy files are gone from the repository, and the remaining docs teach only the Harbor workflow. The Harbor generator, Harbor evaluator, and Harbor debug scripts must continue to work, the generated task must live under `tasks/medagentbench/`, and the full test suite must pass with the reduced surface.

Behaviorally, there must be no importable `medcli.agents.oai_agent` package, no top-level `run.py` or `demo.py`, no `tasks/*/sources/medagentbench/*.yaml` manifests, no `harbor_tasks/` tree, and no standalone local MedAgentBench FHIR runtime scripts. `AGENTS.md` and `CLAUDE.md` must remain byte-for-byte identical.

## Idempotence and Recovery

The file deletions are one-way at the repository level, but the Harbor task generator remains idempotent. If `tasks/medagentbench/` needs to be refreshed after the cleanup, rerun `scripts/medagentbench/generate_harbor_tasks.py`. If a documentation rewrite accidentally leaves stale references behind, rerun the repository-wide grep in this plan and fix the remaining matches. Do not restore the deleted legacy files as compatibility shims or recreate the old `harbor_tasks/` or `debug/harbor/` layouts.

## Artifacts and Notes

Expected remaining MedAgentBench commands after cleanup:

    uv run python scripts/medagentbench/generate_harbor_tasks.py \
      --input-json scripts/medagentbench/assets/test_data_v2.json \
      --output-root tasks/medagentbench
    uv run harbor run -c jobs/medagentbench_meta.yaml
    bash debug/medagentbench/smoke-meta-task.sh

Expected deleted commands after cleanup:

    uv run python run.py --task medagentbench ...
    uv run python demo.py ...
    uv run python scripts/medagentbench/import_tasks.py ...
    uv run python scripts/medagentbench/evaluate.py ...

This cleanup plan follows the completed Harbor raw-JSON conversion plan in `.agent/plans/harbor_raw_json_medagentbench_execplan.md`. That earlier plan explains how Harbor became canonical; this plan records the deletion of the now-obsolete parallel MedAgentBench runtime.

## Interfaces and Dependencies

The remaining MedAgentBench implementation surface is:
- `scripts/medagentbench/generate_harbor_tasks.py`
- `scripts/medagentbench/assets/`
- `scripts/medagentbench/normalization.py`
- `scripts/medagentbench/harbor_evaluator.py`
- `tasks/medagentbench/`
- `jobs/medagentbench_meta.yaml`
- `debug/` helpers

No code in `src/` or `tests/` should continue to import `medcli.agents.oai_agent` or rely on `tool_trace`-based MedAgentBench result rows.
