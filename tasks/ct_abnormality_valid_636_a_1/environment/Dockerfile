FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends bash ca-certificates curl procps jq tmux asciinema ripgrep util-linux && rm -rf /var/lib/apt/lists/*
# Node.js preinstalled from NodeSource (one package). Harbor's codex setup only
# apt-installs curl/node/npm/ripgrep when the commands are missing; Debian's
# ``npm`` meta-package pulls in ~700 debs and made five concurrent trials exceed
# the agent-setup timeout on shared hosts. Codex itself is still installed by
# Harbor at setup time (nvm + npm), reproducibly and per its own version pin.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash -     && apt-get install -y --no-install-recommends nodejs     && rm -rf /var/lib/apt/lists/*     && node --version && npm --version

# huggingface_hub is needed only by the bootstrap service (CT-RATE download).
# Analysis stack preinstalled: the agent phase has no internet beyond the model API
# (task.toml [agent] allowlist), so nothing can be pip-installed later.
RUN pip install --no-cache-dir huggingface_hub==0.27.0 nibabel==5.4.2 \
        numpy==2.4.2 pillow==12.1.1 matplotlib==3.10.8 \
        scipy==1.18.1 scikit-image==0.26.0 opencv-python-headless==5.0.0.93 \
        scikit-learn==1.9.1 pandas==3.0.6

# Don't write .pyc files anywhere -- keeps the bind-mounted /tests dir free of
# root-owned __pycache__ residue that the host can't delete.
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace
# No COPY of environment/workspace/: that directory is intentionally empty
# for ct_abnormality (the bootstrap service populates /workspace/data/
# via a named compose volume at runtime), and Docker BuildKit refuses to
# COPY an empty directory ("failed to compute cache key").
# NOTE: bootstrap.sh and gold_derivation.py are deliberately NOT COPY'd into
# the image. They are bind-mounted into the *bootstrap* service only (see
# docker-compose.yaml), so the agent's ``main`` container can never read them.
# bootstrap.sh names the CT-RATE source + the exact HF report path, and
# gold_derivation.py is the full label-derivation recipe (phrase rules) — both
# would leak provenance/answers to a download-capable agent.
RUN mkdir -p /workspace/submission /workspace/data

# No ENTRYPOINT/CMD: Harbor's docker-compose-build.yaml overrides main's
# command to ``sleep infinity`` so the container stays alive. The bootstrap
# service uses an explicit ``command:`` in docker-compose.yaml to run
# /bootstrap.sh and exit cleanly.
