# How to Add Tasks to the MedCLI Codebase

This document outlines the key steps required to add a new task to the MedCLI system. The MedAgentBench benchmark serves as the canonical example—follow this workflow for similar task integration work.

## Overview

Adding a task to MedCLI involves eight major phases:

1. **Data Preparation** — Create and validate raw task definitions
2. **Data Normalization & Preprocessing** — Transform raw data into normalized format
3. **Task Selection & Slicing** — Choose which tasks to include in the benchmark slice
4. **Harbor Task Generation** — Generate the runnable Harbor task artifact from normalized data
5. **Environment Setup** — Create the Docker-based execution environment with primitives and workspace
6. **Evaluation & Verification** — Define answer keys and implement evaluation logic
7. **Job Configuration** — Create Harbor job file for orchestration
8. **Documentation** — Update project-level docs and developer guides

---

## 1. Data Preparation

### Goal
Create a canonical raw task data file that defines the tasks in the target domain.

### Steps

- **Define task structure**: Create a JSON file (e.g., `data/<task-name>/raw_tasks.json`) containing task objects
- **Required fields per task**:
  - `id` — unique task identifier (e.g., `"task1_1"`, `"task2_5"`)
  - `instruction` — the user-facing task prompt
  - `context` — optional background information or constraints
  - `sol` — list of acceptable solutions for validation
  - Domain-specific fields (e.g., `eval_MRN`, `eval_patient_id` for medical tasks)

- **Example** (from MedAgentBench):
  ```json
  [
    {
      "id": "task1_1",
      "instruction": "What's the MRN of the patient with name Peter Stafford and DOB of 1932-12-29?",
      "context": "",
      "sol": ["S6534835"],
      "eval_MRN": "S6534835"
    }
  ]
  ```

- **Store alongside metadata**:
  - Task type mapping files (e.g., `task_type_mapping.yaml`)
  - Supplementary data (e.g., function definitions in `funcs_v1.json`)
  - Validation checksums (e.g., `SHA256SUMS`)

### MedAgentBench Example
- Location: `data/medagentbench/test_data_v2.json`
- Contains 10 task groups (task1–task10) with multiple variants each
- Uses reference time and medical code mappings for evaluation

---

## 2. Data Normalization & Preprocessing

### Goal
Transform raw task data into a standardized format ready for Harbor consumption.

### Steps

- **Create a normalization module** (e.g., `normalization.py`):
  - **Load raw tasks**: Parse JSON and validate structure
  - **Define mappings**: Map task identifiers to task types, categories, and difficulty levels
  - **Infer metadata**: Extract task group, classify as read/write, determine evaluation method
  - **Build answer key**: Extract solutions and expected payloads

- **Key functions** (from MedAgentBench):
  - `load_raw_tasks(path)` — parse and validate JSON
  - `infer_group(task_id)` — extract group prefix (e.g., `"task1"` from `"task1_5"`)
  - `normalize_harbor_task(task)` — convert raw task to Harbor format
  - `build_harbor_answer_key(tasks)` — extract hidden validation data
  - `build_instruction(task)` — format user-facing instruction text

- **Define classification mappings**:
  ```python
  GROUP_TO_MED_TASK_TYPE = {
      "task1": "patient_information_retrieval",
      "task3": "recording_patient_data",
      "task6": "patient_data_aggregation",
      # ... etc
  }

  MED_TASK_TYPE_TO_REPO_TASK_TYPE = {
      "patient_information_retrieval": "factual_qa",
      "patient_data_aggregation": "data_aggregation",
      # ... etc
  }
  ```

### MedAgentBench Example
- Location: `scripts/medagentbench/normalization.py`
- Maps 10 task groups to 6 medical task types
- Marks read-only vs. write tasks via `ACTION_GROUPS` set
- Builds answer keys with task-specific evaluation fields

---

## 3. Task Selection & Slicing

### Goal
Choose which tasks from the full raw dataset to include in the runnable benchmark artifact.

### Steps

- **Define selection strategy**:
  - Determine criteria for which tasks to include:
    - **By group**: Select one representative from each logical group or category
    - **By difficulty**: Include tasks across a range of difficulty levels
    - **By type**: Mix different task types (read, write, multi-step, etc.)
    - **By coverage**: Ensure broad coverage of domain features
    - **All tasks**: Include the full dataset if size permits
    - **Custom**: Allow explicit task ID selection via configuration
  - Validate that all requested task IDs exist in the raw data

- **Implement selection function(s)**:
  ```python
  def default_selected_task_ids(raw_tasks) -> list[str]:
      # Apply your selection strategy to determine the default slice
      ...

  def select_tasks(raw_tasks, selected_task_ids) -> list[dict]:
      # Filter raw_tasks to match requested IDs
      ...
  ```

- **Support multiple slices**:
  - Define multiple benchmark configurations (e.g., `smoke`, `std`, `full`)
  - Store slice metadata in the Harbor task configuration (e.g., `task.toml`)
  - Allow runtime override via generator CLI arguments

- **Document slice composition**:
  - Record selected task IDs in Harbor configuration
  - Include rationale in comments or README (e.g., "one representative per group", "stratified by difficulty")

### MedAgentBench Example
- **Selection strategy**: One representative `_1` task from each of 10 task groups
- **Default slice**: 10 tasks covering all task types
- **Configuration**: Recorded in `harbor_tasks/medagentbench/task.toml` → `[metadata] selected_task_ids`
- **Runtime selection**: `generate_harbor_tasks.py --selected-task-ids task1_1,task2_5,task3_2,...`

### Other Example Strategies
- **Smoke test**: 2–3 tasks per task type (quick validation)
- **Stratified**: Equal distribution across difficulty levels
- **Edge cases**: Include boundary conditions and error scenarios
- **Difficulty ramp**: Introductory → intermediate → advanced

---

## 4. Harbor Task Generation

### Goal
Synthesize a complete, runnable Harbor meta-task from normalized data.

### Steps

- **Create a generator script** (e.g., `generate_harbor_tasks.py`):
  - Parse CLI arguments for input JSON, output directory, and optional task selections
  - Load and normalize raw tasks
  - Select the task slice (default or custom)
  - Generate Harbor task structure

- **Generate files**:
  - **`task.toml`** — Harbor meta-task configuration
    - Version, benchmark name, mode (`"meta-task"`)
    - Selected task IDs
    - Verifier and agent timeouts
    - Environment specifications (CPUs, memory, network, etc.)

  - **`instruction.md`** — User-facing documentation
    - Describe the task environment and tools
    - Explain submission format and workflow
    - Provide primitive helper examples

  - **`benchmark_tasks.json`** — Normalized tasks for the agent workspace
    - Public rows with task text, `final_answer`, `payload` fields
    - Ready for agent editing

  - **Hidden answer key** (e.g., `tests/task_answer_key.json`)
    - Complete task definitions with solutions
    - Task-specific evaluation fields
    - Stored separately from public submission file

- **Handle task-specific logic**:
  - For read tasks: set `payload` to `null`
  - For write tasks: generate expected `payload` objects (FHIR, SQL, etc.)
  - Attach reference metadata (reference time, evaluation keys, etc.)

### MedAgentBench Example
- Location: `scripts/medagentbench/generate_harbor_tasks.py`
- Generates 10-task meta-task at `harbor_tasks/medagentbench/`
- Reference time: `2023-11-13T10:15:00+00:00`
- Task-specific payload logic for FHIR write operations (e.g., Observations, ServiceRequests)

---

## 5. Environment Setup

### Goal
Create a Docker-based execution environment with all tools and data needed for task completion.

### Steps

- **Create a Dockerfile** (e.g., `harbor_tasks/<task-name>/environment/Dockerfile`):
  - Base image: `python:3.12-slim` or language-appropriate equivalent
  - Install required system packages (bash, curl, jq, etc.)
  - Set working directory to `/workspace`
  - Copy workspace files into the image

- **Set up the workspace** at `harbor_tasks/<task-name>/environment/workspace/`:
  - **`benchmark_tasks.json`** — the normalized task list (copied from generator)
  - **`submission.json`** — editable task rows template for the agent to fill in
  - **`scripts/primitives/`** — helper scripts for domain-specific operations:
    - Read operations: `get_patient.py`, `get_observation_labs.py`, `get_condition.py`, etc.
    - Write operations: `post_servicerequest.py`, `post_medicationrequest.py`, etc.
    - Each script supports `--help` and accepts domain-relevant parameters
  - **`scripts/primitives/fhir_common.py`** — shared utilities (HTTP clients, payload builders)

- **Document the workspace** in `README.md`:
  - Describe each file's purpose
  - Provide usage examples for primitive helpers
  - Explain submission format and verification process

- **Optional: Docker Compose** for local backend services:
  - Define a FHIR server container, database, or other domain service
  - Set up networking for the task environment to communicate with backends
  - Example: `scripts/medagentbench/docker-compose.yaml` + `fhir_up.sh` / `fhir_down.sh`

### MedAgentBench Example
- Dockerfile: `harbor_tasks/medagentbench/environment/Dockerfile`
- Workspace primitives: 11 scripts in `scripts/primitives/` (7 read, 4 write)
- Local FHIR server via Docker Compose at `http://fhir:8080/fhir`
- Submission template auto-generated at generation time

---

## 6. Evaluation & Verification

### Goal
Define answer validation logic and implement the verifier script.

### Steps

- **Create an evaluator module** (e.g., `harbor_evaluator.py`):
  - **Load submission**: Parse agent-filled `submission.json`
  - **Load answer key**: Parse hidden ground-truth answers
  - **Merge submission with answer key**: Join by task ID
  - **Compare answers**: Implement task-type-specific comparison logic
    - Numeric: allow small floating-point tolerance
    - Text: case-insensitive string matching
    - Lists: set comparison or ordered list matching
    - Payloads: deep structural comparison of nested objects
  - **Generate report**: Return per-task pass/fail and overall score

- **Implement answer type handling**:
  ```python
  def _to_float(value) -> float | None:
      # Convert various types to float for numeric comparison
      ...

  def _to_text(value) -> str:
      # Normalize text for string comparison
      ...

  def _to_list(value) -> list[Any] | None:
      # Parse list from JSON or Python literal
      ...

  def _payload_list(row) -> list[dict[str, Any]]:
      # Extract and normalize payload objects for comparison
      ...
  ```

- **Create a verifier script** (e.g., `tests/test.sh` or `tests/verify_meta_task.py`):
  - Invoked by Harbor after the agent completes
  - Reads submission from `submission.json`
  - Calls evaluator functions
  - Outputs pass/fail status and score
  - Exits with status code 0 for success, non-zero for failure

- **Define validation rules per task group**:
  - Different groups may have different evaluation strategies
  - Task-specific thresholds (e.g., "within ±5%" for numeric answers)
  - Reference data injection (e.g., reference time for date-based tasks)

### MedAgentBench Example
- Evaluator: `scripts/medagentbench/harbor_evaluator.py`
- Verifier: `harbor_tasks/medagentbench/tests/verify_meta_task.py`
- Reference time: `2023-11-13T10:15:00+00:00`
- Handles numeric (CBG, lab values), text (MRN, patient names), and FHIR payload validation
- Hidden answer key: `harbor_tasks/medagentbench/tests/task_answer_key.json`

---

## 7. Job Configuration

### Goal
Create a Harbor job configuration file that orchestrates the benchmark run.

### Steps

- **Create a job YAML file** at `jobs/<task-name>_meta.yaml`:
  ```yaml
  jobs_dir: results/harbor          # Output directory for run artifacts
  n_attempts: 1                      # Number of trials
  timeout_multiplier: 1.0
  orchestrator:
    type: local                      # or 'kubernetes', etc.
    n_concurrent_trials: 1           # Parallelism setting
    quiet: false

  environment:
    type: docker                     # Container-based execution
    force_build: true                # Always rebuild image
    delete: true                     # Clean up after run
    env:
      - CODEX_AUTH_JSON=${CODEX_AUTH_JSON}  # Pass auth token to container

  agents:
    - import_path: medcli.agents.harbor.installed.codex:Codex
      model_name: gpt-5.1-codex-mini      # or your chosen model
      kwargs:
        reasoning_effort: medium           # or 'low'/'high'

  datasets:
    - path: harbor_tasks
      task_names:
        - <task-name>                      # e.g., 'ehrsql', 'medagentbench'
  ```

- **Key configuration points**:
  - `jobs_dir`: Output directory where run results will be written
  - `agents.import_path`: Must reference the installed agent wrapper (Codex for Claude)
  - `agents.model_name`: Set to your preferred Claude model ID
  - `datasets.task_names`: Must match the `harbor_tasks/<task-name>/` directory name
  - Environment variables (e.g., `CODEX_AUTH_JSON`) are injected at runtime

### MedAgentBench & EHRSQL Examples
- MedAgentBench: `jobs/medagentbench_meta.yaml`
- EHRSQL: `jobs/ehrsql_meta.yaml`

---

## 8. Documentation

### Goal
Update project-level documentation and developer guides to reflect the new task.

### Steps

- **Update `README.md`**:
  - Add the new benchmark to the "Task Sources" section
  - Update the "Project Structure" to include `data/<task-name>/` and `harbor_tasks/<task-name>/`
  - Add the new benchmark to "Harbor Usage" with example generation and run commands
  - Add a new subsection under "Benchmarks" if the benchmark is substantial

- **Update `CLAUDE.md` and `AGENTS.md`** (keep them in sync):
  - **Note**: These are developer-facing only; they are not loaded by Harbor at runtime
  - Add the benchmark to the "Repository Layout" section
  - Add example commands to the "Harbor Usage" section showing how to generate and run the task
  - Optionally add a dedicated section for the new benchmark if it has special setup requirements
  - Always maintain exact parity between CLAUDE.md and AGENTS.md

- **Create `scripts/<task-name>/README.md`**:
  - Document the setup process (e.g., downloading datasets, installing dependencies)
  - Explain the generation script arguments and customization options
  - Provide troubleshooting guidance
  - Include references to the original benchmark paper/repository if applicable

- **Document test coverage** (optional but recommended):
  - Add a comment block at the top of `tests/test_<task-name>_*.py` files explaining what they test
  - Include instructions for running: `uv run pytest tests/test_<task-name>*.py -v`

### Example Changes for EHRSQL
- README.md: Added EHRSQL to Task Sources, Project Structure, and Harbor Usage
- CLAUDE.md: Added EHRSQL to Repository Layout and Harbor Usage commands
- AGENTS.md: Mirrored all CLAUDE.md changes (kept in sync)
- scripts/ehrsql/README.md: Comprehensive operational guide with multiple customization examples

---

## Workflow Summary

```bash
# 1. Prepare raw task data
# → data/<task-name>/raw_tasks.json

# 2. Implement normalization module
# → scripts/<task-name>/normalization.py

# 3. Implement tests for normalization (optional but recommended)
# → tests/test_<task-name>_normalization.py

# 4. Create Harbor task generator
# → scripts/<task-name>/generate_harbor_tasks.py

# 5. Implement evaluator module
# → scripts/<task-name>/harbor_evaluator.py

# 6. Implement tests for evaluator (optional but recommended)
# → tests/test_<task-name>_evaluator.py

# 7. Run generator to create the Harbor task artifact
uv run python scripts/<task-name>/generate_harbor_tasks.py \
  --input-json data/<task-name>/raw_tasks.json \
  --output-root harbor_tasks/<task-name>

# 8. Set up environment and workspace files (typically auto-generated)
# → harbor_tasks/<task-name>/environment/Dockerfile
# → harbor_tasks/<task-name>/environment/workspace/*

# 9. Implement verifier script (typically auto-generated)
# → harbor_tasks/<task-name>/tests/verify_meta_task.py

# 10. Create job configuration file
# → jobs/<task-name>_meta.yaml

# 11. Update project documentation
# → README.md (add to Task Sources, Project Structure, Harbor Usage)
# → CLAUDE.md and AGENTS.md (keep in sync, update Repository Layout and Harbor Usage)
# → scripts/<task-name>/README.md (operational guide)

# 12. Run the Harbor task
export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"
uv run harbor run -c jobs/<task-name>_meta.yaml
```

---

## Key Design Principles

- **Separation of concerns**: Raw data, normalization, generation, environment, and evaluation are distinct modules
- **Generality**: Normalization and generation logic should be task-agnostic; task-specific mapping lives in small configuration dictionaries
- **Harbor-first**: Canonical task artifacts are Harbor meta-tasks, not legacy YAML manifests or OpenAI-style runners
- **Hidden answer keys**: Ground truth is stored separately from public submission files for integrity and security
- **Primitive helpers**: Task logic uses domain-specific primitive scripts, not arbitrary shell or Python commands
- **Metadata-driven**: Task.toml and answer keys are self-documenting; verifier reads structured metadata, not ad-hoc logic
- **Developer-facing docs**: CLAUDE.md and AGENTS.md are developer guides (not used by Harbor at runtime); keep them in sync and update when adding new benchmarks
- **Self-contained tasks**: Each Harbor task directory is runnable independently; all required code, configuration, and data are bundled in `harbor_tasks/<task-name>/`

---

## Appendix: Harbor Runtime vs. Developer Documentation

### What Harbor Actually Uses at Runtime

Harbor executes a meta-task using only these files from `harbor_tasks/<task-name>/`:

| File | Purpose |
|------|---------|
| **task.toml** | Meta-task configuration (timeouts, environment, task count) |
| **benchmark_tasks.json** | Public task definitions for agent workspace |
| **instruction.md** | Agent-facing instructions (displayed to the agent) |
| **environment/Dockerfile** | Container image definition |
| **environment/workspace/** | Agent workspace (submission.json, primitives, helpers) |
| **tests/verify_meta_task.py** | Verifier script (called after agent completes) |
| **tests/task_answer_key.json** | Hidden ground-truth answers |

### What AGENTS.md and CLAUDE.md Are

**AGENTS.md** and **CLAUDE.md** are **developer-facing documentation only**. They:
- Document the project structure for developers and coding agents
- Provide example commands for generating and running Harbor tasks
- Explain conventions, tool categories, and repository layout
- Are **NOT** loaded or used by Harbor during task execution
- Should be kept in sync (they have identical content)

When you add a new task:
1. Update CLAUDE.md with the new benchmark's directory structure and runtime commands
2. Copy all changes to AGENTS.md (maintain parity)
3. These changes help developers understand the system; they don't affect Harbor's execution

---

## References

- **MedAgentBench canonical source**: `data/medagentbench/test_data_v2.json`
- **MedAgentBench generator**: `scripts/medagentbench/generate_harbor_tasks.py`
- **MedAgentBench normalization**: `scripts/medagentbench/normalization.py`
- **MedAgentBench Harbor task**: `harbor_tasks/medagentbench/`
- **MedAgentBench evaluator**: `scripts/medagentbench/harbor_evaluator.py`
- **Scripts README**: `scripts/medagentbench/README.md`
