# `ehr_data_quality_task_inconsistency_hard`

Version **2.0** of this EHR data-quality audit uses fixed, deliberately modified
MIMIC-IV Clinical Database Demo v2.2 tables. The generic hard prompt asks for all data-entry errors.
Its standard/hard counterpart uses identical data and labels.

Passing requires recall **1.0** over **32 injected clusters** and
row precision **at least 0.1**. Any accepted evidence row finds its cluster.
The labels include 64 injected-cluster entries and
110 reviewed source-error entries. Source errors earn precision
credit but are never required for recall. Further unlabeled anomalies may exist.

The agent image contains the eight fixed tables and analysis tools. Authoring
keys, raw source, source-review notes, and labels are excluded. The verifier runs
separately without network access. Both prompts use the same full-audit oracle,
with no hidden family selector.

See the [shared authoring documentation](../../scripts/ehr_data_quality/README.md)
for data attribution, regeneration, shortcut defenses, validation, and limitations.
The [artifact manifest](authoring/manifest.json) pins data and label checksums;
[source-review notes](authoring/source-review.csv) retain the adjudicated evidence.
Version 1 scores should not be compared directly with version 2.

```bash
uv run harbor run --path tasks/ehr_data_quality_task_inconsistency_hard --agent oracle
```
