FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash ca-certificates curl util-linux \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir nibabel==5.4.2 pillow==10.4.0 huggingface_hub==0.27.0 numpy==2.3.4 pyyaml==6.0.2

# Don't write .pyc files anywhere -- keeps the bind-mounted /tests dir free of
# root-owned __pycache__ residue that the host can't delete.
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace
# No COPY of environment/workspace/: that directory is intentionally empty
# for ct_abnormality (the bootstrap service populates /workspace/data/
# via a named compose volume at runtime), and Docker BuildKit refuses to
# COPY an empty directory ("failed to compute cache key").
COPY environment/bootstrap.sh /bootstrap.sh
RUN chmod +x /bootstrap.sh \
    && mkdir -p /workspace/submission /workspace/data

# No ENTRYPOINT/CMD: Harbor's docker-compose-build.yaml overrides main's
# command to ``sleep infinity`` so the container stays alive. The bootstrap
# service uses an explicit ``command:`` in docker-compose.yaml to run
# /bootstrap.sh and exit cleanly.
