"""Generate Harbor task subdirectories for the clinical_trial_matching benchmark.

For each topic listed in ``assets/task_configs.yaml`` this writes::

    tasks/clinical_trial_matching/task_<topic_id>/
        task.toml
        instruction.md
        environment/
            Dockerfile
            docker-compose.yaml          # mounts assets/raw_cache rw
            entrypoint.sh                # per-topic flock + bootstrap
            workspace/
                topic.txt
                topic_id.txt
                trial_ncts.txt
                fetch_trials.py
        tests/
            test.sh
            verify.py
            harbor_evaluator.py
            qrels.txt

Pattern (mirrors ``mimic_report_gen``):

- The host directory ``scripts/clinical_trial_matching/assets/raw_cache/`` is
  bind-mounted into each container at ``/data/_cache`` (read-write so the
  entrypoint can fill in missing NCTs from the upstream zip snapshot, and
  subsequent task containers reuse what was downloaded).
- ``entrypoint.sh`` acquires a per-topic ``flock`` to serialize concurrent
  same-task containers from racing the same files. After the bootstrap
  finishes, the cache directory is ``chmod -R a-w``-ed so neither the
  agent nor any later step can mutate cached files.
- The host generator pre-stages NCTs into the cache when invoked
  (idempotent; uses ``filelock`` per NCT). If the user skips the host
  pre-stage, the entrypoint's container-side fetch fills the gap.

Usage::

    uv run python scripts/clinical_trial_matching/generate_harbor_tasks.py \\
        --output-root tasks/clinical_trial_matching [--refresh-topics] \\
        [--skip-prefetch]
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import yaml

# Make sibling fetch_trials.py importable when running this generator.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_trials import fetch_from_zip, DEFAULT_ZIP_URLS  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
ASSETS = SCRIPTS_DIR / "assets"
TASK_CONFIGS_PATH = ASSETS / "task_configs.yaml"
RAW_CACHE = ASSETS / "raw_cache"

PYTHON_BASE = "3.12-slim"
PIP_PINS = "remotezip==0.12.3 pyyaml==6.0.3 filelock==3.18.0"


# ---------------------------------------------------------------------------
# Upstream fetch (topics + qrels, ~1 MB combined)
# ---------------------------------------------------------------------------


def _http_get(url: str, user_agent: str) -> bytes:
    req = Request(url, headers={"User-Agent": user_agent})
    with urlopen(req, timeout=60) as resp:
        return resp.read()


def fetch_topics_and_qrels(
    topics_url: str,
    qrels_url: str,
    user_agent: str,
    cache_dir: Path,
    *,
    refresh: bool = False,
) -> tuple[Path, Path]:
    """Download topics + qrels into ``cache_dir`` if not already present."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    topics_path = cache_dir / "topics2021.xml"
    qrels_path = cache_dir / "qrels2021.txt"
    for url, dest in [(topics_url, topics_path), (qrels_url, qrels_path)]:
        if dest.exists() and dest.stat().st_size > 0 and not refresh:
            continue
        print(f"[generate] downloading {url}", flush=True)
        for attempt in range(3):
            try:
                dest.write_bytes(_http_get(url, user_agent))
                break
            except Exception as exc:  # noqa: BLE001
                if attempt == 2:
                    raise
                print(
                    f"[generate] {url}: attempt {attempt + 1} failed ({exc!r}); "
                    "retrying in 5s",
                    file=sys.stderr,
                )
                time.sleep(5)
    return topics_path, qrels_path


def parse_topics(topics_path: Path) -> dict[int, str]:
    tree = ET.parse(topics_path)
    return {
        int(t.get("number")): " ".join((t.text or "").split())
        for t in tree.findall("topic")
    }


def parse_qrels_for_topic(qrels_path: Path, topic_id: int) -> list[tuple[str, int]]:
    """Return [(nct_id, grade)] for the given topic."""
    rows: list[tuple[str, int]] = []
    for line in qrels_path.read_text().splitlines():
        parts = line.split()
        if len(parts) != 4:
            continue
        if int(parts[0]) != topic_id:
            continue
        rows.append((parts[2], int(parts[3])))
    return rows


# ---------------------------------------------------------------------------
# Host-side cache prefetch
# ---------------------------------------------------------------------------


def host_prefetch(
    nct_ids: set[str],
    cache_dir: Path,
    user_agent: str,
) -> None:
    """Populate ``cache_dir`` with the union of NCTs across all selected
    topics. Skips any NCT already present. Uses per-NCT filelocks
    (handled inside fetch_from_zip) so concurrent generator runs are
    safe.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    needed = {n for n in nct_ids if not (cache_dir / f"{n}.xml").is_file()}
    if not needed:
        print(
            f"[generate] cache already complete ({len(nct_ids)} NCTs)",
            flush=True,
        )
        return
    print(
        f"[generate] prefetching {len(needed)} of {len(nct_ids)} NCTs into "
        f"{cache_dir} (this is a one-time cost; ~1-2 min over 5 zip parts)",
        flush=True,
    )
    fetched: set[str] = set()
    # Each fetch_from_zip writes into ``cache_dir`` via its own ``cache_dir``
    # codepath. We pass ``out_dir = cache_dir`` so the network-extracted
    # bytes land directly into the host cache; no separate copy needed.
    for url in DEFAULT_ZIP_URLS:
        remaining = needed - fetched
        if not remaining:
            break
        t0 = time.time()
        got = fetch_from_zip(
            url,
            remaining,
            cache_dir,
            user_agent,
            cache_dir=cache_dir,
            retries=3,
            backoff_seconds=5.0,
        )
        fetched |= got
        print(
            f"[generate] {url.rsplit('/', 1)[-1]}: extracted {len(got)} "
            f"({len(fetched)}/{len(needed)}) in {time.time() - t0:.1f}s",
            flush=True,
        )
    missing = needed - fetched
    if missing:
        raise SystemExit(
            f"[generate] {len(missing)} NCTs not found in any zip part: "
            f"{sorted(missing)[:5]}..."
        )


# ---------------------------------------------------------------------------
# Per-task content
# ---------------------------------------------------------------------------


def build_task_toml(task_id: str) -> str:
    return f"""version = "1.0"

[metadata]
benchmark = "clinical_trial_matching"
mode = "etl-task"
task_id = "{task_id}"
submission_path = "/workspace/submission/ranked_trials.txt"

[verifier]
timeout_sec = 300.0

[agent]
timeout_sec = 3600.0

[environment]
build_timeout_sec = 1800.0
allow_internet = true
cpus = 2
memory_mb = 2048
storage_mb = 4096
gpus = 0
mcp_servers = []

[verifier.env]

[solution.env]
"""


INSTRUCTION_TEMPLATE = """# Patient-to-Trial Eligibility (Ranked)

You are working inside an environment that contains a single patient's
free-text admission note and a directory of clinical-trial documents.
**Identify every trial in the directory that the patient is eligible
for** -- meaning the patient meets all of the trial's inclusion
criteria *and* none of its exclusion criteria -- and **list them
ordered most-confident-first** (rank 1 = the trial you are most sure
the patient is eligible for).

## Inputs

- `/workspace/data/topic.txt` -- the patient case description.
- `/workspace/data/topic_id.txt` -- the integer topic ID for this task.
- `/workspace/data/trials/<NCT_ID>.xml` -- one file per candidate trial
  (typically 300-600 files). Each XML follows the standard
  ClinicalTrials.gov v1 schema with at least the following elements
  populated: `id_info/nct_id`, `brief_title`, `condition`, `intervention`,
  `eligibility/criteria/textblock`, `eligibility/gender`,
  `eligibility/minimum_age`, `eligibility/maximum_age`, and
  `brief_summary/textblock`.

## Output

Write a plain text file at
`/workspace/submission/ranked_trials.txt` containing **one NCT
identifier per line**: every trial you believe the patient is
eligible for, and **no** entries for trials where the patient is
excluded or unrelated. **The order matters** -- put the trial you
are most confident about on the first line, the next most confident
on the second, and so on. Make sure you flag all the eligible trials.

Format example (most-confident first):

    NCT00012345
    NCT00067890
    NCT00111222

Blank lines and lines starting with `#` are ignored. Duplicates are
de-duplicated keeping the first (highest-rank) occurrence.

## Rules

Solve the task using only the patient note and the trial documents in
`/workspace/data/trials/`, applying standard medical reasoning over the
patient's clinical history. Do not search the internet for benchmark
answers.
"""


def build_dockerfile() -> str:
    """The per-task Dockerfile.

    No build-time fetch -- everything bootstraps in the entrypoint where
    the host cache mount is available.
    """
    return f"""FROM python:{PYTHON_BASE}

RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        bash ca-certificates curl util-linux \\
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir {PIP_PINS}

# Don't write .pyc files anywhere — keeps the bind-mounted /tests dir
# free of root-owned __pycache__ residue that the host can't delete.
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace
COPY environment/workspace/ /workspace/
COPY environment/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \\
    && mkdir -p /workspace/submission /workspace/data \\
    && mv /workspace/topic.txt /workspace/data/topic.txt \\
    && mv /workspace/topic_id.txt /workspace/data/topic_id.txt

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
"""


def build_docker_compose(host_cache_path: Path) -> str:
    """Per-task docker-compose override that mounts the host cache rw.

    Harbor merges this with its base + build compose files, so the
    standard verifier/agent log mounts continue to work.
    """
    return f"""services:
  main:
    build:
      context: ..
      dockerfile: environment/Dockerfile
    volumes:
      - {host_cache_path}:/data/_cache:rw
    environment:
      - PYTHONUNBUFFERED=1
"""


ENTRYPOINT_SH = r"""#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Bootstrap the per-topic clinical-trial corpus.
#
# Mounts:
#   /data/_cache  -- host-side cache (rw). Shared across concurrent task
#                    containers.
#
# Behaviour:
#   1. Re-make the cache writable (a previous run may have chmod'd it ro).
#   2. Check if all NCTs for this topic are already in the cache.
#      - Warm path (all cached): run fetch_trials.py directly; pure cache
#        hits, no network, no global lock needed.
#      - Cold path (any missing): acquire a global download lock so that
#        concurrent containers serialize network downloads and do not
#        overwhelm the upstream zip server with simultaneous range requests.
#        Release the lock as soon as fetch_trials.py returns, before the
#        agent starts, so other containers can proceed in parallel.
#   3. Chmod -R a-w /data/_cache so the agent cannot mutate cached files.
#   4. Exec the agent.
# ---------------------------------------------------------------------------

CACHE=/data/_cache
TRIALS=/workspace/data/trials
LOCK_DIR="$CACHE/.locks"
GLOBAL_LOCK="$LOCK_DIR/global_download.lock"

mkdir -p "$CACHE" "$LOCK_DIR" "$TRIALS"

# Signal to Harbor agent setup that bootstrap is in progress.
# The Codex wrapper polls for .bootstrap_done before starting the agent.
touch /workspace/.bootstrap_required

# Re-grant write permissions for the lock window. (chmod is idempotent.)
chmod -R u+w "$CACHE" 2>/dev/null || true

# Returns 0 if every NCT ID listed in trial_ncts.txt has a non-empty XML
# file in the cache; non-zero otherwise.
_all_cached() {
    while IFS= read -r nct; do
        nct="${nct%%#*}"
        nct="${nct//[[:space:]]/}"
        [ -z "$nct" ] && continue
        [ -f "$CACHE/${nct}.xml" ] || return 1
    done < /workspace/trial_ncts.txt
    return 0
}

_fetch() {
    python3 /workspace/fetch_trials.py \
        --ids /workspace/trial_ncts.txt \
        --out "$TRIALS" \
        --cache-dir "$CACHE" \
        --user-agent "clinical_trial_matching/1.0 (medcli benchmark)" \
        --retries 3
}

if _all_cached; then
    # Warm path: every NCT is already cached — skip global lock so all
    # containers run fully concurrently.
    _fetch
else
    # Cold path: serialize downloads behind a global lock to avoid
    # hammering the upstream server with simultaneous range requests.
    exec 9>"$GLOBAL_LOCK"
    flock 9
    _fetch
    flock -u 9  # Release before exec so other containers can proceed.
fi

# Lock the cache to read-only so neither the agent nor any later step can
# mutate cached files. Tolerant to filesystem oddities.
chmod -R a-w "$CACHE" 2>/dev/null || true

# Signal that bootstrap is complete; the Codex setup_command will unblock.
touch /workspace/.bootstrap_done

exec "$@"
"""


TEST_SH = """#!/bin/bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
mkdir -p /logs/verifier /logs/artifacts
python verify.py
"""


VERIFY_PY = """#!/usr/bin/env python3
\"\"\"Per-task verifier entry point. Calls harbor_evaluator.evaluate.\"\"\"

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harbor_evaluator import evaluate  # noqa: E402


def main() -> None:
    submission = Path("/workspace/submission/ranked_trials.txt")
    qrels = Path(__file__).resolve().parent / "qrels.txt"
    log_dir = Path("/logs/verifier")
    score = evaluate(submission, qrels, log_dir)
    print(f"ndcg_at_10={score:.6f}")


if __name__ == "__main__":
    main()
"""


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def _ensure_clean(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_task(
    task_root: Path,
    topic_id: int,
    topic_text: str,
    judged: list[tuple[str, int]],
    host_cache_path: Path,
) -> None:
    _ensure_clean(task_root)
    task_id = f"task_{topic_id}"

    _write(task_root / "task.toml", build_task_toml(task_id))
    _write(task_root / "instruction.md", INSTRUCTION_TEMPLATE)

    env_dir = task_root / "environment"
    workspace = env_dir / "workspace"
    tests_dir = task_root / "tests"
    workspace.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    # Workspace files (agent-visible).
    _write(workspace / "topic.txt", topic_text)
    _write(workspace / "topic_id.txt", str(topic_id))
    nct_ids = sorted({nct for nct, _grade in judged})
    _write(workspace / "trial_ncts.txt", "\n".join(nct_ids) + "\n")
    shutil.copyfile(SCRIPTS_DIR / "fetch_trials.py", workspace / "fetch_trials.py")

    # Tests (verifier-only).
    qrels_lines = [f"{topic_id} 0 {nct} {grade}" for nct, grade in judged]
    _write(tests_dir / "qrels.txt", "\n".join(qrels_lines) + "\n")
    shutil.copyfile(SCRIPTS_DIR / "harbor_evaluator.py", tests_dir / "harbor_evaluator.py")
    _write(tests_dir / "verify.py", VERIFY_PY)
    test_sh_path = tests_dir / "test.sh"
    _write(test_sh_path, TEST_SH)
    test_sh_path.chmod(0o755)

    # Environment: Dockerfile + compose override + entrypoint.
    _write(env_dir / "Dockerfile", build_dockerfile())
    _write(env_dir / "docker-compose.yaml", build_docker_compose(host_cache_path))
    entry_path = env_dir / "entrypoint.sh"
    _write(entry_path, ENTRYPOINT_SH)
    entry_path.chmod(0o755)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        type=Path,
        default=REPO_ROOT / "tasks" / "clinical_trial_matching",
    )
    parser.add_argument(
        "--task-ids",
        type=str,
        default=None,
        help="Comma-separated topic IDs to generate (subset of selected_topics).",
    )
    parser.add_argument(
        "--refresh-topics",
        action="store_true",
        help="Force re-download of topics2021.xml and qrels2021.txt.",
    )
    parser.add_argument(
        "--skip-prefetch",
        action="store_true",
        help="Skip host-side NCT prefetch; the entrypoint will fill the cache "
             "lazily on first ``harbor run``. Faster generator pass.",
    )
    args = parser.parse_args(argv)

    cfg: dict[str, Any] = yaml.safe_load(TASK_CONFIGS_PATH.read_text())
    selected = list(cfg.get("selected_topics") or [])
    if args.task_ids:
        wanted = {int(t.strip()) for t in args.task_ids.split(",") if t.strip()}
        selected = [t for t in selected if t in wanted]
    if not selected:
        raise SystemExit("no topics selected; check task_configs.yaml or --task-ids")

    upstream = cfg.get("upstream", {}) or {}
    topics_path, qrels_path = fetch_topics_and_qrels(
        topics_url=upstream["topics_url"],
        qrels_url=upstream["qrels_url"],
        user_agent=upstream.get("user_agent", "clinical_trial_matching/1.0"),
        cache_dir=ASSETS / "raw_cache",
        refresh=args.refresh_topics,
    )

    topics = parse_topics(topics_path)

    args.output_root.mkdir(parents=True, exist_ok=True)
    _write(
        args.output_root / "README.md",
        "Generated by `scripts/clinical_trial_matching/generate_harbor_tasks.py`. "
        "Each `task_<topic_id>/` subdirectory is a Harbor task. The per-topic "
        "trial corpus is cached under `scripts/clinical_trial_matching/assets/"
        "raw_cache/` (gitignored, host-mounted into each container at "
        "`/data/_cache`); the entrypoint pulls anything missing from the "
        "upstream snapshot via HTTP range requests.\n",
    )

    # Collect every NCT we'll need across all selected tasks for host prefetch.
    union_ncts: set[str] = set()
    per_task: dict[int, list[tuple[str, int]]] = {}
    for topic_id in selected:
        if topic_id not in topics:
            raise SystemExit(f"topic {topic_id} not present in {topics_path}")
        judged = parse_qrels_for_topic(qrels_path, topic_id)
        if not judged:
            raise SystemExit(f"topic {topic_id} has no qrels rows")
        if not any(grade == 2 for _nct, grade in judged):
            raise SystemExit(f"topic {topic_id} has no eligible trials in qrels")
        per_task[topic_id] = judged
        for nct, _grade in judged:
            union_ncts.add(nct)

    # Host-side prefetch (one-time; idempotent).
    if not args.skip_prefetch:
        host_prefetch(
            union_ncts,
            cache_dir=RAW_CACHE,
            user_agent=upstream.get(
                "user_agent", "clinical_trial_matching/1.0"
            ),
        )

    for topic_id, judged in per_task.items():
        task_root = args.output_root / f"task_{topic_id}"
        print(
            f"[generate] task_{topic_id} ({len(judged)} judged trials)",
            flush=True,
        )
        _build_task(
            task_root,
            topic_id,
            topics[topic_id],
            judged,
            host_cache_path=RAW_CACHE.resolve(),
        )


if __name__ == "__main__":
    main()
