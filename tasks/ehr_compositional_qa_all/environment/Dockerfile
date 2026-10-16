FROM python:3.12-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates curl procps ripgrep unzip \
    && rm -rf /var/lib/apt/lists/*
# Node.js preinstalled from NodeSource (one package) so agent CLIs (Codex, Claude
# Code) install quickly at setup; Debian's npm meta-package pulls in ~700 debs and
# conflicts with NodeSource nodejs when Harbor apt-installs missing dependencies.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash -     && apt-get install -y --no-install-recommends nodejs     && rm -rf /var/lib/apt/lists/*     && node --version && npm --version
RUN pip install --no-cache-dir duckdb==1.5.3 pandas==2.2.2 numpy==1.26.4 pyarrow==15.0.2
WORKDIR /workspace
# Only public inputs. Neither bootstrap code nor verifier labels enter this image.
COPY workspace/ /workspace/
RUN mkdir -p /workspace/data
CMD ["sleep", "infinity"]
