# Benchmark Addition Workflow

This document is the canonical repo-level workflow for adding a new benchmark to MedCLI.

MedCLI is Harbor-first. For any integrated benchmark:

- the canonical source assets live under `scripts/<benchmark>/assets/`
- the canonical runnable task artifact lives under `tasks/<benchmark>/`
- Harbor jobs under `jobs/` are the supported execution path

Do not add alternate benchmark runners outside the Harbor path.

## 1. Intake and Decision

Start in `design/` before touching implementation paths.

1. Add or update a note under `design/related_work/` for the benchmark, paper, or external artifact.
2. Add the benchmark to the `Benchmarks` section in `design/tasks.md`.
3. Place it in the correct table:
   - `Review Queue`: relevant, but not yet accepted for integration
   - `Planned`: accepted for integration, but not yet implemented
   - `Integrated`: implemented and supported in this repo
4. Make sure the `Details` column in `design/tasks.md` points to the `design/related_work/` note.

Only proceed to implementation once the benchmark is in `Planned` or `Integrated`.

## 2. Decide Whether the Benchmark Is Straightforward or Adapted

Before implementing the benchmark, decide whether it can be integrated mostly as-is or whether it needs redesign work.

A **straightforward benchmark** can be integrated without changing its basic task semantics. The environment shape, tool surface, agent-visible inputs, verifier contract, and scoring logic all map cleanly into the Harbor path with only mechanical setup work.

An **adapted benchmark** needs non-trivial design choices before implementation. Common signs include:

- the original task has to be reworded, split, or recomposed for Harbor
- the agent-visible interface changes relative to the original benchmark
- hidden answers, private verifier data, or scoring rules need redesign
- the benchmark needs a new environment, tool surface, or interaction model
- evaluator behavior cannot be carried over mechanically from the original release

If the benchmark is adapted, do design back-and-forth first and strongly consider writing an ExecPlan under `.agent/plans/` before editing `scripts/<benchmark>/`, `tasks/<benchmark>/`, `jobs/`, or `debug/`. Use `PLANS.md` as the rulebook for when an ExecPlan is appropriate. This is strongly recommended for adapted benchmarks because the design choices need to be made decision-complete before implementation starts.

For adapted benchmarks, knock down these decisions first:

1. What parts of the original benchmark remain unchanged.
2. What task semantics are being modified or simplified.
3. What the agent-visible interface will be.
4. What stays verifier-only or hidden from the agent.
5. Whether the environment, tool model, or job shape changes.
6. How evaluation and scoring map from the original benchmark into Harbor.
7. What new docs, artifacts, and validation commands will be required.

Two patterns are worth calling out explicitly because they recur in real integrations:

- If the original upstream path depends on live downloads or unstable external services, prefer staging the needed input in the task environment so the agent run itself is stable and reproducible.
- If environment setup is part of the benchmark skill being evaluated, ship the task with the setup tool available, but require the agent to perform the setup steps itself and make the verifier check for observable setup artifacts.

## 3. Create the Benchmark Integration

Create a benchmark-specific directory under `scripts/<benchmark>/`.

The expected structure is:

```text
scripts/<benchmark>/
├── README.md
├── assets/                  # canonical source data and metadata
├── setup.sh                 # optional idempotent bootstrap or download step
├── generate_harbor_tasks.py # task generator, if needed
├── normalization.py         # optional shared normalization helpers
└── <evaluator or helpers>   # benchmark-specific evaluation/runtime utilities
```

Use the benchmark directory to hold benchmark-specific logic only. Shared Harbor or repo-wide logic should stay outside the integration directory.

Implementation expectations:

1. Put canonical source assets in `scripts/<benchmark>/assets/`.
2. Add setup/bootstrap scripts only when the raw assets need downloading, validation, or normalization.
3. Add a Harbor task generator when the benchmark needs a generated task under `tasks/<benchmark>/`.
4. Add benchmark-specific evaluator or normalization code only when the benchmark requires it.

## 4. Generate the Harbor Task

The integrated benchmark task must live under `tasks/<benchmark>/`.

At minimum, the integrated task path should be able to serve as the canonical Harbor task artifact for the benchmark. Depending on the benchmark, this may be committed directly, generated from raw assets, or regenerated as part of the benchmark workflow.

Typical required pieces are:

- Harbor task config and instruction files
- verifier/test assets under the generated task tree
- any environment files needed by Harbor to run the benchmark task

If the benchmark is generated from raw assets, the generator should take source inputs from `scripts/<benchmark>/assets/` and produce the runnable task under `tasks/<benchmark>/`.

For adapted ETL-style benchmarks, it is often correct for the runnable output to be a generated directory tree rather than a JSON answer file. In that case, make the agent-facing output path explicit in both `instruction.md` and `task.toml`.

Every integrated benchmark should also have a **canonical manual replay path**: a short, explicit sequence a human can run inside a clean task environment to reproduce the intended task workflow without depending on agent behavior. This manual replay path is how you answer the question "is this an agent failure or a task failure?" when a Harbor run goes wrong.

## 5. Add the Run Path

Every integrated benchmark needs a Harbor job config under `jobs/`.

Typical job responsibilities:

- point Harbor at the correct task root
- choose the supported agent configuration
- define trial count and run parameters appropriate for the benchmark

If the benchmark needs manual or iterative debugging support, add benchmark-specific helpers under `debug/<benchmark>/` and document them in `debug/<benchmark>/README.md`.

If repo-level debug helpers or Harbor-adjacent tooling assume a particular task-environment shape, either make the benchmark satisfy those assumptions or document the divergence clearly in the benchmark-specific debug path. Do not let local debug-tooling drift masquerade as a task failure.

Keep the split clear:

- `debug/README.md`: generic Harbor debug workflow
- `debug/<benchmark>/README.md`: benchmark-specific debug flow

## 6. Update Documentation

Once the benchmark is integrated, update the user-facing docs that should know about it.

Required updates:

1. Add or update `scripts/<benchmark>/README.md` with benchmark-specific setup, generation, and runtime details.
2. Add or update `debug/<benchmark>/README.md` if the benchmark has a benchmark-specific debug path.
3. Update `tasks/README.md` once the benchmark is supported in this repo.
4. Update `design/tasks.md` so the benchmark is listed under `Integrated`.
5. Update `paper/benchmarks.md` with a new section describing the benchmark at the paper level. The section should answer: (a) what capability the task measures, (b) why it is medically meaningful, and (c) what the standardized MedCLI packaging contributes beyond the upstream resource. Match the style of existing sections.

When the verifier depends on a reference run, keep only a compact verifier-side summary in `scripts/<benchmark>/assets/`. Do not expose the gold reference output to the agent unless the benchmark is specifically about reproducing a known artifact byte-for-byte.

`paper/baselines.md` is an **auto-generated artifact** produced by `scripts/run_harbor_baselines*.py` — do not hand-edit its generated sections. Baselines become part of the paper only after a real Harbor run populates that file.

Optional updates:

- update `README.md` if the benchmark becomes a primary public entry point
- update `AGENTS.md` and `CLAUDE.md` only if repo-level agent instructions need to change
- update `paper/related_work.md` and `paper/draft.md` only when those paper sections need to reflect the new benchmark

## 7. Validate the Integration

Before considering the benchmark integrated, validate the full Harbor path.

When a run fails, debug it in isolation before changing the benchmark. The point of the debugging pass is to distinguish among four different failure classes:

- **agent failure**: the task works manually, but the agent did not execute the required steps correctly
- **task or environment failure**: the documented workflow cannot be replayed successfully in a clean task environment
- **verifier failure**: the task completes, but the verifier crashes or rejects semantically correct output
- **debug-tooling drift**: Harbor and the task are fine, but repo-local debug helpers assume a different environment shape

Use this sequence:

1. Inspect the Harbor run result and logs first.
2. Determine whether the run reached evaluation or failed before the verifier ran.
3. Reconstruct the agent's attempted command or workflow from the logs.
4. Replay the documented benchmark workflow manually in a clean task environment.
5. If the manual replay fails the same way, treat it as a task, environment, or verifier problem rather than an agent problem.
6. If the manual replay succeeds, treat the original failure as likely agent-execution or instruction-following failure.
7. Run the verifier separately against the manual output to isolate verifier bugs from task bugs.
8. If Harbor succeeds but local debug helpers fail, treat that as tooling drift and fix or document the helper path separately.

Recommended checks:

1. Benchmark-specific setup/bootstrap succeeds, if present.
2. Harbor task generation succeeds, if generation is part of the benchmark path.
3. The generated or committed task under `tasks/<benchmark>/` can be built from scratch as a clean task environment.
4. The benchmark's canonical workflow can be replayed manually inside that clean task environment using the same command shape or steps the agent is expected to follow.
5. The verifier can be run separately against that manual output inside the shipped task environment.
6. The Harbor job under `jobs/` runs successfully after the manual replay path and verifier path are both confirmed.
7. Benchmark-specific tests pass.
8. Benchmark-specific debug instructions are accurate if a debug path is documented.

For adapted benchmarks that require agent-run setup, include at least one test that proves the verifier fails when the expected setup artifacts are missing even if the rest of the workspace shape looks plausible.

For verifier design, prefer semantic checks over brittle incidental ones. Validate the invariants that matter for benchmark correctness, and avoid depending on formatting details, field ordering, or byte-level artifacts unless those details are explicitly part of the benchmark contract.

Typical validation commands will look like:

```bash
# Install dependencies
uv sync --all-extras

# Run benchmark-specific setup if needed
bash scripts/<benchmark>/setup.sh

# Generate the Harbor task if needed
uv run python scripts/<benchmark>/generate_harbor_tasks.py ...

# Run benchmark-specific tests
uv run pytest tests/... -q

# Run the benchmark job
uv run harbor run -c jobs/<benchmark>.yaml
```

Document the exact benchmark-specific commands in `scripts/<benchmark>/README.md`.

## 8. Definition of Done

A benchmark is integrated when all of the following are true:

- design context exists under `design/related_work/` and `design/tasks.md`
- canonical source assets exist under `scripts/<benchmark>/assets/`, if applicable
- canonical Harbor task artifact exists under `tasks/<benchmark>/`
- Harbor job config exists under `jobs/`
- benchmark-specific docs exist under `scripts/<benchmark>/README.md`
- benchmark is listed in `tasks/README.md`
- benchmark is described in `paper/benchmarks.md`
- the documented task workflow can be replayed manually in a clean task environment
- the verifier can run against that manual replay path using the shipped task environment
- validation commands are documented and reproducible

If any of those are missing, the benchmark is not fully integrated yet.


# Special Notice
1. Make sure the agent cannot see task name or original task ID so that it will not use this information to search for answers from internet. Also write in the instruction to not allow agents to search for answers from online. 
2. Make sure we can have the on-line data downloading capabilities when running each container so that the user can do a one-click run without having to set up things before the harbor run. Follow the example from ct_abnormality. Make sure to include any authentification instructions in ReadME in the scripts/task folder. 
3. Make sure we define success criterial so that we can aggregate pass rate as reward
4. Make sure we do not have hardcoded absolute paths as we want to make sure we can run the codebase in other machines. 


# What humans should check
Starting from a freshly pulled repo in a fresh directory in a fresh machine.

For each task: 
1. Check data setup and authentification from readme file from scripts/{task}/readme.md
2. Review the instruction.md for agent
3. Check that we don't have test leakage
a. remove task name and task ID in agent container so that the agent has no clue what the task is
b. make sure the instruction.md contain information on not allowing agent to look up answers from internet
c. make sure tests are not copied to the agent container

4. Set up 1 hour constraint for agent
5. Check that harbor run will download all required data and there is no data redistribution checked in into the repo
6. Run `uv harbor run` to test one model is working with a job/yaml file
7. Then run multitask baseline bash script to run all models each with 3 attempts and write results. Remember to export predictions and submissions
8. check model trajectory is present and that the model is not cheating. 
9. Review the evaluation is working as it is. 
10. Review the result directory, make sure failed attempts are counted and are not because of environment setup errors. 
11. All results are in /mnt mounted blob storage

For all tasks:
1. Create a job yaml file that we can run with `uv harbor run` for all tasks and try for one run and collect pass rate
