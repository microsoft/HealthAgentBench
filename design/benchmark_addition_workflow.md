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

## 5. Add the Run Path

Every integrated benchmark needs a Harbor job config under `jobs/`.

Typical job responsibilities:

- point Harbor at the correct task root
- choose the supported agent configuration
- define trial count and run parameters appropriate for the benchmark

If the benchmark needs manual or iterative debugging support, add benchmark-specific helpers under `debug/<benchmark>/` and document them in `debug/<benchmark>/README.md`.

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

Optional updates:

- update `README.md` if the benchmark becomes a primary public entry point
- update `AGENTS.md` and `CLAUDE.md` only if repo-level agent instructions need to change

## 7. Validate the Integration

Before considering the benchmark integrated, validate the full Harbor path.

Recommended checks:

1. Benchmark-specific setup/bootstrap succeeds, if present.
2. Harbor task generation succeeds, if generation is part of the benchmark path.
3. The generated or committed task under `tasks/<benchmark>/` is runnable.
4. The Harbor job under `jobs/` runs successfully.
5. Benchmark-specific tests pass.
6. Benchmark-specific debug instructions are accurate if a debug path is documented.

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
- validation commands are documented and reproducible

If any of those are missing, the benchmark is not fully integrated yet.
