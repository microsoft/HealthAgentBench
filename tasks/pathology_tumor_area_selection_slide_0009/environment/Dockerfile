FROM python:3.12-slim

# Whole-slide-image tooling (openslide, tifffile, imagecodecs) and a general
# analysis stack are preinstalled; the agent works out how to read the slide.
# The verifier runs in Harbor's separate container (tests/Dockerfile) and needs
# none of this: its answer key carries precomputed tumor tiles.
RUN apt-get update && apt-get install -y --no-install-recommends bash ca-certificates curl procps jq tmux asciinema ripgrep wget util-linux && rm -rf /var/lib/apt/lists/*
# Node.js preinstalled from NodeSource (one package). Harbor's codex setup only
# apt-installs curl/node/npm/ripgrep when the commands are missing; Debian's
# ``npm`` meta-package pulls in ~700 debs and made five concurrent trials exceed
# the agent-setup timeout on shared hosts. Codex itself is still installed by
# Harbor at setup time (nvm + npm), reproducibly and per its own version pin.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash -     && apt-get install -y --no-install-recommends nodejs     && rm -rf /var/lib/apt/lists/*     && node --version && npm --version
# Analysis stack preinstalled: the agent phase has no internet beyond the model API
# (task.toml [agent] allowlist), so nothing can be pip-installed later.
RUN pip install --no-cache-dir openslide-bin==4.0.1.2 openslide-python==1.4.6 \
        tifffile==2026.9.20 imagecodecs==2026.8.16 requests==2.34.2 \
        numpy==2.4.2 pillow==12.1.1 matplotlib==3.10.8 \
        scipy==1.18.1 scikit-image==0.26.0 opencv-python-headless==5.0.0.93 \
        scikit-learn==1.9.1 pandas==3.0.6

ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /workspace

# Only the agent-visible workspace is baked into the image. The download URL
# lives in the bind-mounted bootstrap.sh (bootstrap service only), never here.
COPY environment/workspace/ /workspace/

RUN mkdir -p /logs/verifier /logs/artifacts /data/slide/current

# No ENTRYPOINT/CMD: Harbor keeps main alive; the bootstrap service runs
# bootstrap.sh via an explicit command in docker-compose.yaml.
