# Convert MedAgentBench into a Single Harbor Meta-Task

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

`PLANS.md` is checked into this repository at `/PLANS.md`; this document must be maintained in accordance with that file.

## Purpose / Big Picture

After this change, a user will be able to run a representative MedAgentBench slice through Harbor as a single benchmark-style meta-task instead of as hundreds of per-instance Harbor tasks. The existing YAML manifests under `tasks/*/sources/medagentbench/*.yaml` remain the source of truth. Harbor will expose one task directory at `tasks/medagentbench/`, whose environment includes a provided benchmark harness. The agent's job is to invoke that harness. The verifier will score the aggregate benchmark result and write one numeric Harbor reward equal to the mean pass@1 across the configured MedAgentBench slice.

For fast iteration, the initial slice is exactly one case from each MedAgentBench `taskN` family: `task1_1` through `task10_1`.

## Progress

- [x] (2026-03-11 23:55Z) Read `/PLANS.md`, inspected the current task manifests under `tasks/`, and confirmed Harbor's task directory contract and local path dataset discovery model from DeepWiki.
- [x] (2026-03-11 23:58Z) Collected the original Harbor integration decisions: generated artifacts under `harbor_tasks/`, Harbor local path execution, evaluator reuse, and Harbor scaffold alignment.
- [x] (2026-03-12 00:08Z) Confirmed from repository data that the current MedAgentBench manifests contain 10 `source_group` families (`task1` through `task10`) and selected the fast-iteration representative slice as `task1_1` through `task10_1`.
- [x] (2026-03-12 00:11Z) Reframed the Harbor design from a per-instance dataset to a single Harbor meta-task with one trial running a benchmark harness and one aggregate reward.
- [x] (2026-03-12 00:39Z) Replaced the obsolete per-instance generator with a single-task generator that emits `tasks/medagentbench/` using Harbor's scaffold command.
- [x] (2026-03-12 00:39Z) Added benchmark task/config artifacts for the fixed 10-task slice: `benchmark_tasks.json`, `submission_template.json`, and `action_payload_templates.json`.
- [x] (2026-03-12 00:39Z) Implemented the Harbor task workspace contract: local FHIR sidecar, helper scripts under `/workspace/scripts/`, and `/workspace/submission.json` as the agent output file.
- [x] (2026-03-12 00:39Z) Implemented a benchmark-level verifier bridge that converts `submission.json` into evaluator-compatible rows and computes mean pass@1 with the existing MedAgentBench evaluator.
- [x] (2026-03-12 00:40Z) Added a Harbor job example at `jobs/medagentbench_meta.yaml` targeting the single meta-task.
- [x] (2026-03-12 00:43Z) Validated generator determinism and verifier parity locally: repository tests pass and a perfect synthetic submission scores `1.0`.
- [x] (2026-03-12 18:20Z) Hardened the generated Harbor task to match Harbor examples more closely: pinned the MedAgentBench FHIR image by digest, removed generated runtime artifacts from the committed task tree, and cleaned up `instruction.md`.
- [x] (2026-03-12 18:20Z) Replaced the impossible in-container FHIR healthcheck with a pinned readiness helper sidecar and gated `main` on `service_completed_successfully`.
- [x] (2026-03-12 18:27Z) Fixed the MedAgentBench Harbor smoke helper so it copies a perfect submission into the live container before verification; the direct debug smoke path again scores `1.000000`.
- [x] (2026-03-12 19:05Z) Added a manual Harbor Codex debugging path with reusable helper scripts: raw shell, task-aware shell handoff, Codex install, Codex auth/runtime prep, and a MedAgentBench-specific manual wrapper.
- [x] (2026-03-12 19:18Z) Fixed the manual Codex command template to match the actual Harbor wrapper flags by using `-c model_reasoning_effort=medium` instead of `--reasoning-effort medium`.
- [x] (2026-03-12 19:52Z) Refactored default-agent bootstrapping into a generic `debug/setup-agent.sh` step and updated the MedAgentBench manual wrapper to use it before opening a ready-to-use shell.
- [x] (2026-03-12 21:25Z) Reworked the MedAgentBench Harbor task prompt into a hybrid of the original MedAgentBench instructions and the Harbor submission-file contract, so the task now foregrounds primitive FHIR operations and the original GET/POST/FINISH semantics while still writing outputs to `/workspace/submission.json`.
- [x] (2026-03-12 21:25Z) Replaced the old convenience FHIR tool surface with primitive MedAgentBench-aligned tools (`get_*` / `post_*`), updated task manifests and Harbor artifacts to use the new canonical names, and validated the refactor with the full pytest suite.
- [ ] Complete a Harbor trial to termination and record the observed runtime behavior of the Codex and nop smoke runs.

## Surprises & Discoveries

- Observation: Harbor's standard local dataset model expects one task directory per instance-like task, not one directory representing many benchmark cases.
  Evidence: DeepWiki repository-grounded answer confirmed Harbor discovers subdirectories with `task.toml`, `instruction.md`, `environment/`, and `tests/test.sh` as individual tasks.

- Observation: The user explicitly wants a single Harbor task anyway, which means this integration is intentionally a benchmark harness meta-task rather than a standard Harbor dataset adaptation.
  Evidence: User decision during planning on 2026-03-11 after discussing Harbor's usual task model.

- Observation: The current manifests expose 10 benchmark families via `source_group` (`task1` through `task10`), while the normalized `source_task_type` field collapses those into fewer broader labels.
  Evidence: Local manifest inspection over `tasks/*/sources/medagentbench/*.yaml` counted 300 rows and 10 distinct `source_group` values.

- Observation: Using one representative case per `source_group` gives a fixed 10-case slice that is easy to iterate on while still covering the full MedAgentBench family spread.
  Evidence: Local manifest inspection showed every `taskN` group includes a `_1` example, allowing a deterministic default slice of `task1_1` through `task10_1`.

- Observation: Harbor verification remains file-based and expects the verifier to write a numeric reward to `/logs/verifier/reward.txt`, which fits aggregate benchmark scoring just as well as binary pass/fail.
  Evidence: Harbor task documentation and DeepWiki both describe the verifier reward file contract.

- Observation: The previously implemented per-instance Harbor task generator is now the wrong abstraction for the desired Harbor UX, even though its Harbor scaffold alignment remains useful.
  Evidence: The user changed the design goal from "all manifest rows become Harbor tasks" to "MedAgentBench is one Harbor meta-task".

- Observation: The task environment should not embed the MedCLI runtime. It only needs the FHIR sidecar, the selected task slice, helper scripts that show how to query the database, and a submission-file contract for the agent.
  Evidence: User clarification during implementation on 2026-03-11.

- Observation: Reusing the current evaluator does not require shipping the full repository into the Harbor environment. Copying the evaluator into the task verifier bundle is sufficient because Harbor uploads `tests/` separately before verification.
  Evidence: Harbor verifier implementation uploads only the task `tests/` directory into the environment before running `tests/test.sh`, and the local verifier sanity check scored a perfect submission at `1.0`.

- Observation: The upstream MedAgentBench Docker image is a Java-only image without a shell utility layer, so a normal Docker Compose HTTP healthcheck cannot run inside it.
  Evidence: Local Docker inspection on 2026-03-12 showed the image exposes port `8080` and runs Java directly; probing it with `docker run --entrypoint sh ...` failed because `sh` is not present.

- Observation: The MedAgentBench Harbor debug helper was previously writing the synthetic perfect submission only to the host workspace after the image was already built, so the running container never saw it.
  Evidence: The first smoke rerun after cleaning the task tree returned verifier reward `0.400000` until the helper was changed to `docker compose cp` the generated submission into `/workspace/submission.json` inside the live `main` container.

- Observation: Manual Codex debugging requires two distinct setup phases inside the live Harbor container: installing the Codex CLI itself, and then wiring auth plus `CODEX_HOME` the same way the Harbor-installed Codex wrapper does.
  Evidence: Harbor's `install-codex.sh.j2` installs NVM, Node 22, and `@openai/codex`, while `src/medcli/agents/harbor/installed/codex.py` separately writes `/tmp/codex-secrets/auth.json`, links `/logs/agent/auth.json`, and then runs `codex exec`.

- Observation: Opening the interactive shell before installing Codex causes a confusing developer experience because the already-open shell does not automatically pick up the new NVM/Codex environment.
  Evidence: Manual repro on 2026-03-12 showed that Codex was not visible in the first shell until the user exited and re-entered after installation.

- Observation: The original MedAgentBench prompt is stricter than the Harbor meta-task contract because it expects one raw `GET`, `POST`, or `FINISH(...)` action per turn with no extra text.
  Evidence: DeepWiki summary of `src/server/tasks/medagentbench/__init__.py` confirmed the original output contract and invalid-action rules.

- Observation: Matching `scripts/medagentbench/assets/funcs_v1.json` faithfully requires primitive POST tools to accept raw top-level payload fields rather than the earlier MedCLI-specific `args.resource` wrapper.
  Evidence: Local inspection of `funcs_v1.json` showed that the original functions expose raw JSON bodies for POST requests, not nested wrapper objects.

## Decision Log

- Decision: Keep `tasks/*/sources/medagentbench/*.yaml` as the source of truth.
  Rationale: The existing manifest layout is already the canonical authored representation of MedAgentBench tasks in this repository. Harbor output should be generated from it rather than becoming a second authored source.
  Date/Author: 2026-03-11 / User+Codex

- Decision: Bootstrap Harbor output with Harbor's official `harbor tasks init` command rather than hard-coding Harbor's task skeleton.
  Rationale: This keeps the generated Harbor task aligned with Harbor's canonical layout as Harbor evolves.
  Date/Author: 2026-03-11 / User+Codex

- Decision: Represent MedAgentBench in Harbor as a single meta-task at `tasks/medagentbench/`, not as one Harbor task per manifest row.
  Rationale: The user wants one shared environment, one shared evaluator, and one Harbor-facing benchmark task rather than hundreds of Harbor task directories.
  Date/Author: 2026-03-12 / User+Codex

- Decision: The agent's role in the Harbor meta-task is to invoke a provided benchmark harness inside the task environment.
  Rationale: This keeps the Harbor task stable and testable. In implementation, the harness is a lightweight workspace contract: the agent reads the task JSON, uses the helper scripts against the FHIR sidecar, and writes `submission.json`.
  Date/Author: 2026-03-12 / User+Codex

- Decision: The Harbor verifier reward is the raw mean pass@1 over the configured benchmark slice.
  Rationale: An aggregate float score is a better fit for a benchmark meta-task than binary task success.
  Date/Author: 2026-03-12 / User+Codex

- Decision: The initial Harbor benchmark slice is exactly `task1_1` through `task10_1`.
  Rationale: This gives one representative from each MedAgentBench `taskN` family and keeps iteration fast while still spanning the full family set.
  Date/Author: 2026-03-12 / User+Codex

- Decision: Task selection for the Harbor meta-task should live in a task file config, not be permanently hard-coded in Python.
  Rationale: The initial slice is intentionally small for iteration, but the Harbor task should be able to expand later without redesigning the interface.
  Date/Author: 2026-03-12 / User+Codex

- Decision: Reuse the current MedAgentBench evaluator logic from `scripts/medagentbench/evaluator.py` for Harbor scoring.
  Rationale: The existing evaluator already encodes the repository's benchmark semantics and should remain the scoring source of truth.
  Date/Author: 2026-03-11 / User+Codex

- Decision: Keep the sidecar-based Harbor environment, but pin the FHIR image by digest and gate `main` with a separate readiness helper container instead of an in-image healthcheck.
  Rationale: The official MedAgentBench image is reproducible by digest, but does not contain shell tooling needed for a Docker Compose HTTP healthcheck. A tiny readiness helper preserves the sidecar design while providing real startup gating.
  Date/Author: 2026-03-12 / User+Codex

- Decision: The generated Harbor task tree should contain only source artifacts and templates, not runtime outputs such as `submission.json` or Python bytecode.
  Rationale: Harbor tasks should be deterministic, reviewable source artifacts. Runtime files belong in containers or result directories, not the committed task tree.
  Date/Author: 2026-03-12 / Codex

- Decision: The default manual Harbor debug agent is Codex, and its installation/auth bootstrapping should be exposed through reusable Harbor-level helpers rather than being duplicated inside task-specific wrappers.
  Rationale: Codex setup is task-agnostic as long as Codex remains the default debug agent. Reusable primitives (`install-codex-agent.sh`, `prepare-codex-agent.sh`) plus a generic orchestration step (`setup-agent.sh`) keep task wrappers focused on task instructions.
  Date/Author: 2026-03-12 / User+Codex

- Decision: The recommended MedAgentBench manual debug flow is a one-command wrapper that performs generic agent setup before opening the shell.
  Rationale: Doing install/auth prep before shell handoff avoids the confusing state where Codex is installed in a later `docker compose exec` but not visible in the already-open shell.
  Date/Author: 2026-03-12 / User+Codex

- Decision: Align the Harbor MedAgentBench instruction with the original MedAgentBench prompt as a hybrid, not a literal port.
  Rationale: The Harbor task must keep its `/workspace/submission.json` contract, but it should still emphasize the original primitive FHIR function semantics and stricter output expectations.
  Date/Author: 2026-03-12 / User+Codex

- Decision: Replace the convenience FHIR tool names with primitive MedAgentBench-aligned canonical names (`get_patient`, `get_condition`, `get_observation_labs`, `get_observation_vitals`, `get_medicationrequest`, `get_procedure`, `post_observation_vitals`, `post_medicationrequest`, `post_servicerequest`).
  Rationale: `scripts/medagentbench/assets/funcs_v1.json` is the schema source of truth for the MedAgentBench primitive tool surface, and the repo should use one clean canonical mapping instead of compatibility aliases.
  Date/Author: 2026-03-12 / User+Codex

## Outcomes & Retrospective

The original per-instance Harbor dataset plan is now obsolete. The repository still has useful Harbor-related work in progress, but the implementation target changed materially: Harbor now exposes MedAgentBench as one benchmark meta-task, not as a local dataset of hundreds of tasks.

That change simplifies the Harbor-facing UX and aligns with the user's goal of one shared environment and one shared evaluator, but it also means this integration deliberately departs from Harbor's normal one-task-per-instance model. The remaining implementation risk is therefore less about task generation volume and more about designing a clean harness/verifier contract for a single trial that internally runs multiple benchmark cases.

The fast-iteration slice is now fixed and implemented: one task from each `taskN` family, scored by mean pass@1. The generator, workspace contract, verifier bridge, and Harbor-aligned debug path are complete. The generated task now uses a pinned FHIR image digest, a readiness helper sidecar for startup gating, and a clean source-only task tree without committed runtime artifacts. The Harbor debug toolbox now also includes a generic default-agent setup step and a one-command MedAgentBench manual Codex workflow. The Harbor prompt now explicitly explains the original MedAgentBench GET/POST/FINISH model and how Harbor adapts it, and the repo's FHIR tool surface now matches the original primitive MedAgentBench functions instead of the earlier convenience wrappers. The remaining open item is Harbor runtime validation to completion with real agent execution.

## Context and Orientation

The current source-of-truth tasks live under `tasks/` and are grouped by task type, for example `tasks/factual_qa/sources/medagentbench/std.yaml`. Each YAML file contains a `tasks:` list where each row already has the benchmark instruction and evaluation-relevant metadata such as `task_id`, `category`, `task_type`, `source_group`, `expected_answer`, `required_actions`, `eval_mrn`, and `allowed_tools`. These rows are currently consumed by the MedCLI benchmark pipeline implemented in `run.py`, `demo.py`, and `scripts/medagentbench/evaluator.py`.

Harbor is already installed in this repository and can run local tasks. A Harbor task is a directory with four required pieces: `instruction.md`, `task.toml`, `environment/`, and `tests/test.sh`. Harbor verification is shell-driven: `tests/test.sh` runs in the verifier flow and must write a numeric reward to `/logs/verifier/reward.txt`.

The repository already has a custom Harbor Codex wrapper at `src/medcli/agents/harbor/installed/codex.py` and a working Harbor job example at `jobs/example.yaml`. That means the missing piece is not Harbor itself; the missing piece is a Harbor-compatible MedAgentBench task contract.

In this document, “manifest tasks” means the existing YAML rows under `tasks/`. “Harbor meta-task” means the single generated runnable directory under `tasks/medagentbench/`. “Harness” means the benchmark command inside the Harbor task environment that runs the configured MedAgentBench slice. “Verifier bridge” means the code that reads the harness outputs, calls the existing MedAgentBench evaluator logic, and writes the aggregate Harbor reward.

## Plan of Work

First, replace the current per-instance Harbor generator with a meta-task generator under `scripts/medagentbench/`. That generator must initialize exactly one Harbor task directory at `tasks/medagentbench/` using Harbor's official scaffold command, then deterministically replace the scaffolded content with MedCLI-owned files. It must emit one benchmark-level `instruction.md`, one benchmark-level `task.toml`, one benchmark selection config file, and the environment/verifier files needed for the benchmark harness contract.

Second, define the benchmark selection config. The config must live inside the Harbor task so the selected benchmark slice is explicit and editable. The default config for this milestone is the fixed 10-case slice `task1_1` through `task10_1`. The harness must read this config rather than having those task IDs duplicated in multiple code paths.

Third, implement the benchmark harness inside the Harbor task environment. The environment must contain everything needed to run the selected MedAgentBench slice without relying on an externally started FHIR server. The task instruction must tell the agent to invoke the provided harness command. The harness must write machine-readable outputs to a fixed path that the verifier bridge consumes.

Fourth, implement the benchmark-level verifier bridge. Instead of reading one task's final answer, it must read the harness outputs for the configured task slice, invoke the existing MedAgentBench evaluator logic across those results, compute mean pass@1, and write that aggregate float to `/logs/verifier/reward.txt`. Failures such as missing outputs, malformed output files, or incomplete benchmark runs must result in a clear verifier failure.

Fifth, update Harbor job examples and docs. Add a Harbor job example that targets the single meta-task path. Update README and related docs so contributors understand that Harbor currently exposes MedAgentBench as one benchmark meta-task using a default 10-case slice, while the YAML manifests under `tasks/` remain canonical.

Finally, validate the full path on the 10-task slice before considering broader benchmark expansion. The validation must prove both that Harbor can run the single meta-task end-to-end and that the resulting aggregate score matches the current MedAgentBench evaluator semantics for the same 10 tasks.

## Concrete Steps

Work from the repository root.

1. Inspect the manifest source tree and confirm the selected representative task IDs.

       find tasks -maxdepth 4 -type f | sort

   Expected outcome: the MedAgentBench YAML manifests exist under `tasks/*/sources/medagentbench/`, and the selected default Harbor slice is `task1_1` through `task10_1`.

2. Replace the current Harbor generator with a single-task generator.

       uv run python scripts/medagentbench/generate_harbor_tasks.py \
         --input-root tasks \
         --output-root tasks/medagentbench

   Internally, the generator must initialize one Harbor task using Harbor's official scaffold command and then overwrite the scaffolded files deterministically.

   Expected outcome: one Harbor task directory exists at `tasks/medagentbench/` with Harbor-required files plus task selection config and helper files.

3. Add the benchmark harness and verifier bridge.

   The harness must execute the configured benchmark slice and write results to a fixed path. The verifier entrypoint must call a Python helper in this repository, reuse the current evaluator logic, and write the mean pass@1 float to `/logs/verifier/reward.txt`.

   Expected outcome: a completed Harbor trial yields one numeric reward representing aggregate performance over the configured 10 tasks.

4. Add or update a Harbor job example for the single meta-task.

       export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"
       uv run harbor run -c jobs/medagentbench_meta.yaml

   Expected outcome: Harbor runs the single MedAgentBench meta-task and writes standard Harbor artifacts under `results/...`.

5. Validate end-to-end on the default 10-task slice.

   Expected outcome: the benchmark harness runs the configured tasks, the verifier computes mean pass@1, and the Harbor reward matches the score produced by the current MedAgentBench evaluator over the same task IDs.

## Validation and Acceptance

Acceptance is behavioral.

First, run the generator and inspect the output tree. There must be exactly one Harbor task directory at `tasks/medagentbench/`, and it must contain the Harbor-required files plus a task-selection config that defaults to `task1_1` through `task10_1`.

Second, run the repository test suite that covers the generator and verifier bridge:

    uv run pytest tests/ -q

Expected outcome: the suite passes, and added tests cover single-task generation, selection config correctness, verifier aggregation, and evaluator reuse.

Third, run a Harbor smoke test on the single meta-task with the custom Codex wrapper.

    export CODEX_AUTH_JSON="$(cat ~/.codex/auth.json)"
    uv run harbor run -c jobs/medagentbench_meta.yaml

Expected outcome: Harbor completes one trial, writes standard result artifacts under `results/...`, and the verifier reward is a float equal to the aggregate mean pass@1 across the configured 10 tasks.

Fourth, compare the Harbor reward against the score produced by the current MedAgentBench evaluator on the same task IDs. The values must match within normal floating-point formatting.

The change is complete when a contributor can regenerate the single Harbor MedAgentBench task, run Harbor directly against it, and observe an aggregate score matching the repository's current MedAgentBench rules for the configured 10-task slice.

## Idempotence and Recovery

The generator must be safe to run repeatedly. Re-running it should replace or refresh the generated Harbor meta-task deterministically without requiring manual cleanup. If generation fails partway through, the contributor should delete only the incomplete `tasks/medagentbench/` output and rerun the generator; the source manifests under `tasks/` must never be modified by the generator.

The harness and verifier bridge must be additive and must not break the existing `run.py` or `demo.py` evaluation path except where shared scoring helpers are intentionally extracted. If Harbor verification fails during development, the contributor should debug using the Harbor trial logs under `results/` rather than manually editing task outputs.

## Artifacts and Notes

Relevant current-state evidence:

    $ find tasks -maxdepth 4 -type f | sort
    tasks/README.md
    tasks/care_ordering/sources/medagentbench/std.yaml
    tasks/clinical_data_recording/sources/medagentbench/std.yaml
    tasks/data_aggregation/sources/medagentbench/std.yaml
    tasks/factual_qa/sources/medagentbench/std.yaml
    tasks/medication_reconciliation/sources/medagentbench/std.yaml

Representative selected benchmark slice:

    task1_1
    task2_1
    task3_1
    task4_1
    task5_1
    task6_1
    task7_1
    task8_1
    task9_1
    task10_1

Representative existing Harbor artifact shape from a successful local run:

    results/<run-id>/<trial>/agent/trajectory.json
    results/<run-id>/<trial>/result.json
    results/<run-id>/<trial>/verifier/reward.txt
    results/<run-id>/<trial>/verifier/test-stdout.txt

Those artifacts are the contract the Harbor verifier bridge must target.

## Interfaces and Dependencies

The implementation must continue using Harbor from the existing dependency pin in `pyproject.toml`. Do not add a second task-execution framework.

Define a generator entrypoint under `scripts/medagentbench/` that accepts an input manifest root and output Harbor task root. Even though only one Harbor task is generated, the interface should still support command-line regeneration from the repository root.

Define a harness entrypoint under `scripts/medagentbench/` that reads the Harbor task's benchmark selection config, runs the selected MedAgentBench cases, and writes machine-readable outputs for the verifier.

Define a verifier helper under `scripts/medagentbench/` that reads the harness outputs and returns an aggregate numeric score by invoking shared MedAgentBench evaluation logic.

If shared evaluator extraction helpers are needed, place them in `scripts/medagentbench/evaluator.py` or a nearby module so the Harbor verifier bridge and the existing evaluation CLI share the same semantics.


## Supersession Note

This plan is now superseded for MedAgentBench implementation details by `.agent/plans/harbor_raw_json_medagentbench_execplan.md`. The repository originally converted YAML-derived MedAgentBench tasks into one Harbor meta-task, but the canonical path has since changed: Harbor MedAgentBench is now generated directly from `scripts/medagentbench/assets/test_data_v2.json`, uses its own Harbor-specific evaluator, and treats the YAML manifest path only as a temporary compatibility layer during migration.
