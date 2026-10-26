FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends bash ca-certificates curl procps jq tmux asciinema ripgrep util-linux unzip libgomp1 && rm -rf /var/lib/apt/lists/*
# Node.js preinstalled from NodeSource (one package). Harbor's codex setup only
# apt-installs curl/node/npm/ripgrep when the commands are missing; Debian's
# ``npm`` meta-package pulls in ~700 debs and made five concurrent trials exceed
# the agent-setup timeout on shared hosts. Codex itself is still installed by
# Harbor at setup time (nvm + npm), reproducibly and per its own version pin.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash -     && apt-get install -y --no-install-recommends nodejs     && rm -rf /var/lib/apt/lists/*     && node --version && npm --version

# numpy + pandas + a pinned scikit-learn are pre-installed: the verifier
# (tests/evaluate.py) computes AUROC/AUPRC/Brier with sklearn.metrics, and
# the pin keeps scoring identical across trials and machines. The agent phase
# has no internet beyond the model API (task.toml [agent] allowlist), so the
# modelling stack is preinstalled here as well. ``redivis`` lives in
# the separate bootstrap image (Dockerfile.bootstrap) because it drags in
# polars/pyarrow/geopandas and an unpinned scikit-learn.
RUN pip install --no-cache-dir \
    numpy==2.1.3 \
    pandas==2.2.3 \
    scikit-learn==1.5.2 \
    scipy==1.18.1 \
    lightgbm==4.7.0 \
    xgboost==3.4.1 \
    pyarrow==25.0.1 \
    polars==1.44.2 \
    matplotlib==3.10.8

ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace
# Nothing task-specific or source-revealing is baked into this image.
# The bootstrap entrypoint (bootstrap.sh) and the slicer (stage_data.py) are
# bind-mounted into the bootstrap service ONLY (see docker-compose.yaml); the
# scorer (evaluate.py) ships in tests/ (mounted only at verify time). So the
# agent's main container cannot read any of them.
RUN mkdir -p /workspace/submission /workspace/data

# No ENTRYPOINT/CMD: Harbor's docker-compose-build.yaml overrides main's
# command to ``sleep infinity``. The bootstrap service uses an explicit
# ``command:`` in docker-compose.yaml to run /bootstrap.sh and exit cleanly.
