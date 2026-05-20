FROM python:3.12-slim

# bash, curl/wget, flock for the bootstrap script. git is needed for the
# verifier-venv's `pip install git+...chexprompt`. ripgrep + jq are
# convenience tools the agent often needs.
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    wget \
    git \
    util-linux \
    jq \
    ripgrep \
    && rm -rf /var/lib/apt/lists/*

# Verifier-only venv: chexprompt + the legacy openai==0.28 SDK pin it
# requires. Isolated from anything the agent might install at runtime.
RUN python -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        'openai==0.28.0' \
        'aiolimiter>=1.1.0' \
        'git+https://github.com/microsoft/chexprompt.git@main'

# Don't write .pyc files anywhere — keeps the bind-mounted /tests dir free
# of root-owned __pycache__ residue.
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace

# Only the empty workspace skeleton is baked in; everything else is
# populated by the bootstrap service via named compose volumes.
COPY environment/workspace/ /workspace/
RUN mkdir -p /logs/verifier /data/patient

# No ENTRYPOINT/CMD: Harbor's docker-compose-build.yaml overrides main's
# command to ``sleep infinity`` so the container stays alive for the
# agent + verifier. The bootstrap service uses an explicit ``command:``
# in docker-compose.yaml to run /bootstrap.sh (bind-mounted) and exit.
