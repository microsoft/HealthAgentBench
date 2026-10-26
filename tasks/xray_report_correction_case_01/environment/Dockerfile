FROM python:3.12-slim

# bash, curl/wget, flock for the bootstrap script. ripgrep + jq are convenience
# tools for the agent. The chexprompt judge lives in the separate verifier image
# (tests/Dockerfile), not here.
RUN apt-get update && apt-get install -y --no-install-recommends bash ca-certificates curl procps jq tmux asciinema ripgrep wget util-linux && rm -rf /var/lib/apt/lists/*
# Node.js preinstalled from NodeSource (one package). Harbor's codex setup only
# apt-installs curl/node/npm/ripgrep when the commands are missing; Debian's
# ``npm`` meta-package pulls in ~700 debs and made five concurrent trials exceed
# the agent-setup timeout on shared hosts. Codex itself is still installed by
# Harbor at setup time (nvm + npm), reproducibly and per its own version pin.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash -     && apt-get install -y --no-install-recommends nodejs     && rm -rf /var/lib/apt/lists/*     && node --version && npm --version


# Analysis stack preinstalled: the agent phase has no internet beyond the model API
# (task.toml [agent] allowlist), so nothing can be pip-installed later.
RUN pip install --no-cache-dir numpy==2.4.2 pillow==12.1.1 matplotlib==3.10.8 \
        scipy==1.18.1 scikit-image==0.26.0 opencv-python-headless==5.0.0.93 \
        scikit-learn==1.9.1 pandas==3.0.6
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
