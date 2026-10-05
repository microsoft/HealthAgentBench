FROM python:3.12-slim@sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203

# Agent image contains only the fixed dataset and analysis tools.
RUN apt-get update && apt-get install -y --no-install-recommends bash ca-certificates curl jq tmux asciinema ripgrep wget util-linux && rm -rf /var/lib/apt/lists/*
# Node.js preinstalled from NodeSource (one package). Harbor's codex setup only
# apt-installs curl/node/npm/ripgrep when the commands are missing; Debian's
# ``npm`` meta-package pulls in ~700 debs and made five concurrent trials exceed
# the agent-setup timeout on shared hosts. Codex itself is still installed by
# Harbor at setup time (nvm + npm), reproducibly and per its own version pin.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash -     && apt-get install -y --no-install-recommends nodejs     && rm -rf /var/lib/apt/lists/*     && node --version && npm --version
# Analysis stack preinstalled: the agent phase has no internet beyond the model API
# (task.toml [agent] allowlist), so nothing can be pip-installed later.
RUN pip install --no-cache-dir pandas==3.0.1 pyarrow==23.0.1 duckdb==1.5.2 numpy==2.4.2 \
        polars==1.44.2 scipy==1.18.1 scikit-learn==1.9.1 matplotlib==3.10.8

ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace
COPY workspace/ /workspace/
COPY data/csv/ /workspace/data/csv/
RUN find /workspace/data/csv -type f -exec touch -d @0 {} + && \
    mkdir -p /workspace/submission
