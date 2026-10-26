# mri_qa_set_06

Three knee MRI exams, two binary questions each (ACL tear, meniscal tear),
exact-match reward: all six answers must be correct. Exams come from the
MRNet knee MRI dataset (Stanford AIMI, via Redivis); labels are the released
validation-split labels, derived at run time by the bootstrap service.

## Run

```bash
uv run harbor run -p tasks/mri_qa_set_06 -a <agent> -m <vision-capable-model>
# whole category:
uv run harbor run -p tasks --include-task-name 'mri_qa_set_*' -a <agent> -m <model>
```

The `bootstrap` compose service runs first. On a cache miss it uses
`REDIVIS_API_TOKEN` from the repo-root `.env` to download only these three exams'
series and the public validation label tables into
`assets/mri_qa/assets/raw_cache/`, verifies every source checksum against
`environment/task_manifest.json`, derives the gold answers at run time, writes
them to `tests/gold.json` (gitignored), and stages the three arrays per exam into a
read-only volume for the agent under `/workspace/mri/exam_1..3/`. The token, the manifest,
the raw cache, and the gold never enter the agent image or its container.
