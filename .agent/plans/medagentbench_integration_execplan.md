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
- [x] (2026-03-05 00:31Z) Implemented runnable scripts for setup, mock FHIR startup/shutdown, and task import under `scripts/medagentbench/` to satisfy first three concrete steps.
- [ ] Implement MedAgentBench asset ingestion scripts and documentation.
- [ ] Implement Docker Compose based FHIR runtime and health checks.
- [ ] Implement FHIR tool modules and task adapters in `src/ehr_co_scientist/tools/`.
- [ ] Implement MedAgentBench runner and evaluator under `experiments/` and `benchmarks/`.
- [ ] Add unit and integration tests for import, tool calls, and scoring.
- [ ] Validate end-to-end on a small split and capture reproducible outputs.

## Surprises & Discoveries

- Observation: The current repository is still largely a scaffold: `src/ehr_co_scientist/agent.py` and `config/agent.yaml` are empty, and there are very few task/benchmark/test/runtime files; however, a non-empty Azure backend module now exists.
  Evidence: `wc -c src/ehr_co_scientist/agent.py config/agent.yaml` reported `0` bytes for both files, while `src/ehr_co_scientist/backends/azure_openai.py` is present and non-empty as of 2026-03-04.

- Observation: The mostly scaffold status means integration work must include first implementations for runner/evaluator abstractions instead of only adding MedAgentBench-specific glue.
  Evidence: `rg --files src tests tasks benchmarks experiments` returned only a small set of files (core package stubs, one backend module, and one CLI examples test) on 2026-03-04.

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

## Outcomes & Retrospective

At plan creation time, no implementation has been started yet. The immediate outcome is a concrete, repository-specific path that can be executed by a novice from a clean clone. Retrospective and measured outcomes will be added after each milestone is implemented.

## Context and Orientation

This repository currently provides a project skeleton for an EHR agent system but not yet a functioning benchmark runtime. The key folders relevant to this plan are `src/ehr_co_scientist/` for shared runtime code, `tasks/` for first-class task-type packages (metadata + task-local adapters + fixtures), `benchmarks/` for cross-task scoring harness logic, `experiments/` for runnable orchestration entry points, and `scripts/` for setup automation. MedAgentBench is an external benchmark with a FHIR-based task environment and de-identified patient data exposed through FHIR APIs. In this plan, “FHIR server” means an HTTP service implementing the HL7 FHIR REST patterns used by MedAgentBench tasks. “Task adapter” means the code that transforms MedAgentBench task JSON into this repository’s internal task execution request shape and routes it to the matching task-type package.

The implementation target is not to re-create MedAgentBench internals. The target is to add a compatible benchmark integration layer that can run MedAgentBench tasks against a configured FHIR endpoint, collect outputs, and score the run with pass@1 and category-level breakdowns. The implementation also must define a stable internal task contract with fields that separate task intent from backend source details so task prompts can later be rebound to non-MedAgentBench datasets.

## Plan of Work

Milestone 1 establishes reproducible benchmark assets and container orchestration.

Create `scripts/medagentbench/setup.sh` to download or verify required MedAgentBench artifacts into `benchmarks/medagentbench/assets/`. The script must be idempotent: if files already exist and checksums match, it exits without modifying files. Create `benchmarks/medagentbench/docker-compose.yaml` with a single `fhir` service exposing port `8080`, and add `scripts/medagentbench/fhir_up.sh` and `scripts/medagentbench/fhir_down.sh` wrappers. Add `benchmarks/medagentbench/README.md` documenting prerequisites, expected files, and one-command startup.

Milestone 2 adds foundational runtime config and FHIR client tools.

Populate `config/agent.yaml` with a concrete model/tool config that includes FHIR query and action tools, sets backend `azure_openai`, and uses default model `gpt-5.2` unless overridden by CLI. Implement `src/ehr_co_scientist/tools/fhir_client.py` with a typed client class that supports: search (`GET /<Resource>?...`), create (`POST /<Resource>`), and capability check (`GET /metadata`). Implement `src/ehr_co_scientist/tools/fhir_medagentbench_tools.py` exposing MedAgentBench-aligned tool wrappers (`patient.search`, `lab.search`, `condition.search`, `procedure.search`, `medicationrequest.search`, plus create endpoints used by action tasks). Add shared request/retry utilities in `src/ehr_co_scientist/utils/http.py`.

Milestone 3 introduces task ingestion, task selection, and execution loop.

Create and/or populate task-type packages under `tasks/<task_type>/` (for example `tasks/cohort_construction/`, `tasks/temporal_reasoning/`) with `task.yaml`, `runner.py`, `evaluator.py`, and canonical manifest files generated from source JSON using `scripts/medagentbench/import_tasks.py`. The import script must map each source task to fields required by this repository (`task_id`, `category`, `difficulty`, `instruction`, `expected_answer`, `required_actions`, split labels, and `backend_profile`) and write split manifests under task-type package paths such as `tasks/<task_type>/sources/medagentbench/<split>.yaml`. Add a generic selector file format at `tasks/selectors/*.yaml` with include/exclude rules by `task_id`, category, difficulty, and task type (query or action). Implement `src/ehr_co_scientist/agent.py` with a minimal loop supporting up to 8 tool interaction rounds to align with MedAgentBench protocol. Add `experiments/run.py` CLI accepting `--task medagentbench`, `--split`, `--max-tasks`, `--backend`, `--model`, `--fhir-base-url`, `--task-ids`, `--task-categories`, `--task-selector-file`, `--endpoint-name`, and `--api-version`, where `--backend` defaults to `azure_openai`. Implement backend dispatch in runner through a provider-neutral adapter call (for example `run_chat_completion(backend, config, messages, **kwargs)`) with an Azure-backed implementation for this milestone.

Milestone 4 adds evaluation and reporting.

Implement `benchmarks/evaluate.py` with MedAgentBench scorer logic in `benchmarks/medagentbench/evaluator.py`. Scoring must compute pass@1 overall and per category, and separate query versus action tasks. Persist machine-readable results to `experiments/results/medagentbench/<timestamp>/results.jsonl` and summary metrics to `summary.json` and `summary.md`. Add simple error taxonomy counters for tool schema violations, HTTP failures, and final-answer mismatch.

Milestone 5 hardens quality with tests and smoke runs.

Add unit tests in `tests/test_fhir_client.py`, `tests/test_medagentbench_task_import.py`, and `tests/test_medagentbench_evaluator.py`. Add an integration smoke test `tests/integration/test_medagentbench_smoke.py` that runs a tiny fixed subset (for example 3 tasks) against the running Dockerized FHIR endpoint. Update `README.md` with a “MedAgentBench” section linking to setup, run, and evaluate commands.

## Concrete Steps

All commands below are run from `/home/shezhan/repos/ehr-co-scientist`.

1. Create asset and orchestration files and scripts.

    uv run python -m pytest -q

Expected: existing tests pass (initially may be zero tests).

2. Start the FHIR service.

    bash scripts/medagentbench/fhir_up.sh
    curl -sSf http://localhost:8080/metadata | head -c 200

Expected: the second command prints JSON containing a FHIR CapabilityStatement payload.

3. Import and normalize MedAgentBench task files.

    uv run python scripts/medagentbench/import_tasks.py \
      --input benchmarks/medagentbench/assets/tasks.json \
      --output tasks/cohort_construction/sources/medagentbench/std.yaml

Expected: output file exists and contains deterministic ordering by `task_id`.

4. Smoke-test Azure OpenAI backend defaults used by benchmark runs.

    uv run ehr-azure-openai \
      --example direct \
      --model gpt-5.2 \
      --endpoint-name "$AZURE_OPENAI_ENDPOINT_NAME" \
      --prompt "Reply with exactly: backend_ok"

Expected: command returns a direct chat completion payload from Azure OpenAI and confirms endpoint/model wiring. If `$AZURE_OPENAI_ENDPOINT_NAME` is unset, pass `--endpoint-name <your-endpoint-name>` explicitly.

5. Run a filtered benchmark slice by explicit task IDs.

    uv run python experiments/run.py \
      --task medagentbench \
      --split std \
      --task-ids mab_001,mab_017,mab_043 \
      --model gpt-5.2 \
      --endpoint-name "$AZURE_OPENAI_ENDPOINT_NAME" \
      --api-version 2025-03-01-preview \
      --fhir-base-url http://localhost:8080

Expected: run executes exactly those task IDs, and the run metadata file records the resolved selector.

6. Run a filtered benchmark slice by selector file.

    uv run python experiments/run.py \
      --task medagentbench \
      --split std \
      --task-selector-file tasks/selectors/medagentbench_query_easy.yaml \
      --model gpt-5.2 \
      --endpoint-name "$AZURE_OPENAI_ENDPOINT_NAME" \
      --api-version 2025-03-01-preview \
      --fhir-base-url http://localhost:8080

Expected: only tasks matching selector rules are executed, and skipped counts by rule are reported.

7. Run a tiny benchmark slice with max-task cap.

    uv run python experiments/run.py \
      --task medagentbench \
      --split std \
      --max-tasks 3 \
      --model gpt-5.2 \
      --endpoint-name "$AZURE_OPENAI_ENDPOINT_NAME" \
      --api-version 2025-03-01-preview \
      --fhir-base-url http://localhost:8080

Expected: run directory under `experiments/results/medagentbench/` with `results.jsonl` containing 3 records.

8. Evaluate run outputs.

    uv run python benchmarks/evaluate.py \
      --task medagentbench \
      --results experiments/results/medagentbench/<run-id>/results.jsonl

Expected: printed summary includes `pass_at_1`, category breakdowns, and query/action split.

9. Run quality gates.

    uv run pytest tests/
    uv run ruff check src/ tests/
    uv run ruff format src/ tests/

Expected: tests pass, lint passes, formatter makes no additional changes on second run.

## Validation and Acceptance

Acceptance is achieved when a novice can clone the repository, run the MedAgentBench setup script, start the Dockerized FHIR service, execute at least one MedAgentBench split through `experiments/run.py`, execute a filtered subset through selector configuration, and generate scoring outputs through `benchmarks/evaluate.py` without manually editing source files.

The concrete observable checks are:

- `GET http://localhost:8080/metadata` succeeds while Docker service is up.
- `experiments/run.py` produces one JSONL record per attempted task with final answer, tool trace, and success flag.
- `experiments/run.py` supports task selection by explicit IDs, category filters, and selector file, and records the effective resolved task set in run metadata.
- `experiments/run.py` records backend call metadata including backend name, model name, endpoint name, and API version for reproducibility.
- `benchmarks/evaluate.py` writes both machine-readable and human-readable summaries.
- `tests/integration/test_medagentbench_smoke.py` passes when the FHIR service is running.

## Idempotence and Recovery

The setup scripts must be idempotent. Re-running `scripts/medagentbench/setup.sh` should only re-download missing or checksum-mismatched assets. Re-running `scripts/medagentbench/fhir_up.sh` should either report the existing running service or restart cleanly. If container startup fails due to a stale container, `scripts/medagentbench/fhir_down.sh` followed by `scripts/medagentbench/fhir_up.sh` must recover. Task import must overwrite outputs deterministically so repeated imports do not create drift.

No destructive operations on unrelated repository files are allowed. All generated run artifacts must stay under `experiments/results/medagentbench/`.

## Artifacts and Notes

Expected key file additions and modifications:

- `scripts/medagentbench/setup.sh`: Idempotent downloader/verifier for MedAgentBench assets into repository-local benchmark paths.
- `scripts/medagentbench/fhir_up.sh`: One-command wrapper to start the Dockerized FHIR service with health checks.
- `scripts/medagentbench/fhir_down.sh`: Wrapper to stop and cleanly tear down the Dockerized FHIR service.
- `scripts/medagentbench/import_tasks.py`: Deterministic converter from source MedAgentBench task JSON into internal canonical YAML schema.
- `tasks/selectors/medagentbench_query_easy.yaml`: Example selector manifest demonstrating include/exclude filtering for a simple query subset.
- `benchmarks/medagentbench/README.md`: Operator guide for setup, startup, task import, benchmark execution, and troubleshooting.
- `benchmarks/medagentbench/docker-compose.yaml`: Container orchestration definition for the local MedAgentBench-compatible FHIR runtime.
- `benchmarks/medagentbench/evaluator.py`: MedAgentBench scoring logic that computes pass@1 and category/query-action breakdowns.
- `tasks/<task_type>/task.yaml`: Task-type package metadata with manifest and entrypoint wiring.
- `tasks/<task_type>/sources/medagentbench/std.yaml`: Canonical normalized task manifest for standard split routed to the corresponding task type.
- `tasks/<task_type>/runner.py`: Task-local execution adapter invoked by top-level experiment runner.
- `tasks/<task_type>/evaluator.py`: Task-local scoring adapter used by benchmark harness.
- `experiments/run.py`: Main benchmark runner CLI handling task resolution, agent execution, backend dispatch, and result persistence.
- `benchmarks/evaluate.py`: Top-level evaluation CLI entrypoint that loads run outputs and writes summary metrics artifacts.
- `src/ehr_co_scientist/agent.py`: Agent loop implementation coordinating prompt construction, tool calls, and final answer extraction.
- `src/ehr_co_scientist/backends/__init__.py`: Backend package exports and registry entrypoint for available backend adapters.
- `src/ehr_co_scientist/backends/adapter.py`: Provider-neutral backend interface and dispatch layer used by the runner.
- `src/ehr_co_scientist/backends/azure_openai.py`: Azure OpenAI backend implementation and CLI smoke-test utility used as the default backend.
- `src/ehr_co_scientist/tools/fhir_client.py`: Typed FHIR HTTP client abstraction for capability checks, search, and resource creation.
- `src/ehr_co_scientist/tools/fhir_medagentbench_tools.py`: MedAgentBench-aligned tool wrappers that map agent tool calls to FHIR client operations.
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

In `src/ehr_co_scientist/tools/fhir_client.py`, define:

    class FHIRClient:
        def __init__(self, base_url: str, timeout_s: float = 30.0) -> None: ...
        def capability_statement(self) -> dict: ...
        def search(self, resource_type: str, params: dict[str, str]) -> dict: ...
        def create(self, resource_type: str, resource_body: dict) -> dict: ...

In `src/ehr_co_scientist/tools/fhir_medagentbench_tools.py`, define:

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

In `benchmarks/medagentbench/evaluator.py`, define:

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
