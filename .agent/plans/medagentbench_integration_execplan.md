# Integrate MedAgentBench Dataset and Tasks via Dockerized FHIR into EHR Co-Scientist

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

`PLANS.md` is checked into this repository at `/PLANS.md`; this document must be maintained in accordance with that file.

## Purpose / Big Picture

After this change, a user can run MedAgentBench tasks from this repository against a local FHIR endpoint that is started with Docker Compose, while the Python agent and benchmark runner remain local in the project virtual environment. This enables realistic FHIR-standard evaluation without introducing local Java/HAPI dependency conflicts. A user will be able to run one setup command, run benchmarks with configurable task selection (whole split, IDs, categories, or manifest file), and see task-level results plus pass@1 aggregate metrics.

## Related Context Pointer

For MedAgentBench background and design context used when refining this plan, see:

- `design/related_work/medagentbench_2501.14654.md`
- DeepWiki MCP for repository-grounded context discovery before integration decisions (use `mcp__deepwiki__read_wiki_structure`, `mcp__deepwiki__read_wiki_contents`, and `mcp__deepwiki__ask_question`).

## Progress

- [x] (2026-03-03 18:52Z) Created initial ExecPlan covering dataset ingestion, FHIR tooling, task execution loop, and benchmark evaluation.
- [x] (2026-03-04 01:26Z) Reviewed plan for PLANS.md compliance and repository drift; corrected backend default assumptions, interface duplication, and evidence wording for scaffold state.
- [x] (2026-03-04 23:40Z) Aligned repository architecture and docs to treat `tasks/` as first-class task packages (metadata + task-local runner/evaluator + fixtures), and created scaffold directories/files.
- [x] (2026-03-04 23:58Z) Updated architecture to organize `tasks/` by task type (README task taxonomy) and removed pre-created MedAgentBench task package scaffold pending integration milestones.
- [x] (2026-03-05 00:31Z) Implemented runnable scripts for setup, Dockerized FHIR startup/shutdown, and task import under `scripts/medagentbench/` to satisfy first three concrete steps.
- [x] (2026-03-05 01:07Z) Implemented idempotent MedAgentBench asset ingestion + schema validation + checksum generation in `scripts/medagentbench/setup.sh`, and documented usage in `scripts/medagentbench/README.md`.
- [x] (2026-03-05 01:07Z) Implemented Docker Compose-based local FHIR runtime with container healthcheck and compose-managed startup/shutdown scripts.
- [x] (2026-03-05 01:18Z) Implemented `FHIRClient`, MedAgentBench-aligned FHIR tool wrappers, and shared JSON HTTP retry utilities in `src/ehr_co_scientist/tools/` and `src/ehr_co_scientist/utils/http.py`.
- [x] (2026-03-05 04:10Z) Imported real MedAgentBench files (`data/medagentbench/test_data_v2.json`, `data/medagentbench/funcs_v1.json`) and grouped 300 tasks into repo task-type folders under `tasks/<task_type>/sources/medagentbench/` using an explicit 6-type alignment map.
- [x] (2026-03-04 19:30Z) Implemented MedAgentBench runner and evaluator CLIs (`experiments/run.py`, `scripts/medagentbench/evaluate.py`, `scripts/medagentbench/evaluator.py`) plus backend adapter and minimal agent loop wiring.
- [x] (2026-03-04 19:33Z) Added unit tests for FHIR client, task import, and evaluator, plus integration smoke test for Dockerized runtime workflow.
- [x] (2026-03-04 19:34Z) Validated end-to-end on small slices (explicit IDs, selector-based run, and `--max-tasks 3`) and generated summary artifacts.
- [x] (2026-03-04 21:05Z) Implemented and validated interactive terminal demo CLI (`experiments/demo.py`) for ad-hoc prompt/task execution against a running FHIR server.
- [x] (2026-03-04 23:19Z) Refactored `src/ehr_co_scientist/tools/fhir_tools.py` to be schema-first (tool definitions + handlers), added OpenAI function-tools JSON export helpers/CLI, and validated with new `tests/test_fhir_tools.py`.
- [x] (2026-03-05 00:30Z) Switched runtime to preloaded MedAgentBench FHIR image (`jyxsu6/medagentbench:latest`), diagnosed first factual QA failure with `--show-full-trace`, and fixed `patient_search` schema/handler to use MedAgentBench-style `family/given` matching (with full-name fallback).
- [x] (2026-03-05 08:10Z) Backfilled expected answers (`sol`) in `data/medagentbench/test_data_v2.json` for all query-derived groups supported by `refsol.py` (`task2`, `task4`, `task5`, `task6`, `task7`, `task9`, `task10`) using live FHIR queries against the MedAgentBench server.
- [x] (2026-03-05 05:22Z) Executed Milestone 7 repo-structure/tooling refactor: moved remaining benchmark artifacts into `scripts/medagentbench/` (including evaluation CLI), merged `FHIRClient` implementation into `fhir_tools.py` with compatibility shim, and extracted tool-agnostic registry/schema/export helpers into `src/ehr_co_scientist/tools/tooling/`.
- [x] (2026-03-05 10:22Z) Added evaluation-mode write-tool short-circuit: when `--evaluation-mode` is enabled, `run_task` now terminates immediately on write-tool calls (`vital_create`, `procedure_create`, `medicationrequest_create`) without executing HTTP writes; wired through both `experiments/run.py` and `experiments/demo.py` flags and validated with new agent/tool tests.
- [x] (2026-03-05 11:05Z) Enforced per-task `allowed_tools` in benchmark runs: `experiments/run.py` now passes task-scoped OpenAI tool schemas and `allowed_tools` policy into `run_task`, and `run_task` now blocks/terminates on disallowed tool calls (`blocked_not_allowed`) for both native function-calling and fallback tool-call paths.
- [x] (2026-03-05 13:45Z) Refactored tool registration to a central decorator-backed catalog (`src/ehr_co_scientist/tools/catalog.py`) with explicit module imports, and removed transitional wrapper usage from `fhir_tools.py`.
- [x] (2026-03-05 14:05Z) Standardized canonical tool IDs to function-safe underscore names (for example `patient_search`, `vital_create`) and removed `function_name` alias mapping/translation from shared tooling and agent dispatch.
- [x] (2026-03-05 14:12Z) Removed unused compatibility adapter `scripts/medagentbench/fhir_medagentbench_tools.py` after verifying no runtime references; updated `scripts/medagentbench/README.md`.
- [x] (2026-03-05 14:20Z) Consolidated redundant agent/tool tests via parametrization to reduce duplicate fallback/native cases while preserving coverage.
- [x] (2026-03-05 15:08Z) Decoupled `run_task` from direct FHIR client construction by introducing shared `ToolRuntime`; moved FHIR client instantiation to caller entrypoints (`experiments/run.py`, `experiments/demo.py`) and updated tool handlers/dispatch to consume `tool_runtime`.
- [x] (2026-03-05 15:16Z) Refactored `run_task` internals with dedicated helper functions for policy checks, termination payloads, and tool execution to reduce core-loop complexity without changing behavior.
- [x] (2026-03-05 15:32Z) Split monolithic `src/ehr_co_scientist/agent.py` into package modules under `src/ehr_co_scientist/agent/` (`core.py`, `parsing.py`, `policy.py`, `tool_exec.py`) while preserving public imports via `src/ehr_co_scientist/agent/__init__.py`.
- [x] (2026-03-05 16:05Z) Implemented action-trace evaluation overrides for MedAgentBench writing tasks `task3_*` and `task8_*` in `scripts/medagentbench/evaluator.py`, aligned with `data/medagentbench/refsol.py` semantics (tool/payload validation over final-answer matching).
- [x] (2026-03-05 23:01Z) Sampled and executed two writing tasks (`task3_1`, `task8_1`) with actual backend + FHIR runtime, analyzed payload-shape mismatches, tightened write-call guidance, and updated evaluator normalization (list/dict shape compatibility) so both tasks now pass under action-trace scoring.
- [x] (2026-03-06 01:06Z) Removed schema post-processing and switched to strict-native tool schemas directly in `src/ehr_co_scientist/tools/fhir_tools.py` (nullable optional fields + explicit `required` + `additionalProperties: false` on object nodes), then revalidated writing-task tool invocation with `gpt-5.2`.
- [x] (2026-03-06 01:20Z) Added deterministic action-trace evaluation overrides for writing-task groups and diagnostics, then simplified evaluator modes to keep strict deterministic scoring as baseline.
- [x] (2026-03-06 03:58Z) Added `llm_assisted` evaluator mode with batched strict-failure adjudication via Azure backend reuse (`o4-mini` default), including batch-size controls, split-retry fallback, and `llm_judgments.jsonl` audit artifacts.
- [x] (2026-03-06 04:25Z) Removed `balanced` mode to reduce heuristic rule sprawl; evaluator now supports `strict` and `llm_assisted` only, with default LLM judge endpoint set to `hanover-openai-east`.
- [x] (2026-03-06 01:30Z) Added expected-answer (`sol`) derivation pathway for `task3_*` records via action/payload validation semantics in evaluator/runtime flow (non-final-answer scoring path).
- [x] (2026-03-06 01:30Z) Added expected-answer (`sol`) derivation pathway for `task8_*` records via action/payload validation semantics in evaluator/runtime flow (non-final-answer scoring path).
- [x] (2026-03-06 22:47Z) Refactored benchmark flow to keep `experiments/run.py` generation-only: removed in-run expected-answer scoring (`success`/`final_answer_mismatch`) and centralized query success computation in `scripts/medagentbench/evaluator.py`.
- [x] (2026-03-06 22:49Z) Updated evaluator matching to treat numeric-like strings as numeric values during expected-answer comparison (for example `1`, `1.0`, `-1.0`), reducing false negatives for query tasks.
- [x] (2026-03-06 22:50Z) Re-ran strict evaluation on 20-task sample (`sample_2_per_type_20260306_escalated`) and regenerated strict error-summary JSON (`error_summary_strict.json`): `pass@1=0.60`, `12/20` passed, `8` failures.
- [x] (2026-03-06 23:35Z) Replaced evaluation-mode write-tool early termination with simulated tool feedback in agent loop; write tools now append `"The action has been taken. Please return the final answer."` and continue generation without executing writes.
- [x] (2026-03-06 23:40Z) Renamed tool policy metadata from `stop_on_call_in_evaluation` to `pretend_on_call_in_evaluation` and updated catalog/policy helpers plus tests accordingly.
- [x] (2026-03-07 00:10Z) Added task-group-aware query matcher in evaluator (`task1` string MRN, `task2/4/5/6/7/9` numeric, `task10` list `[value,timestamp]` or `[-1]`) and reran sampled pipelines.
- [x] (2026-03-07 00:16Z) Re-sampled 2 tasks per `task1..task10` and reran full pipeline with elevated permissions (`sample_2_per_type_20260306_161445_escalated`): strict `pass@1=0.90` (`18/20`), action `10/10`, query `8/10`; strict error summary now has 4 failures.

## Surprises & Discoveries

- Observation: The current repository is still largely a scaffold: `src/ehr_co_scientist/agent.py` and `config/agent.yaml` are empty, and there are very few task/benchmark/test/runtime files; however, a non-empty Azure backend module now exists.
  Evidence: `wc -c src/ehr_co_scientist/agent.py config/agent.yaml` reported `0` bytes for both files, while `src/ehr_co_scientist/backends/azure_openai.py` is present and non-empty as of 2026-03-04.

- Observation: The mostly scaffold status means integration work must include first implementations for runner/evaluator abstractions instead of only adding MedAgentBench-specific glue.
  Evidence: `rg --files src tests tasks benchmarks experiments` returned only a small set of files (core package stubs, one backend module, and one CLI examples test) on 2026-03-04.

- Observation: Real MedAgentBench task records in `test_data_v2.json` do not include an explicit task-type field; grouping must be inferred from `id` prefixes (`task1`..`task10`) and instruction patterns.
  Evidence: Parsing `data/medagentbench/test_data_v2.json` showed keys `id`, `instruction`, `context`, `eval_MRN`, optional `sol`, with no `task_type`/`category` fields.

- Observation: Concrete step 4 (Azure backend smoke) is environment-dependent and requires valid Azure identity/endpoint access from the execution environment.
  Evidence: Endpoint and credential checks must succeed for direct Azure completion calls.

- Observation: The temporary split between dotted tool IDs and function-safe names created avoidable complexity in dispatch and policy enforcement.
  Evidence: Runtime previously required alias maps and resolution logic; this was removed after converting canonical tool IDs to underscore names.

- Observation: For task `task1_1`, HAPI/MedAgentBench patient lookup returned zero when queried with `name="Peter Stafford"` + `birthdate`, but returned the expected patient when queried with `family="Stafford"` + `given="Peter"` + `birthdate`.
  Evidence: Demo full trace showed `Patient?...&name=Peter%20Stafford` -> `total: 0`; direct FHIR query with family/given returned `total: 1` and MRN `S6534835`.

- Observation: Non-`task1` expected-answer backfill is partially automatable; `refsol.py` provides query-derived reference logic for `task2/task4/task5/task6/task7/task9/task10`, but `task3` and `task8` are action-validation tasks that do not currently expose a direct query-to-`sol` mapping.
  Evidence: Backfill run updated 210 records and left `task3`/`task8` `sol` empty by design (`non_empty_sol_by_group` includes task groups above, while `empty_sol_by_group` remains `task3:30`, `task8:30`).

- Observation: Creating runtime clients inside `run_task` tightly couples agent orchestration to a specific tool backend and makes multi-runtime task support awkward.
  Evidence: Prior implementation unconditionally built `FHIRClient` inside `run_task`; refactor introduced `ToolRuntime` so clients are supplied by caller entrypoints.

- Observation: Non-elevated sandbox runs can fail Azure identity flows due to write permissions on Azure CLI session files, causing widespread `runtime_exception` noise in benchmark results.
  Evidence: Repeated permission errors for `/home/shezhan/.azure/az.sess` were observed during non-escalated runs; rerunning with elevated permissions restored normal scoring behavior.

## Decision Log

- Decision: Use Dockerized FHIR as the default runtime for MedAgentBench integration; do not provide non-Docker local Java server as first-class path in this milestone.
  Rationale: Docker isolates the heavy FHIR server dependencies and minimizes future conflicts when additional datasets/benchmarks are added.
  Date/Author: 2026-03-03 / Codex

- Decision: Keep agent runtime and benchmark orchestration outside Docker.
  Rationale: The project’s Python workflow (`uv`, `pytest`, `ruff`) remains simple while only FHIR infrastructure is containerized.
  Date/Author: 2026-03-03 / Codex

- Decision: Add a small, idempotent ingestion layer to pin benchmark assets and provide deterministic local paths.
  Rationale: Benchmark reproducibility depends on stable task files and reference assets, not ad-hoc manual downloads.
  Date/Author: 2026-03-03 / Codex

- Decision: Introduce a dataset-agnostic internal task schema plus selector filters in the runner.
  Rationale: The project will later combine multiple datasets and may reuse only subsets of MedAgentBench or rebind equivalent tasks to another database; this requires explicit task selection and backend-agnostic task descriptors.
  Date/Author: 2026-03-03 / Codex

- Decision: Standardize MedAgentBench integration on the existing Azure OpenAI backend and default model `gpt-5.2`; do not reference unavailable Claude models in runnable steps.
  Rationale: Current repository runtime only has `src/ehr_co_scientist/backends/azure_openai.py` as an implemented backend path, so benchmark integration must use that backend for executable, reproducible commands.
  Date/Author: 2026-03-04 / Codex

- Decision: Keep runner/backend boundaries provider-agnostic even while using Azure OpenAI as the only implemented backend in this milestone.
  Rationale: MedAgentBench orchestration (task loading, tool traces, scoring, selectors) should not depend on provider-specific request/response shapes so future backends can be added by implementing one adapter interface.
  Date/Author: 2026-03-04 / Codex

- Decision: Remove hardcoded endpoint defaults from runnable commands and interface requirements; require explicit endpoint configuration via CLI flags or environment variables.
  Rationale: Endpoint names are deployment-specific and not portable for a novice clone; hardcoded values reduce reproducibility and cause avoidable startup failures.
  Date/Author: 2026-03-04 / Codex

- Decision: Organize `tasks/` by task type from `README.md`, not by benchmark/source. MedAgentBench artifacts are mapped into the relevant task-type packages during integration.
  Rationale: Task type taxonomy is the durable public contribution, while benchmark source is a transient provenance dimension.
  Date/Author: 2026-03-04 / User+Codex

- Decision: Align MedAgentBench 6 task types to repo task taxonomy using explicit mapping and create new repo task types only where no existing type is semantically correct.
  Rationale: Keeps benchmark compatibility while preserving reusable, task-type-centric organization in this repository.
  Date/Author: 2026-03-05 / User+Codex

- Decision: Treat `fhir_tools.py` as the single source of truth for both runtime tool dispatch and OpenAI function-calling schemas.
  Rationale: Prevents drift between advertised tools and executable handlers, and enables deterministic `--tools` JSON generation for `gpt-5.2` runs.
  Date/Author: 2026-03-04 / Codex

- Decision: Use the MedAgentBench preloaded server image (`jyxsu6/medagentbench:latest`) as the benchmark runtime image for data-faithful task execution.
  Rationale: The generic HAPI image has no benchmark patient data; the preloaded image includes the benchmark dataset and supports real task validation.
  Date/Author: 2026-03-05 / User+Codex

- Decision: In evaluation mode, simulate write-tool success and continue the loop instead of terminating immediately.
  Rationale: Returning a synthetic tool output lets the model produce a final answer while still avoiding DB mutation; this improves alignment with full turn-taking tool-call flows.
  Date/Author: 2026-03-06 / User+Codex

- Decision: Treat `allowed_tools` in task manifests as an enforced execution policy (not metadata-only) by restricting advertised function schemas per task and blocking disallowed tool calls at runtime.
  Rationale: Defense-in-depth avoids policy bypass when models emit unadvertised tools and keeps benchmark behavior aligned with task manifests.
  Date/Author: 2026-03-05 / User+Codex

- Decision: Use function-safe canonical tool IDs directly (for example `patient_search`, `vital_create`) and remove `function_name` alias metadata.
  Rationale: Eliminates duplicate naming sources and alias translation paths, reducing registry drift and dispatch bugs.
  Date/Author: 2026-03-05 / User+Codex

- Decision: Centralize tool definitions/registry materialization in `src/ehr_co_scientist/tools/catalog.py` with explicit module imports instead of dynamic module loading.
  Rationale: Keeps registration mechanics predictable and discoverable while retaining extensibility for future non-FHIR tools.
  Date/Author: 2026-03-05 / User+Codex

- Decision: Pass a generic `ToolRuntime` object into agent/tool dispatch and construct concrete clients at orchestration entrypoints instead of inside `run_task`.
  Rationale: Keeps the agent loop backend-agnostic for future non-FHIR tasks and cleanly separates orchestration from client wiring.
  Date/Author: 2026-03-05 / User+Codex

- Decision: Prefer strict-native OpenAI function schemas in source definitions (`fhir_tools.py`) instead of runtime schema mutation.
  Rationale: Makes schema behavior explicit, auditable, and stable across tooling/export paths.
  Date/Author: 2026-03-06 / User+Codex

- Decision: Keep evaluator surface minimal (`strict` + `llm_assisted`) and remove `balanced`.
  Rationale: `balanced` required growing hand-crafted heuristics; batched LLM adjudication provides cleaner secondary scoring for strict failures with auditable artifacts.
  Date/Author: 2026-03-06 / User+Codex

- Decision: Keep `experiments/run.py` strictly as inference/generation and move all success/failure determination into evaluator code.
  Rationale: Single source of truth for scoring prevents drift and keeps run artifacts backend-agnostic.
  Date/Author: 2026-03-06 / User+Codex

## Outcomes & Retrospective

Implemented outcomes now include: grouped ingestion of all 300 real MedAgentBench tasks into task-type folders, Dockerized FHIR runtime with health checks, provider-neutral runner/evaluator CLIs, reusable FHIR tool modules, canonicalized tool catalog/dispatch abstractions, and passing unit/integration coverage for the implemented scope. Measured validation evidence:

- `uv run pytest tests/ -q` -> `20 passed, 2 skipped`.
- `RUN_MEDAGENTBENCH_SMOKE=1 pytest tests/integration/test_medagentbench_smoke.py -q` -> `1 passed`.
- Run artifacts generated under `experiments/results/medagentbench/20260304T191914Z`, `...191921Z`, and `...191930Z`.
- Evaluation artifacts generated: `experiments/results/medagentbench/20260304T191930Z/summary.json` and `summary.md`.
- Azure backend rerun without `--endpoint-name` succeeded on 2026-03-04:
  - `uv run ehr-azure-openai --example direct --model gpt-5.2 --prompt "Reply with exactly: backend_ok"` returned `backend_ok`.
  - Additional run IDs with actual backend: `20260304T193527Z`, `20260304T193547Z`, `20260304T194005Z`; evaluation artifact at `experiments/results/medagentbench/20260304T194005Z/summary.json`.
- Interactive demo validation on 2026-03-04:
- `printf 'For patient S2874099, summarize known conditions.\nquit\n' | uv run python experiments/demo.py --backend azure_openai --model gpt-5.2 --api-version 2025-03-01-preview --fhir-base-url http://localhost:8080/fhir` executed successfully and returned structured JSON output with `task_id`, `final_answer`, `rounds_used`, and tool trace summary fields.
- Function-tools schema export and dispatch alignment validation on 2026-03-04:
  - `uv run pytest tests/test_fhir_tools.py tests/test_fhir_client.py tests/test_medagentbench_task_import.py -q` -> `10 passed`.
  - `uv run ruff check src/ehr_co_scientist/tools/fhir_tools.py tests/test_fhir_tools.py` -> `All checks passed`.
- Real dataset runtime + first-task validation on 2026-03-05:
  - After switching to `jyxsu6/medagentbench:latest`, `Patient?identifier=S6534835` returned `total: 1`.
  - Full-trace demo run with first factual task initially failed due to `name`-based search (`total: 0`), then succeeded after schema/handler fix.
  - `printf '<task1_1 prompt>\nquit\n' | uv run python experiments/demo.py ... --show-full-trace` now returns final answer `S6534835`.
- Evaluator mode simplification + LLM batch adjudication validation on 2026-03-06:
  - Strict-mode baseline over 100-sample slice: `pass@1 = 0.30`.
  - LLM-assisted mode (`o4-mini`, batch size 20, endpoint `hanover-openai-east`) over same slice: `pass@1 = 0.76`.
  - Audit traces emitted to `experiments/results/medagentbench/<run>/llm_judgments.jsonl`.
- Generation/evaluation boundary refactor validation on 2026-03-06:
  - `experiments/run.py` output rows no longer include `success`; evaluator derives query/action outcomes from `expected_answer`, `final_answer`, and action traces.
  - Re-evaluated `experiments/results/medagentbench/sample_2_per_type_20260306_escalated/results.jsonl` (strict): `pass@1 = 0.60` (`12/20`), `query 8/10`, `action 4/10`.
  - Regenerated strict failure artifact at `experiments/results/medagentbench/sample_2_per_type_20260306_escalated/error_summary_strict.json` with `total_failed_rows = 8`.
- Evaluation-mode simulation + task-aware matcher validation on 2026-03-07:
  - Agent evaluation mode now simulates write-tool output text and continues generation; no HTTP writes are executed.
  - Re-sampled 20-task run (`experiments/results/medagentbench/sample_2_per_type_20260306_161445_escalated/results.jsonl`) re-evaluated to `pass@1 = 0.90` (`18/20`), with `action 10/10` and `query 8/10`.
  - Strict failure artifact regenerated at `experiments/results/medagentbench/sample_2_per_type_20260306_161445_escalated/error_summary_strict.json` (`4` failed rows: `2` payload mismatch, `2` final answer mismatch).

## Context and Orientation

This repository currently provides a project skeleton for an EHR agent system but not yet a functioning benchmark runtime. The key folders relevant to this plan are `src/ehr_co_scientist/` for shared runtime code, `tasks/` for first-class task-type packages (metadata + task-local adapters + fixtures), `experiments/` for runnable orchestration entry points, and `scripts/` for setup/runtime/evaluation automation. MedAgentBench is an external benchmark with a FHIR-based task environment and de-identified patient data exposed through FHIR APIs. In this plan, “FHIR server” means an HTTP service implementing the HL7 FHIR REST patterns used by MedAgentBench tasks. “Task adapter” means the code that transforms MedAgentBench task JSON into this repository’s internal task execution request shape and routes it to the matching task-type package.

The implementation target is not to re-create MedAgentBench internals. The target is to add a compatible benchmark integration layer that can run MedAgentBench tasks against a configured FHIR endpoint, collect outputs, and score the run with pass@1 and category-level breakdowns. The implementation also must define a stable internal task contract with fields that separate task intent from backend source details so task prompts can later be rebound to non-MedAgentBench datasets.

## Plan of Work

Milestone 1 establishes reproducible benchmark assets and container orchestration.

Create `scripts/medagentbench/setup.sh` to download or verify required MedAgentBench artifacts into `data/medagentbench/`. The script must be idempotent: if files already exist and checksums match, it exits without modifying files. Create `scripts/medagentbench/docker-compose.yaml` with a single `fhir` service exposing port `8080`, and add `scripts/medagentbench/fhir_up.sh` and `scripts/medagentbench/fhir_down.sh` wrappers. Add `scripts/medagentbench/README.md` documenting prerequisites, expected files, and one-command startup.

Milestone 2 adds foundational runtime config and FHIR client tools.

Populate `config/agent.yaml` with a concrete model/tool config that includes FHIR query and action tools, sets backend `azure_openai`, and uses default model `gpt-5.2` unless overridden by CLI. Implement a typed FHIR client class (now co-located in `src/ehr_co_scientist/tools/fhir_tools.py`) that supports: search (`GET /<Resource>?...`), create (`POST /<Resource>`), and capability check (`GET /metadata`). Implement reusable FHIR tool wrappers in `src/ehr_co_scientist/tools/fhir_tools.py` (`patient_search`, `lab_search`, `condition_search`, `procedure_search`, `medicationrequest_search`, plus create endpoints used by action tasks). Keep these tools dataset-agnostic so they can be reused across MedAgentBench and future task suites. Add shared request/retry utilities in `src/ehr_co_scientist/utils/http.py`.

Milestone 3 introduces task ingestion, task selection, and execution loop.

Create and/or populate task-type packages under `tasks/<task_type>/` (for example `tasks/cohort_construction/`, `tasks/temporal_reasoning/`) with `task.yaml`, `runner.py`, `evaluator.py`, and canonical manifest files generated from source JSON using `scripts/medagentbench/import_tasks.py`. The import script must map each source task to fields required by this repository (`task_id`, `category`, `difficulty`, `instruction`, `expected_answer`, `required_actions`, split labels, and `backend_profile`) and write split manifests under task-type package paths such as `tasks/<task_type>/sources/medagentbench/<split>.yaml`. Add a generic selector file format at `tasks/selectors/*.yaml` with include/exclude rules by `task_id`, category, difficulty, and task type (query or action). Implement `src/ehr_co_scientist/agent/core.py` with a minimal loop supporting up to 8 tool interaction rounds to align with MedAgentBench protocol. Add `experiments/run.py` CLI accepting `--task medagentbench`, `--split`, `--max-tasks`, `--backend`, `--model`, `--fhir-base-url`, `--task-ids`, `--task-categories`, `--task-selector-file`, `--endpoint-name`, and `--api-version`, where `--backend` defaults to `azure_openai`. Implement backend dispatch in runner through a provider-neutral adapter call (for example `run_chat_completion(backend, config, messages, **kwargs)`) with an Azure-backed implementation for this milestone.

Milestone 4 adds evaluation and reporting.

Implement `scripts/medagentbench/evaluate.py` with MedAgentBench scorer logic in `scripts/medagentbench/evaluator.py`. Scoring must compute pass@1 overall and per category, and separate query versus action tasks. Persist machine-readable results to `experiments/results/medagentbench/<timestamp>/results.jsonl` and summary metrics to `summary.json` and `summary.md`. Add simple error taxonomy counters for tool schema violations, HTTP failures, and final-answer mismatch.

Milestone 5 hardens quality with tests and smoke runs.

Add unit tests in `tests/test_fhir_client.py`, `tests/test_medagentbench_task_import.py`, and `tests/test_medagentbench_evaluator.py`. Add an integration smoke test `tests/integration/test_medagentbench_smoke.py` that runs a tiny fixed subset (for example 3 tasks) against the running Dockerized FHIR endpoint. Update `README.md` with a “MedAgentBench” section linking to setup, run, and evaluate commands.

Milestone 6 adds an interactive demo mode for terminal users.

Assuming FHIR runtime is already running, add a CLI entrypoint `experiments/demo.py` that starts an interactive prompt loop in terminal. A user can type an ad-hoc clinical task/prompt, the system runs one task execution flow using existing agent/backend/tool stack, and prints structured output (final answer, rounds used, and tool trace summary). The demo must support `--backend`, `--model`, `--api-version`, and `--fhir-base-url`, and should exit cleanly on `exit`/`quit`/EOF.

Milestone 7 consolidates structure and extracts shared tooling abstractions.

Refactor repository boundaries so all MedAgentBench-specific operational/runtime code lives under `scripts/medagentbench/`, including any remaining benchmark-coupled adapters/assets currently under `benchmarks/`. Refactor `src/ehr_co_scientist/tools/fhir_client.py` into `src/ehr_co_scientist/tools/fhir_tools.py` so FHIR transport/query logic is co-located with FHIR tool implementations. Then extract tool-agnostic helpers (registry, schema definitions, OpenAI tools export helpers such as `get_openai_function_tools`, and common property/normalization utilities) out of `fhir_tools.py` into a new shared non-FHIR module (for example `src/ehr_co_scientist/tools/tooling/`) so future non-FHIR tools can reuse the same framework. Keep backward-compatible wrapper functions during transition, update imports/tests/docs, and remove wrappers only after parity validation.

## Concrete Steps

All commands below are run from `/home/shezhan/repos/ehr-co-scientist`.

1. Start the FHIR service (required before `setup.sh` expected-answer backfill).

    bash scripts/medagentbench/fhir_up.sh
    curl -sSf http://localhost:8080/fhir/metadata | head -c 200

Expected: the second command prints JSON containing a FHIR CapabilityStatement payload.

2. Prepare MedAgentBench assets (download + format + expected-answer backfill).

    bash scripts/medagentbench/setup.sh

Expected: `data/medagentbench/test_data_v2.json`, `funcs_v1.json`, and `refsol.py` exist; JSON files are pretty-formatted; setup logs include validation counts and checksum write confirmation.

3. Create asset and orchestration files and scripts.

    uv run python -m pytest -q

Expected: existing tests pass (initially may be zero tests).

4. Import and normalize MedAgentBench task files.

    uv run python scripts/medagentbench/import_tasks.py \
      --input data/medagentbench/test_data_v2.json \
      --funcs-json data/medagentbench/funcs_v1.json \
      --output-root tasks \
      --split std

Expected: grouped output files exist under `tasks/<task_type>/sources/medagentbench/std.yaml` with deterministic ordering by `task_id`.

5. Smoke-test Azure OpenAI backend defaults used by benchmark runs.

    uv run ehr-azure-openai \
      --example direct \
      --model gpt-5.2 \
      --prompt "Reply with exactly: backend_ok"

Expected: command returns a direct chat completion payload from Azure OpenAI and confirms default endpoint/model wiring.

6. Run a filtered benchmark slice by explicit task IDs.

    uv run python experiments/run.py \
      --task medagentbench \
      --split std \
      --task-ids task1_1,task4_1,task9_1 \
      --model gpt-5.2 \
      --api-version 2025-03-01-preview \
      --fhir-base-url http://localhost:8080/fhir

Expected: run executes exactly those task IDs, and the run metadata file records the resolved selector.

7. Run a filtered benchmark slice by selector file.

    uv run python experiments/run.py \
      --task medagentbench \
      --split std \
      --task-selector-file tasks/selectors/medagentbench_query_easy.yaml \
      --model gpt-5.2 \
      --api-version 2025-03-01-preview \
      --fhir-base-url http://localhost:8080/fhir

Expected: only tasks matching selector rules are executed, and skipped counts by rule are reported.

8. Run a tiny benchmark slice with max-task cap.

    uv run python experiments/run.py \
      --task medagentbench \
      --split std \
      --max-tasks 3 \
      --model gpt-5.2 \
      --api-version 2025-03-01-preview \
      --fhir-base-url http://localhost:8080/fhir

Expected: run directory under `experiments/results/medagentbench/` with `results.jsonl` containing 3 records.

9. Evaluate run outputs.

    uv run python scripts/medagentbench/evaluate.py \
      --task medagentbench \
      --results experiments/results/medagentbench/<run-id>/results.jsonl

Expected: printed summary includes `pass_at_1`, category breakdowns, and query/action split.

10. Run quality gates.

    uv run pytest tests/
    uv run ruff check src/ tests/
    uv run ruff format src/ tests/

Expected: tests pass, lint passes, formatter makes no additional changes on second run.

11. Run interactive demo CLI (FHIR server already running).

    uv run python experiments/demo.py \
      --backend azure_openai \
      --model gpt-5.2 \
      --api-version 2025-03-01-preview \
      --fhir-base-url http://localhost:8080/fhir

Expected: terminal enters interactive mode, accepts free-form task prompts, and prints task result payload per prompt until user exits with `quit`/`exit`.

## Validation and Acceptance

Acceptance is achieved when a novice can clone the repository, run the MedAgentBench setup script, start the Dockerized FHIR service, execute at least one MedAgentBench split through `experiments/run.py`, execute a filtered subset through selector configuration, and generate scoring outputs through `scripts/medagentbench/evaluate.py` without manually editing source files.

The concrete observable checks are:

- `GET http://localhost:8080/fhir/metadata` succeeds while Docker service is up.
- `experiments/run.py` produces one JSONL record per attempted task with final answer, tool trace, and success flag.
- `experiments/run.py` supports task selection by explicit IDs, category filters, and selector file, and records the effective resolved task set in run metadata.
- `experiments/run.py` records backend call metadata including backend name, model name, endpoint name, and API version for reproducibility.
- `scripts/medagentbench/evaluate.py` writes both machine-readable and human-readable summaries.
- `tests/integration/test_medagentbench_smoke.py` passes when the FHIR service is running.
- `experiments/demo.py` provides interactive terminal workflow and returns structured outputs for user-entered prompts while FHIR server is running.

## Idempotence and Recovery

The setup scripts must be idempotent. Re-running `scripts/medagentbench/setup.sh` should only re-download missing or checksum-mismatched assets under `data/medagentbench/`. Re-running `scripts/medagentbench/fhir_up.sh` should either report the existing running service or restart cleanly. If container startup fails due to a stale container, `scripts/medagentbench/fhir_down.sh` followed by `scripts/medagentbench/fhir_up.sh` must recover. Task import must overwrite outputs deterministically so repeated imports do not create drift.

No destructive operations on unrelated repository files are allowed. All generated run artifacts must stay under `experiments/results/medagentbench/`.

## Artifacts and Notes

Expected key file additions and modifications:

- `scripts/medagentbench/setup.sh`: Idempotent downloader/verifier for MedAgentBench assets under `data/medagentbench/`.
- `scripts/medagentbench/fhir_up.sh`: One-command wrapper to start the Dockerized FHIR service with health checks.
- `scripts/medagentbench/fhir_down.sh`: Wrapper to stop and cleanly tear down the Dockerized FHIR service.
- `scripts/medagentbench/import_tasks.py`: Deterministic converter from source MedAgentBench task JSON into internal canonical YAML schema, including grouped output under `tasks/<task_type>/sources/medagentbench/`.
- `data/medagentbench/test_data_v2.json`: Real MedAgentBench task dataset (300 tasks) used as import source of truth.
- `data/medagentbench/funcs_v1.json`: MedAgentBench tool/function schema file used for allowed-tool metadata during import.
- `data/medagentbench/task_type_mapping.yaml`: Explicit alignment map from MedAgentBench 6 task types to repo task types and source task groups.
- `tasks/selectors/medagentbench_query_easy.yaml`: Example selector manifest demonstrating include/exclude filtering for a simple query subset.
- `scripts/medagentbench/README.md`: Operator guide for setup, startup, task import, benchmark execution, and troubleshooting.
- `scripts/medagentbench/docker-compose.yaml`: Container orchestration definition for the local MedAgentBench-compatible FHIR runtime.
- `scripts/medagentbench/evaluator.py`: MedAgentBench scoring logic that computes pass@1 and category/query-action breakdowns.
- `tasks/<task_type>/task.yaml`: Task-type package metadata with manifest and entrypoint wiring.
- `tasks/<task_type>/sources/medagentbench/std.yaml`: Canonical normalized task manifest for standard split routed to the corresponding task type.
- `tasks/data_aggregation/task.yaml`: New task type package metadata for aggregation-style tasks.
- `tasks/clinical_data_recording/task.yaml`: New task type package metadata for chart-recording tasks.
- `tasks/care_ordering/task.yaml`: New task type package metadata for non-medication ordering/referral tasks.
- `tasks/<task_type>/runner.py`: Task-local execution adapter invoked by top-level experiment runner.
- `tasks/<task_type>/evaluator.py`: Task-local scoring adapter used by benchmark harness.
- `experiments/run.py`: Main benchmark runner CLI handling task resolution, agent execution, backend dispatch, and result persistence.
- `scripts/medagentbench/evaluate.py`: Top-level MedAgentBench evaluation CLI entrypoint that loads run outputs and writes summary metrics artifacts.
- `experiments/demo.py`: Interactive terminal demo CLI for ad-hoc prompt/task execution using the same backend/tool pipeline.
- `src/ehr_co_scientist/agent/core.py`: Agent loop implementation coordinating prompt construction, tool calls, and final answer extraction.
- `src/ehr_co_scientist/backends/__init__.py`: Backend package exports and registry entrypoint for available backend adapters.
- `src/ehr_co_scientist/backends/adapter.py`: Provider-neutral backend interface and dispatch layer used by the runner.
- `src/ehr_co_scientist/backends/azure_openai.py`: Azure OpenAI backend implementation and CLI smoke-test utility used as the default backend.
- `src/ehr_co_scientist/tools/catalog.py`: Central tool catalog with explicit tool-module imports and materialized registry/definitions.
- `src/ehr_co_scientist/tools/fhir_tools.py`: Reusable FHIR client + tool wrappers plus schema-first tool definitions that can export OpenAI-compatible function-calling `tools` JSON.
- `tests/test_fhir_tools.py`: Unit tests for function-tools schema export, registry/schema consistency, and canonical-name dispatch.
- `src/ehr_co_scientist/utils/http.py`: Shared HTTP retry/timeout/error-handling helpers used by FHIR and backend integrations.
- `tests/test_fhir_client.py`: Unit tests for FHIR client request building, response parsing, and retry/error behavior.
- `tests/test_medagentbench_task_import.py`: Unit tests ensuring deterministic and schema-correct MedAgentBench task import output.
- `tests/test_medagentbench_evaluator.py`: Unit tests for evaluator metrics, category splits, and error taxonomy accounting.
- `tests/integration/test_medagentbench_smoke.py`: Integration smoke test covering minimal end-to-end execution against a running local FHIR service.
- `README.md`: Project-level documentation updates adding MedAgentBench quickstart and command references.
- `config/agent.yaml`: Default runtime configuration for backend/model/tool wiring used by MedAgentBench runs.

When implementing this plan, append short command transcripts and metric snippets here as evidence, keeping only output that proves milestone completion.

## Interfaces and Dependencies

Use the existing Python 3.11+ project toolchain and dependencies already managed by `pyproject.toml`. Add new dependencies only when strictly needed and through `uv add`.

Required runtime interfaces to exist after implementation:

In `src/ehr_co_scientist/tools/fhir_tools.py`, define:

    class FHIRClient:
        def __init__(self, base_url: str, timeout_s: float = 30.0) -> None: ...
        def capability_statement(self) -> dict: ...
        def search(self, resource_type: str, params: dict[str, str]) -> dict: ...
        def create(self, resource_type: str, resource_body: dict) -> dict: ...

In `src/ehr_co_scientist/tools/fhir_tools.py`, define:

    def patient_search(client: FHIRClient, **kwargs) -> dict: ...
    def lab_search(client: FHIRClient, **kwargs) -> dict: ...
    def condition_search(client: FHIRClient, **kwargs) -> dict: ...
    def procedure_search(client: FHIRClient, **kwargs) -> dict: ...
    def medicationrequest_search(client: FHIRClient, **kwargs) -> dict: ...
    def vital_create(client: FHIRClient, resource: dict) -> dict: ...
    def procedure_create(client: FHIRClient, resource: dict) -> dict: ...
    def medicationrequest_create(client: FHIRClient, resource: dict) -> dict: ...

In `experiments/run.py`, define CLI entrypoint:

    def main() -> None: ...

with flags `--task`, `--split`, `--max-tasks`, `--backend`, `--model`, `--fhir-base-url`, `--task-ids`, `--task-categories`, `--task-selector-file`, `--endpoint-name`, and `--api-version`, plus output directory selection.
with backend wiring that routes completion calls through a provider-neutral backend adapter, defaulting to `--backend azure_openai` and `--model gpt-5.2`. Endpoint name must come from `--endpoint-name` or an environment-backed config value.

In `src/ehr_co_scientist/backends/adapter.py`, define provider-neutral interfaces:

    @dataclass
    class BackendConfig:
        backend: str
        model: str
        endpoint_name: str | None = None
        api_version: str | None = None

    def run_chat_completion(
        *,
        config: BackendConfig,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> dict[str, Any]: ...

The Azure implementation in this milestone must be one adapter branch that delegates to `azure_openai.run_direct_chat_completion`, while preserving a normalized response envelope consumed by the runner/evaluator.

In `tasks/selectors/*.yaml`, define selector schema:

    include:
      task_ids: []
      categories: []
      difficulties: []
      task_types: []   # query | action
    exclude:
      task_ids: []
      categories: []
      difficulties: []
      task_types: []

In `experiments/run.py`, selector precedence must be deterministic:

- `--task-ids` has highest priority.
- `--task-selector-file` is applied next.
- `--task-categories` is applied next.
- `--split` default selection is base set.
- `--max-tasks` truncates final resolved list with stable ordering by `task_id`.

In `scripts/medagentbench/evaluator.py`, define:

    def evaluate_results(results_path: str, task_manifest_path: str) -> dict: ...

The evaluation dictionary must contain keys:

- `pass_at_1`
- `total_tasks`
- `by_category`
- `query_vs_action`
- `error_taxonomy`

Revision note (2026-03-03): Initial ExecPlan authored to guide first implementation of MedAgentBench integration in an otherwise scaffold-only repository.
Revision note (2026-03-03): Updated plan to require configurable task selection (IDs/categories/selector files) and dataset-agnostic task mapping to support future subset and cross-dataset task reuse.
Revision note (2026-03-04): Reviewed plan for consistency with current repository state and PLANS.md guidance; removed non-portable hardcoded endpoint defaults, fixed duplicated interface text, and refreshed scaffold evidence wording.
Revision note (2026-03-05): Updated plan to reflect canonical underscore tool IDs, central catalog-based tool registration, removal of unused MedAgentBench compatibility adapter file, and current test evidence totals.
