# Design Directory Instructions

This directory contains design docs, brainstorm notes, planning materials, and related-work notes for MedCLI.

## Purpose

Use `design/` for work that clarifies what to build before implementation:

- benchmark review and intake
- related-work reading notes
- task brainstorming
- scope and architecture discussions

## Benchmark Intake Workflow

The canonical repo-level workflow for benchmark implementation lives in `benchmark_addition_workflow.md`.

When adding or considering a benchmark, follow this order:

1. Add or update a benchmark note in `design/related_work/`.
2. Update `design/tasks.md` in the `Benchmarks` section.
3. If the benchmark needs adaptation or redesign, do design back-and-forth first and strongly consider an ExecPlan under `.agent/plans/` before implementation.
4. Only after that, implement repo changes under `scripts/<benchmark>/`, `tasks/<benchmark>/`, `jobs/`, and `debug/` as needed.

Do not add a benchmark directly to implementation paths without first creating the design context in `design/`. Use `benchmark_addition_workflow.md` as the canonical decision point for whether a benchmark is straightforward or adapted.

## Benchmark Tables in `design/tasks.md`

`design/tasks.md` is the source of truth for benchmark tracking in this directory.

- `Integrated` means the benchmark is already added to the repo/framework.
- `Planned` means we have agreed to add it, but implementation has not started or is not complete.
- `Review Queue` means it is relevant, but still needs discussion or review before commitment.

Rules:

- Only the `Integrated` table should include `Task Directory`.
- Every benchmark row must include a `Details` link to its `design/related_work/` entry.
- Keep benchmark descriptions short and factual.
- Keep the benchmark summary in `design/tasks.md` aligned with `tasks/README.md` once a benchmark is integrated.

## Related Work Notes

Related-work notes should be concise and decision-useful.

Include:

- citation or source link
- short summary
- why it is relevant to MedCLI
- implications for possible integration, if any

Prefer one file per paper, benchmark, or external evaluation artifact.

## Editing Guidance

- Preserve planning history where it is still useful.
- Prefer incremental updates over rewriting large design docs without need.
- Keep design docs implementation-aware, but do not treat them as code specs unless they are intended to drive implementation.
