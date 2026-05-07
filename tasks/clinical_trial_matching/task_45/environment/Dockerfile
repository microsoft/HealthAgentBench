FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash ca-certificates curl util-linux \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir remotezip==0.12.3 pyyaml==6.0.3 filelock==3.18.0

# Don't write .pyc files anywhere — keeps the bind-mounted /tests dir
# free of root-owned __pycache__ residue that the host can't delete.
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace
COPY environment/workspace/ /workspace/
COPY environment/bootstrap.sh /bootstrap.sh
RUN chmod +x /bootstrap.sh \
    && mkdir -p /workspace/submission /workspace/data

# No ENTRYPOINT/CMD: Harbor's docker-compose-build.yaml overrides main's
# command to ``sleep infinity`` so the container stays alive. The bootstrap
# service uses an explicit ``command:`` in docker-compose.yaml to run
# /bootstrap.sh and exit cleanly. The bootstrap copies topic.txt and
# topic_id.txt from /workspace/ (built into the image at /workspace/) into
# the shared /workspace/data named volume so main sees them at the
# documented paths /workspace/data/topic.txt and /workspace/data/topic_id.txt.
